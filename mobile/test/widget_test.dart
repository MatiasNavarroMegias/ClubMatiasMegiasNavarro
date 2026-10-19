import 'package:club_matias_megias_navarro/app/app.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('muestra la estructura inicial de la aplicacion', (
    WidgetTester tester,
  ) async {
    // Construye ClubApp dentro del entorno de pruebas de Flutter.
    await tester.pumpWidget(const ClubApp());

    // Verifica el titulo mostrado en la barra superior.
    expect(find.text('ClubMatiasMegiasNavarro'), findsOneWidget);

    // Verifica el contenido temporal de la pantalla inicial.
    expect(find.text('Configuracion inicial completada'), findsOneWidget);
  });
}
