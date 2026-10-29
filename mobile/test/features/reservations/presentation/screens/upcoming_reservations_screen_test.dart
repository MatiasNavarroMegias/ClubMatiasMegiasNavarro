import 'dart:async';
import 'dart:convert';

import 'package:club_matias_megias_navarro/features/reservations/data/services/reservation_api_client.dart';
import 'package:club_matias_megias_navarro/features/reservations/presentation/screens/upcoming_reservations_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';
  const accessToken = 'test-access-token';

  Map<String, dynamic> reservationJson({
    int id = 1,
    int sportsSpaceId = 8,
    String startAt = '2026-11-03T18:00:00-03:00',
    String endAt = '2026-11-03T19:00:00-03:00',
  }) {
    return {
      'id': id,
      'user_id': 7,
      'sports_space_id': sportsSpaceId,
      'start_at': startAt,
      'end_at': endAt,
      'status': 'confirmed',
      'cancelled_at': null,
      'created_at': '2026-10-29T12:00:00Z',
      'updated_at': '2026-10-29T12:00:00Z',
    };
  }

  Widget createTestApp({
    required ReservationApiClient apiClient,
    String token = accessToken,
  }) {
    return MaterialApp(
      home: UpcomingReservationsScreen(
        accessToken: token,
        apiClient: apiClient,
      ),
    );
  }

  String formatLocalDate(DateTime value) {
    final localValue = value.toLocal();
    final day = localValue.day.toString().padLeft(2, '0');
    final month = localValue.month.toString().padLeft(2, '0');

    return '$day/$month/${localValue.year}';
  }

  String formatLocalTime(DateTime value) {
    final localValue = value.toLocal();
    final hour = localValue.hour.toString().padLeft(2, '0');
    final minute = localValue.minute.toString().padLeft(2, '0');

    return '$hour:$minute';
  }

  testWidgets('muestra el indicador mientras carga las reservas', (
    tester,
  ) async {
    final responseCompleter = Completer<http.Response>();

    final httpClient = MockClient((request) {
      return responseCompleter.future;
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));

    expect(
      find.byKey(const Key('upcoming-reservations-screen')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('upcoming-reservations-loading')),
      findsOneWidget,
    );
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    responseCompleter.complete(
      http.Response(jsonEncode(<Map<String, dynamic>>[]), 200),
    );

    await tester.pumpAndSettle();
  });

  testWidgets('consulta las proximas reservas con token Bearer', (
    tester,
  ) async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      expect(request.method, 'GET');
      expect(request.url.path, '/reservations/upcoming');
      expect(request.headers['Authorization'], 'Bearer $accessToken');

      return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(requestCount, 1);
    expect(find.text('Mis reservas'), findsOneWidget);
  });

  testWidgets('muestra las proximas reservas recibidas', (tester) async {
    const firstStartText = '2026-11-03T18:00:00-03:00';
    const firstEndText = '2026-11-03T19:00:00-03:00';

    const secondStartText = '2026-11-04T20:00:00-03:00';
    const secondEndText = '2026-11-04T21:00:00-03:00';

    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([
          reservationJson(
            id: 1,
            sportsSpaceId: 8,
            startAt: firstStartText,
            endAt: firstEndText,
          ),
          reservationJson(
            id: 2,
            sportsSpaceId: 10,
            startAt: secondStartText,
            endAt: secondEndText,
          ),
        ]),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    final firstStart = DateTime.parse(firstStartText);
    final firstEnd = DateTime.parse(firstEndText);

    expect(find.byKey(const Key('upcoming-reservations-list')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('upcoming-reservation-1')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('upcoming-reservation-2')),
      findsOneWidget,
    );

    expect(find.text('Reserva #1'), findsOneWidget);
    expect(find.text('Reserva #2'), findsOneWidget);
    expect(find.text('Espacio deportivo 8'), findsOneWidget);
    expect(find.text('Espacio deportivo 10'), findsOneWidget);
    expect(find.text(formatLocalDate(firstStart)), findsOneWidget);
    expect(
      find.text(
        '${formatLocalTime(firstStart)}'
        ' - ${formatLocalTime(firstEnd)}',
      ),
      findsOneWidget,
    );
    expect(find.text('Confirmada'), findsNWidgets(2));
  });

  testWidgets('muestra el estado vacio sin proximas reservas', (tester) async {
    final httpClient = MockClient((request) async {
      return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('upcoming-reservations-empty')),
      findsOneWidget,
    );
    expect(find.text('No tenes proximas reservas'), findsOneWidget);
    expect(
      find.text(
        'Cuando reserves un espacio, el turno '
        'aparecera en esta seccion.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('muestra el error recibido desde FastAPI', (tester) async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({'detail': 'No se pudieron consultar las reservas.'}),
        500,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('upcoming-reservations-error')),
      findsOneWidget,
    );
    expect(find.text('No se pudieron cargar tus reservas'), findsOneWidget);
    expect(find.text('No se pudieron consultar las reservas.'), findsOneWidget);
    expect(
      find.byKey(const Key('upcoming-reservations-retry')),
      findsOneWidget,
    );
  });

  testWidgets('reintenta la consulta despues de un error', (tester) async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      if (requestCount == 1) {
        return http.Response(
          jsonEncode({'detail': 'No se pudieron consultar las reservas.'}),
          500,
        );
      }

      return http.Response(
        jsonEncode([reservationJson(id: 5, sportsSpaceId: 12)]),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(requestCount, 1);
    expect(
      find.byKey(const Key('upcoming-reservations-error')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const Key('upcoming-reservations-retry')));
    await tester.pumpAndSettle();

    expect(requestCount, 2);
    expect(find.byKey(const Key('upcoming-reservations-list')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('upcoming-reservation-5')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('upcoming-reservations-error')), findsNothing);
  });

  testWidgets('consulta nuevamente cuando cambia el token', (tester) async {
    final receivedTokens = <String>[];

    final httpClient = MockClient((request) async {
      receivedTokens.add(request.headers['Authorization'] ?? '');

      return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(
      createTestApp(apiClient: apiClient, token: 'first-token'),
    );
    await tester.pumpAndSettle();

    await tester.pumpWidget(
      createTestApp(apiClient: apiClient, token: 'second-token'),
    );
    await tester.pumpAndSettle();

    expect(receivedTokens, ['Bearer first-token', 'Bearer second-token']);
  });
}
