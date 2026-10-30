import 'dart:convert';

import 'package:club_matias_megias_navarro/features/notifications/data/services/push_device_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Map<String, dynamic> pushDeviceJson({
    int id = 15,
    int userId = 7,
    String installationId = 'firebase-installation-id',
    String platform = 'android',
    bool isActive = true,
  }) {
    return {
      'id': id,
      'user_id': userId,
      'installation_id': installationId,
      'platform': platform,
      'is_active': isActive,
      'created_at': '2026-10-30T15:00:00Z',
      'updated_at': '2026-10-30T15:00:00Z',
    };
  }

  group('PushDeviceApiClient', () {
    test('register envia el FID con autenticacion Bearer', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.toString(), '$baseUrl/push-devices');
        expect(request.headers['Accept'], 'application/json');
        expect(request.headers['Content-Type'], 'application/json');
        expect(request.headers['Authorization'], 'Bearer signed-access-token');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {
          'installation_id': 'firebase-installation-id',
          'platform': 'android',
        });

        return http.Response(
          jsonEncode(pushDeviceJson()),
          201,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final apiClient = PushDeviceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      final device = await apiClient.register(
        accessToken: 'signed-access-token',
        installationId: 'firebase-installation-id',
        platform: 'android',
      );

      expect(device.id, 15);
      expect(device.userId, 7);
      expect(device.installationId, 'firebase-installation-id');
      expect(device.platform, 'android');
      expect(device.isActive, isTrue);
      expect(device.createdAt.isUtc, isTrue);
      expect(device.updatedAt.isUtc, isTrue);

      apiClient.close();
    });

    test('register normaliza el FID y la plataforma', () async {
      final httpClient = MockClient((request) async {
        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {
          'installation_id': 'firebase-installation-id',
          'platform': 'android',
        });

        return http.Response(jsonEncode(pushDeviceJson()), 201);
      });

      final apiClient = PushDeviceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      await apiClient.register(
        accessToken: 'signed-access-token',
        installationId: '  firebase-installation-id  ',
        platform: '  ANDROID  ',
      );

      apiClient.close();
    });

    test('conserva el mensaje y codigo de sesion invalida', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'No se pudo validar la sesion.'}),
          401,
        );
      });

      final apiClient = PushDeviceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.register(
          accessToken: 'expired-access-token',
          installationId: 'firebase-installation-id',
          platform: 'android',
        ),
        throwsA(
          isA<PushDeviceApiException>()
              .having((error) => error.statusCode, 'statusCode', 401)
              .having(
                (error) => error.message,
                'message',
                'No se pudo validar la sesion.',
              )
              .having(
                (error) => error.isUnauthorized,
                'isUnauthorized',
                isTrue,
              ),
        ),
      );

      apiClient.close();
    });

    test('conserva el primer error de validacion 422', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': [
              {
                'type': 'value_error',
                'loc': ['body', 'platform'],
                'msg': 'Plataforma no soportada.',
              },
            ],
          }),
          422,
        );
      });

      final apiClient = PushDeviceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.register(
          accessToken: 'signed-access-token',
          installationId: 'firebase-installation-id',
          platform: 'windows',
        ),
        throwsA(
          isA<PushDeviceApiException>()
              .having((error) => error.statusCode, 'statusCode', 422)
              .having(
                (error) => error.message,
                'message',
                'Plataforma no soportada.',
              )
              .having(
                (error) => error.isValidationError,
                'isValidationError',
                isTrue,
              ),
        ),
      );

      apiClient.close();
    });

    test('transforma errores de conexion en excepcion conocida', () async {
      final httpClient = MockClient((request) async {
        throw http.ClientException('Connection refused');
      });

      final apiClient = PushDeviceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.register(
          accessToken: 'signed-access-token',
          installationId: 'firebase-installation-id',
          platform: 'android',
        ),
        throwsA(
          isA<PushDeviceApiException>()
              .having((error) => error.statusCode, 'statusCode', isNull)
              .having(
                (error) => error.message,
                'message',
                'No se pudo establecer una conexion con la API.',
              )
              .having(
                (error) => error.isConnectionError,
                'isConnectionError',
                isTrue,
              ),
        ),
      );

      apiClient.close();
    });

    test('rechaza una respuesta exitosa con JSON invalido', () async {
      final httpClient = MockClient((request) async {
        return http.Response(jsonEncode({'unexpected': 'value'}), 201);
      });

      final apiClient = PushDeviceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.register(
          accessToken: 'signed-access-token',
          installationId: 'firebase-installation-id',
          platform: 'android',
        ),
        throwsA(
          isA<PushDeviceApiException>().having(
            (error) => error.message,
            'message',
            'La API devolvio un dispositivo push invalido.',
          ),
        ),
      );

      apiClient.close();
    });

    test('usa mensaje general ante una respuesta sin JSON', () async {
      final httpClient = MockClient((request) async {
        return http.Response('Internal Server Error', 500);
      });

      final apiClient = PushDeviceApiClient(
        httpClient: httpClient,
        baseUrl: baseUrl,
      );

      expect(
        apiClient.register(
          accessToken: 'signed-access-token',
          installationId: 'firebase-installation-id',
          platform: 'android',
        ),
        throwsA(
          isA<PushDeviceApiException>().having(
            (error) => error.message,
            'message',
            'La API no pudo registrar el dispositivo.',
          ),
        ),
      );

      apiClient.close();
    });
  });
}
