import 'package:club_matias_megias_navarro/features/notifications/data/services/push_installation_store.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PushInstallationStore', () {
    test('comienza sin un identificador registrado', () {
      final store = PushInstallationStore();

      expect(store.currentInstallationId, isNull);

      store.dispose();
    });

    test('conserva el ultimo identificador recibido', () {
      final store = PushInstallationStore();

      store.update('firebase-installation-id');

      expect(store.currentInstallationId, 'firebase-installation-id');

      store.dispose();
    });

    test('normaliza los espacios externos', () {
      final store = PushInstallationStore();

      store.update('  firebase-installation-id  ');

      expect(store.currentInstallationId, 'firebase-installation-id');

      store.dispose();
    });

    test('ignora identificadores vacios', () {
      final store = PushInstallationStore();

      store.update('   ');

      expect(store.currentInstallationId, isNull);

      store.dispose();
    });

    test('informa un identificador nuevo mediante el stream', () async {
      final store = PushInstallationStore();

      final emittedInstallationId = expectLater(
        store.installationIds,
        emits('firebase-installation-id'),
      );

      store.update('firebase-installation-id');

      await emittedInstallationId;

      store.dispose();
    });

    test('no vuelve a informar el mismo identificador', () async {
      final store = PushInstallationStore();
      final emittedIds = <String>[];

      final subscription = store.installationIds.listen(emittedIds.add);

      store.update('firebase-installation-id');
      store.update('firebase-installation-id');
      store.update('  firebase-installation-id  ');

      await Future<void>.delayed(Duration.zero);

      expect(emittedIds, ['firebase-installation-id']);

      await subscription.cancel();
      store.dispose();
    });

    test('reemplaza e informa un identificador diferente', () async {
      final store = PushInstallationStore();
      final emittedIds = <String>[];

      final subscription = store.installationIds.listen(emittedIds.add);

      store.update('first-installation-id');
      store.update('second-installation-id');

      await Future<void>.delayed(Duration.zero);

      expect(store.currentInstallationId, 'second-installation-id');

      expect(emittedIds, ['first-installation-id', 'second-installation-id']);

      await subscription.cancel();
      store.dispose();
    });
  });
}
