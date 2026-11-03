import 'package:timezone/data/latest.dart' as timezone_data;
import 'package:timezone/timezone.dart' as timezone;

/// Centraliza la zona civil donde funciona la sede.
class ClubTime {
  ClubTime._();

  static const String zoneName = 'America/Argentina/Buenos_Aires';
  static timezone.Location? _location;

  static timezone.Location get location {
    final currentLocation = _location;
    if (currentLocation != null) {
      return currentLocation;
    }

    timezone_data.initializeTimeZones();
    final initializedLocation = timezone.getLocation(zoneName);
    _location = initializedLocation;
    return initializedLocation;
  }

  /// Construye una hora civil de la sede, independiente del dispositivo.
  static DateTime fromCivil({
    required int year,
    required int month,
    required int day,
    required int hour,
    int minute = 0,
  }) {
    return timezone.TZDateTime(location, year, month, day, hour, minute);
  }

  /// Convierte un instante recibido de la API a la hora civil de la sede.
  static DateTime fromApi(DateTime value) {
    return timezone.TZDateTime.from(value, location);
  }

  /// Devuelve la fecha y hora actuales en la zona de la sede.
  static DateTime now() {
    return timezone.TZDateTime.now(location);
  }

  /// Serializa una hora de sede con su offset real, por ejemplo -03:00.
  static String toApi(DateTime value) {
    final venueValue = timezone.TZDateTime.from(value, location);
    final offset = venueValue.timeZoneOffset;
    final sign = offset.isNegative ? '-' : '+';
    final absoluteMinutes = offset.inMinutes.abs();
    final hours = (absoluteMinutes ~/ 60).toString().padLeft(2, '0');
    final minutes = (absoluteMinutes % 60).toString().padLeft(2, '0');
    final milliseconds = venueValue.millisecond == 0
        ? ''
        : '.${venueValue.millisecond.toString().padLeft(3, '0')}';

    return '${venueValue.year.toString().padLeft(4, '0')}-'
        '${venueValue.month.toString().padLeft(2, '0')}-'
        '${venueValue.day.toString().padLeft(2, '0')}T'
        '${venueValue.hour.toString().padLeft(2, '0')}:'
        '${venueValue.minute.toString().padLeft(2, '0')}:'
        '${venueValue.second.toString().padLeft(2, '0')}'
        '$milliseconds$sign$hours:$minutes';
  }

  static String formatDate(DateTime value) {
    final venueValue = fromApi(value);
    return '${venueValue.day.toString().padLeft(2, '0')}/'
        '${venueValue.month.toString().padLeft(2, '0')}/'
        '${venueValue.year}';
  }

  static String formatTime(DateTime value) {
    final venueValue = fromApi(value);
    return '${venueValue.hour.toString().padLeft(2, '0')}:'
        '${venueValue.minute.toString().padLeft(2, '0')}';
  }
}
