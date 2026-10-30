import 'dart:convert';

import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/session_storage.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/controllers/auth_controller.dart';
import 'package:club_matias_megias_navarro/features/notifications/data/services/push_device_api_client.dart';
import 'package:club_matias_megias_navarro/features/notifications/data/services/push_installation_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Map<String, dynamic> userJson() {
    return {
      'id': 7,
      'first_name': 'Matias',
      'last_name': 'Megias Navarro',
      'birth_date': '2000-01-15',
      'email': 'matias@example.com',
      'is_active': true,
      'created_at': '2026-10-23T12:00:00Z',
      'updated_at': '2026-10-23T13:00:00Z',
    };
  }

  Map<String, dynamic> pushDeviceJson() {
    return {
      'id': 15,
      'user_id': 7,
      'installation_id': 'firebase-installation-id',
      'platform': 'android',
      'is_active': true,
      'created_at': '2026-10-30T15:00:00Z',
      'updated_at': '2026-10-30T15:00:00Z',
    };
  }

  AuthApiClient createAuthApiClient() {
    return AuthApiClient(
      baseUrl: baseUrl,
      httpClient: MockClient((request) async {
        if (request.url.path == '/auth/login') {
          return http.Response(
            jsonEncode({
              'access_token': 'signed-access-token',
              'token_type': 'bearer',
            }),
            200,
          );
        }

        if (request.url.path == '/users/me') {
          expect(
            request.headers['Authorization'],
            'Bearer signed-access-token',
          );

          return http.Response(jsonEncode(userJson()), 200);
        }

        throw StateError(
          'Solicitud de autenticacion inesperada: '
          '${request.method} ${request.url.path}',
        );
      }),
    );
  }

  test('login registra el FID disponible con el JWT recibido', () async {
    var pushRequestCount = 0;

    final pushInstallationStore = PushInstallationStore();
    pushInstallationStore.update('firebase-installation-id');

    final pushDeviceApiClient = PushDeviceApiClient(
      baseUrl: baseUrl,
      httpClient: MockClient((request) async {
        pushRequestCount++;

        expect(request.method, 'POST');
        expect(request.url.toString(), '$baseUrl/push-devices');
        expect(request.headers['Authorization'], 'Bearer signed-access-token');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {
          'installation_id': 'firebase-installation-id',
          'platform': 'android',
        });

        return http.Response(jsonEncode(pushDeviceJson()), 201);
      }),
    );

    final controller = AuthController(
      apiClient: createAuthApiClient(),
      sessionStorage: MemorySessionStorage(),
      pushDeviceApiClient: pushDeviceApiClient,
      pushInstallationStore: pushInstallationStore,
    );

    final result = await controller.login(
      email: 'matias@example.com',
      password: 'ClaveSegura123',
    );

    expect(result, isTrue);
    expect(controller.status, AuthStatus.authenticated);
    expect(pushRequestCount, 1);

    controller.dispose();
    pushInstallationStore.dispose();
  });

  test('un error push no bloquea un login valido', () async {
    final pushInstallationStore = PushInstallationStore();
    pushInstallationStore.update('firebase-installation-id');

    final pushDeviceApiClient = PushDeviceApiClient(
      baseUrl: baseUrl,
      httpClient: MockClient((request) async {
        throw http.ClientException('Connection refused');
      }),
    );

    final controller = AuthController(
      apiClient: createAuthApiClient(),
      sessionStorage: MemorySessionStorage(),
      pushDeviceApiClient: pushDeviceApiClient,
      pushInstallationStore: pushInstallationStore,
    );

    final result = await controller.login(
      email: 'matias@example.com',
      password: 'ClaveSegura123',
    );

    expect(result, isTrue);
    expect(controller.status, AuthStatus.authenticated);
    expect(controller.currentUser?.id, 7);
    expect(controller.accessToken, 'signed-access-token');
    expect(controller.errorMessage, isNull);

    controller.dispose();
    pushInstallationStore.dispose();
  });

  test('initialize registra el FID al restaurar una sesion', () async {
    var pushRequestCount = 0;

    final pushInstallationStore = PushInstallationStore();
    pushInstallationStore.update('firebase-installation-id');

    final pushDeviceApiClient = PushDeviceApiClient(
      baseUrl: baseUrl,
      httpClient: MockClient((request) async {
        pushRequestCount++;

        expect(request.headers['Authorization'], 'Bearer signed-access-token');

        return http.Response(jsonEncode(pushDeviceJson()), 201);
      }),
    );

    final controller = AuthController(
      apiClient: createAuthApiClient(),
      sessionStorage: MemorySessionStorage(initialToken: 'signed-access-token'),
      pushDeviceApiClient: pushDeviceApiClient,
      pushInstallationStore: pushInstallationStore,
    );

    await controller.initialize();

    expect(controller.status, AuthStatus.authenticated);
    expect(pushRequestCount, 1);

    controller.dispose();
    pushInstallationStore.dispose();
  });

  test('registra un FID recibido despues del login', () async {
    var pushRequestCount = 0;

    final pushInstallationStore = PushInstallationStore();

    final pushDeviceApiClient = PushDeviceApiClient(
      baseUrl: baseUrl,
      httpClient: MockClient((request) async {
        pushRequestCount++;

        expect(request.headers['Authorization'], 'Bearer signed-access-token');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody['installation_id'], 'firebase-installation-id');

        return http.Response(jsonEncode(pushDeviceJson()), 201);
      }),
    );

    final controller = AuthController(
      apiClient: createAuthApiClient(),
      sessionStorage: MemorySessionStorage(),
      pushDeviceApiClient: pushDeviceApiClient,
      pushInstallationStore: pushInstallationStore,
    );

    final result = await controller.login(
      email: 'matias@example.com',
      password: 'ClaveSegura123',
    );

    expect(result, isTrue);
    expect(pushRequestCount, 0);

    pushInstallationStore.update('firebase-installation-id');

    await Future<void>.delayed(Duration.zero);

    expect(pushRequestCount, 1);

    controller.dispose();
    pushInstallationStore.dispose();
  });

  test('no registra un FID recibido sin sesion autenticada', () async {
    var pushRequestCount = 0;

    final pushInstallationStore = PushInstallationStore();

    final pushDeviceApiClient = PushDeviceApiClient(
      baseUrl: baseUrl,
      httpClient: MockClient((request) async {
        pushRequestCount++;

        return http.Response(jsonEncode(pushDeviceJson()), 201);
      }),
    );

    final controller = AuthController(
      apiClient: createAuthApiClient(),
      sessionStorage: MemorySessionStorage(),
      pushDeviceApiClient: pushDeviceApiClient,
      pushInstallationStore: pushInstallationStore,
    );

    pushInstallationStore.update('firebase-installation-id');

    await Future<void>.delayed(Duration.zero);

    expect(controller.status, AuthStatus.initializing);
    expect(pushRequestCount, 0);

    controller.dispose();
    pushInstallationStore.dispose();
  });
}
