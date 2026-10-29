import 'dart:convert';

import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/screens/password_recovery_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Widget createTestApp({required AuthApiClient apiClient}) {
    return MaterialApp(home: PasswordRecoveryScreen(apiClient: apiClient));
  }

  testWidgets('muestra inicialmente el formulario de correo', (tester) async {
    final apiClient = AuthApiClient(
      httpClient: MockClient((request) async {
        throw StateError('No debe realizar solicitudes HTTP.');
      }),
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));

    expect(find.byKey(const Key('password-recovery-screen')), findsOneWidget);
    expect(
      find.byKey(const Key('password-recovery-email-field')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('password-recovery-request-submit')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('password-recovery-code-field')), findsNothing);
    expect(find.text('Recuperar contrasena'), findsWidgets);
  });

  testWidgets('valida el correo antes de consultar la API', (tester) async {
    var requestCount = 0;

    final apiClient = AuthApiClient(
      httpClient: MockClient((request) async {
        requestCount++;

        return http.Response(
          jsonEncode({'message': 'Mensaje inesperado.'}),
          200,
        );
      }),
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));

    await tester.tap(find.byKey(const Key('password-recovery-request-submit')));
    await tester.pump();

    expect(find.text('Ingresa tu correo electronico.'), findsOneWidget);
    expect(requestCount, 0);

    await tester.enterText(
      find.byKey(const Key('password-recovery-email-field')),
      'correo-invalido',
    );

    await tester.tap(find.byKey(const Key('password-recovery-request-submit')));
    await tester.pump();

    expect(find.text('Ingresa un correo electronico valido.'), findsOneWidget);
    expect(requestCount, 0);
  });

  testWidgets('solicita el codigo y avanza a la confirmacion', (tester) async {
    var requestCount = 0;

    final apiClient = AuthApiClient(
      httpClient: MockClient((request) async {
        requestCount++;

        expect(request.method, 'POST');
        expect(request.url.path, '/auth/password-recovery/request');

        final body = jsonDecode(request.body) as Map<String, dynamic>;

        expect(body, {'email': 'matias@example.com'});

        return http.Response(
          jsonEncode({
            'message':
                'Si el correo pertenece a una cuenta, '
                'recibiras instrucciones para recuperar '
                'la contrasena.',
          }),
          200,
        );
      }),
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));

    await tester.enterText(
      find.byKey(const Key('password-recovery-email-field')),
      ' MATIAS@EXAMPLE.COM ',
    );

    await tester.tap(find.byKey(const Key('password-recovery-request-submit')));
    await tester.pumpAndSettle();

    expect(requestCount, 1);
    expect(
      find.byKey(const Key('password-recovery-code-field')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('password-recovery-new-password-field')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('password-recovery-confirmation-field')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('password-recovery-confirm-submit')),
      findsOneWidget,
    );
    expect(
      find.text(
        'Si el correo pertenece a una cuenta, '
        'recibiras instrucciones para recuperar '
        'la contrasena.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('permite cambiar el correo despues de solicitar el codigo', (
    tester,
  ) async {
    final apiClient = AuthApiClient(
      httpClient: MockClient((request) async {
        return http.Response(
          jsonEncode({
            'message':
                'Si el correo pertenece a una cuenta, '
                'recibiras instrucciones para recuperar '
                'la contrasena.',
          }),
          200,
        );
      }),
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));

    await tester.enterText(
      find.byKey(const Key('password-recovery-email-field')),
      'matias@example.com',
    );

    await tester.tap(find.byKey(const Key('password-recovery-request-submit')));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('password-recovery-code-field')),
      '48392175',
    );

    await tester.enterText(
      find.byKey(const Key('password-recovery-new-password-field')),
      'NuevaClave123',
    );

    final changeEmailButton = find.byKey(
      const Key('password-recovery-change-email'),
    );

    tester.testTextInput.hide();
    await tester.pumpAndSettle();

    await tester.ensureVisible(changeEmailButton);
    await tester.pumpAndSettle();

    await tester.tap(changeEmailButton);
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('password-recovery-email-field')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('password-recovery-code-field')), findsNothing);

    final emailField = tester.widget<TextFormField>(
      find.byKey(const Key('password-recovery-email-field')),
    );

    expect(emailField.controller?.text, 'matias@example.com');
  });

  testWidgets('valida codigo y contrasenas antes de confirmar', (tester) async {
    var confirmationRequestCount = 0;

    final apiClient = AuthApiClient(
      httpClient: MockClient((request) async {
        if (request.url.path.endsWith('/request')) {
          return http.Response(
            jsonEncode({
              'message':
                  'Si el correo pertenece a una cuenta, '
                  'recibiras instrucciones para recuperar '
                  'la contrasena.',
            }),
            200,
          );
        }

        confirmationRequestCount++;

        return http.Response(
          jsonEncode({
            'message': 'La contrasena fue actualizada correctamente.',
          }),
          200,
        );
      }),
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));

    await tester.enterText(
      find.byKey(const Key('password-recovery-email-field')),
      'matias@example.com',
    );

    await tester.tap(find.byKey(const Key('password-recovery-request-submit')));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('password-recovery-code-field')),
      '123',
    );

    await tester.enterText(
      find.byKey(const Key('password-recovery-new-password-field')),
      'nuevaclave123',
    );

    await tester.enterText(
      find.byKey(const Key('password-recovery-confirmation-field')),
      'otraClave456',
    );

    final confirmButton = find.byKey(
      const Key('password-recovery-confirm-submit'),
    );

    tester.testTextInput.hide();
    await tester.pumpAndSettle();

    await tester.ensureVisible(confirmButton);
    await tester.pumpAndSettle();

    await tester.tap(confirmButton);
    await tester.pump();

    expect(find.text('Ingresa el codigo de ocho digitos.'), findsOneWidget);
    expect(
      find.text('La contrasena debe incluir una letra mayuscula.'),
      findsOneWidget,
    );
    expect(find.text('Las contrasenas no coinciden.'), findsOneWidget);
    expect(confirmationRequestCount, 0);
  });

  testWidgets('confirma la recuperacion y vuelve a la pantalla anterior', (
    tester,
  ) async {
    var confirmationRequestCount = 0;

    final apiClient = AuthApiClient(
      httpClient: MockClient((request) async {
        if (request.url.path.endsWith('/request')) {
          return http.Response(
            jsonEncode({
              'message':
                  'Si el correo pertenece a una cuenta, '
                  'recibiras instrucciones para recuperar '
                  'la contrasena.',
            }),
            200,
          );
        }

        confirmationRequestCount++;

        expect(request.url.path, '/auth/password-recovery/confirm');

        final body = jsonDecode(request.body) as Map<String, dynamic>;

        expect(body, {
          'email': 'matias@example.com',
          'code': '48392175',
          'new_password': 'NuevaClave123',
          'new_password_confirmation': 'NuevaClave123',
        });

        return http.Response(
          jsonEncode({
            'message': 'La contrasena fue actualizada correctamente.',
          }),
          200,
        );
      }),
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) {
            return Scaffold(
              body: Center(
                child: FilledButton(
                  key: const Key('open-password-recovery'),
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (context) {
                          return PasswordRecoveryScreen(apiClient: apiClient);
                        },
                      ),
                    );
                  },
                  child: const Text('Abrir recuperacion'),
                ),
              ),
            );
          },
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('open-password-recovery')));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('password-recovery-email-field')),
      'matias@example.com',
    );

    await tester.tap(find.byKey(const Key('password-recovery-request-submit')));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('password-recovery-code-field')),
      '48392175',
    );

    await tester.enterText(
      find.byKey(const Key('password-recovery-new-password-field')),
      'NuevaClave123',
    );

    await tester.enterText(
      find.byKey(const Key('password-recovery-confirmation-field')),
      'NuevaClave123',
    );

    final confirmButton = find.byKey(
      const Key('password-recovery-confirm-submit'),
    );

    tester.testTextInput.hide();
    await tester.pumpAndSettle();

    await tester.ensureVisible(confirmButton);
    await tester.pumpAndSettle();

    await tester.tap(confirmButton);
    await tester.pumpAndSettle();

    expect(confirmationRequestCount, 1);
    expect(find.byKey(const Key('password-recovery-screen')), findsNothing);
    expect(find.byKey(const Key('open-password-recovery')), findsOneWidget);
  });
}
