import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../../core/config/api_config.dart';
import '../models/availability_slot.dart';
import '../models/reservation.dart';

/// Indica que una operacion de reservas no pudo completarse.
///
/// La excepcion conserva el codigo HTTP cuando FastAPI respondio.
/// El codigo permanece en null ante errores de conexion o respuestas
/// locales invalidas.
class ReservationApiException implements Exception {
  const ReservationApiException({required this.message, this.statusCode});

  /// Mensaje recibido desde FastAPI o generado por el cliente.
  final String message;

  /// Codigo HTTP recibido desde el backend.
  final int? statusCode;

  /// Indica que el token no es valido o ya vencio.
  bool get isUnauthorized => statusCode == 401;

  /// Indica que la cuenta autenticada no puede realizar la operacion.
  bool get isForbidden => statusCode == 403;

  /// Indica que el recurso solicitado no existe.
  bool get isNotFound => statusCode == 404;

  /// Indica que existe un conflicto con el estado actual.
  ///
  /// Puede representar un turno ocupado, una reserva ya cancelada o
  /// una reserva que ya comenzo.
  bool get isConflict => statusCode == 409;

  /// Indica que los datos enviados no superaron la validacion.
  bool get isValidationError => statusCode == 422;

  /// Indica que FastAPI no pudo ser contactado.
  bool get isConnectionError => statusCode == null;

  @override
  String toString() => message;
}

/// Administra la comunicacion con disponibilidad y reservas.
class ReservationApiClient {
  ReservationApiClient({
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

  /// Consulta los turnos disponibles de un espacio y una fecha local.
  ///
  /// FastAPI espera la fecha con formato YYYY-MM-DD.
  Future<List<AvailabilitySlot>> getAvailability({
    required int sportsSpaceId,
    required DateTime selectedDate,
  }) async {
    final uri = Uri.parse('$baseUrl/sports-spaces/$sportsSpaceId/availability')
        .replace(queryParameters: {'date': _formatDate(selectedDate)});

    final response = await _sendRequest(
      () => _httpClient.get(uri, headers: _jsonHeaders),
    );

    return _decodeAvailabilityList(response);
  }

  /// Crea una reserva para el usuario autenticado.
  ///
  /// El usuario se obtiene desde el token. El cliente envia solamente
  /// el espacio deportivo y el horario de inicio seleccionado.
  Future<Reservation> createReservation({
    required String accessToken,
    required int sportsSpaceId,
    required DateTime startAt,
  }) async {
    final uri = Uri.parse('$baseUrl/reservations');

    final response = await _sendRequest(
      () => _httpClient.post(
        uri,
        headers: _authenticatedHeaders(accessToken),
        body: jsonEncode({
          'sports_space_id': sportsSpaceId,
          'start_at': startAt.toIso8601String(),
        }),
      ),
    );

    return Reservation.fromJson(
      _decodeJsonObject(
        response,
        invalidMessage: 'La API devolvio una reserva invalida.',
      ),
    );
  }

  /// Obtiene las proximas reservas del usuario autenticado.
  Future<List<Reservation>> getUpcomingReservations({
    required String accessToken,
  }) async {
    final uri = Uri.parse('$baseUrl/reservations/upcoming');

    final response = await _sendRequest(
      () => _httpClient.get(uri, headers: _authenticatedHeaders(accessToken)),
    );

    return _decodeReservationList(
      response,
      invalidMessage:
          'La API devolvio un listado de proximas reservas invalido.',
    );
  }

  /// Obtiene el historial de reservas del usuario autenticado.
  Future<List<Reservation>> getReservationHistory({
    required String accessToken,
  }) async {
    final uri = Uri.parse('$baseUrl/reservations/history');

    final response = await _sendRequest(
      () => _httpClient.get(uri, headers: _authenticatedHeaders(accessToken)),
    );

    return _decodeReservationList(
      response,
      invalidMessage: 'La API devolvio un historial de reservas invalido.',
    );
  }

  /// Cancela una reserva futura del usuario autenticado.
  Future<Reservation> cancelReservation({
    required String accessToken,
    required int reservationId,
  }) async {
    final uri = Uri.parse('$baseUrl/reservations/$reservationId/cancel');

    final response = await _sendRequest(
      () => _httpClient.patch(uri, headers: _authenticatedHeaders(accessToken)),
    );

    return Reservation.fromJson(
      _decodeJsonObject(
        response,
        invalidMessage: 'La API devolvio una reserva cancelada invalida.',
      ),
    );
  }

  /// Construye encabezados JSON con autenticacion Bearer.
  Map<String, String> _authenticatedHeaders(String accessToken) {
    return {..._jsonHeaders, 'Authorization': 'Bearer $accessToken'};
  }

  /// Convierte una fecha local al formato YYYY-MM-DD.
  ///
  /// No utiliza toUtc porque el endpoint interpreta la fecha dentro de
  /// la zona horaria configurada por el backend.
  String _formatDate(DateTime value) {
    final year = value.year.toString().padLeft(4, '0');
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');

    return '$year-$month-$day';
  }

  /// Convierte una respuesta exitosa en una lista de turnos.
  List<AvailabilitySlot> _decodeAvailabilityList(http.Response response) {
    try {
      final decodedBody = jsonDecode(utf8.decode(response.bodyBytes));

      if (decodedBody is! List) {
        throw const ReservationApiException(
          message: 'La API devolvio un listado de horarios invalido.',
        );
      }

      return decodedBody.map((item) {
        if (item is! Map<String, dynamic>) {
          throw const ReservationApiException(
            message: 'La API devolvio un horario disponible invalido.',
          );
        }

        return AvailabilitySlot.fromJson(item);
      }).toList();
    } on ReservationApiException {
      rethrow;
    } on FormatException {
      throw const ReservationApiException(
        message: 'La API devolvio un listado de horarios invalido.',
      );
    }
  }

  /// Convierte una respuesta exitosa en una lista de reservas.
  List<Reservation> _decodeReservationList(
    http.Response response, {
    required String invalidMessage,
  }) {
    try {
      final decodedBody = jsonDecode(utf8.decode(response.bodyBytes));

      if (decodedBody is! List) {
        throw ReservationApiException(
          message: invalidMessage,
          statusCode: response.statusCode,
        );
      }

      return decodedBody.map((item) {
        if (item is! Map<String, dynamic>) {
          throw ReservationApiException(
            message: invalidMessage,
            statusCode: response.statusCode,
          );
        }

        return Reservation.fromJson(item);
      }).toList();
    } on ReservationApiException {
      rethrow;
    } on FormatException {
      throw ReservationApiException(
        message: invalidMessage,
        statusCode: response.statusCode,
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

    throw ReservationApiException(
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

      throw ReservationApiException(
        message: _readErrorMessage(response),
        statusCode: response.statusCode,
      );
    } on ReservationApiException {
      rethrow;
    } on Exception {
      throw const ReservationApiException(
        message: 'No se pudo establecer una conexion con la API.',
      );
    }
  }

  /// Obtiene el mensaje detail devuelto por FastAPI.
  ///
  /// Las respuestas 422 pueden devolver detail como una lista. En ese
  /// caso se utiliza el primer mensaje disponible.
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
      403 => 'La cuenta no puede realizar esta operacion.',
      404 => 'No se encontro la reserva o el espacio solicitado.',
      409 => 'La operacion entra en conflicto con el estado actual.',
      422 => 'Los datos enviados no son validos.',
      _ => 'La API no pudo completar la operacion solicitada.',
    };
  }

  /// Libera los recursos utilizados por el cliente HTTP.
  void close() {
    _httpClient.close();
  }
}
