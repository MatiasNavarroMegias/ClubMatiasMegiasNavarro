/// Representa una actualizacion parcial del perfil.
///
/// El correo no forma parte de esta clase porque el backend lo mantiene
/// inmutable.
class ProfileUpdateData {
  const ProfileUpdateData({this.firstName, this.lastName, this.birthDate});

  final String? firstName;
  final String? lastName;
  final DateTime? birthDate;

  /// Genera solamente los campos incluidos en la actualizacion.
  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};

    final receivedFirstName = firstName;
    final receivedLastName = lastName;
    final receivedBirthDate = birthDate;

    if (receivedFirstName != null) {
      json['first_name'] = receivedFirstName.trim();
    }

    if (receivedLastName != null) {
      json['last_name'] = receivedLastName.trim();
    }

    if (receivedBirthDate != null) {
      json['birth_date'] = _formatDate(receivedBirthDate);
    }

    return json;
  }

  String _formatDate(DateTime value) {
    final year = value.year.toString().padLeft(4, '0');
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');

    return '$year-$month-$day';
  }
}
