import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content.strip())

# Core
env_dart = """
import 'package:flutter_dotenv/flutter_dotenv.dart';

class Env {
  static String get mapTileUrl => dotenv.env['MAP_TILE_URL'] ?? 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  static String get nominatimBaseUrl => dotenv.env['NOMINATIM_BASE_URL'] ?? 'https://nominatim.openstreetmap.org';
  static String get osrmBaseUrl => dotenv.env['OSRM_BASE_URL'] ?? 'https://router.project-osrm.org';
}
"""

dio_client_dart = """
import 'package:dio/dio.dart';

class DioClient {
  static final Dio instance = Dio();
}
"""

location_service_dart = """
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';

class LocationService {
  Future<LatLng> getCurrentLocation() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception('GPS is disabled. Please enable it.');
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        throw Exception('Location permissions are denied');
      }
    }
    
    if (permission == LocationPermission.deniedForever) {
      throw Exception('Location permissions are permanently denied.');
    }

    Position position = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
    return LatLng(position.latitude, position.longitude);
  }

  Stream<LatLng> getLocationStream() {
    return Geolocator.getPositionStream(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, distanceFilter: 10)
    ).map((Position p) => LatLng(p.latitude, p.longitude));
  }
}
"""

# Models
models_dart = """
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
"""

# Services
nominatim_service_dart = """
import '../../../core/network/dio_client.dart';
import '../../../core/config/env.dart';
import '../models/models.dart';

class NominatimService {
  Future<List<PlaceResult>> searchPlaces(String query) async {
    if (query.trim().isEmpty) return [];
    try {
      final response = await DioClient.instance.get(
        '${Env.nominatimBaseUrl}/search',
        queryParameters: {
          'q': query,
          'format': 'jsonv2',
          'limit': 5,
          'countrycodes': 'in'
        }
      );
      if (response.data is List) {
        return (response.data as List).map((e) => PlaceResult.fromJson(e)).toList();
      }
      return [];
    } catch (e) {
      throw Exception('Failed to search places: $e');
    }
  }
}
"""

osrm_service_dart = """
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
          'alternatives': 'true'
        }
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
"""

# Widgets
widgets_dart = """
import 'dart:async';
import 'package:flutter/material.dart';
import '../models/models.dart';

class SearchBarWidget extends StatefulWidget {
  final Function(String) onSearch;
  final VoidCallback onClear;
  
  const SearchBarWidget({Key? key, required this.onSearch, required this.onClear}) : super(key: key);

  @override
  State<SearchBarWidget> createState() => _SearchBarWidgetState();
}

class _SearchBarWidgetState extends State<SearchBarWidget> {
  Timer? _debounce;
  final TextEditingController _controller = TextEditingController();

  void _onChanged(String value) {
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    if (value.trim().isEmpty) {
      widget.onClear();
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 600), () {
      widget.onSearch(value);
    });
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4)]
      ),
      child: TextField(
        controller: _controller,
        onChanged: _onChanged,
        decoration: InputDecoration(
          hintText: 'Search destination...',
          prefixIcon: const Icon(Icons.search),
          suffixIcon: IconButton(
            icon: const Icon(Icons.clear),
            onPressed: () {
              _controller.clear();
              widget.onClear();
            },
          ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14)
        ),
      ),
    );
  }
}

class SearchResultsWidget extends StatelessWidget {
  final List<PlaceResult> results;
  final Function(PlaceResult) onSelect;

  const SearchResultsWidget({Key? key, required this.results, required this.onSelect}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (results.isEmpty) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.only(top: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4)]
      ),
      child: ListView.builder(
        shrinkWrap: true,
        padding: EdgeInsets.zero,
        itemCount: results.length,
        itemBuilder: (context, index) {
          final p = results[index];
          return ListTile(
            leading: const Icon(Icons.location_on, color: Colors.blue),
            title: Text(p.name, style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(p.address, maxLines: 1, overflow: TextOverflow.ellipsis),
            onTap: () => onSelect(p),
          );
        },
      ),
    );
  }
}
"""

