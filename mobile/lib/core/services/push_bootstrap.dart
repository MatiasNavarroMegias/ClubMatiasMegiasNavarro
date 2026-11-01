import 'dart:async';
import 'dart:developer' as developer;

/// Inicia Firebase y las notificaciones sin bloquear la interfaz.
///
/// Las funciones se reciben como dependencias para que el arranque pueda
/// probarse sin inicializar Firebase ni acceder a servicios nativos reales.
Future<void> initializeFirebaseAndPush({
  required Future<void> Function() initializeFirebase,
  required void Function() registerBackgroundHandler,
  required Future<void> Function() initializePush,
  Duration timeout = const Duration(seconds: 10),
}) async {
  try {
    await initializeFirebase().timeout(timeout);
    registerBackgroundHandler();
    await initializePush().timeout(timeout);
  } on Object catch (error, stackTrace) {
    developer.log(
      'La inicializacion de notificaciones no se pudo completar.',
      name: 'PushBootstrap',
      error: error,
      stackTrace: stackTrace,
    );
  }
}
