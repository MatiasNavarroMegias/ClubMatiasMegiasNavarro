import 'package:club_matias_megias_navarro/features/reservations/data/models/reservation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  Map<String, dynamic> confirmedReservationJson() {
    return {
      'id': 1,
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

  test('construye una reserva confirmada desde JSON', () {
    final reservation = Reservation.fromJson(confirmedReservationJson());

    expect(reservation.id, 1);
    expect(reservation.userId, 7);
    expect(reservation.sportsSpaceId, 8);
    expect(reservation.startAt, DateTime.parse('2026-11-03T18:00:00-03:00'));
    expect(reservation.endAt, DateTime.parse('2026-11-03T19:00:00-03:00'));
    expect(reservation.status, 'confirmed');
    expect(reservation.cancelledAt, isNull);
    expect(reservation.isConfirmed, isTrue);
    expect(reservation.isCancelled, isFalse);
    expect(reservation.duration, const Duration(hours: 1));
    expect(reservation.isOneHour, isTrue);
  });

  test('construye una reserva cancelada desde JSON', () {
    final json = confirmedReservationJson()
      ..['status'] = 'cancelled'
      ..['cancelled_at'] = '2026-10-30T10:15:00-03:00'
      ..['updated_at'] = '2026-10-30T10:15:00-03:00';

    final reservation = Reservation.fromJson(json);

    expect(reservation.status, 'cancelled');
    expect(reservation.isConfirmed, isFalse);
    expect(reservation.isCancelled, isTrue);
    expect(
      reservation.cancelledAt,
      DateTime.parse('2026-10-30T10:15:00-03:00'),
    );
  });

  test('convierte la reserva nuevamente a JSON', () {
    final reservation = Reservation(
      id: 1,
      userId: 7,
      sportsSpaceId: 8,
      startAt: DateTime.utc(2026, 11, 3, 21),
      endAt: DateTime.utc(2026, 11, 3, 22),
      status: 'confirmed',
      cancelledAt: null,
      createdAt: DateTime.utc(2026, 10, 29, 12),
      updatedAt: DateTime.utc(2026, 10, 29, 12),
    );

    expect(reservation.toJson(), {
      'id': 1,
      'user_id': 7,
      'sports_space_id': 8,
      'start_at': '2026-11-03T21:00:00.000Z',
      'end_at': '2026-11-03T22:00:00.000Z',
      'status': 'confirmed',
      'cancelled_at': null,
      'created_at': '2026-10-29T12:00:00.000Z',
      'updated_at': '2026-10-29T12:00:00.000Z',
    });
  });

  test('detecta una duracion diferente de una hora', () {
    final json = confirmedReservationJson()
      ..['end_at'] = '2026-11-03T20:00:00-03:00';

    final reservation = Reservation.fromJson(json);

    expect(reservation.duration, const Duration(hours: 2));
    expect(reservation.isOneHour, isFalse);
  });

  test('rechaza identificadores no positivos', () {
    final invalidFields = ['id', 'user_id', 'sports_space_id'];

    for (final fieldName in invalidFields) {
      final json = confirmedReservationJson()..[fieldName] = 0;

      expect(
        () => Reservation.fromJson(json),
        throwsA(isA<FormatException>()),
        reason: 'Debe rechazar $fieldName igual a cero.',
      );
    }
  });

  test('rechaza un estado desconocido', () {
    final json = confirmedReservationJson()..['status'] = 'pending';

    expect(
      () => Reservation.fromJson(json),
      throwsA(
        isA<FormatException>().having(
          (error) => error.message,
          'message',
          'El estado de la reserva no es valido.',
        ),
      ),
    );
  });

  test('rechaza una reserva confirmada con fecha de cancelacion', () {
    final json = confirmedReservationJson()
      ..['cancelled_at'] = '2026-10-30T10:15:00-03:00';

    expect(
      () => Reservation.fromJson(json),
      throwsA(
        isA<FormatException>().having(
          (error) => error.message,
          'message',
          'Una reserva confirmada no puede tener '
              'fecha de cancelacion.',
        ),
      ),
    );
  });

  test('rechaza una reserva cancelada sin fecha de cancelacion', () {
    final json = confirmedReservationJson()..['status'] = 'cancelled';

    expect(
      () => Reservation.fromJson(json),
      throwsA(
        isA<FormatException>().having(
          (error) => error.message,
          'message',
          'Una reserva cancelada debe tener '
              'fecha de cancelacion.',
        ),
      ),
    );
  });

  test('rechaza un horario final anterior al inicio', () {
    final json = confirmedReservationJson()
      ..['end_at'] = '2026-11-03T17:00:00-03:00';

    expect(
      () => Reservation.fromJson(json),
      throwsA(
        isA<FormatException>().having(
          (error) => error.message,
          'message',
          'El horario final debe ser posterior al inicio.',
        ),
      ),
    );
  });

  test('rechaza fechas obligatorias invalidas', () {
    final invalidFields = ['start_at', 'end_at', 'created_at', 'updated_at'];

    for (final fieldName in invalidFields) {
      final json = confirmedReservationJson()..[fieldName] = 'fecha-invalida';

      expect(
        () => Reservation.fromJson(json),
        throwsA(isA<FormatException>()),
        reason: 'Debe rechazar $fieldName invalido.',
      );
    }
  });

  test('rechaza una fecha de cancelacion invalida', () {
    final json = confirmedReservationJson()
      ..['status'] = 'cancelled'
      ..['cancelled_at'] = 'fecha-invalida';

    expect(() => Reservation.fromJson(json), throwsA(isA<FormatException>()));
  });
}
