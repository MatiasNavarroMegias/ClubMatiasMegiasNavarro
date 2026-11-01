import 'dart:async';
import 'dart:developer' as developer;

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';

import 'app/app.dart';
import 'core/services/push_bootstrap.dart';
import 'core/services/push_notification_service.dart';
import 'features/notifications/data/services/push_installation_store.dart';
import 'firebase_options.dart';

/// Maneja mensajes recibidos cuando la aplicacion esta cerrada
/// o en segundo plano.
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
}

/// Punto de entrada de la aplicacion.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  developer.log('Inicio de main.', name: 'AppBootstrap');

  final pushInstallationStore = PushInstallationStore();

  runApp(ClubApp(pushInstallationStore: pushInstallationStore));
  developer.log('ClubApp fue enviado a runApp.', name: 'AppBootstrap');

  unawaited(
    initializeFirebaseAndPush(
      initializeFirebase: () => Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform,
      ),
      registerBackgroundHandler: () {
        FirebaseMessaging.onBackgroundMessage(
          firebaseMessagingBackgroundHandler,
        );
      },
      initializePush: () => PushNotificationService.initialize(
        installationStore: pushInstallationStore,
      ),
    ),
  );
}
