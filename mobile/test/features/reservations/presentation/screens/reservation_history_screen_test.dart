import 'dart:async';
import 'dart:convert';

import 'package:club_matias_megias_navarro/features/reservations/data/services/reservation_api_client.dart';
import 'package:club_matias_megias_navarro/features/reservations/presentation/screens/reservation_history_screen.dart';
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
    String startAt = '2026-10-25T18:00:00-03:00',
    String endAt = '2026-10-25T19:00:00-03:00',
    String status = 'confirmed',
    String? cancelledAt,
  }) {
    return {
      'id': id,
      'user_id': 7,
      'sports_space_id': sportsSpaceId,
      'start_at': startAt,
      'end_at': endAt,
      'status': status,
      'cancelled_at': cancelledAt,
      'created_at': '2026-10-20T12:00:00Z',
      'updated_at': cancelledAt ?? '2026-10-20T12:00:00Z',
    };
  }

  Widget createTestApp({
    required ReservationApiClient apiClient,
    String token = accessToken,
  }) {
    return MaterialApp(
      home: ReservationHistoryScreen(accessToken: token, apiClient: apiClient),
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

  String formatLocalDateTime(DateTime value) {
    return '${formatLocalDate(value)} ${formatLocalTime(value)}';
  }

  testWidgets('muestra el indicador mientras carga el historial', (
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

    expect(find.byKey(const Key('reservation-history-screen')), findsOneWidget);
    expect(
      find.byKey(const Key('reservation-history-loading')),
      findsOneWidget,
    );
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    responseCompleter.complete(
      http.Response(jsonEncode(<Map<String, dynamic>>[]), 200),
    );

    await tester.pumpAndSettle();
  });

  testWidgets('consulta el historial con token Bearer', (tester) async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      expect(request.method, 'GET');
      expect(request.url.path, '/reservations/history');
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
    expect(find.byKey(const Key('reservation-history-empty')), findsOneWidget);
  });

  testWidgets('muestra reservas finalizadas y canceladas', (tester) async {
    const finishedStartText = '2026-10-25T18:00:00-03:00';
    const finishedEndText = '2026-10-25T19:00:00-03:00';
    const cancelledStartText = '2026-11-03T20:00:00-03:00';
    const cancelledEndText = '2026-11-03T21:00:00-03:00';
    const cancellationText = '2026-10-29T12:30:00-03:00';

    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([
          reservationJson(
            id: 1,
            sportsSpaceId: 8,
            startAt: finishedStartText,
            endAt: finishedEndText,
          ),
          reservationJson(
            id: 2,
            sportsSpaceId: 10,
            startAt: cancelledStartText,
            endAt: cancelledEndText,
            status: 'cancelled',
            cancelledAt: cancellationText,
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

    final finishedStart = DateTime.parse(finishedStartText);
    final finishedEnd = DateTime.parse(finishedEndText);
    final cancellationDate = DateTime.parse(cancellationText);

    expect(find.byKey(const Key('reservation-history-list')), findsOneWidget);
    expect(find.byKey(const ValueKey('history-reservation-1')), findsOneWidget);
    expect(find.byKey(const ValueKey('history-reservation-2')), findsOneWidget);

    expect(find.text('Reserva #1'), findsOneWidget);
    expect(find.text('Reserva #2'), findsOneWidget);
    expect(find.text('Espacio deportivo 8'), findsOneWidget);
    expect(find.text('Espacio deportivo 10'), findsOneWidget);

    expect(find.text('Finalizada'), findsOneWidget);
    expect(find.text('Cancelada'), findsOneWidget);

    expect(find.text(formatLocalDate(finishedStart)), findsOneWidget);
    expect(
      find.text(
        '${formatLocalTime(finishedStart)}'
        ' - ${formatLocalTime(finishedEnd)}',
      ),
      findsOneWidget,
    );
    expect(
      find.text(
        'Cancelada el '
        '${formatLocalDateTime(cancellationDate)}',
      ),
      findsOneWidget,
    );
  });

  testWidgets('muestra el estado vacio sin historial', (tester) async {
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

    expect(find.byKey(const Key('reservation-history-empty')), findsOneWidget);
    expect(find.text('Todavia no tenes historial'), findsOneWidget);
    expect(
      find.text(
        'Las reservas canceladas o finalizadas '
        'apareceran en esta seccion.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('muestra el error recibido desde FastAPI', (tester) async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({'detail': 'No se pudo consultar el historial.'}),
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

    expect(find.byKey(const Key('reservation-history-error')), findsOneWidget);
    expect(find.text('No se pudo cargar el historial'), findsOneWidget);
    expect(find.text('No se pudo consultar el historial.'), findsOneWidget);
    expect(find.byKey(const Key('reservation-history-retry')), findsOneWidget);
  });

  testWidgets('reintenta la consulta despues de un error', (tester) async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      if (requestCount == 1) {
        return http.Response(
          jsonEncode({'detail': 'No se pudo consultar el historial.'}),
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
    expect(find.byKey(const Key('reservation-history-error')), findsOneWidget);

    await tester.tap(find.byKey(const Key('reservation-history-retry')));
    await tester.pumpAndSettle();

    expect(requestCount, 2);
    expect(find.byKey(const Key('reservation-history-list')), findsOneWidget);
    expect(find.byKey(const ValueKey('history-reservation-5')), findsOneWidget);
    expect(find.byKey(const Key('reservation-history-error')), findsNothing);
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
