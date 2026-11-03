import 'dart:convert';

import 'package:club_matias_megias_navarro/features/sports_spaces/data/services/sports_space_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Map<String, dynamic> sportsSpaceJson({
    int id = 5,
    int venueId = 2,
    String name = 'Cancha de Futbol 1',
    String sportType = 'Futbol',
    int spaceNumber = 1,
    bool isActive = true,
  }) {
    return {
      'id': id,
      'venue_id': venueId,
      'name': name,
      'sport_type': sportType,
      'space_number': spaceNumber,
      'is_active': isActive,
      'created_at': '2026-10-25T12:00:00Z',
      'updated_at': '2026-10-25T13:00:00Z',
    };
  }

  group('SportsSpaceApiClient', () {
    test('obtiene todos los espacios sin filtros', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.toString(), '$baseUrl/sports-spaces');
        expect(request.headers['Accept'], 'application/json');

        return http.Response(
          jsonEncode([
            sportsSpaceJson(),
            sportsSpaceJson(
              id: 6,
              name: 'Cancha de Tenis 1',
              sportType: 'Tenis',
            ),
          ]),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final spaces = await apiClient.getSportsSpaces();

      expect(spaces, hasLength(2));
      expect(spaces.first.id, 5);
      expect(spaces.first.sportType, 'Futbol');
      expect(spaces.last.id, 6);
      expect(spaces.last.sportType, 'Tenis');

      apiClient.close();
    });

    test('envia filtros combinados en la consulta', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.path, '/sports-spaces');
        expect(request.url.queryParameters, {
          'venue_id': '2',
          'sport_type': 'Futbol',
          'is_active': 'true',
        });

        return http.Response(jsonEncode([sportsSpaceJson()]), 200);
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final spaces = await apiClient.getSportsSpaces(
        venueId: 2,
        sportType: ' Futbol ',
        isActive: true,
      );

      expect(spaces, hasLength(1));
      expect(spaces.single.venueId, 2);

      apiClient.close();
    });

    test('envia is_active false sin omitirlo', () async {
      final httpClient = MockClient((request) async {
        expect(request.url.queryParameters, {'is_active': 'false'});

        return http.Response(
          jsonEncode([sportsSpaceJson(isActive: false)]),
          200,
        );
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final spaces = await apiClient.getSportsSpaces(isActive: false);

      expect(spaces, hasLength(1));
      expect(spaces.single.isActive, isFalse);

      apiClient.close();
    });

    test('omite el filtro deportivo vacio', () async {
      final httpClient = MockClient((request) async {
        expect(request.url.queryParameters, isEmpty);

        return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final spaces = await apiClient.getSportsSpaces(sportType: '   ');

      expect(spaces, isEmpty);

      apiClient.close();
    });

    test('obtiene un espacio mediante su identificador', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.toString(), '$baseUrl/sports-spaces/5');

        return http.Response(jsonEncode(sportsSpaceJson()), 200);
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final sportsSpace = await apiClient.getSportsSpace(5);

      expect(sportsSpace.id, 5);
      expect(sportsSpace.name, 'Cancha de Futbol 1');
      expect(sportsSpace.isActive, isTrue);

      apiClient.close();
    });

    test('conserva el mensaje y codigo de un error 404', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail':
                'No existe un espacio deportivo con el '
                'identificador 999.',
          }),
          404,
        );
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.getSportsSpace(999),
        throwsA(
          isA<SportsSpaceApiException>()
              .having((error) => error.statusCode, 'statusCode', 404)
              .having((error) => error.isNotFound, 'isNotFound', isTrue)
              .having(
                (error) => error.message,
                'message',
                'No existe un espacio deportivo con el '
                    'identificador 999.',
              ),
        ),
      );

      apiClient.close();
    });

    test('lee el primer mensaje de validacion 422', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': [
              {
                'type': 'greater_than',
                'loc': ['query', 'venue_id'],
                'msg': 'Input should be greater than 0',
              },
            ],
          }),
          422,
        );
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.getSportsSpaces(venueId: 0),
        throwsA(
          isA<SportsSpaceApiException>()
              .having((error) => error.statusCode, 'statusCode', 422)
              .having(
                (error) => error.isValidationError,
                'isValidationError',
                isTrue,
              )
              .having(
                (error) => error.message,
                'message',
                'Input should be greater than 0',
              ),
        ),
      );

      apiClient.close();
    });

    test('rechaza un listado JSON invalido', () async {
      final httpClient = MockClient((request) async {
        return http.Response(jsonEncode({'unexpected': 'object'}), 200);
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.getSportsSpaces(),
        throwsA(
          isA<SportsSpaceApiException>().having(
            (error) => error.message,
            'message',
            'La API devolvio un listado de espacios invalido.',
          ),
        ),
      );

      apiClient.close();
    });

    test('rechaza elementos invalidos dentro del listado', () async {
      final httpClient = MockClient((request) async {
        return http.Response(jsonEncode(['not-an-object']), 200);
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.getSportsSpaces(),
        throwsA(
          isA<SportsSpaceApiException>().having(
            (error) => error.message,
            'message',
            'La API devolvio un espacio deportivo invalido.',
          ),
        ),
      );

      apiClient.close();
    });

    test('transforma errores de conexion', () async {
      final httpClient = MockClient((request) async {
        throw http.ClientException('Connection refused');
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.getSportsSpaces(),
        throwsA(
          isA<SportsSpaceApiException>()
              .having((error) => error.statusCode, 'statusCode', isNull)
              .having(
                (error) => error.isConnectionError,
                'isConnectionError',
                isTrue,
              )
              .having(
                (error) => error.message,
                'message',
                'No se pudo establecer una conexion con la API.',
              ),
        ),
      );

      apiClient.close();
    });

    test('usa mensaje general para un error sin JSON', () async {
      final httpClient = MockClient((request) async {
        return http.Response('Internal Server Error', 500);
      });

      final apiClient = SportsSpaceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.getSportsSpaces(),
        throwsA(
          isA<SportsSpaceApiException>().having(
            (error) => error.message,
            'message',
            'La API no pudo completar la operacion solicitada.',
          ),
        ),
      );

      apiClient.close();
    });
  });
}
