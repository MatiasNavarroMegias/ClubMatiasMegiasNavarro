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
  developer.log('Inicio de PushBootstrap.', name: 'PushBootstrap');
  try {
    await initializeFirebase().timeout(timeout);
    developer.log('Firebase inicializado.', name: 'PushBootstrap');
    registerBackgroundHandler();
    await initializePush().timeout(timeout);
    developer.log('PushBootstrap finalizado.', name: 'PushBootstrap');
  } on Object catch (error, stackTrace) {
    developer.log(
      'La inicializacion de notificaciones no se pudo completar.',
      name: 'PushBootstrap',
      error: error,
      stackTrace: stackTrace,
    );
    developer.log('PushBootstrap finalizo con error.', name: 'PushBootstrap');
  }
}
