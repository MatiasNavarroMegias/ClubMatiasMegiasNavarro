import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../../core/config/api_config.dart';
import '../models/push_device.dart';

/// Indica que el registro de una instalacion push no pudo completarse.
///
/// El codigo HTTP permanece en null cuando FastAPI no pudo ser
/// contactado.
class PushDeviceApiException implements Exception {
  const PushDeviceApiException({required this.message, this.statusCode});

  /// Mensaje recibido desde FastAPI o generado por el cliente.
  final String message;

  /// Codigo HTTP recibido desde el backend.
  final int? statusCode;

  /// Indica que el token no es valido o ya vencio.
  bool get isUnauthorized => statusCode == 401;

  /// Indica que los datos enviados no superaron la validacion.
  bool get isValidationError => statusCode == 422;

  /// Indica que FastAPI no pudo ser contactado.
  bool get isConnectionError => statusCode == null;

  @override
  String toString() => message;
}

/// Administra la comunicacion con los dispositivos push.
///
/// El cliente registra el Firebase Installation ID del dispositivo
/// para asociarlo con el usuario autenticado.
class PushDeviceApiClient {
  PushDeviceApiClient({
    http.Client? httpClient,
    this.baseUrl = ApiConfig.baseUrl,
  }) : _httpClient = httpClient ?? http.Client();

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

  /// Registra una instalacion mediante POST /push-devices.
  Future<PushDevice> register({
    required String accessToken,
    required String installationId,
    required String platform,
  }) async {
    final uri = Uri.parse('$baseUrl/push-devices');

    final response = await _sendRequest(
      () => _httpClient.post(
        uri,
        headers: _authenticatedHeaders(accessToken),
        body: jsonEncode({
          'installation_id': installationId.trim(),
          'platform': platform.trim().toLowerCase(),
        }),
      ),
    );

    try {
      return PushDevice.fromJson(
        _decodeJsonObject(
          response,
          invalidMessage: 'La API devolvio un dispositivo push invalido.',
        ),
      );
    } on FormatException {
      throw PushDeviceApiException(
        message: 'La API devolvio un dispositivo push invalido.',
        statusCode: response.statusCode,
      );
    }
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

      throw PushDeviceApiException(
        message: _readErrorMessage(response),
        statusCode: response.statusCode,
      );
    } on PushDeviceApiException {
      rethrow;
    } on Exception {
      throw const PushDeviceApiException(
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
      // El error se transforma debajo en una excepcion conocida.
    }

    throw PushDeviceApiException(
      message: invalidMessage,
      statusCode: response.statusCode,
    );
  }

  /// Obtiene el mensaje detail devuelto por FastAPI.
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

  /// Traduce codigos conocidos cuando FastAPI no entrega detail.
  String _defaultErrorMessage(int statusCode) {
    return switch (statusCode) {
      401 => 'La sesion no es valida o ya vencio.',
      422 => 'Los datos enviados no son validos.',
      _ => 'La API no pudo registrar el dispositivo.',
    };
  }

  /// Libera los recursos utilizados por el cliente HTTP.
  void close() {
    _httpClient.close();
  }
}
