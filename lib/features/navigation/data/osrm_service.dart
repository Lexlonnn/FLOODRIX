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
          results.add(RouteResult(distance: distance, duration: duration, geometry: geometry));
        }
        return results;
      }
      throw Exception('No routes found');
    } catch (e) {
      throw Exception('Unable to calculate route: $e');
    }
  }
}