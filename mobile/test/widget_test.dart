import 'package:club_matias_megias_navarro/app/app.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/session_storage.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  testWidgets('muestra el login cuando no existe una sesion almacenada', (
    tester,
  ) async {
    final httpClient = MockClient((request) async {
      throw StateError('No debe realizar solicitudes sin un token almacenado.');
    });

    final authController = AuthController(
      apiClient: AuthApiClient(
        httpClient: httpClient,
        baseUrl: 'http://example.test',
      ),
      sessionStorage: MemorySessionStorage(),
    );

    addTearDown(authController.dispose);

    await tester.pumpWidget(ClubApp(authController: authController));

    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login-email-field')), findsOneWidget);
    expect(find.byKey(const Key('login-password-field')), findsOneWidget);
    expect(find.byKey(const Key('login-submit')), findsOneWidget);
    expect(find.byKey(const Key('login-show-registration')), findsOneWidget);
    expect(find.text('Iniciar sesion'), findsOneWidget);
    expect(find.byKey(const Key('authenticated-home')), findsNothing);
  });

  testWidgets('permite navegar entre login y registro', (tester) async {
    final authController = AuthController(
      apiClient: AuthApiClient(
        httpClient: MockClient((request) async {
          return http.Response('{}', 500);
        }),
        baseUrl: 'http://example.test',
      ),
      sessionStorage: MemorySessionStorage(),
    );

    addTearDown(authController.dispose);

    await tester.pumpWidget(ClubApp(authController: authController));

    await tester.pumpAndSettle();

    final showRegistrationButton = find.byKey(
      const Key('login-show-registration'),
    );

    expect(showRegistrationButton, findsOneWidget);

    await tester.tap(showRegistrationButton);
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('registration-first-name-field')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('registration-last-name-field')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('registration-submit')), findsOneWidget);

    final showLoginButton = find.byKey(const Key('registration-show-login'));

    expect(showLoginButton, findsOneWidget);

    // El formulario de registro es mas alto que la pantalla simulada
    // del test. Se desplaza hasta el boton antes de intentar tocarlo.
    await tester.ensureVisible(showLoginButton);
    await tester.pumpAndSettle();

    await tester.tap(showLoginButton);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login-email-field')), findsOneWidget);
    expect(find.byKey(const Key('login-password-field')), findsOneWidget);
  });
}
