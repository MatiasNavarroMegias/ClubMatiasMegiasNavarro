import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../../core/config/api_config.dart';
import '../models/auth_session.dart';
import '../models/authenticated_user.dart';
import '../models/profile_update_data.dart';
import '../models/registration_data.dart';

/// Indica que una operacion de autenticacion no pudo completarse.
///
/// La excepcion conserva el codigo HTTP cuando el backend respondio.
/// El codigo permanece en null ante errores de conexion.
class AuthApiException implements Exception {
  const AuthApiException({required this.message, this.statusCode});

  /// Mensaje recibido desde FastAPI o generado por el cliente.
  final String message;

  /// Codigo HTTP recibido desde el backend.
  final int? statusCode;

  /// Indica que las credenciales o la sesion no son validas.
  bool get isUnauthorized => statusCode == 401;

  /// Indica que la cuenta existe, pero se encuentra inactiva.
  bool get isForbidden => statusCode == 403;

  /// Indica que el correo ya pertenece a otra cuenta.
  bool get isConflict => statusCode == 409;

  /// Indica que se alcanzo un limite temporal de intentos.
  bool get isTooManyRequests => statusCode == 429;

  /// Indica que los datos enviados no superaron la validacion.
  bool get isValidationError => statusCode == 422;

  /// Indica que el backend no pudo responder.
  bool get isConnectionError => statusCode == null;

  @override
  String toString() => message;
}

/// Administra la comunicacion con autenticacion y perfil.
///
/// El cliente permite registrar usuarios, iniciar sesion, consultar el
/// perfil autenticado y modificar sus campos editables.
class AuthApiClient {
  AuthApiClient({http.Client? httpClient, this.baseUrl = ApiConfig.baseUrl})
    : _httpClient = httpClient ?? http.Client();

  /// Cliente utilizado para ejecutar solicitudes HTTP.
  ///
  /// Puede reemplazarse por MockClient durante las pruebas.
  final http.Client _httpClient;

  /// Direccion base de FastAPI.
  final String baseUrl;

