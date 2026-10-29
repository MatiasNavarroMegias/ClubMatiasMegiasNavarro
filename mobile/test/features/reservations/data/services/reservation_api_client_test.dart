import 'dart:convert';

import 'package:club_matias_megias_navarro/features/reservations/data/services/reservation_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';
  const accessToken = 'test-access-token';

  Map<String, dynamic> reservationJson({
    int id = 1,
    int userId = 7,
    int sportsSpaceId = 8,
    String status = 'confirmed',
    String? cancelledAt,
  }) {
    return {
      'id': id,
      'user_id': userId,
      'sports_space_id': sportsSpaceId,
      'start_at': '2026-11-03T18:00:00-03:00',
      'end_at': '2026-11-03T19:00:00-03:00',
      'status': status,
      'cancelled_at': cancelledAt,
      'created_at': '2026-10-29T12:00:00Z',
      'updated_at': cancelledAt ?? '2026-10-29T12:00:00Z',
    };
  }

  test('consulta la disponibilidad con el identificador y la fecha', () async {
    final httpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/sports-spaces/8/availability');
      expect(request.url.queryParameters, {'date': '2026-11-03'});
      expect(request.headers['Accept'], 'application/json');

      return http.Response(
        jsonEncode([
          {
            'start_at': '2026-11-03T18:00:00-03:00',
            'end_at': '2026-11-03T19:00:00-03:00',
          },
          {
            'start_at': '2026-11-03T20:00:00-03:00',
            'end_at': '2026-11-03T21:00:00-03:00',
          },
        ]),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    final slots = await apiClient.getAvailability(
      sportsSpaceId: 8,
      selectedDate: DateTime(2026, 11, 3, 23, 45),
    );

    expect(slots, hasLength(2));
    expect(slots.first.isOneHour, isTrue);
    expect(slots.first.startAt, DateTime.parse('2026-11-03T18:00:00-03:00'));
  });

  test('crea una reserva autenticada', () async {
    final httpClient = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path, '/reservations');
      expect(request.headers['Authorization'], 'Bearer $accessToken');
      expect(request.headers['Content-Type'], 'application/json');

      final decodedBody = jsonDecode(request.body) as Map<String, dynamic>;

      expect(decodedBody, {
        'sports_space_id': 8,
        'start_at': '2026-11-03T21:00:00.000Z',
      });

      return http.Response(
        jsonEncode(reservationJson()),
        201,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    final reservation = await apiClient.createReservation(
      accessToken: accessToken,
      sportsSpaceId: 8,
      startAt: DateTime.utc(2026, 11, 3, 21),
    );

    expect(reservation.id, 1);
    expect(reservation.userId, 7);
    expect(reservation.sportsSpaceId, 8);
    expect(reservation.isConfirmed, isTrue);
    expect(reservation.cancelledAt, isNull);
  });

  test('consulta las proximas reservas con token Bearer', () async {
    final httpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/reservations/upcoming');
      expect(request.headers['Authorization'], 'Bearer $accessToken');

      return http.Response(
        jsonEncode([reservationJson(), reservationJson(id: 2)]),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    final reservations = await apiClient.getUpcomingReservations(
      accessToken: accessToken,
    );

    expect(reservations, hasLength(2));
    expect(reservations.first.id, 1);
    expect(reservations.last.id, 2);
  });

  test('consulta el historial con token Bearer', () async {
    final cancellationDate = '2026-10-30T10:15:00-03:00';

    final httpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/reservations/history');
      expect(request.headers['Authorization'], 'Bearer $accessToken');

      return http.Response(
        jsonEncode([
          reservationJson(status: 'cancelled', cancelledAt: cancellationDate),
        ]),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    final reservations = await apiClient.getReservationHistory(
      accessToken: accessToken,
    );

    expect(reservations, hasLength(1));
    expect(reservations.single.isCancelled, isTrue);
    expect(reservations.single.cancelledAt, DateTime.parse(cancellationDate));
  });

  test('cancela una reserva autenticada', () async {
    final cancellationDate = '2026-10-30T10:15:00-03:00';

    final httpClient = MockClient((request) async {
      expect(request.method, 'PATCH');
      expect(request.url.path, '/reservations/5/cancel');
      expect(request.headers['Authorization'], 'Bearer $accessToken');

      return http.Response(
        jsonEncode(
          reservationJson(
            id: 5,
            status: 'cancelled',
            cancelledAt: cancellationDate,
          ),
        ),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    final reservation = await apiClient.cancelReservation(
      accessToken: accessToken,
      reservationId: 5,
    );

    expect(reservation.id, 5);
    expect(reservation.isCancelled, isTrue);
    expect(reservation.cancelledAt, DateTime.parse(cancellationDate));
  });

  test('devuelve listas vacias correctamente', () async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    final slots = await apiClient.getAvailability(
      sportsSpaceId: 8,
      selectedDate: DateTime(2026, 11, 3),
    );
    final upcoming = await apiClient.getUpcomingReservations(
      accessToken: accessToken,
    );
    final history = await apiClient.getReservationHistory(
      accessToken: accessToken,
    );

    expect(slots, isEmpty);
    expect(upcoming, isEmpty);
    expect(history, isEmpty);
    expect(requestCount, 3);
  });

  test('conserva el codigo y detail de FastAPI', () async {
    final httpClient = MockClient((request) async {
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

    await expectLater(
      apiClient.createReservation(
        accessToken: accessToken,
        sportsSpaceId: 8,
        startAt: DateTime.utc(2026, 11, 3, 21),
      ),
      throwsA(
        isA<ReservationApiException>()
            .having((error) => error.statusCode, 'statusCode', 409)
            .having(
              (error) => error.message,
              'message',
              'El turno solicitado ya '
                  'se encuentra reservado.',
            )
            .having((error) => error.isConflict, 'isConflict', isTrue),
      ),
    );
  });

  test('lee el primer mensaje de una validacion 422', () async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({
          'detail': [
            {'msg': 'La fecha de inicio debe incluir una zona horaria.'},
          ],
        }),
        422,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await expectLater(
      apiClient.createReservation(
        accessToken: accessToken,
        sportsSpaceId: 8,
        startAt: DateTime.utc(2026, 11, 3, 21),
      ),
      throwsA(
        isA<ReservationApiException>()
            .having((error) => error.statusCode, 'statusCode', 422)
            .having(
              (error) => error.message,
              'message',
              'La fecha de inicio debe incluir '
                  'una zona horaria.',
            )
            .having(
              (error) => error.isValidationError,
              'isValidationError',
              isTrue,
            ),
      ),
    );
  });

  test('detecta una respuesta de disponibilidad invalida', () async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({'start_at': '2026-11-03T18:00:00-03:00'}),
        200,
      );
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await expectLater(
      apiClient.getAvailability(
        sportsSpaceId: 8,
        selectedDate: DateTime(2026, 11, 3),
      ),
      throwsA(
        isA<ReservationApiException>().having(
          (error) => error.message,
          'message',
          'La API devolvio un listado '
              'de horarios invalido.',
        ),
      ),
    );
  });

  test('detecta un listado de reservas invalido', () async {
    final httpClient = MockClient((request) async {
      return http.Response(jsonEncode({'id': 1}), 200);
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await expectLater(
      apiClient.getUpcomingReservations(accessToken: accessToken),
      throwsA(
        isA<ReservationApiException>().having(
          (error) => error.message,
          'message',
          'La API devolvio un listado '
              'de proximas reservas invalido.',
        ),
      ),
    );
  });

  test('transforma los errores de conexion', () async {
    final httpClient = MockClient((request) async {
      throw Exception('connection failed');
    });

    final apiClient = ReservationApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await expectLater(
      apiClient.getReservationHistory(accessToken: accessToken),
      throwsA(
        isA<ReservationApiException>()
            .having((error) => error.statusCode, 'statusCode', isNull)
            .having(
              (error) => error.message,
              'message',
              'No se pudo establecer una '
                  'conexion con la API.',
            )
            .having(
              (error) => error.isConnectionError,
              'isConnectionError',
              isTrue,
            ),
      ),
    );
  });
}
