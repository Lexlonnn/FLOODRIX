import 'package:dio/dio.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/config/env.dart';
import '../models/models.dart';
import 'package:latlong2/latlong.dart';

class OsrmService {
  Future<List<RouteResult>> getRoute(LatLng origin, LatLng destination) async {
    try {
      final String coordinates = '${origin.longitude},${origin.latitude};${destination.longitude},${destination.latitude}';
      final response = await DioClient.instance.get(
        '${Env.osrmBaseUrl}/route/v1/driving/$coordinates',
        queryParameters: {
          'overview': 'full',
          'geometries': 'geojson',
          'steps': 'true',
          'alternatives': '3'
        },
        options: Options(headers: {
          'User-Agent': 'FloodrixApp/1.0.0 (contact@floodrix.app)',
        })
      );

      final data = response.data;
      if (data != null && data['routes'] != null) {
        List<RouteResult> results = [];
        for (var route in data['routes']) {
          final double distance = (route['distance'] as num).toDouble();
          final double duration = (route['duration'] as num).toDouble();
          final List coords = route['geometry']['coordinates'];
          List<LatLng> geometry = coords.map((c) => LatLng((c[1] as num).toDouble(), (c[0] as num).toDouble())).toList();
          List<RouteStep> parsedSteps = [];
          if (route['legs'] != null && route['legs'].isNotEmpty) {
            final leg = route['legs'][0];
            if (leg['steps'] != null) {
              for (var step in leg['steps']) {
                final maneuver = step['maneuver'] ?? {};
                final locationCoords = maneuver['location'];
                LatLng stepLoc = LatLng(0,0);
                if (locationCoords != null && locationCoords.length == 2) {
                  stepLoc = LatLng((locationCoords[1] as num).toDouble(), (locationCoords[0] as num).toDouble());
                }
                
                String type = maneuver['type'] ?? '';
                String modifier = maneuver['modifier'] ?? '';
                String name = step['name'] ?? '';
                double stepDist = (step['distance'] as num).toDouble();
                
                String instruction = type;
                if (modifier.isNotEmpty) instruction += ' $modifier';
                if (name.isNotEmpty) instruction += ' onto $name';
                if (instruction.trim().isEmpty) instruction = 'Continue';
                
                parsedSteps.add(RouteStep(
                  distance: stepDist,
                  instruction: instruction,
                  type: type,
                  modifier: modifier,
                  location: stepLoc
                ));
              }
            }
          }
          results.add(RouteResult(distance: distance, duration: duration, geometry: geometry, steps: parsedSteps));
        }
        return results;
      }
      throw Exception('No routes found');
    } catch (e) {
      throw Exception('Unable to calculate route: $e');
    }
  }
}