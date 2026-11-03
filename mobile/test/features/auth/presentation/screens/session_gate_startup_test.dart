import 'dart:async';

import 'package:club_matias_megias_navarro/app/app.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/session_storage.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

void main() {
  testWidgets('ClubApp real muestra login sin token', (tester) async {
    final controller = _controller(MemorySessionStorage());
    addTearDown(controller.dispose);

    await tester.pumpWidget(ClubApp(authController: controller));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login-email-field')), findsOneWidget);
    expect(find.byKey(const Key('login-password-field')), findsOneWidget);
    expect(find.byKey(const Key('login-submit')), findsOneWidget);
  });

  testWidgets('una restauracion demorada muestra carga visible', (
    tester,
  ) async {
    final controller = _controller(_HangingSessionStorage());
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      ClubApp(
        authController: controller,
        initializationTimeout: const Duration(milliseconds: 20),
      ),
    );
    await tester.pump(const Duration(milliseconds: 1));

    expect(find.byKey(const Key('session-initializing')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 30));
    expect(find.byKey(const Key('login-submit')), findsOneWidget);
  });

  testWidgets('un error de restauracion deja disponible el login', (
    tester,
  ) async {
    final controller = _controller(_FailingSessionStorage());
    addTearDown(controller.dispose);

    await tester.pumpWidget(ClubApp(authController: controller));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login-email-field')), findsOneWidget);
    expect(find.byKey(const Key('login-password-field')), findsOneWidget);
    expect(find.byKey(const Key('login-submit')), findsOneWidget);
  });
}

AuthController _controller(SessionStorage storage) {
  return AuthController(
    apiClient: AuthApiClient(
      httpClient: MockClient((request) async {
        throw StateError('No debe realizar solicitudes sin sesion.');
      }),
      baseUrl: 'http://example.test',
    ),
    sessionStorage: storage,
  );
}

class _HangingSessionStorage implements SessionStorage {
  @override
  Future<String?> readToken() => Completer<String?>().future;

  @override
  Future<void> saveToken(String token) async {}

  @override
  Future<void> deleteToken() async {}
}

class _FailingSessionStorage implements SessionStorage {
  @override
  Future<String?> readToken() async {
    throw StateError('Secure storage no disponible');
  }

  @override
  Future<void> saveToken(String token) async {}

  @override
  Future<void> deleteToken() async {}
}