  static const Map<String, String> _jsonHeaders = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };

  /// Registra una cuenta mediante POST /auth/register.
  ///
  /// La respuesta contiene el perfil publico del usuario y nunca
  /// incluye la contrasena ni su hash.
  Future<AuthenticatedUser> register(RegistrationData registrationData) async {
    final uri = Uri.parse('$baseUrl/auth/register');

    final response = await _sendRequest(
      () => _httpClient.post(
        uri,
        headers: _jsonHeaders,
        body: jsonEncode(registrationData.toJson()),
      ),
    );

    return AuthenticatedUser.fromJson(
      _decodeJsonObject(
        response,
        invalidMessage: 'La API devolvio un usuario invalido.',
      ),
    );
  }

  /// Inicia sesion mediante POST /auth/login.
  Future<AuthSession> login({
    required String email,
    required String password,
  }) async {
    final uri = Uri.parse('$baseUrl/auth/login');

    final response = await _sendRequest(
      () => _httpClient.post(
        uri,
        headers: _jsonHeaders,
        body: jsonEncode({
          'email': email.trim().toLowerCase(),
          'password': password,
        }),
      ),
    );

    return AuthSession.fromJson(
      _decodeJsonObject(
        response,
        invalidMessage: 'La API devolvio una sesion invalida.',
      ),
    );
  }

  /// Solicita un codigo mediante POST /auth/password-recovery/request.
  ///
  /// El backend devuelve siempre un mensaje generico para no revelar
  /// si el correo pertenece a una cuenta registrada.
  Future<String> requestPasswordRecovery({required String email}) async {
    final uri = Uri.parse('$baseUrl/auth/password-recovery/request');

    final response = await _sendRequest(
      () => _httpClient.post(
        uri,
        headers: _jsonHeaders,
        body: jsonEncode({'email': email.trim().toLowerCase()}),
      ),
    );

    return _decodeMessage(
      response,
      invalidMessage: 'La API devolvio una respuesta de recuperacion invalida.',
    );
  }

  /// Confirma el codigo y establece una nueva contrasena.
  ///
  /// La nueva contrasena se envia dos veces para que FastAPI compruebe
  /// que ambos valores coincidan antes de modificar la cuenta.
  Future<String> confirmPasswordRecovery({
    required String email,
    required String code,
    required String newPassword,
    required String newPasswordConfirmation,
  }) async {
    final uri = Uri.parse('$baseUrl/auth/password-recovery/confirm');

    final response = await _sendRequest(
      () => _httpClient.post(
        uri,
        headers: _jsonHeaders,
        body: jsonEncode({
          'email': email.trim().toLowerCase(),
          'code': code.trim(),
          'new_password': newPassword,
          'new_password_confirmation': newPasswordConfirmation,
        }),
      ),
    );

    return _decodeMessage(
      response,
      invalidMessage:
          'La API devolvio una confirmacion de recuperacion invalida.',
    );
  }

  /// Obtiene el perfil asociado al token mediante GET /users/me.
  Future<AuthenticatedUser> getCurrentUser({
    required String accessToken,
  }) async {
    final uri = Uri.parse('$baseUrl/users/me');

    final response = await _sendRequest(
      () => _httpClient.get(uri, headers: _authenticatedHeaders(accessToken)),
    );

    return AuthenticatedUser.fromJson(
      _decodeJsonObject(
        response,
        invalidMessage: 'La API devolvio un usuario invalido.',
      ),
    );
  }

  /// Modifica el perfil mediante PATCH /users/me.
  ///
  /// ProfileUpdateData genera solamente los campos editables incluidos
  /// por el usuario. El correo no puede formar parte de esta solicitud.
  Future<AuthenticatedUser> updateProfile({
    required String accessToken,
    required ProfileUpdateData updateData,
  }) async {
    final uri = Uri.parse('$baseUrl/users/me');

    final response = await _sendRequest(
      () => _httpClient.patch(
        uri,
        headers: _authenticatedHeaders(accessToken),
        body: jsonEncode(updateData.toJson()),
      ),
    );

    return AuthenticatedUser.fromJson(
      _decodeJsonObject(
        response,
        invalidMessage: 'La API devolvio un usuario invalido.',
      ),
    );
  }

  /// Construye encabezados JSON con autenticacion Bearer.
  Map<String, String> _authenticatedHeaders(String accessToken) {
    return {..._jsonHeaders, 'Authorization': 'Bearer $accessToken'};
  }

  /// Ejecuta una solicitud y transforma los fallos en excepciones.
  Future<http.Response> _sendRequest(
    Future<http.Response> Function() request,
  ) async {
    try {
      final response = await request();

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response;
      }

      throw AuthApiException(
        message: _readErrorMessage(response),
        statusCode: response.statusCode,
      );
    } on AuthApiException {
      rethrow;
    } on Exception {
      throw const AuthApiException(
        message: 'No se pudo establecer una conexion con la API.',
      );
    }
  }

  /// Convierte una respuesta exitosa en un objeto JSON.
  Map<String, dynamic> _decodeJsonObject(
    http.Response response, {
    required String invalidMessage,
  }) {
    try {
      final decodedBody = jsonDecode(utf8.decode(response.bodyBytes));

      if (decodedBody is Map<String, dynamic>) {
        return decodedBody;
      }
    } on FormatException {
      // El error se transforma en AuthApiException debajo.
    }

    throw AuthApiException(
      message: invalidMessage,
      statusCode: response.statusCode,
    );
  }

  /// Obtiene el campo message de una respuesta exitosa.
  String _decodeMessage(
    http.Response response, {
    required String invalidMessage,
  }) {
    final decodedBody = _decodeJsonObject(
      response,
      invalidMessage: invalidMessage,
    );

    final message = decodedBody['message'];

    if (message is! String || message.trim().isEmpty) {
      throw AuthApiException(
        message: invalidMessage,
        statusCode: response.statusCode,
      );
    }

    return message.trim();
  }

  /// Obtiene el mensaje detail devuelto por FastAPI.
  ///
  /// Las validaciones 422 pueden devolver detail como una lista. En ese
  /// caso se busca el primer mensaje disponible.
  String _readErrorMessage(http.Response response) {
    try {
      final decodedBody = jsonDecode(utf8.decode(response.bodyBytes));

      if (decodedBody is Map<String, dynamic>) {
        final detail = decodedBody['detail'];

        if (detail is String && detail.isNotEmpty) {
          return detail;
        }

        if (detail is List && detail.isNotEmpty) {
          final firstError = detail.first;

          if (firstError is Map<String, dynamic>) {
            final message = firstError['msg'];

            if (message is String && message.isNotEmpty) {
              return message;
            }
          }
        }
      }
    } on FormatException {
      // Se utiliza el mensaje general definido debajo.
    }

    return _defaultErrorMessage(response.statusCode);
  }

  /// Traduce codigos conocidos cuando la API no entrega detail.
  String _defaultErrorMessage(int statusCode) {
    return switch (statusCode) {
      400 => 'La solicitud no pudo completarse.',
      401 => 'Las credenciales o la sesion no son validas.',
      403 => 'La cuenta de usuario se encuentra inactiva.',
      409 => 'El correo ya pertenece a una cuenta registrada.',
      422 => 'Los datos enviados no son validos.',
      429 => 'Se alcanzo la cantidad maxima de intentos.',
      _ => 'La API no pudo completar la operacion solicitada.',
    };
  }

  /// Libera los recursos utilizados por el cliente HTTP.
  void close() {
    _httpClient.close();
  }
}
