import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../../core/config/api_config.dart';
import '../models/sports_space.dart';

/// Indica que una operacion de espacios deportivos no pudo completarse.
///
/// La excepcion conserva el codigo HTTP cuando FastAPI respondio.
/// El codigo permanece en null ante errores de conexion.
class SportsSpaceApiException implements Exception {
  const SportsSpaceApiException({required this.message, this.statusCode});

  /// Mensaje recibido desde FastAPI o generado por el cliente.
  final String message;

  /// Codigo HTTP recibido desde el backend.
  final int? statusCode;

  /// Indica que el espacio solicitado no existe.
  bool get isNotFound => statusCode == 404;

  /// Indica que existe una colision con otro espacio.
  bool get isConflict => statusCode == 409;

  /// Indica que los filtros o datos enviados no son validos.
  bool get isValidationError => statusCode == 422;

  /// Indica que el servidor no pudo ser contactado.
  bool get isConnectionError => statusCode == null;

  @override
  String toString() => message;
}

/// Administra la comunicacion con los endpoints de espacios deportivos.
class SportsSpaceApiClient {
  SportsSpaceApiClient({
    http.Client? httpClient,
    this.baseUrl = ApiConfig.baseUrl,
  }) : _httpClient = httpClient ?? http.Client();

  /// Cliente utilizado para ejecutar las solicitudes HTTP.
  final http.Client _httpClient;

  /// Direccion base de FastAPI.
  final String baseUrl;

  static const Map<String, String> _jsonHeaders = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };

  /// Obtiene espacios deportivos utilizando filtros opcionales.
  ///
  /// isActive utiliza tres estados:
  ///
  /// - true: solamente espacios activos.
  /// - false: solamente espacios inactivos.
  /// - null: activos e inactivos.
  Future<List<SportsSpace>> getSportsSpaces({
    int? venueId,
    String? sportType,
    bool? isActive,
  }) async {
    final queryParameters = <String, String>{};

    if (venueId != null) {
      queryParameters['venue_id'] = venueId.toString();
    }

    final normalizedSportType = sportType?.trim();

    if (normalizedSportType != null && normalizedSportType.isNotEmpty) {
      queryParameters['sport_type'] = normalizedSportType;
    }

    if (isActive != null) {
      queryParameters['is_active'] = isActive.toString();
    }

    final uri = Uri.parse('$baseUrl/sports-spaces').replace(
      queryParameters: queryParameters.isEmpty ? null : queryParameters,
    );

    final response = await _sendRequest(
      () => _httpClient.get(uri, headers: _jsonHeaders),
    );

    return _decodeSportsSpaceList(response);
  }

  /// Obtiene un espacio mediante GET /sports-spaces/{id}.
  Future<SportsSpace> getSportsSpace(int sportsSpaceId) async {
    final uri = Uri.parse('$baseUrl/sports-spaces/$sportsSpaceId');

    final response = await _sendRequest(
      () => _httpClient.get(uri, headers: _jsonHeaders),
    );

    return SportsSpace.fromJson(
      _decodeJsonObject(
        response,
        invalidMessage: 'La API devolvio un espacio deportivo invalido.',
      ),
    );
  }

  /// Convierte una respuesta exitosa en una lista de espacios.
  List<SportsSpace> _decodeSportsSpaceList(http.Response response) {
    try {
      final decodedBody = jsonDecode(utf8.decode(response.bodyBytes));

      if (decodedBody is! List) {
        throw const SportsSpaceApiException(
          message: 'La API devolvio un listado de espacios invalido.',
        );
      }

      return decodedBody.map((item) {
        if (item is! Map<String, dynamic>) {
          throw const SportsSpaceApiException(
            message: 'La API devolvio un espacio deportivo invalido.',
          );
        }

        return SportsSpace.fromJson(item);
      }).toList();
    } on SportsSpaceApiException {
      rethrow;
    } on FormatException {
      throw const SportsSpaceApiException(
        message: 'La API devolvio un listado de espacios invalido.',
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

    throw SportsSpaceApiException(
      message: invalidMessage,
      statusCode: response.statusCode,
    );
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

      throw SportsSpaceApiException(
        message: _readErrorMessage(response),
        statusCode: response.statusCode,
      );
    } on SportsSpaceApiException {
      rethrow;
    } on Exception {
      throw const SportsSpaceApiException(
        message: 'No se pudo establecer una conexion con la API.',
      );
    }
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
      404 => 'No se encontro el espacio deportivo solicitado.',
      409 => 'El espacio deportivo entra en conflicto con otro registro.',
      422 => 'Los filtros o datos enviados no son validos.',
      _ => 'La API no pudo completar la operacion solicitada.',
    };
  }

  /// Libera los recursos del cliente HTTP.
  void close() {
    _httpClient.close();
  }
}
