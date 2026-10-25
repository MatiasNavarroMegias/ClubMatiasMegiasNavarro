import 'dart:async';
import 'dart:convert';

import 'package:club_matias_megias_navarro/features/venues/data/services/venue_api_client.dart';
import 'package:club_matias_megias_navarro/features/venues/presentation/screens/venue_list_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Map<String, dynamic> venueJson({
    int id = 1,
    String name = 'Sede Ramos Mejia',
    bool isActive = true,
  }) {
    return {
      'id': id,
      'name': name,
      'address': 'Avenida de Mayo 1000',
      'opening_time': '08:00:00',
      'closing_time': '23:00:00',
      'is_active': isActive,
      'created_at': '2026-10-20T12:00:00Z',
      'updated_at': '2026-10-20T13:00:00Z',
    };
  }

  Widget createTestApp(VenueApiClient apiClient) {
    return MaterialApp(home: VenueListScreen(apiClient: apiClient));
  }

  testWidgets('muestra el indicador mientras carga las sedes', (tester) async {
    final responseCompleter = Completer<http.Response>();

    final httpClient = MockClient((request) {
      return responseCompleter.future;
    });

    final apiClient = VenueApiClient(httpClient: httpClient, baseUrl: baseUrl);

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient));

    expect(find.byKey(const Key('venue-list-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    responseCompleter.complete(
      http.Response(jsonEncode(<Map<String, dynamic>>[]), 200),
    );

    await tester.pumpAndSettle();
  });

  testWidgets('muestra las sedes obtenidas desde la API', (tester) async {
    final httpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.toString(), '$baseUrl/venues');

      return http.Response(
        jsonEncode([
          venueJson(id: 1, name: 'Sede Moron'),
          venueJson(id: 2, name: 'Sede Ramos Mejia', isActive: false),
        ]),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final apiClient = VenueApiClient(httpClient: httpClient, baseUrl: baseUrl);

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient));
    await tester.pumpAndSettle();

    expect(find.text('Seleccionar sede'), findsOneWidget);
    expect(find.byKey(const Key('venue-list')), findsOneWidget);
    expect(find.text('Sede Moron'), findsOneWidget);
    expect(find.text('Sede Ramos Mejia'), findsOneWidget);
    expect(find.text('Avenida de Mayo 1000'), findsNWidgets(2));
    expect(find.text('08:00 - 23:00'), findsNWidgets(2));
    expect(find.text('Activa'), findsOneWidget);
    expect(find.text('Inactiva'), findsOneWidget);
    expect(find.text('Ver espacios'), findsOneWidget);
    expect(find.text('Sede no disponible'), findsOneWidget);
    expect(find.byKey(const ValueKey('venue-card-1')), findsOneWidget);
    expect(find.byKey(const ValueKey('venue-card-2')), findsOneWidget);
  });

  testWidgets('muestra el estado vacio cuando no existen sedes', (
    tester,
  ) async {
    final httpClient = MockClient((request) async {
      return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
    });

    final apiClient = VenueApiClient(httpClient: httpClient, baseUrl: baseUrl);

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('venue-list-empty')), findsOneWidget);
    expect(find.text('No hay sedes disponibles'), findsOneWidget);
    expect(
      find.text('Las sedes registradas apareceran en esta pantalla.'),
      findsOneWidget,
    );
    expect(find.byIcon(Icons.location_city_outlined), findsOneWidget);
  });

  testWidgets('muestra el error recibido desde el cliente', (tester) async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({'detail': 'No se pudieron consultar las sedes.'}),
        500,
      );
    });

    final apiClient = VenueApiClient(httpClient: httpClient, baseUrl: baseUrl);

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('venue-list-error')), findsOneWidget);
    expect(find.text('No se pudieron cargar las sedes'), findsOneWidget);
    expect(find.text('No se pudieron consultar las sedes.'), findsOneWidget);
    expect(find.byKey(const Key('venue-list-retry')), findsOneWidget);
  });

  testWidgets('reintenta la consulta despues de un error', (tester) async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      if (requestCount == 1) {
        return http.Response(
          jsonEncode({'detail': 'No se pudieron consultar las sedes.'}),
          500,
        );
      }

      return http.Response(
        jsonEncode([venueJson(id: 3, name: 'Sede Recuperada')]),
        200,
      );
    });

    final apiClient = VenueApiClient(httpClient: httpClient, baseUrl: baseUrl);

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient));
    await tester.pumpAndSettle();

    expect(requestCount, 1);
    expect(find.byKey(const Key('venue-list-error')), findsOneWidget);
    expect(find.byKey(const Key('venue-list-retry')), findsOneWidget);

    await tester.tap(find.byKey(const Key('venue-list-retry')));
    await tester.pumpAndSettle();

    expect(requestCount, 2);
    expect(find.byKey(const Key('venue-list')), findsOneWidget);
    expect(find.text('Sede Recuperada'), findsOneWidget);
    expect(find.byKey(const Key('venue-list-error')), findsNothing);
  });
}
