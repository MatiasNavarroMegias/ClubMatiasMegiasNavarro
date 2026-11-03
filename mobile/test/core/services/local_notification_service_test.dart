import 'package:flutter_test/flutter_test.dart';

import 'package:club_matias_megias_navarro/core/services/local_notification_service.dart';

void main() {
  test('el cliente local define la interfaz de inicializacion y envio', () {
    final client = _FakeLocalNotificationClient();

    expect(client, isA<LocalNotificationClient>());
  });
}

class _FakeLocalNotificationClient implements LocalNotificationClient {
  @override
  Future<void> initialize() async {}

  @override
  Future<void> show({
    required int id,
    required String title,
    required String body,
  }) async {}
}
