import 'package:club_matias_megias_navarro/features/sports_spaces/data/models/sports_space.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  Map<String, dynamic> sportsSpaceJson() {
    return {
      'id': 5,
      'venue_id': 2,
      'name': 'Cancha de Futbol 1',
      'sport_type': 'Futbol',
      'space_number': 1,
      'is_active': true,
      'created_at': '2026-10-25T12:00:00Z',
      'updated_at': '2026-10-25T13:00:00Z',
    };
  }

  group('SportsSpace', () {
    test('construye el modelo desde JSON', () {
      final sportsSpace = SportsSpace.fromJson(sportsSpaceJson());

      expect(sportsSpace.id, 5);
      expect(sportsSpace.venueId, 2);
      expect(sportsSpace.name, 'Cancha de Futbol 1');
      expect(sportsSpace.sportType, 'Futbol');
      expect(sportsSpace.spaceNumber, 1);
      expect(sportsSpace.isActive, isTrue);
      expect(sportsSpace.createdAt, DateTime.parse('2026-10-25T12:00:00Z'));
      expect(sportsSpace.updatedAt, DateTime.parse('2026-10-25T13:00:00Z'));
    });

    test('convierte el modelo nuevamente en JSON', () {
      final sportsSpace = SportsSpace.fromJson(sportsSpaceJson());

      expect(sportsSpace.toJson(), {
        'id': 5,
        'venue_id': 2,
        'name': 'Cancha de Futbol 1',
        'sport_type': 'Futbol',
        'space_number': 1,
        'is_active': true,
        'created_at': '2026-10-25T12:00:00.000Z',
        'updated_at': '2026-10-25T13:00:00.000Z',
      });
    });

    test('rechaza un identificador no numerico', () {
      final json = sportsSpaceJson();
      json['id'] = '5';

      expect(
        () => SportsSpace.fromJson(json),
        throwsA(
          isA<FormatException>().having(
            (error) => error.message,
            'message',
            'El campo id debe ser un numero entero.',
          ),
        ),
      );
    });

    test('rechaza un nombre vacio', () {
      final json = sportsSpaceJson();
      json['name'] = '   ';

      expect(
        () => SportsSpace.fromJson(json),
        throwsA(
          isA<FormatException>().having(
            (error) => error.message,
            'message',
            'El campo name debe contener texto.',
          ),
        ),
      );
    });

    test('rechaza un estado no booleano', () {
      final json = sportsSpaceJson();
      json['is_active'] = 1;

      expect(
        () => SportsSpace.fromJson(json),
        throwsA(
          isA<FormatException>().having(
            (error) => error.message,
            'message',
            'El campo is_active debe ser booleano.',
          ),
        ),
      );
    });

    test('rechaza una fecha invalida', () {
      final json = sportsSpaceJson();
      json['created_at'] = 'fecha-invalida';

      expect(
        () => SportsSpace.fromJson(json),
        throwsA(
          isA<FormatException>().having(
            (error) => error.message,
            'message',
            'El campo created_at contiene una fecha invalida.',
          ),
        ),
      );
    });
  });
}
