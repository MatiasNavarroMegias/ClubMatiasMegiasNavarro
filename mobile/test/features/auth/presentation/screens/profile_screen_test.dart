import 'dart:convert';

import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/session_storage.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/controllers/auth_controller.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/screens/profile_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Map<String, dynamic> userJson({
    String firstName = 'Matias',
    String lastName = 'Megias Navarro',
    String birthDate = '2000-01-15',
    String email = 'matias@example.com',
  }) {
    return {
      'id': 7,
      'first_name': firstName,
      'last_name': lastName,
      'birth_date': birthDate,
      'email': email,
      'is_active': true,
      'created_at': '2026-10-23T12:00:00Z',
      'updated_at': '2026-10-24T12:00:00Z',
    };
  }

  Future<AuthController> createInitializedController({
    required MockClient httpClient,
    MemorySessionStorage? sessionStorage,
  }) async {
    final controller = AuthController(
      apiClient: AuthApiClient(httpClient: httpClient, baseUrl: baseUrl),
      sessionStorage:
          sessionStorage ??
          MemorySessionStorage(initialToken: 'stored-access-token'),
    );

    await controller.initialize();

    return controller;
  }

  Widget createTestApp(AuthController controller) {
    return MaterialApp(home: ProfileScreen(authController: controller));
  }

  Future<void> startEditing(WidgetTester tester) async {
    final editButton = find.byKey(const Key('profile-edit'));

    expect(editButton, findsOneWidget);

    await tester.tap(editButton);
    await tester.pumpAndSettle();
  }

  Future<void> scrollToButton(WidgetTester tester, Key buttonKey) async {
    final buttonFinder = find.byKey(buttonKey);

    await tester.scrollUntilVisible(
      buttonFinder,
      250,
      scrollable: find.byType(Scrollable).first,
    );

    await tester.pumpAndSettle();

    expect(buttonFinder, findsOneWidget);
  }

  testWidgets('muestra los datos del usuario autenticado', (tester) async {
    final controller = await createInitializedController(
      httpClient: MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.toString(), '$baseUrl/users/me');
        expect(request.headers['Authorization'], 'Bearer stored-access-token');

        return http.Response(jsonEncode(userJson()), 200);
      }),
    );

    addTearDown(controller.dispose);

    await tester.pumpWidget(createTestApp(controller));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('profile-screen')), findsOneWidget);
    expect(find.text('Matias Megias Navarro'), findsOneWidget);
    expect(find.text('matias@example.com'), findsWidgets);

    expect(find.byKey(const Key('profile-first-name-field')), findsOneWidget);
    expect(find.byKey(const Key('profile-last-name-field')), findsOneWidget);
    expect(find.byKey(const Key('profile-birth-date-field')), findsOneWidget);
    expect(find.byKey(const Key('profile-email-field')), findsOneWidget);

    expect(find.byKey(const Key('profile-edit')), findsOneWidget);

    // Este boton se encuentra al final del ListView y puede no estar
    // construido todavia dentro de la pantalla simulada del test.
    expect(find.byKey(const Key('profile-logout')), findsNothing);
  });

  testWidgets('mantiene el correo deshabilitado', (tester) async {
    final controller = await createInitializedController(
      httpClient: MockClient((request) async {
        return http.Response(jsonEncode(userJson()), 200);
      }),
    );

    addTearDown(controller.dispose);

    await tester.pumpWidget(createTestApp(controller));
    await tester.pumpAndSettle();

    final emailField = tester.widget<TextFormField>(
      find.byKey(const Key('profile-email-field')),
    );

    expect(emailField.enabled, isFalse);
    expect(find.text('El correo no puede modificarse.'), findsOneWidget);

    await startEditing(tester);

    final emailFieldDuringEdition = tester.widget<TextFormField>(
      find.byKey(const Key('profile-email-field')),
    );

    expect(emailFieldDuringEdition.enabled, isFalse);
  });

  testWidgets('habilita los campos editables al presionar editar perfil', (
    tester,
  ) async {
    final controller = await createInitializedController(
      httpClient: MockClient((request) async {
        return http.Response(jsonEncode(userJson()), 200);
      }),
    );

    addTearDown(controller.dispose);

    await tester.pumpWidget(createTestApp(controller));
    await tester.pumpAndSettle();

    final firstNameBeforeEdition = tester.widget<TextFormField>(
      find.byKey(const Key('profile-first-name-field')),
    );

    expect(firstNameBeforeEdition.enabled, isFalse);

    await startEditing(tester);

    final firstNameDuringEdition = tester.widget<TextFormField>(
      find.byKey(const Key('profile-first-name-field')),
    );
    final lastNameDuringEdition = tester.widget<TextFormField>(
      find.byKey(const Key('profile-last-name-field')),
    );
    final birthDateDuringEdition = tester.widget<TextFormField>(
      find.byKey(const Key('profile-birth-date-field')),
    );
    final emailDuringEdition = tester.widget<TextFormField>(
      find.byKey(const Key('profile-email-field')),
    );

    expect(firstNameDuringEdition.enabled, isTrue);
    expect(lastNameDuringEdition.enabled, isTrue);
    expect(birthDateDuringEdition.enabled, isTrue);
    expect(emailDuringEdition.enabled, isFalse);

    await scrollToButton(tester, const Key('profile-save'));

    expect(find.byKey(const Key('profile-save')), findsOneWidget);
    expect(find.byKey(const Key('profile-cancel')), findsOneWidget);
  });

  testWidgets('cancela la edicion y restaura los datos originales', (
    tester,
  ) async {
    final controller = await createInitializedController(
      httpClient: MockClient((request) async {
        return http.Response(jsonEncode(userJson()), 200);
      }),
    );

    addTearDown(controller.dispose);

    await tester.pumpWidget(createTestApp(controller));
    await tester.pumpAndSettle();

    await startEditing(tester);

    await tester.enterText(
      find.byKey(const Key('profile-first-name-field')),
      'Nombre Temporal',
    );

    expect(find.text('Nombre Temporal'), findsOneWidget);

    await scrollToButton(tester, const Key('profile-cancel'));

    await tester.tap(find.byKey(const Key('profile-cancel')));
    await tester.pumpAndSettle();

    final firstNameField = tester.widget<TextFormField>(
      find.byKey(const Key('profile-first-name-field')),
    );

    expect(firstNameField.controller?.text, 'Matias');
    expect(firstNameField.enabled, isFalse);

    expect(find.byKey(const Key('profile-edit')), findsOneWidget);
  });

  testWidgets('actualiza el nombre mediante PATCH users me', (tester) async {
    var getRequestCount = 0;
    var patchRequestCount = 0;

    final httpClient = MockClient((request) async {
      if (request.method == 'GET' && request.url.path == '/users/me') {
        getRequestCount++;

        return http.Response(jsonEncode(userJson()), 200);
      }

      if (request.method == 'PATCH' && request.url.path == '/users/me') {
        patchRequestCount++;

        expect(request.headers['Authorization'], 'Bearer stored-access-token');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {'first_name': 'Matias Actualizado'});
        expect(requestBody.containsKey('email'), isFalse);
        expect(requestBody.containsKey('last_name'), isFalse);
        expect(requestBody.containsKey('birth_date'), isFalse);

        return http.Response(
          jsonEncode(userJson(firstName: 'Matias Actualizado')),
          200,
        );
      }

      throw StateError(
        'Solicitud HTTP inesperada: '
        '${request.method} ${request.url}',
      );
    });

    final controller = await createInitializedController(
      httpClient: httpClient,
    );

    addTearDown(controller.dispose);

    await tester.pumpWidget(createTestApp(controller));
    await tester.pumpAndSettle();

    await startEditing(tester);

    await tester.enterText(
      find.byKey(const Key('profile-first-name-field')),
      'Matias Actualizado',
    );

    await scrollToButton(tester, const Key('profile-save'));

    await tester.tap(find.byKey(const Key('profile-save')));
    await tester.pumpAndSettle();

    expect(getRequestCount, 1);
    expect(patchRequestCount, 1);

    expect(controller.currentUser?.firstName, 'Matias Actualizado');
    expect(find.text('Matias Actualizado Megias Navarro'), findsOneWidget);
    expect(find.text('Perfil actualizado correctamente.'), findsOneWidget);
    expect(find.byKey(const Key('profile-edit')), findsOneWidget);
  });

  testWidgets('informa cuando se intenta guardar sin cambios', (tester) async {
    var patchRequestCount = 0;

    final controller = await createInitializedController(
      httpClient: MockClient((request) async {
        if (request.method == 'PATCH') {
          patchRequestCount++;
        }

        return http.Response(jsonEncode(userJson()), 200);
      }),
    );

    addTearDown(controller.dispose);

    await tester.pumpWidget(createTestApp(controller));
    await tester.pumpAndSettle();

    await startEditing(tester);

    await scrollToButton(tester, const Key('profile-save'));

    await tester.tap(find.byKey(const Key('profile-save')));
    await tester.pumpAndSettle();

    expect(patchRequestCount, 0);
    expect(find.text('No realizaste cambios en el perfil.'), findsOneWidget);
  });

  testWidgets('muestra el error recibido durante la actualizacion', (
    tester,
  ) async {
    final controller = await createInitializedController(
      httpClient: MockClient((request) async {
        if (request.method == 'GET') {
          return http.Response(jsonEncode(userJson()), 200);
        }

        if (request.method == 'PATCH') {
          return http.Response(
            jsonEncode({'detail': 'No se pudo actualizar el perfil.'}),
            400,
          );
        }

        throw StateError('Solicitud HTTP inesperada.');
      }),
    );

    addTearDown(controller.dispose);

    await tester.pumpWidget(createTestApp(controller));
    await tester.pumpAndSettle();

    await startEditing(tester);

    await tester.enterText(
      find.byKey(const Key('profile-first-name-field')),
      'Matias Modificado',
    );

    await scrollToButton(tester, const Key('profile-save'));

    await tester.tap(find.byKey(const Key('profile-save')));
    await tester.pumpAndSettle();

    expect(controller.status, AuthStatus.authenticated);
    expect(find.text('No se pudo actualizar el perfil.'), findsOneWidget);
  });

  testWidgets('cierra la sesion desde la pantalla de perfil', (tester) async {
    final sessionStorage = MemorySessionStorage(
      initialToken: 'stored-access-token',
    );

    final controller = await createInitializedController(
      httpClient: MockClient((request) async {
        return http.Response(jsonEncode(userJson()), 200);
      }),
      sessionStorage: sessionStorage,
    );

    addTearDown(controller.dispose);

    await tester.pumpWidget(createTestApp(controller));
    await tester.pumpAndSettle();

    await scrollToButton(tester, const Key('profile-logout'));

    await tester.tap(find.byKey(const Key('profile-logout')));
    await tester.pumpAndSettle();

    expect(controller.status, AuthStatus.unauthenticated);
    expect(controller.currentUser, isNull);
    expect(await sessionStorage.readToken(), isNull);
  });
}
