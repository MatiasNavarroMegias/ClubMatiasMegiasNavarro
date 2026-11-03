import 'dart:convert';

import 'package:club_matias_megias_navarro/features/auth/data/models/profile_update_data.dart';
import 'package:club_matias_megias_navarro/features/auth/data/models/registration_data.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Map<String, dynamic> userJson({
    int id = 7,
    String firstName = 'Matias',
    String lastName = 'Megias Navarro',
    String email = 'matias@example.com',
  }) {
    return {
      'id': id,
      'first_name': firstName,
      'last_name': lastName,
      'birth_date': '2000-01-15',
      'email': email,
      'is_active': true,
      'created_at': '2026-10-23T12:00:00Z',
      'updated_at': '2026-10-23T13:00:00Z',
    };
  }

  group('AuthApiClient', () {
    test('register envia los datos y devuelve el usuario', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.toString(), '$baseUrl/auth/register');
        expect(request.headers['Accept'], 'application/json');
        expect(request.headers['Content-Type'], 'application/json');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {
          'first_name': 'Matias',
          'last_name': 'Megias Navarro',
          'birth_date': '2000-01-15',
          'email': 'matias@example.com',
          'password': 'ClaveSegura123',
        });

        return http.Response(
          jsonEncode(userJson()),
          201,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      final user = await apiClient.register(
        RegistrationData(
          firstName: ' Matias ',
          lastName: ' Megias Navarro ',
          birthDate: DateTime(2000, 1, 15),
          email: 'MATIAS@EXAMPLE.COM',
          password: 'ClaveSegura123',
        ),
      );

      expect(user.id, 7);
      expect(user.firstName, 'Matias');
      expect(user.lastName, 'Megias Navarro');
      expect(user.email, 'matias@example.com');
      expect(user.fullName, 'Matias Megias Navarro');

      apiClient.close();
    });

    test('login normaliza el correo y devuelve la sesion', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.toString(), '$baseUrl/auth/login');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {
          'email': 'matias@example.com',
          'password': 'ClaveSegura123',
        });

        return http.Response(
          jsonEncode({
            'access_token': 'signed-access-token',
            'token_type': 'bearer',
          }),
          200,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      final session = await apiClient.login(
        email: ' MATIAS@EXAMPLE.COM ',
        password: 'ClaveSegura123',
      );

      expect(session.accessToken, 'signed-access-token');
      expect(session.tokenType, 'bearer');

      apiClient.close();
    });

    test('getCurrentUser envia el encabezado Bearer', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.toString(), '$baseUrl/users/me');
        expect(request.headers['Authorization'], 'Bearer signed-access-token');

        return http.Response(jsonEncode(userJson()), 200);
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      final user = await apiClient.getCurrentUser(
        accessToken: 'signed-access-token',
      );

      expect(user.id, 7);
      expect(user.email, 'matias@example.com');
      expect(user.isActive, isTrue);

      apiClient.close();
    });

    test('updateProfile envia solamente los cambios recibidos', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'PATCH');
        expect(request.url.toString(), '$baseUrl/users/me');
        expect(request.headers['Authorization'], 'Bearer signed-access-token');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {'first_name': 'Matias Actualizado'});

        return http.Response(
          jsonEncode(userJson(firstName: 'Matias Actualizado')),
          200,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      final user = await apiClient.updateProfile(
        accessToken: 'signed-access-token',
        updateData: const ProfileUpdateData(firstName: ' Matias Actualizado '),
      );

      expect(user.firstName, 'Matias Actualizado');
      expect(user.lastName, 'Megias Navarro');
      expect(user.email, 'matias@example.com');

      apiClient.close();
    });

    test('conserva el mensaje y codigo de credenciales invalidas', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'Correo o contrasena incorrectos.'}),
          401,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.login(
          email: 'matias@example.com',
          password: 'ClaveIncorrecta123',
        ),
        throwsA(
          isA<AuthApiException>()
              .having((error) => error.statusCode, 'statusCode', 401)
              .having(
                (error) => error.message,
                'message',
                'Correo o contrasena incorrectos.',
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

    test('identifica una cuenta inactiva', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'La cuenta de usuario se encuentra inactiva.'}),
          403,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.login(
          email: 'matias@example.com',
          password: 'ClaveSegura123',
        ),
        throwsA(
          isA<AuthApiException>()
              .having((error) => error.statusCode, 'statusCode', 403)
              .having((error) => error.isForbidden, 'isForbidden', isTrue),
        ),
      );

      apiClient.close();
    });

    test('identifica un correo ya registrado', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': 'Ya existe un usuario registrado con ese correo.',
          }),
          409,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.register(
          RegistrationData(
            firstName: 'Matias',
            lastName: 'Megias Navarro',
            birthDate: DateTime(2000, 1, 15),
            email: 'matias@example.com',
            password: 'ClaveSegura123',
          ),
        ),
        throwsA(
          isA<AuthApiException>()
              .having((error) => error.statusCode, 'statusCode', 409)
              .having((error) => error.isConflict, 'isConflict', isTrue),
        ),
      );

      apiClient.close();
    });

    test('obtiene el primer mensaje de validacion 422', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': [
              {
                'type': 'value_error',
                'loc': ['body', 'password'],
                'msg': 'La contrasena no es valida.',
              },
            ],
          }),
          422,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.login(email: 'matias@example.com', password: ''),
        throwsA(
          isA<AuthApiException>()
              .having(
                (error) => error.message,
                'message',
                'La contrasena no es valida.',
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

    test('transforma errores de conexion en AuthApiException', () async {
      final httpClient = MockClient((request) async {
        throw http.ClientException('Connection refused');
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.login(
          email: 'matias@example.com',
          password: 'ClaveSegura123',
        ),
        throwsA(
          isA<AuthApiException>()
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

    test('rechaza una sesion con estructura JSON invalida', () async {
      final httpClient = MockClient((request) async {
        return http.Response(jsonEncode({'unexpected': 'value'}), 200);
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.login(
          email: 'matias@example.com',
          password: 'ClaveSegura123',
        ),
        throwsA(
          isA<FormatException>().having(
            (error) => error.message,
            'message',
            'La API devolvio un token de acceso invalido.',
          ),
        ),
      );

      apiClient.close();
    });

    test('rechaza un usuario con estructura JSON no valida', () async {
      final httpClient = MockClient((request) async {
        return http.Response(jsonEncode(['not', 'an', 'object']), 200);
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.getCurrentUser(accessToken: 'signed-access-token'),
        throwsA(
          isA<AuthApiException>().having(
            (error) => error.message,
            'message',
            'La API devolvio un usuario invalido.',
          ),
        ),
      );

      apiClient.close();
    });

    test('usa mensaje general para un error sin JSON', () async {
      final httpClient = MockClient((request) async {
        return http.Response('Internal Server Error', 500);
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.getCurrentUser(accessToken: 'signed-access-token'),
        throwsA(
          isA<AuthApiException>().having(
            (error) => error.message,
            'message',
            'La API no pudo completar la operacion solicitada.',
          ),
        ),
      );

      apiClient.close();
    });

    test('requestPasswordRecovery normaliza el correo', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(
          request.url.toString(),
          '$baseUrl/auth/password-recovery/request',
        );
        expect(request.headers['Accept'], 'application/json');
        expect(request.headers['Content-Type'], 'application/json');

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {'email': 'matias@example.com'});

        return http.Response(
          jsonEncode({
            'message':
                'Si el correo pertenece a una cuenta, '
                'recibiras instrucciones para recuperar '
                'la contrasena.',
          }),
          200,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      final message = await apiClient.requestPasswordRecovery(
        email: ' MATIAS@EXAMPLE.COM ',
      );

      expect(
        message,
        'Si el correo pertenece a una cuenta, '
        'recibiras instrucciones para recuperar '
        'la contrasena.',
      );

      apiClient.close();
    });

    test('confirmPasswordRecovery envia el codigo y las contrasenas', () async {
      final httpClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(
          request.url.toString(),
          '$baseUrl/auth/password-recovery/confirm',
        );

        final requestBody = jsonDecode(request.body) as Map<String, dynamic>;

        expect(requestBody, {
          'email': 'matias@example.com',
          'code': '48392175',
          'new_password': 'NuevaClave123',
          'new_password_confirmation': 'NuevaClave123',
        });

        return http.Response(
          jsonEncode({
            'message': 'La contrasena fue actualizada correctamente.',
          }),
          200,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      final message = await apiClient.confirmPasswordRecovery(
        email: ' MATIAS@EXAMPLE.COM ',
        code: ' 48392175 ',
        newPassword: 'NuevaClave123',
        newPasswordConfirmation: 'NuevaClave123',
      );

      expect(message, 'La contrasena fue actualizada correctamente.');

      apiClient.close();
    });

    test('confirmPasswordRecovery conserva el error 400', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail':
                'El codigo de recuperacion no es '
                'valido o ha vencido.',
          }),
          400,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.confirmPasswordRecovery(
          email: 'matias@example.com',
          code: '48392175',
          newPassword: 'NuevaClave123',
          newPasswordConfirmation: 'NuevaClave123',
        ),
        throwsA(
          isA<AuthApiException>()
              .having((error) => error.statusCode, 'statusCode', 400)
              .having(
                (error) => error.message,
                'message',
                'El codigo de recuperacion no es '
                    'valido o ha vencido.',
              ),
        ),
      );

      apiClient.close();
    });

    test('confirmPasswordRecovery identifica el limite de intentos', () async {
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail':
                'El codigo de recuperacion supero '
                'la cantidad maxima de intentos.',
          }),
          429,
        );
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.confirmPasswordRecovery(
          email: 'matias@example.com',
          code: '48392175',
          newPassword: 'NuevaClave123',
          newPasswordConfirmation: 'NuevaClave123',
        ),
        throwsA(
          isA<AuthApiException>()
              .having((error) => error.statusCode, 'statusCode', 429)
              .having(
                (error) => error.isTooManyRequests,
                'isTooManyRequests',
                isTrue,
              ),
        ),
      );

      apiClient.close();
    });

    test('requestPasswordRecovery rechaza un mensaje invalido', () async {
      final httpClient = MockClient((request) async {
        return http.Response(jsonEncode({'unexpected': 'value'}), 200);
      });

      final apiClient = AuthApiClient(httpClient: httpClient, baseUrl: baseUrl);

      expect(
        apiClient.requestPasswordRecovery(email: 'matias@example.com'),
        throwsA(
          isA<AuthApiException>().having(
            (error) => error.message,
            'message',
            'La API devolvio una respuesta '
                'de recuperacion invalida.',
          ),
        ),
      );

      apiClient.close();
    });
  });
}
