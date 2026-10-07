import 'package:latlong2/latlong.dart';

class PlaceResult {
  final String name;
  final String address;
  final LatLng location;

  PlaceResult({required this.name, required this.address, required this.location});

  factory PlaceResult.fromJson(Map<String, dynamic> json) {
    String name = json['name'] ?? '';
    String address = json['display_name'] ?? '';
    double lat = double.tryParse(json['lat'].toString()) ?? 0.0;
    double lon = double.tryParse(json['lon'].toString()) ?? 0.0;
    return PlaceResult(name: name.isNotEmpty ? name : address.split(',').first, address: address, location: LatLng(lat, lon));
  }
}

class RouteResult {
  final double distance; // in meters
  final double duration; // in seconds
  final List<LatLng> geometry;

  RouteResult({required this.distance, required this.duration, required this.geometry});
}

enum NavState { idle, planning, routeFound, journeyActive, journeyCompleted, error }