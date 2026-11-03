import 'package:club_matias_megias_navarro/features/venues/data/models/venue.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Venue', () {
    test('construye una sede desde una respuesta JSON', () {
      final json = <String, dynamic>{
        'id': 1,
        'name': 'Sede Ramos Mejia',
        'address': 'Avenida de Mayo 1000',
        'opening_time': '08:00:00',
        'closing_time': '23:00:00',
        'is_active': true,
        'created_at': '2026-10-20T12:00:00Z',
        'updated_at': '2026-10-20T13:00:00Z',
      };

      final venue = Venue.fromJson(json);

      expect(venue.id, 1);
      expect(venue.name, 'Sede Ramos Mejia');
      expect(venue.address, 'Avenida de Mayo 1000');
      expect(venue.openingTime, '08:00:00');
      expect(venue.closingTime, '23:00:00');
      expect(venue.isActive, isTrue);
      expect(venue.createdAt, DateTime.parse('2026-10-20T12:00:00Z'));
      expect(venue.updatedAt, DateTime.parse('2026-10-20T13:00:00Z'));
    });

    test('genera el JSON necesario para crear una sede', () {
      final venue = Venue(
        id: 1,
        name: 'Sede Ramos Mejia',
        address: 'Avenida de Mayo 1000',
        openingTime: '08:00:00',
        closingTime: '23:00:00',
        isActive: true,
        createdAt: DateTime.parse('2026-10-20T12:00:00Z'),
        updatedAt: DateTime.parse('2026-10-20T12:00:00Z'),
      );

      final json = venue.toCreateJson();

      expect(json, <String, dynamic>{
        'name': 'Sede Ramos Mejia',
        'address': 'Avenida de Mayo 1000',
        'opening_time': '08:00:00',
        'closing_time': '23:00:00',
      });

      expect(json.containsKey('id'), isFalse);
      expect(json.containsKey('is_active'), isFalse);
      expect(json.containsKey('created_at'), isFalse);
      expect(json.containsKey('updated_at'), isFalse);
    });

    test('copyWith reemplaza solamente los valores indicados', () {
      final venue = Venue(
        id: 1,
        name: 'Sede Ramos Mejia',
        address: 'Avenida de Mayo 1000',
        openingTime: '08:00:00',
        closingTime: '23:00:00',
        isActive: true,
        createdAt: DateTime.parse('2026-10-20T12:00:00Z'),
        updatedAt: DateTime.parse('2026-10-20T12:00:00Z'),
      );

      final updatedVenue = venue.copyWith(
        name: 'Sede Ramos Mejia Centro',
        isActive: false,
      );

      expect(updatedVenue.id, venue.id);
      expect(updatedVenue.name, 'Sede Ramos Mejia Centro');
      expect(updatedVenue.address, venue.address);
      expect(updatedVenue.openingTime, venue.openingTime);
      expect(updatedVenue.closingTime, venue.closingTime);
      expect(updatedVenue.isActive, isFalse);
      expect(updatedVenue.createdAt, venue.createdAt);
      expect(updatedVenue.updatedAt, venue.updatedAt);

      // La instancia original debe permanecer sin modificaciones.
      expect(venue.name, 'Sede Ramos Mejia');
      expect(venue.isActive, isTrue);
    });
  });
}
