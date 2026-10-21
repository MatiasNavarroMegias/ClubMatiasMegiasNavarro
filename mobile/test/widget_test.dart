import 'dart:convert';

import 'package:club_matias_megias_navarro/app/app.dart';
import 'package:club_matias_megias_navarro/features/venues/data/services/venue_api_client.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  testWidgets('muestra el estado vacio del listado de sedes', (tester) async {
    final httpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/venues');

      return http.Response(
        jsonEncode(<Map<String, dynamic>>[]),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final venueApiClient = VenueApiClient(
      httpClient: httpClient,
      baseUrl: 'http://example.test',
    );

    addTearDown(venueApiClient.close);

    await tester.pumpWidget(ClubApp(venueApiClient: venueApiClient));

    // Permite que la solicitud simulada termine y actualice la pantalla.
    await tester.pumpAndSettle();

    expect(find.text('Gestionar sedes'), findsOneWidget);
    expect(find.text('No hay sedes disponibles'), findsOneWidget);
    expect(
      find.text('Las sedes registradas apareceran en esta pantalla.'),
      findsOneWidget,
    );
    expect(find.byIcon(Icons.location_city_outlined), findsOneWidget);
  });
}
