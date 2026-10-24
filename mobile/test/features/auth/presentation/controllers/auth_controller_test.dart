import 'dart:convert';

import 'package:club_matias_megias_navarro/features/auth/data/models/profile_update_data.dart';
import 'package:club_matias_megias_navarro/features/auth/data/models/registration_data.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/session_storage.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Map<String, dynamic> userJson({String firstName = 'Matias'}) {
    return {
      'id': 7,
      'first_name': firstName,
      'last_name': 'Megias Navarro',
      'birth_date': '2000-01-15',
      'email': 'matias@example.com',
      'is_active': true,
      'created_at': '2026-10-23T12:00:00Z',
      'updated_at': '2026-10-23T13:00:00Z',
    };
  }

  AuthController createController({
    required MockClient httpClient,
    required MemorySessionStorage sessionStorage,
  }) {
    return AuthController(
      apiClient: AuthApiClient(httpClient: httpClient, baseUrl: baseUrl),
      sessionStorage: sessionStorage,
    );
  }

  test('initialize deja la sesion como no autenticada sin token', () async {
    final controller = createController(
      httpClient: MockClient((request) async {
        throw StateError('No debe ejecutar solicitudes HTTP.');
      }),
      sessionStorage: MemorySessionStorage(),
    );

    await controller.initialize();

    expect(controller.status, AuthStatus.unauthenticated);
    expect(controller.currentUser, isNull);
    expect(controller.errorMessage, isNull);
    expect(controller.isLoading, isFalse);

    controller.dispose();
  });

  test('initialize restaura una sesion valida', () async {
    final httpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.toString(), '$baseUrl/users/me');
      expect(request.headers['Authorization'], 'Bearer stored-token');

      return http.Response(jsonEncode(userJson()), 200);
    });

    final sessionStorage = MemorySessionStorage(initialToken: 'stored-token');

    final controller = createController(
      httpClient: httpClient,
      sessionStorage: sessionStorage,
    );

    await controller.initialize();

    expect(controller.status, AuthStatus.authenticated);
    expect(controller.currentUser?.id, 7);
    expect(controller.currentUser?.email, 'matias@example.com');
    expect(controller.errorMessage, isNull);

    controller.dispose();
  });

  test('initialize elimina un token almacenado invalido', () async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({'detail': 'No se pudo validar la sesion.'}),
        401,
      );
    });

    final sessionStorage = MemorySessionStorage(initialToken: 'expired-token');

    final controller = createController(
      httpClient: httpClient,
      sessionStorage: sessionStorage,
    );

    await controller.initialize();

    expect(controller.status, AuthStatus.unauthenticated);
    expect(controller.currentUser, isNull);
    expect(await sessionStorage.readToken(), isNull);

    controller.dispose();
  });

  test('login guarda el token y obtiene el usuario', () async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      if (request.url.path == '/auth/login') {
        expect(request.method, 'POST');

        return http.Response(
          jsonEncode({'access_token': 'signed-token', 'token_type': 'bearer'}),
          200,
        );
      }

      if (request.url.path == '/users/me') {
        expect(request.method, 'GET');
        expect(request.headers['Authorization'], 'Bearer signed-token');

        return http.Response(jsonEncode(userJson()), 200);
      }

      throw StateError('Solicitud HTTP inesperada.');
    });

    final sessionStorage = MemorySessionStorage();

    final controller = createController(
      httpClient: httpClient,
      sessionStorage: sessionStorage,
    );

    final result = await controller.login(
      email: 'MATIAS@EXAMPLE.COM',
      password: 'ClaveSegura123',
    );

    expect(result, isTrue);
    expect(requestCount, 2);
    expect(controller.status, AuthStatus.authenticated);
    expect(controller.currentUser?.fullName, 'Matias Megias Navarro');
    expect(await sessionStorage.readToken(), 'signed-token');

    controller.dispose();
  });

  test('login conserva el error y no guarda una sesion invalida', () async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({'detail': 'Correo o contrasena incorrectos.'}),
        401,
      );
    });

    final sessionStorage = MemorySessionStorage();

    final controller = createController(
      httpClient: httpClient,
      sessionStorage: sessionStorage,
    );

    final result = await controller.login(
      email: 'matias@example.com',
      password: 'ClaveIncorrecta123',
    );

    expect(result, isFalse);
    expect(controller.status, AuthStatus.unauthenticated);
    expect(controller.currentUser, isNull);
    expect(controller.errorMessage, 'Correo o contrasena incorrectos.');
    expect(await sessionStorage.readToken(), isNull);

    controller.dispose();
  });

  test('register crea la cuenta e inicia sesion', () async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      if (request.url.path == '/auth/register') {
        expect(request.method, 'POST');

        return http.Response(jsonEncode(userJson()), 201);
      }

      if (request.url.path == '/auth/login') {
        expect(request.method, 'POST');

        return http.Response(
          jsonEncode({
            'access_token': 'registration-token',
            'token_type': 'bearer',
          }),
          200,
        );
      }

      if (request.url.path == '/users/me') {
        expect(request.headers['Authorization'], 'Bearer registration-token');

        return http.Response(jsonEncode(userJson()), 200);
      }

      throw StateError('Solicitud HTTP inesperada.');
    });

    final sessionStorage = MemorySessionStorage();

    final controller = createController(
      httpClient: httpClient,
      sessionStorage: sessionStorage,
    );

    final result = await controller.register(
      RegistrationData(
        firstName: 'Matias',
        lastName: 'Megias Navarro',
        birthDate: DateTime(2000, 1, 15),
        email: 'matias@example.com',
        password: 'ClaveSegura123',
      ),
    );

    expect(result, isTrue);
    expect(requestCount, 3);
    expect(controller.status, AuthStatus.authenticated);
    expect(controller.currentUser?.id, 7);
    expect(await sessionStorage.readToken(), 'registration-token');

    controller.dispose();
  });

  test('updateProfile reemplaza el usuario actual', () async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      if (request.method == 'GET') {
        return http.Response(jsonEncode(userJson()), 200);
      }

      if (request.method == 'PATCH') {
        expect(request.headers['Authorization'], 'Bearer stored-token');

        return http.Response(
          jsonEncode(userJson(firstName: 'Matias Actualizado')),
          200,
        );
      }

      throw StateError('Solicitud HTTP inesperada.');
    });

    final sessionStorage = MemorySessionStorage(initialToken: 'stored-token');

    final controller = createController(
      httpClient: httpClient,
      sessionStorage: sessionStorage,
    );

    await controller.initialize();

    final result = await controller.updateProfile(
      const ProfileUpdateData(firstName: 'Matias Actualizado'),
    );

    expect(result, isTrue);
    expect(requestCount, 2);
    expect(controller.status, AuthStatus.authenticated);
    expect(controller.currentUser?.firstName, 'Matias Actualizado');

    controller.dispose();
  });

  test('updateProfile cierra la sesion ante un error 401', () async {
    final httpClient = MockClient((request) async {
      if (request.method == 'GET') {
        return http.Response(jsonEncode(userJson()), 200);
      }

      return http.Response(
        jsonEncode({'detail': 'No se pudo validar la sesion.'}),
        401,
      );
    });

    final sessionStorage = MemorySessionStorage(initialToken: 'stored-token');

    final controller = createController(
      httpClient: httpClient,
      sessionStorage: sessionStorage,
    );

    await controller.initialize();

    final result = await controller.updateProfile(
      const ProfileUpdateData(firstName: 'Matias Actualizado'),
    );

    expect(result, isFalse);
    expect(controller.status, AuthStatus.unauthenticated);
    expect(controller.currentUser, isNull);
    expect(await sessionStorage.readToken(), isNull);

    controller.dispose();
  });

  test('refreshProfile actualiza los datos visibles', () async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      return http.Response(
        jsonEncode(
          userJson(
            firstName: requestCount == 1 ? 'Matias' : 'Matias Actualizado',
          ),
        ),
        200,
      );
    });

    final controller = createController(
      httpClient: httpClient,
      sessionStorage: MemorySessionStorage(initialToken: 'stored-token'),
    );

    await controller.initialize();

    expect(controller.currentUser?.firstName, 'Matias');

    final result = await controller.refreshProfile();

    expect(result, isTrue);
    expect(controller.currentUser?.firstName, 'Matias Actualizado');

    controller.dispose();
  });

  test('logout elimina el token y el usuario', () async {
    final sessionStorage = MemorySessionStorage(initialToken: 'stored-token');

    final controller = createController(
      httpClient: MockClient((request) async {
        return http.Response(jsonEncode(userJson()), 200);
      }),
      sessionStorage: sessionStorage,
    );

    await controller.initialize();
    await controller.logout();

    expect(controller.status, AuthStatus.unauthenticated);
    expect(controller.currentUser, isNull);
    expect(controller.errorMessage, isNull);
    expect(await sessionStorage.readToken(), isNull);

    controller.dispose();
  });

  test('clearError elimina el mensaje visible', () async {
    final controller = createController(
      httpClient: MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'Correo o contrasena incorrectos.'}),
          401,
        );
      }),
      sessionStorage: MemorySessionStorage(),
    );

    await controller.login(email: 'matias@example.com', password: 'incorrecta');

    expect(controller.errorMessage, isNotNull);

    controller.clearError();

    expect(controller.errorMessage, isNull);

    controller.dispose();
  });
}
