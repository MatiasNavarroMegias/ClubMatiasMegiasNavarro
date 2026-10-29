import 'package:club_matias_megias_navarro/features/reservations/data/models/availability_slot.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('construye un horario disponible desde JSON', () {
    final slot = AvailabilitySlot.fromJson({
      'start_at': '2026-11-03T18:00:00-03:00',
      'end_at': '2026-11-03T19:00:00-03:00',
    });

    expect(slot.startAt, DateTime.parse('2026-11-03T18:00:00-03:00'));
    expect(slot.endAt, DateTime.parse('2026-11-03T19:00:00-03:00'));
    expect(slot.duration, const Duration(hours: 1));
    expect(slot.isOneHour, isTrue);
  });

  test('convierte el horario nuevamente a JSON', () {
    final slot = AvailabilitySlot(
      startAt: DateTime.utc(2026, 11, 3, 21),
      endAt: DateTime.utc(2026, 11, 3, 22),
    );

    expect(slot.toJson(), {
      'start_at': '2026-11-03T21:00:00.000Z',
      'end_at': '2026-11-03T22:00:00.000Z',
    });
  });

  test('detecta una duracion diferente de una hora', () {
    final slot = AvailabilitySlot.fromJson({
      'start_at': '2026-11-03T18:00:00-03:00',
      'end_at': '2026-11-03T20:00:00-03:00',
    });

    expect(slot.duration, const Duration(hours: 2));
    expect(slot.isOneHour, isFalse);
  });

  test('rechaza una fecha de inicio invalida', () {
    expect(() {
      AvailabilitySlot.fromJson({
        'start_at': 'fecha-invalida',
        'end_at': '2026-11-03T19:00:00-03:00',
      });
    }, throwsA(isA<FormatException>()));
  });

  test('rechaza una fecha final inexistente', () {
    expect(() {
      AvailabilitySlot.fromJson({'start_at': '2026-11-03T18:00:00-03:00'});
    }, throwsA(isA<FormatException>()));
  });

  test('rechaza un horario final anterior al inicio', () {
    expect(
      () {
        AvailabilitySlot.fromJson({
          'start_at': '2026-11-03T19:00:00-03:00',
          'end_at': '2026-11-03T18:00:00-03:00',
        });
      },
      throwsA(
        isA<FormatException>().having(
          (error) => error.message,
          'message',
          'El horario final debe ser posterior al inicio.',
        ),
      ),
    );
  });

  test('rechaza un horario final igual al inicio', () {
    expect(() {
      AvailabilitySlot.fromJson({
        'start_at': '2026-11-03T18:00:00-03:00',
        'end_at': '2026-11-03T18:00:00-03:00',
      });
    }, throwsA(isA<FormatException>()));
  });
}
