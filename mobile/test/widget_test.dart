import 'package:club_matias_megias_navarro/app/app.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/session_storage.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'dart:convert';

import 'package:club_matias_megias_navarro/features/reservations/data/services/reservation_api_client.dart';
import 'package:club_matias_megias_navarro/features/venues/data/services/venue_api_client.dart';

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

  testWidgets('abre la pestaña de reservas con la sesion autenticada', (
    tester,
  ) async {
    const accessToken = 'stored-access-token';
    const baseUrl = 'http://example.test';

    final authHttpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/users/me');
      expect(request.headers['Authorization'], 'Bearer $accessToken');

      return http.Response(
        jsonEncode({
          'id': 7,
          'first_name': 'Matias',
          'last_name': 'Megias Navarro',
          'birth_date': '2000-01-15',
          'email': 'matias@example.com',
          'is_active': true,
          'created_at': '2026-10-23T12:00:00Z',
          'updated_at': '2026-10-23T13:00:00Z',
        }),
        200,
      );
    });

    final venueHttpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/venues');

      return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
    });

    var reservationRequestCount = 0;

    final reservationHttpClient = MockClient((request) async {
      reservationRequestCount++;

      expect(request.method, 'GET');
      expect(request.url.path, '/reservations/upcoming');
      expect(request.headers['Authorization'], 'Bearer $accessToken');

      return http.Response(
        jsonEncode([
          {
            'id': 15,
            'user_id': 7,
            'sports_space_id': 8,
            'start_at': '2026-11-03T18:00:00-03:00',
            'end_at': '2026-11-03T19:00:00-03:00',
            'status': 'confirmed',
            'cancelled_at': null,
            'created_at': '2026-10-29T12:00:00Z',
            'updated_at': '2026-10-29T12:00:00Z',
          },
        ]),
        200,
      );
    });

    final authController = AuthController(
      apiClient: AuthApiClient(httpClient: authHttpClient, baseUrl: baseUrl),
      sessionStorage: MemorySessionStorage(initialToken: accessToken),
    );

    final venueApiClient = VenueApiClient(
      httpClient: venueHttpClient,
      baseUrl: baseUrl,
    );

    final reservationApiClient = ReservationApiClient(
      httpClient: reservationHttpClient,
      baseUrl: baseUrl,
    );

    addTearDown(authController.dispose);
    addTearDown(venueApiClient.close);
    addTearDown(reservationApiClient.close);

    await tester.pumpWidget(
      ClubApp(
        authController: authController,
        venueApiClient: venueApiClient,
        reservationApiClient: reservationApiClient,
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('authenticated-bottom-navigation')),
      findsOneWidget,
    );
    expect(reservationRequestCount, 1);

    await tester.tap(find.byKey(const Key('navigation-reservations')));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('upcoming-reservations-screen')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('upcoming-reservations-list')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('upcoming-reservation-15')),
      findsOneWidget,
    );
    expect(find.text('Mis reservas'), findsOneWidget);
    expect(find.text('Reserva #15'), findsOneWidget);
    expect(find.text('Espacio deportivo 8'), findsOneWidget);
    expect(find.text('Confirmada'), findsOneWidget);
  });

  testWidgets('abre la recuperacion de contrasena desde el login', (
    tester,
  ) async {
    final httpClient = MockClient((request) async {
      throw StateError('No debe realizar solicitudes HTTP.');
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

    final recoveryButton = find.byKey(
      const Key('login-show-password-recovery'),
    );

    expect(recoveryButton, findsOneWidget);

    await tester.ensureVisible(recoveryButton);
    await tester.pumpAndSettle();

    await tester.tap(recoveryButton);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('password-recovery-screen')), findsOneWidget);
    expect(
      find.byKey(const Key('password-recovery-email-field')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('password-recovery-request-submit')),
      findsOneWidget,
    );
    expect(find.text('Recuperar contrasena'), findsWidgets);
    expect(find.byKey(const Key('login-email-field')), findsNothing);

    final backButton = find.byKey(const Key('password-recovery-back-login'));

    await tester.ensureVisible(backButton);
    await tester.pumpAndSettle();

    await tester.tap(backButton);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('password-recovery-screen')), findsNothing);
    expect(find.byKey(const Key('login-email-field')), findsOneWidget);
    expect(find.byKey(const Key('login-submit')), findsOneWidget);
  });

  testWidgets('abre la recuperacion de contrasena desde el login', (
    tester,
  ) async {
    final httpClient = MockClient((request) async {
      throw StateError('No debe realizar solicitudes HTTP.');
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

    final recoveryButton = find.byKey(
      const Key('login-show-password-recovery'),
    );

    expect(recoveryButton, findsOneWidget);

    await tester.ensureVisible(recoveryButton);
    await tester.pumpAndSettle();

    await tester.tap(recoveryButton);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('password-recovery-screen')), findsOneWidget);
    expect(
      find.byKey(const Key('password-recovery-email-field')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('password-recovery-request-submit')),
      findsOneWidget,
    );
    expect(find.text('Recuperar contrasena'), findsWidgets);
    expect(find.byKey(const Key('login-email-field')), findsNothing);

    final backButton = find.byKey(const Key('password-recovery-back-login'));

    await tester.ensureVisible(backButton);
    await tester.pumpAndSettle();

    await tester.tap(backButton);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('password-recovery-screen')), findsNothing);
    expect(find.byKey(const Key('login-email-field')), findsOneWidget);
    expect(find.byKey(const Key('login-submit')), findsOneWidget);
  });
}
