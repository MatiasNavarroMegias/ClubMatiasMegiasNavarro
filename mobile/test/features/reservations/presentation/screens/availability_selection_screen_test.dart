import 'dart:async';
import 'dart:convert';

import 'package:club_matias_megias_navarro/features/reservations/data/models/availability_slot.dart';
import 'package:club_matias_megias_navarro/features/reservations/data/services/reservation_api_client.dart';
import 'package:club_matias_megias_navarro/features/reservations/presentation/screens/availability_selection_screen.dart';
import 'package:club_matias_megias_navarro/features/sports_spaces/data/models/sports_space.dart';
import 'package:club_matias_megias_navarro/features/venues/data/models/venue.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  final currentDate = DateTime(2026, 11, 3, 10, 30);

  Venue createVenue() {
    return Venue.fromJson({
      'id': 2,
      'name': 'Sede Ramos Mejia',
      'address': 'Avenida de Mayo 1000',
      'opening_time': '08:00:00',
      'closing_time': '23:00:00',
      'is_active': true,
      'created_at': '2026-10-25T12:00:00Z',
      'updated_at': '2026-10-25T13:00:00Z',
    });
  }

  SportsSpace createSportsSpace() {
    return SportsSpace.fromJson({
      'id': 5,
      'venue_id': 2,
      'name': 'Cancha de Futbol 1',
      'sport_type': 'Futbol',
      'space_number': 1,
      'is_active': true,
      'created_at': '2026-10-25T12:00:00Z',
      'updated_at': '2026-10-25T13:00:00Z',
    });
  }

  Widget createTestApp({
    required ReservationApiClient apiClient,
    String? accessToken,
    ValueChanged<AvailabilitySlot>? onSlotSelected,
  }) {
    return MaterialApp(
      home: AvailabilitySelectionScreen(
        venue: createVenue(),
        sportsSpace: createSportsSpace(),
        apiClient: apiClient,
        accessToken: accessToken,
        nowProvider: () => currentDate,
        onSlotSelected: onSlotSelected,
      ),
    );
  }

  String formatLocalTime(DateTime value) {
    final localValue = value.toLocal();
    final hour = localValue.hour.toString().padLeft(2, '0');
    final minute = localValue.minute.toString().padLeft(2, '0');

    return '$hour:$minute';
  }

  testWidgets('muestra el indicador mientras consulta la disponibilidad', (
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

    expect(find.byKey(const Key('availability-screen')), findsOneWidget);
    expect(find.byKey(const Key('availability-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    responseCompleter.complete(
      http.Response(jsonEncode(<Map<String, dynamic>>[]), 200),
    );

    await tester.pumpAndSettle();
  });

  testWidgets('consulta automaticamente el espacio y la fecha inicial', (
    tester,
  ) async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      expect(request.method, 'GET');
      expect(request.url.path, '/sports-spaces/5/availability');
      expect(request.url.queryParameters, {'date': '2026-11-03'});

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
    expect(find.text('Elegir horario'), findsOneWidget);
    expect(find.text('Cancha de Futbol 1'), findsOneWidget);
    expect(find.text('Sede Ramos Mejia · Futbol'), findsOneWidget);
    expect(find.text('03/11/2026'), findsOneWidget);
  });

  testWidgets('muestra los horarios devueltos por FastAPI', (tester) async {
    const firstStartText = '2026-11-03T18:00:00-03:00';
    const firstEndText = '2026-11-03T19:00:00-03:00';
    const secondStartText = '2026-11-03T20:00:00-03:00';
    const secondEndText = '2026-11-03T21:00:00-03:00';

    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([
          {'start_at': firstStartText, 'end_at': firstEndText},
          {'start_at': secondStartText, 'end_at': secondEndText},
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
    final secondStart = DateTime.parse(secondStartText);
    final secondEnd = DateTime.parse(secondEndText);

    expect(find.byKey(const Key('availability-slot-list')), findsOneWidget);
    expect(
      find.byKey(
        ValueKey(
          'availability-slot-'
          '${firstStart.toIso8601String()}',
        ),
      ),
      findsOneWidget,
    );
    expect(
      find.byKey(
        ValueKey(
          'availability-slot-'
          '${secondStart.toIso8601String()}',
        ),
      ),
      findsOneWidget,
    );
    expect(
      find.text(
        '${formatLocalTime(firstStart)}'
        ' - ${formatLocalTime(firstEnd)}',
      ),
      findsOneWidget,
    );
    expect(
      find.text(
        '${formatLocalTime(secondStart)}'
        ' - ${formatLocalTime(secondEnd)}',
      ),
      findsOneWidget,
    );
  });

  testWidgets('selecciona un horario y ejecuta el callback', (tester) async {
    const startText = '2026-11-03T18:00:00-03:00';
    const endText = '2026-11-03T19:00:00-03:00';

    AvailabilitySlot? selectedSlot;

    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([
          {'start_at': startText, 'end_at': endText},
        ]),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(
      createTestApp(
        apiClient: apiClient,
        onSlotSelected: (slot) {
          selectedSlot = slot;
        },
      ),
    );
    await tester.pumpAndSettle();

    final parsedStart = DateTime.parse(startText);

    final slotFinder = find.byKey(
      ValueKey(
        'availability-slot-'
        '${parsedStart.toIso8601String()}',
      ),
    );

    expect(slotFinder, findsOneWidget);
    expect(find.byKey(const Key('availability-selected-slot')), findsNothing);

    await tester.tap(slotFinder);
    await tester.pumpAndSettle();

    expect(selectedSlot, isNotNull);
    expect(selectedSlot?.startAt, parsedStart);
    expect(find.byKey(const Key('availability-selected-slot')), findsOneWidget);
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
  });

  testWidgets('muestra el estado vacio cuando no existen horarios', (
    tester,
  ) async {
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

    expect(find.byKey(const Key('availability-empty')), findsOneWidget);
    expect(find.text('No hay horarios disponibles'), findsOneWidget);
    expect(
      find.text('Elegí otra fecha para consultar nuevos turnos.'),
      findsOneWidget,
    );
  });

  testWidgets('muestra el error recibido desde FastAPI', (tester) async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({'detail': 'No se pudo consultar la disponibilidad.'}),
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

    expect(find.byKey(const Key('availability-error')), findsOneWidget);
    expect(find.text('No se pudo consultar la disponibilidad'), findsOneWidget);
    expect(
      find.text('No se pudo consultar la disponibilidad.'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('availability-retry')), findsOneWidget);
  });

  testWidgets('reintenta la consulta despues de un error', (tester) async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      if (requestCount == 1) {
        return http.Response(
          jsonEncode({'detail': 'No se pudo consultar la disponibilidad.'}),
          500,
        );
      }

      return http.Response(
        jsonEncode([
          {
            'start_at': '2026-11-03T18:00:00-03:00',
            'end_at': '2026-11-03T19:00:00-03:00',
          },
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

    expect(requestCount, 1);
    expect(find.byKey(const Key('availability-error')), findsOneWidget);

    await tester.tap(find.byKey(const Key('availability-retry')));
    await tester.pumpAndSettle();

    expect(requestCount, 2);
    expect(find.byKey(const Key('availability-slot-list')), findsOneWidget);
    expect(find.byKey(const Key('availability-error')), findsNothing);
  });

  testWidgets('habilita la confirmacion despues de seleccionar un horario', (
    tester,
  ) async {
    const startText = '2026-11-03T18:00:00-03:00';
    const endText = '2026-11-03T19:00:00-03:00';

    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([
          {'start_at': startText, 'end_at': endText},
        ]),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(
      createTestApp(apiClient: apiClient, accessToken: 'test-token'),
    );
    await tester.pumpAndSettle();

    final confirmButton = find.byKey(const Key('availability-confirm-button'));

    expect(confirmButton, findsOneWidget);

    var button = tester.widget<FilledButton>(confirmButton);

    expect(button.onPressed, isNull);

    final startAt = DateTime.parse(startText);

    await tester.tap(
      find.byKey(ValueKey('availability-slot-${startAt.toIso8601String()}')),
    );
    await tester.pumpAndSettle();

    button = tester.widget<FilledButton>(confirmButton);

    expect(button.onPressed, isNotNull);

    await tester.tap(confirmButton);
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('reservation-confirmation-dialog')),
      findsOneWidget,
    );
    expect(find.text('Confirmar reserva'), findsWidgets);
    expect(find.text('Cancha de Futbol 1'), findsWidgets);
    expect(find.text('Sede Ramos Mejia'), findsWidgets);
    expect(
      find.byKey(const Key('reservation-confirmation-accept')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('reservation-confirmation-cancel')),
      findsOneWidget,
    );
  });

  testWidgets('permite volver sin crear la reserva', (tester) async {
    const startText = '2026-11-03T18:00:00-03:00';

    var postRequestCount = 0;

    final httpClient = MockClient((request) async {
      if (request.method == 'POST') {
        postRequestCount++;
      }

      return http.Response(
        jsonEncode([
          {'start_at': startText, 'end_at': '2026-11-03T19:00:00-03:00'},
        ]),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(
      createTestApp(apiClient: apiClient, accessToken: 'test-token'),
    );
    await tester.pumpAndSettle();

    final startAt = DateTime.parse(startText);

    await tester.tap(
      find.byKey(ValueKey('availability-slot-${startAt.toIso8601String()}')),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('availability-confirm-button')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('reservation-confirmation-cancel')));
    await tester.pumpAndSettle();

    expect(postRequestCount, 0);
    expect(
      find.byKey(const Key('reservation-confirmation-dialog')),
      findsNothing,
    );
    expect(find.byKey(const Key('availability-selected-slot')), findsOneWidget);
  });

  testWidgets('crea la reserva y recarga la disponibilidad', (tester) async {
    const startText = '2026-11-03T18:00:00-03:00';
    const endText = '2026-11-03T19:00:00-03:00';

    var availabilityRequestCount = 0;
    var creationRequestCount = 0;

    final httpClient = MockClient((request) async {
      if (request.method == 'GET') {
        availabilityRequestCount++;

        if (availabilityRequestCount == 1) {
          return http.Response(
            jsonEncode([
              {'start_at': startText, 'end_at': endText},
            ]),
            200,
          );
        }

        return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
      }

      if (request.method == 'POST') {
        creationRequestCount++;

        expect(request.url.path, '/reservations');
        expect(request.headers['Authorization'], 'Bearer test-token');

        final body = jsonDecode(request.body) as Map<String, dynamic>;

        expect(body['sports_space_id'], 5);
        expect(
          DateTime.parse(body['start_at'] as String),
          DateTime.parse(startText),
        );

        return http.Response(
          jsonEncode({
            'id': 15,
            'user_id': 7,
            'sports_space_id': 5,
            'start_at': startText,
            'end_at': endText,
            'status': 'confirmed',
            'cancelled_at': null,
            'created_at': '2026-10-29T12:00:00Z',
            'updated_at': '2026-10-29T12:00:00Z',
          }),
          201,
        );
      }

      throw StateError('Solicitud HTTP inesperada.');
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(
      createTestApp(apiClient: apiClient, accessToken: 'test-token'),
    );
    await tester.pumpAndSettle();

    final startAt = DateTime.parse(startText);

    await tester.tap(
      find.byKey(ValueKey('availability-slot-${startAt.toIso8601String()}')),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('availability-confirm-button')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('reservation-confirmation-accept')));
    await tester.pumpAndSettle();

    expect(creationRequestCount, 1);
    expect(availabilityRequestCount, 2);
    expect(find.text('La reserva fue creada correctamente.'), findsOneWidget);
    expect(find.byKey(const Key('availability-empty')), findsOneWidget);
    expect(
      find.byKey(ValueKey('availability-slot-${startAt.toIso8601String()}')),
      findsNothing,
    );
  });

  testWidgets('informa cuando no existe una sesion disponible', (tester) async {
    const startText = '2026-11-03T18:00:00-03:00';

    var postRequestCount = 0;

    final httpClient = MockClient((request) async {
      if (request.method == 'POST') {
        postRequestCount++;
      }

      return http.Response(
        jsonEncode([
          {'start_at': startText, 'end_at': '2026-11-03T19:00:00-03:00'},
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

    final startAt = DateTime.parse(startText);

    await tester.tap(
      find.byKey(ValueKey('availability-slot-${startAt.toIso8601String()}')),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('availability-confirm-button')));
    await tester.pump();

    expect(postRequestCount, 0);
    expect(
      find.text(
        'La sesion no se encuentra disponible. '
        'Inicia sesion nuevamente.',
      ),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('reservation-confirmation-dialog')),
      findsNothing,
    );
  });

  testWidgets('muestra el conflicto recibido al crear la reserva', (
    tester,
  ) async {
    const startText = '2026-11-03T18:00:00-03:00';

    final httpClient = MockClient((request) async {
      if (request.method == 'GET') {
        return http.Response(
          jsonEncode([
            {'start_at': startText, 'end_at': '2026-11-03T19:00:00-03:00'},
          ]),
          200,
        );
      }

      return http.Response(
        jsonEncode({
          'detail': 'El turno solicitado ya se encuentra reservado.',
        }),
        409,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(
      createTestApp(apiClient: apiClient, accessToken: 'test-token'),
    );
    await tester.pumpAndSettle();

    final startAt = DateTime.parse(startText);

    await tester.tap(
      find.byKey(ValueKey('availability-slot-${startAt.toIso8601String()}')),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('availability-confirm-button')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('reservation-confirmation-accept')));
    await tester.pumpAndSettle();

    expect(
      find.text('El turno solicitado ya se encuentra reservado.'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('availability-selected-slot')), findsOneWidget);
  });
}
