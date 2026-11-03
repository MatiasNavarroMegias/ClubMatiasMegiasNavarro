import 'dart:async';

import 'package:club_matias_megias_navarro/app/app.dart';
import 'package:club_matias_megias_navarro/core/services/push_bootstrap.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/session_storage.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

void main() {
  testWidgets('ClubApp aparece aunque el arranque push quede pendiente', (
    tester,
  ) async {
    final authController = AuthController(
      apiClient: AuthApiClient(
        httpClient: MockClient((request) async {
          throw StateError('No debe realizar solicitudes sin sesion.');
        }),
        baseUrl: 'http://example.test',
      ),
      sessionStorage: MemorySessionStorage(),
    );
    addTearDown(authController.dispose);

    final pushInitialization = initializeFirebaseAndPush(
      initializeFirebase: () async {},
      registerBackgroundHandler: () {},
      initializePush: () => Completer<void>().future,
      timeout: const Duration(milliseconds: 20),
    );

    await tester.pumpWidget(ClubApp(authController: authController));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login-submit')), findsOneWidget);
    await pushInitialization;
  });

  testWidgets('un error push no modifica el arbol visual de ClubApp', (
    tester,
  ) async {
    final controller = AuthController(
      apiClient: AuthApiClient(
        httpClient: MockClient((request) async {
          throw StateError('No debe realizar solicitudes sin sesion.');
        }),
        baseUrl: 'http://example.test',
      ),
      sessionStorage: MemorySessionStorage(),
    );
    addTearDown(controller.dispose);

    final pushInitialization = initializeFirebaseAndPush(
      initializeFirebase: () async {},
      registerBackgroundHandler: () {},
      initializePush: () async {
        throw StateError('Firebase no disponible');
      },
    );

    await tester.pumpWidget(ClubApp(authController: controller));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login-email-field')), findsOneWidget);
    expect(find.byKey(const Key('login-submit')), findsOneWidget);
    await pushInitialization;
  });

  test('un arranque push demorado termina por timeout', () async {
    final stopwatch = Stopwatch()..start();

    await initializeFirebaseAndPush(
      initializeFirebase: () async {},
      registerBackgroundHandler: () {},
      initializePush: () => Completer<void>().future,
      timeout: const Duration(milliseconds: 20),
    );

    stopwatch.stop();

    expect(stopwatch.elapsed, lessThan(const Duration(seconds: 1)));
  });
}