# Screen
navigation_screen_dart = """
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../../../core/location/location_service.dart';
import '../data/nominatim_service.dart';
import '../data/osrm_service.dart';
import '../models/models.dart';
import '../widgets/widgets.dart';

class NavigationScreen extends StatefulWidget {
  const NavigationScreen({Key? key}) : super(key: key);

  @override
  State<NavigationScreen> createState() => _NavigationScreenState();
}

class _NavigationScreenState extends State<NavigationScreen> {
  final MapController _mapController = MapController();
  final LocationService _locationService = LocationService();
  final NominatimService _nominatimService = NominatimService();
  final OsrmService _osrmService = OsrmService();

  NavState _state = NavState.idle;
  String _errorMessage = '';

  LatLng? _currentLocation;
  LatLng? _destinationLocation;
  
  List<PlaceResult> _searchResults = [];
  bool _isSearching = false;

  List<RouteResult> _routes = [];
  int _selectedRouteIndex = 0;

  StreamSubscription<LatLng>? _gpsSubscription;

  @override
  void initState() {
    super.initState();
    _initLocation();
  }

  @override
  void dispose() {
    _gpsSubscription?.cancel();
    super.dispose();
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  Future<void> _initLocation() async {
    try {
      final loc = await _locationService.getCurrentLocation();
      setState(() {
        _currentLocation = loc;
      });
      _mapController.move(loc, 14.0);
    } catch (e) {
      _showError(e.toString());
      setState(() => _state = NavState.error);
    }
  }

  Future<void> _search(String query) async {
    setState(() { _isSearching = true; _searchResults = []; });
    try {
      final res = await _nominatimService.searchPlaces(query);
      setState(() { _searchResults = res; _isSearching = false; });
    } catch (e) {
      _showError(e.toString());
      setState(() { _isSearching = false; });
    }
  }

  void _onPlaceSelected(PlaceResult place) {
    setState(() {
      _destinationLocation = place.location;
      _searchResults = [];
      _state = NavState.planning;
    });
    _mapController.move(place.location, 14.0);
  }

  Future<void> _getDirections() async {
    if (_currentLocation == null || _destinationLocation == null) return;
    setState(() => _state = NavState.planning);
    try {
      final routes = await _osrmService.getRoute(_currentLocation!, _destinationLocation!);
      if (routes.isEmpty) throw Exception('No route found');
      setState(() {
        _routes = routes;
        _selectedRouteIndex = 0;
        _state = NavState.routeFound;
      });
      _fitMapToRoute(_routes[0]);
    } catch (e) {
      _showError(e.toString());
      setState(() => _state = NavState.idle);
    }
  }

  void _fitMapToRoute(RouteResult route) {
    final bounds = LatLngBounds.fromPoints(route.geometry);
    _mapController.fitCamera(CameraFit.bounds(
      bounds: bounds,
      padding: const EdgeInsets.all(50.0),
    ));
  }

  void _startJourney() {
    setState(() => _state = NavState.journeyActive);
    _fitMapToRoute(_routes[_selectedRouteIndex]);
    
    _gpsSubscription = _locationService.getLocationStream().listen((LatLng loc) {
      if (mounted) {
        setState(() {
          _currentLocation = loc;
        });
        
        // Simple completion check (distance < 50 meters)
        if (_destinationLocation != null) {
          final distance = const Distance().as(LengthUnit.Meter, loc, _destinationLocation!);
          if (distance < 50) {
            _completeJourney();
          }
        }
      }
    });
  }

  void _completeJourney() {
    _gpsSubscription?.cancel();
    setState(() {
      _state = NavState.journeyCompleted;
    });
  }

  void _endJourney() {
    _gpsSubscription?.cancel();
    setState(() {
      _state = NavState.idle;
      _routes = [];
      _destinationLocation = null;
    });
    if (_currentLocation != null) {
      _mapController.move(_currentLocation!, 14.0);
    }
  }

  String _formatDistance(double meters) {
    if (meters > 1000) return '${(meters / 1000).toStringAsFixed(1)} km';
    return '${meters.toInt()} m';
  }

  String _formatDuration(double seconds) {
    int h = seconds ~/ 3600;
    int m = (seconds % 3600) ~/ 60;
    if (h > 0) return '${h}h ${m}m';
    return '${m}m';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: const MapOptions(
              initialCenter: LatLng(10.8505, 76.2711),
              initialZoom: 7.5,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.example.floodrix',
              ),
              if (_routes.isNotEmpty)
                PolylineLayer(
                  polylines: _routes.asMap().entries.map((entry) {
                    bool isSelected = entry.key == _selectedRouteIndex;
                    return Polyline(
                      points: entry.value.geometry,
                      strokeWidth: isSelected ? 5.0 : 3.0,
                      color: isSelected ? Colors.blue : Colors.grey,
                    );
                  }).toList(),
                ),
              MarkerLayer(
                markers: [
                  if (_currentLocation != null)
                    Marker(
                      point: _currentLocation!,
                      width: 20,
                      height: 20,
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.blue,
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 2),
                        ),
                      ),
                    ),
                  if (_destinationLocation != null)
                    Marker(
                      point: _destinationLocation!,
                      width: 40,
                      height: 40,
                      child: const Icon(Icons.location_on, color: Colors.red, size: 40),
                    ),
                ],
              ),
              const RichAttributionWidget(
                attributions: [
                  TextSourceAttribution('© OpenStreetMap contributors'),
                ],
              ),
            ],
          ),
          
          // Top Search Bar
          if (_state == NavState.idle || _state == NavState.planning)
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: Colors.white,
                          child: IconButton(
                            icon: const Icon(Icons.arrow_back, color: Colors.black),
                            onPressed: () {
                              if (Navigator.canPop(context)) Navigator.pop(context);
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: SearchBarWidget(
                            onSearch: _search,
                            onClear: () => setState(() => _searchResults = []),
                          ),
                        ),
                      ],
                    ),
                    if (_isSearching) const LinearProgressIndicator(),
                    SearchResultsWidget(results: _searchResults, onSelect: _onPlaceSelected),
                  ],
                ),
              ),
            ),
            
          // Active Journey Header
          if (_state == NavState.journeyActive)
            SafeArea(
              child: Align(
                alignment: Alignment.topCenter,
                child: Container(
                  margin: const EdgeInsets.all(16),
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  decoration: BoxDecoration(color: Colors.blue[900], borderRadius: BorderRadius.circular(12)),
                  child: const Text('JOURNEY ACTIVE', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                ),
              ),
            ),

          // Recenter Button
          if (_currentLocation != null)
            Align(
              alignment: Alignment.centerRight,
              child: Padding(
                padding: const EdgeInsets.only(right: 16.0),
                child: FloatingActionButton(
                  mini: true,
                  backgroundColor: Colors.white,
                  onPressed: () => _mapController.move(_currentLocation!, 15.0),
                  child: const Icon(Icons.my_location, color: Colors.blue),
                ),
              ),
            ),
            
          // Bottom Panels
          Align(
            alignment: Alignment.bottomCenter,
            child: _buildBottomPanel(),
          )
        ],
      ),
    );
  }

  Widget _buildBottomPanel() {
    if (_state == NavState.planning) {
      return Container(
        color: Colors.white,
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('From: Current Location', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('To: Selected Destination', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _getDirections,
              child: const Text('GET DIRECTIONS'),
            )
          ],
        ),
      );
    } else if (_state == NavState.routeFound) {
      final r = _routes[_selectedRouteIndex];
      return Container(
        color: Colors.white,
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_routes.length > 1)
              SizedBox(
                height: 60,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: _routes.length,
                  itemBuilder: (ctx, i) {
                    final route = _routes[i];
                    final isSel = i == _selectedRouteIndex;
                    return GestureDetector(
                      onTap: () => setState(() { _selectedRouteIndex = i; _fitMapToRoute(route); }),
                      child: Container(
                        margin: const EdgeInsets.only(right: 8),
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          border: Border.all(color: isSel ? Colors.blue : Colors.grey),
                          borderRadius: BorderRadius.circular(8),
                          color: isSel ? Colors.blue.withOpacity(0.1) : Colors.transparent
                        ),
                        child: Column(
                          children: [
                            Text('Route ${i+1}', style: TextStyle(fontWeight: FontWeight.bold, color: isSel ? Colors.blue : Colors.black)),
                            Text('${_formatDistance(route.distance)} • ${_formatDuration(route.duration)}', style: const TextStyle(fontSize: 12)),
                          ],
                        ),
                      ),
                    );
                  }
                ),
              )
            else
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(_formatDistance(r.distance), style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  Text(_formatDuration(r.duration), style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.green)),
                ],
              ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _startJourney,
              style: ElevatedButton.styleFrom(backgroundColor: Colors.blue[700]),
              child: const Text('START JOURNEY', style: TextStyle(color: Colors.white)),
            )
          ],
        ),
      );
    } else if (_state == NavState.journeyActive) {
      final r = _routes[_selectedRouteIndex];
      return Container(
        color: Colors.white,
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Destination', style: TextStyle(color: Colors.grey)),
            const Text('Selected Destination', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Remaining', style: TextStyle(color: Colors.grey)),
                    Text(_formatDistance(r.distance), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('ETA', style: TextStyle(color: Colors.grey)),
                    Text(_formatDuration(r.duration), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.green)),
                  ],
                )
              ],
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _endJourney,
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
              child: const Text('END JOURNEY', style: TextStyle(color: Colors.white)),
            )
          ],
        ),
      );
    } else if (_state == NavState.journeyCompleted) {
      return Container(
        color: Colors.white,
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.check_circle, color: Colors.green, size: 64),
            const SizedBox(height: 16),
            const Text('Journey Completed', textAlign: TextAlign.center, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _endJourney,
              child: const Text('DONE'),
            )
          ],
        ),
      );
    }
    return const SizedBox.shrink();
  }
}
"""

def main():
    write_file('lib/core/config/env.dart', env_dart)
    write_file('lib/core/network/dio_client.dart', dio_client_dart)
    write_file('lib/core/location/location_service.dart', location_service_dart)
    write_file('lib/features/navigation/models/models.dart', models_dart)
    write_file('lib/features/navigation/data/nominatim_service.dart', nominatim_service_dart)
    write_file('lib/features/navigation/data/osrm_service.dart', osrm_service_dart)
    write_file('lib/features/navigation/widgets/widgets.dart', widgets_dart)
    write_file('lib/features/navigation/screens/navigation_screen.dart', navigation_screen_dart)
    print("Files created.")

if __name__ == '__main__':
    main()
