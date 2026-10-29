import 'dart:convert';

import 'package:club_matias_megias_navarro/features/reservations/data/services/reservation_api_client.dart';
import 'package:club_matias_megias_navarro/features/reservations/presentation/screens/reservations_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';
  const accessToken = 'test-access-token';

  Map<String, dynamic> upcomingReservationJson() {
    return {
      'id': 15,
      'user_id': 7,
      'sports_space_id': 8,
      'start_at': '2026-11-03T18:00:00-03:00',
      'end_at': '2026-11-03T19:00:00-03:00',
      'status': 'confirmed',
      'cancelled_at': null,
      'created_at': '2026-10-29T12:00:00Z',
      'updated_at': '2026-10-29T12:00:00Z',
    };
  }

  Map<String, dynamic> historyReservationJson() {
    return {
      'id': 20,
      'user_id': 7,
      'sports_space_id': 10,
      'start_at': '2026-10-25T18:00:00-03:00',
      'end_at': '2026-10-25T19:00:00-03:00',
      'status': 'cancelled',
      'cancelled_at': '2026-10-24T10:30:00-03:00',
      'created_at': '2026-10-20T12:00:00Z',
      'updated_at': '2026-10-24T13:30:00Z',
    };
  }

  Widget createTestApp({required ReservationApiClient apiClient}) {
    return MaterialApp(
      home: ReservationsScreen(accessToken: accessToken, apiClient: apiClient),
    );
  }

  testWidgets('muestra las pestañas de proximas e historial', (tester) async {
    final requestedPaths = <String>[];

    final httpClient = MockClient((request) async {
      requestedPaths.add(request.url.path);

      return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('reservations-screen')), findsOneWidget);
    expect(find.text('Mis reservas'), findsOneWidget);
    expect(find.byKey(const Key('reservations-upcoming-tab')), findsOneWidget);
    expect(find.byKey(const Key('reservations-history-tab')), findsOneWidget);
    expect(find.text('Proximas'), findsOneWidget);
    expect(find.text('Historial'), findsOneWidget);

    expect(requestedPaths, ['/reservations/upcoming']);
  });

  testWidgets('muestra inicialmente las proximas reservas', (tester) async {
    final httpClient = MockClient((request) async {
      if (request.url.path == '/reservations/upcoming') {
        expect(request.headers['Authorization'], 'Bearer $accessToken');

        return http.Response(jsonEncode([upcomingReservationJson()]), 200);
      }

      if (request.url.path == '/reservations/history') {
        return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
      }

      throw StateError('Solicitud HTTP inesperada.');
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('upcoming-reservations-screen')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('upcoming-reservation-15')),
      findsOneWidget,
    );
    expect(find.text('Reserva #15'), findsOneWidget);
    expect(find.text('Confirmada'), findsOneWidget);

    expect(find.byKey(const ValueKey('history-reservation-20')), findsNothing);
  });

  testWidgets('cambia a la pestaña de historial', (tester) async {
    final httpClient = MockClient((request) async {
      expect(request.headers['Authorization'], 'Bearer $accessToken');

      if (request.url.path == '/reservations/upcoming') {
        return http.Response(jsonEncode([upcomingReservationJson()]), 200);
      }

      if (request.url.path == '/reservations/history') {
        return http.Response(jsonEncode([historyReservationJson()]), 200);
      }

      throw StateError('Solicitud HTTP inesperada.');
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('reservations-history-tab')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('reservation-history-screen')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('history-reservation-20')),
      findsOneWidget,
    );
    expect(find.text('Reserva #20'), findsOneWidget);
    expect(find.text('Cancelada'), findsOneWidget);
  });

  testWidgets('actualiza proximas al volver desde historial', (tester) async {
    var upcomingRequestCount = 0;
    var historyRequestCount = 0;

    final httpClient = MockClient((request) async {
      if (request.url.path == '/reservations/upcoming') {
        upcomingRequestCount++;

        return http.Response(jsonEncode([upcomingReservationJson()]), 200);
      }

      if (request.url.path == '/reservations/history') {
        historyRequestCount++;

        return http.Response(jsonEncode([historyReservationJson()]), 200);
      }

      throw StateError('Solicitud HTTP inesperada.');
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('reservations-history-tab')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('reservations-upcoming-tab')));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('upcoming-reservation-15')),
      findsOneWidget,
    );

    expect(upcomingRequestCount, 2);
    expect(historyRequestCount, 1);
  });
}
