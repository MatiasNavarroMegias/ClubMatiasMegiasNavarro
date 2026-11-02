import 'package:flutter_test/flutter_test.dart';

import 'package:club_matias_megias_navarro/core/time/club_time.dart';

void main() {
  test('conserva 20:00 de Buenos Aires aunque el dispositivo use UTC', () {
    final venueTime = ClubTime.fromCivil(
      year: 2026,
      month: 11,
      day: 3,
      hour: 20,
    );

    expect(ClubTime.toApi(venueTime), '2026-11-03T20:00:00-03:00');
    expect(ClubTime.formatTime(venueTime), '20:00');
  });

  test('convierte una respuesta UTC a la hora civil de la sede', () {
    final apiValue = DateTime.parse('2026-11-03T23:00:00Z');

    expect(ClubTime.formatTime(ClubTime.fromApi(apiValue)), '20:00');
    expect(ClubTime.formatDate(ClubTime.fromApi(apiValue)), '03/11/2026');
  });
}
