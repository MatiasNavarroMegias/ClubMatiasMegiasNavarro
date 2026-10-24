/// Representa la sesion devuelta por POST /auth/login.
///
/// El access token funciona como credencial temporal y debe almacenarse
/// mediante SessionStorage, nunca dentro del codigo fuente.
class AuthSession {
  const AuthSession({required this.accessToken, required this.tokenType});

  /// Token JWT utilizado para autenticar solicitudes posteriores.
  final String accessToken;

  /// Esquema utilizado dentro del encabezado Authorization.
  final String tokenType;

  /// Construye una sesion desde la respuesta JSON del backend.
  factory AuthSession.fromJson(Map<String, dynamic> json) {
    final accessToken = json['access_token'];
    final tokenType = json['token_type'];

    if (accessToken is! String || accessToken.isEmpty) {
      throw const FormatException(
        'La API devolvio un token de acceso invalido.',
      );
    }

    if (tokenType is! String || tokenType.isEmpty) {
      throw const FormatException('La API devolvio un tipo de token invalido.');
    }

    return AuthSession(accessToken: accessToken, tokenType: tokenType);
  }
}
