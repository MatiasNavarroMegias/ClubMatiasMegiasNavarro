import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../../core/config/api_config.dart';
import '../models/venue.dart';

/// Indica que una operacion contra la API de sedes no pudo completarse.
///
/// La excepcion conserva el codigo HTTP y el mensaje enviado por
/// FastAPI para que la interfaz pueda mostrar un error comprensible.
class VenueApiException implements Exception {
  const VenueApiException({required this.message, this.statusCode});

  /// Mensaje recibido desde la API o generado por el cliente.
  final String message;

  /// Codigo HTTP recibido cuando existe una respuesta del servidor.
  ///
  /// El valor permanece en null cuando el servidor no pudo responder,
  /// por ejemplo, ante un problema de conexion.
  final int? statusCode;

  @override
  String toString() => message;
}

/// Administra la comunicacion HTTP con los endpoints de sedes.
///
/// El cliente transforma respuestas JSON en objetos Venue y convierte
/// los errores HTTP en VenueApiException.
class VenueApiClient {
  VenueApiClient({http.Client? httpClient, this.baseUrl = ApiConfig.baseUrl})
    : _httpClient = httpClient ?? http.Client();

  /// Cliente utilizado para ejecutar las solicitudes HTTP.
  ///
  /// Puede reemplazarse por un cliente simulado durante las pruebas.
  final http.Client _httpClient;

  /// Direccion base utilizada para construir los endpoints.
  ///
  /// El valor predeterminado se obtiene desde ApiConfig, pero puede
  /// reemplazarse durante las pruebas o para utilizar otro entorno.
  final String baseUrl;

  /// Encabezados utilizados para enviar y recibir contenido JSON.
  static const Map<String, String> _jsonHeaders = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };

  /// Obtiene todas las sedes mediante GET /venues.
  Future<List<Venue>> getVenues() async {
    final uri = Uri.parse('$baseUrl/venues');

    final response = await _sendRequest(
      () => _httpClient.get(uri, headers: _jsonHeaders),
    );

    final decodedBody = jsonDecode(utf8.decode(response.bodyBytes));

    if (decodedBody is! List) {
      throw const VenueApiException(
        message: 'La API devolvio un listado de sedes invalido.',
      );
    }

    return decodedBody
        .map((item) => Venue.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  /// Obtiene una sede mediante GET /venues/{venue_id}.
  Future<Venue> getVenue(int venueId) async {
    final uri = Uri.parse('$baseUrl/venues/$venueId');

    final response = await _sendRequest(
      () => _httpClient.get(uri, headers: _jsonHeaders),
    );

    return Venue.fromJson(_decodeJsonObject(response));
  }

  /// Crea una sede mediante POST /venues.
  ///
  /// FastAPI administra el identificador, el estado inicial y las
  /// fechas de auditoria, por lo que esos datos no se envian.
  Future<Venue> createVenue({
    required String name,
    required String address,
    required String openingTime,
    required String closingTime,
  }) async {
    final uri = Uri.parse('$baseUrl/venues');

    final response = await _sendRequest(
      () => _httpClient.post(
        uri,
        headers: _jsonHeaders,
        body: jsonEncode({
          'name': name,
          'address': address,
          'opening_time': openingTime,
          'closing_time': closingTime,
        }),
      ),
    );

    return Venue.fromJson(_decodeJsonObject(response));
  }

  /// Modifica parcialmente una sede mediante PATCH.
  ///
  /// Solamente se envian los valores incluidos dentro de changes.
  /// Por ejemplo, para cambiar solamente el nombre:
  ///
  /// {
  ///   'name': 'Sede Ramos Mejia Centro',
  /// }
  Future<Venue> updateVenue({
    required int venueId,
    required Map<String, dynamic> changes,
  }) async {
    final uri = Uri.parse('$baseUrl/venues/$venueId');

    final response = await _sendRequest(
      () => _httpClient.patch(
        uri,
        headers: _jsonHeaders,
        body: jsonEncode(changes),
      ),
    );

    return Venue.fromJson(_decodeJsonObject(response));
  }

  /// Ejecuta una solicitud y transforma los fallos en excepciones.
  ///
  /// Las respuestas con codigos entre 200 y 299 se consideran
  /// exitosas. Los demas codigos generan VenueApiException.
  Future<http.Response> _sendRequest(
    Future<http.Response> Function() request,
  ) async {
    try {
      final response = await request();

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response;
      }

      throw VenueApiException(
        message: _readErrorMessage(response),
        statusCode: response.statusCode,
      );
    } on VenueApiException {
      // Conserva las excepciones que ya contienen informacion de la API.
      rethrow;
    } on Exception {
      // Transforma errores de red, tiempo de espera u otros fallos
      // del cliente HTTP en una excepcion conocida por la interfaz.
      throw const VenueApiException(
        message: 'No se pudo establecer una conexion con la API.',
      );
    }
  }

  /// Convierte una respuesta exitosa en un objeto JSON.
  Map<String, dynamic> _decodeJsonObject(http.Response response) {
    final decodedBody = jsonDecode(utf8.decode(response.bodyBytes));

    if (decodedBody is! Map<String, dynamic>) {
      throw const VenueApiException(
        message: 'La API devolvio una sede invalida.',
      );
    }

    return decodedBody;
  }

  /// Obtiene el mensaje detail devuelto por FastAPI.
  ///
  /// Si la respuesta no contiene un objeto JSON con un detail de texto,
  /// se utiliza un mensaje general.
  String _readErrorMessage(http.Response response) {
    try {
      final decodedBody = jsonDecode(utf8.decode(response.bodyBytes));

      if (decodedBody is Map<String, dynamic>) {
        final detail = decodedBody['detail'];

        if (detail is String) {
          return detail;
        }
      }
    } on FormatException {
      // Si el cuerpo no contiene JSON, se utiliza el mensaje general.
    }

    return 'La API no pudo completar la operacion solicitada.';
  }

  /// Libera los recursos utilizados por el cliente HTTP.
  void close() {
    _httpClient.close();
  }
}
