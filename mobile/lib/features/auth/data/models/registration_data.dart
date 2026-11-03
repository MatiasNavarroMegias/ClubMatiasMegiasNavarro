/// Representa los datos requeridos para registrar una cuenta.
///
/// Esta clase existe solamente durante el formulario y la solicitud.
/// La contrasena no se almacena dentro del dispositivo.
class RegistrationData {
  const RegistrationData({
    required this.firstName,
    required this.lastName,
    required this.birthDate,
    required this.email,
    required this.password,
  });

  final String firstName;
  final String lastName;
  final DateTime birthDate;
  final String email;
  final String password;

  /// Genera el JSON esperado por POST /auth/register.
  Map<String, dynamic> toJson() {
    return {
      'first_name': firstName.trim(),
      'last_name': lastName.trim(),
      'birth_date': _formatDate(birthDate),
      'email': email.trim().toLowerCase(),
      'password': password,
    };
  }

  /// Convierte una fecha a YYYY-MM-DD sin agregar una dependencia.
  String _formatDate(DateTime value) {
    final year = value.year.toString().padLeft(4, '0');
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');

    return '$year-$month-$day';
  }
}
