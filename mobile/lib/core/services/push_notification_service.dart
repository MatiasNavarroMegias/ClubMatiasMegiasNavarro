import 'dart:developer' as developer;

import 'package:firebase_messaging/firebase_messaging.dart';

import '../../features/notifications/data/services/push_installation_store.dart';

/// Administra el registro y la recepcion de notificaciones push.
///
/// La clase utiliza una unica instancia porque Firebase Messaging
/// funciona como un servicio global dentro de la aplicacion.
class PushNotificationService {
  PushNotificationService._();

  static final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  /// Solicita permiso, registra la instalacion y configura
  /// los eventos relacionados con las notificaciones.
  static Future<void> initialize({
    required PushInstallationStore installationStore,
  }) async {
    final settings = await _messaging.requestPermission();

    developer.log(
      'Estado del permiso: ${settings.authorizationStatus}',
      name: 'PushNotificationService',
    );

    _listenForRegistration(installationStore: installationStore);
    _listenForForegroundMessages();
    _listenForOpenedNotifications();

    await _messaging.register();
  }

  /// Escucha el identificador de instalacion asignado por Firebase.
  ///
  /// El valor se conserva para enviarlo al backend una vez que exista
  /// una sesion autenticada.
  static void _listenForRegistration({
    required PushInstallationStore installationStore,
  }) {
    FirebaseMessaging.instance.onRegistered.listen(
      (installationId) {
        installationStore.update(installationId);

        developer.log(
          'Firebase Installation ID recibido.',
          name: 'PushNotificationService',
        );
      },
      onError: (Object error, StackTrace stackTrace) {
        developer.log(
          'No se pudo registrar la instalacion en Firebase.',
          name: 'PushNotificationService',
          error: error,
          stackTrace: stackTrace,
        );
      },
    );
  }

  /// Escucha mensajes recibidos mientras la aplicacion esta abierta.
  static void _listenForForegroundMessages() {
    FirebaseMessaging.onMessage.listen((message) {
      developer.log(
        'Notificacion recibida en primer plano: '
        '${message.notification?.title ?? 'Sin titulo'}',
        name: 'PushNotificationService',
      );
    });
  }

  /// Detecta cuando el usuario abre una notificacion recibida
  /// mientras la aplicacion estaba en segundo plano.
  static void _listenForOpenedNotifications() {
    FirebaseMessaging.onMessageOpenedApp.listen((message) {
      developer.log(
        'Notificacion abierta: '
        '${message.notification?.title ?? 'Sin titulo'}',
        name: 'PushNotificationService',
      );
    });
  }
}
