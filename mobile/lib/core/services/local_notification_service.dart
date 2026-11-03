import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Abstraccion reemplazable para mostrar notificaciones locales.
abstract interface class LocalNotificationClient {
  Future<void> initialize();

  Future<void> show({
    required int id,
    required String title,
    required String body,
  });
}

/// Implementacion Android basada en flutter_local_notifications.
class FlutterLocalNotificationClient implements LocalNotificationClient {
  FlutterLocalNotificationClient({FlutterLocalNotificationsPlugin? plugin})
    : _plugin = plugin ?? FlutterLocalNotificationsPlugin();

  static const _channel = AndroidNotificationChannel(
    'club_notifications',
    'Notificaciones del club',
    description: 'Avisos de reservas y novedades del club.',
    importance: Importance.high,
    playSound: true,
  );

  final FlutterLocalNotificationsPlugin _plugin;

  @override
  Future<void> initialize() async {
    const settings = InitializationSettings(
      android: AndroidInitializationSettings('ic_notification'),
    );

    await _plugin.initialize(settings: settings);

    await _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >()
        ?.createNotificationChannel(_channel);
  }

  @override
  Future<void> show({
    required int id,
    required String title,
    required String body,
  }) {
    return _plugin.show(
      id: id,
      title: title,
      body: body,
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          'club_notifications',
          'Notificaciones del club',
          channelDescription: 'Avisos de reservas y novedades del club.',
          importance: Importance.high,
          priority: Priority.high,
          playSound: true,
          icon: 'ic_notification',
        ),
      ),
    );
  }
}
