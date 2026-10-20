import 'dart:convert';

import 'package:club_matias_megias_navarro/features/venues/data/services/venue_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Map<String, dynamic> venueJson({
    int id = 1,
    String name = 'Sede Ramos Mejia',
  }) {
    return {
      'id': id,
      'name': name,
      'address': 'Avenida de Mayo 1000',
      'opening_time': '08:00:00',
      'closing_time': '23:00:00',
      'is_active': true,
      'created_at': '2026-10-20T12:00:00Z',
      'updated_at': '2026-10-20T13:00:00Z',
    };
  }

  group('VenueApiClient', () {
    test('getVenues obtiene y convierte el listado de sedes', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.toString(), '$baseUrl/venues');
        expect(request.headers['Accept'], 'application/json');

        return http.Response(
          jsonEncode([
            venueJson(id: 1, name: 'Sede Moron'),
            venueJson(id: 2, name: 'Sede Ramos Mejia'),
          ]),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final venues = await apiClient.getVenues();

      expect(venues, hasLength(2));
      expect(venues[0].id, 1);
      expect(venues[0].name, 'Sede Moron');
      expect(venues[1].id, 2);
      expect(venues[1].name, 'Sede Ramos Mejia');

      apiClient.close();
    });

    test('getVenue obtiene una sede mediante su identificador', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.toString(), '$baseUrl/venues/7');

        return http.Response(
          jsonEncode(venueJson(id: 7, name: 'Sede Centro')),
          200,
        );
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final venue = await apiClient.getVenue(7);

      expect(venue.id, 7);
      expect(venue.name, 'Sede Centro');
      expect(venue.openingTime, '08:00:00');
      expect(venue.closingTime, '23:00:00');

      apiClient.close();
    });

    test('createVenue envia el cuerpo esperado y devuelve la sede', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.toString(), '$baseUrl/venues');
        expect(request.headers['Content-Type'], 'application/json');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {
          'name': 'Sede Ramos Mejia',
          'address': 'Avenida de Mayo 1000',
          'opening_time': '08:00:00',
          'closing_time': '23:00:00',
        });

        return http.Response(jsonEncode(venueJson()), 201);
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final venue = await apiClient.createVenue(
        name: 'Sede Ramos Mejia',
        address: 'Avenida de Mayo 1000',
        openingTime: '08:00:00',
        closingTime: '23:00:00',
      );

      expect(venue.id, 1);
      expect(venue.name, 'Sede Ramos Mejia');
      expect(venue.isActive, isTrue);

      apiClient.close();
    });

    test('updateVenue envia solamente los cambios recibidos', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'PATCH');
        expect(request.url.toString(), '$baseUrl/venues/1');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {'name': 'Sede Ramos Mejia Centro'});

        return http.Response(
          jsonEncode(venueJson(name: 'Sede Ramos Mejia Centro')),
          200,
        );
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final venue = await apiClient.updateVenue(
        venueId: 1,
        changes: {'name': 'Sede Ramos Mejia Centro'},
      );

      expect(venue.id, 1);
      expect(venue.name, 'Sede Ramos Mejia Centro');

      apiClient.close();
    });

    test('conserva el codigo y detail de un error HTTP', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': 'No existe una sede con el identificador 999.',
          }),
          404,
        );
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        () => apiClient.getVenue(999),
        throwsA(
          isA<VenueApiException>()
              .having((error) => error.statusCode, 'statusCode', 404)
              .having(
                (error) => error.message,
                'message',
                'No existe una sede con el identificador 999.',
              ),
        ),
      );

      apiClient.close();
    });

    test('usa un mensaje general si el error no contiene JSON', () async {
      final httpClient = MockClient((request) async {
        return http.Response('Internal Server Error', 500);
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        () => apiClient.getVenues(),
        throwsA(
          isA<VenueApiException>()
              .having((error) => error.statusCode, 'statusCode', 500)
              .having(
                (error) => error.message,
                'message',
                'La API no pudo completar la operacion solicitada.',
              ),
        ),
      );

      apiClient.close();
    });

    test('rechaza un listado con estructura JSON invalida', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'id': 1, 'name': 'Sede Ramos Mejia'}),
          200,
        );
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        () => apiClient.getVenues(),
        throwsA(
          isA<VenueApiException>().having(
            (error) => error.message,
            'message',
            'La API devolvio un listado de sedes invalido.',
          ),
        ),
      );

      apiClient.close();
    });

    test('rechaza una sede con estructura JSON invalida', () async {
      final httpClient = MockClient((request) async {
        return http.Response(jsonEncode([venueJson()]), 200);
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        () => apiClient.getVenue(1),
        throwsA(
          isA<VenueApiException>().having(
            (error) => error.message,
            'message',
            'La API devolvio una sede invalida.',
          ),
        ),
      );

      apiClient.close();
    });

    test('transforma un error de conexion en VenueApiException', () async {
      final httpClient = MockClient((request) async {
        throw http.ClientException('Connection refused');
      });

      final apiClient = VenueApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        () => apiClient.getVenues(),
        throwsA(
          isA<VenueApiException>()
              .having((error) => error.statusCode, 'statusCode', isNull)
              .having(
                (error) => error.message,
                'message',
                'No se pudo establecer una conexion con la API.',
              ),
        ),
      );

      apiClient.close();
    });
  });
}
