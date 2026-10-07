import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../../../core/location/location_service.dart';
import '../data/nominatim_service.dart';
import '../data/osrm_service.dart';
import '../models/models.dart';
import '../widgets/widgets.dart';
import 'package:intl/intl.dart';
import 'package:flutter_compass/flutter_compass.dart';

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

  LatLng? _currentLocation;
  double _currentHeading = 0.0;
  double _currentSpeed = 0.0;
  
  PlaceResult? _originPlace; 
  PlaceResult? _destinationPlace;
  
  List<PlaceResult> _searchResults = [];
  bool _isSearching = false;
  bool _searchingForOrigin = false;

  List<RouteResult> _routes = [];
  int _selectedRouteIndex = 0;
  int _currentStepIndex = 0;

  StreamSubscription<Position>? _gpsSubscription;
  StreamSubscription<CompassEvent>? _compassSubscription;
  bool _autoTracking = true;
  bool _isMuted = false;

  @override
  void initState() {
    super.initState();
    _initLocation();
    _initCompass();
  }

  void _initCompass() {
    _compassSubscription = FlutterCompass.events?.listen((event) {
      if (mounted && event.heading != null) {
        setState(() {
          _currentHeading = event.heading!;
        });
      }
    });
  }

  @override
  void dispose() {
    _gpsSubscription?.cancel();
    _compassSubscription?.cancel();
    super.dispose();
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red.shade800));
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

  Future<void> _search(String query, {required bool forOrigin}) async {
    setState(() { _isSearching = true; _searchResults = []; _searchingForOrigin = forOrigin; });
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
      if (_searchingForOrigin) {
        _originPlace = place;
      } else {
        _destinationPlace = place;
      }
      _searchResults = [];
      if (_destinationPlace != null) {
        _state = NavState.planning;
      }
    });
    
    if (_destinationPlace != null) {
      _mapController.move(_destinationPlace!.location, 14.0);
      _getDirections(); 
    }
  }

  Future<void> _getDirections() async {
    final origin = _originPlace?.location ?? _currentLocation;
    if (origin == null || _destinationPlace == null) return;
    
    setState(() => _state = NavState.planning);
    try {
      final routes = await _osrmService.getRoute(origin, _destinationPlace!.location);
      if (routes.isEmpty) throw Exception('No route found');
      
      routes.sort((a, b) => a.duration.compareTo(b.duration));
      
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
      padding: const EdgeInsets.only(top: 150.0, bottom: 250.0, left: 40.0, right: 40.0), 
    ));
  }

  void _startJourney() {
    setState(() {
      _state = NavState.journeyActive;
      _autoTracking = true;
      _currentStepIndex = 0;
    });
    
    if (_currentLocation != null) {
      _mapController.move(_currentLocation!, 18.0);
    }
    
    _gpsSubscription = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, distanceFilter: 2)
    ).listen((Position position) {
      if (mounted) {
        final loc = LatLng(position.latitude, position.longitude);
        setState(() {
          _currentLocation = loc;
          _currentSpeed = position.speed; // meters per second
        });
        
        if (_autoTracking) {
          _mapController.move(loc, _mapController.camera.zoom);
        }
        
        if (_routes.isNotEmpty) {
          final r = _routes[_selectedRouteIndex];
          if (_currentStepIndex < r.steps.length) {
            final distToStep = const Distance().as(LengthUnit.Meter, loc, r.steps[_currentStepIndex].location);
            if (distToStep < 30 && _currentStepIndex < r.steps.length - 1) {
              _currentStepIndex++;
            }
          }
        }
        
        if (_destinationPlace != null) {
          final distance = const Distance().as(LengthUnit.Meter, loc, _destinationPlace!.location);
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
      _destinationPlace = null;
      _originPlace = null;
      _mapController.rotate(0);
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
    if (h > 0) return '${h} hr ${m} min';
    return '${m} min';
  }

  String _formatETA(double seconds) {
    final eta = DateTime.now().add(Duration(seconds: seconds.toInt()));
    return DateFormat.jm().format(eta);
  }

  void _recenter() {
    setState(() {
      _autoTracking = true;
    });
    if (_currentLocation != null) {
      _mapController.move(_currentLocation!, 18.0);
    }
  }

  void _locateMe() {
    if (_currentLocation != null) {
      _mapController.move(_currentLocation!, 15.0);
      _mapController.rotate(0);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: LatLng(10.8505, 76.2711),
              initialZoom: 7.5,
              onPositionChanged: (position, hasGesture) {
                if (hasGesture && _state == NavState.journeyActive && _autoTracking) {
                  setState(() { _autoTracking = false; });
                }
              },
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
                      strokeWidth: isSelected ? (_state == NavState.journeyActive ? 8.0 : 6.0) : 4.0,
                      color: isSelected ? Colors.blue.shade700 : Colors.blueGrey.withOpacity(0.5),
                      borderStrokeWidth: isSelected ? 3.0 : 0.0,
                      borderColor: Colors.blue.shade900,
                    );
                  }).toList().reversed.toList(),
                ),
              MarkerLayer(
                markers: [
                  if (_currentLocation != null && _originPlace == null && _state != NavState.journeyActive)
                    Marker(
                      point: _currentLocation!,
                      width: 24,
                      height: 24,
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.blueAccent.shade400,
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 3),
                          boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 6)]
                        ),
                      ),
                    ),
                  if (_originPlace != null && _state != NavState.journeyActive)
                    Marker(
                      point: _originPlace!.location,
                      width: 32,
                      height: 32,
                      child: const Icon(Icons.adjust, color: Colors.blueAccent, size: 28),
                    ),
                  if (_destinationPlace != null)
                    Marker(
                      point: _destinationPlace!.location,
                      width: 48,
                      height: 48,
                      alignment: Alignment.topCenter,
                      child: Icon(Icons.location_on, color: Colors.red.shade600, size: 48),
                    ),
                    
                  // Navigation Arrow Marker
                  if (_state == NavState.journeyActive && _currentLocation != null)
                    Marker(
                      point: _currentLocation!,
                      width: 60,
                      height: 60,
                      child: Transform.rotate(
                        angle: _currentHeading * (math.pi / 180),
                        child: Container(
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withOpacity(0.5),
                          ),
                          child: Stack(
                            alignment: Alignment.center,
                            children: [
                              Icon(Icons.navigation, color: Colors.blue.shade700, size: 40),
                            ],
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ],
          ),
          
          // Top UI: Search Bars
          if (_state != NavState.journeyActive && _state != NavState.journeyCompleted)
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                child: Column(
                  children: [
                    _buildTopPanel(),
                    if (_isSearching) 
                       const Padding(
                         padding: EdgeInsets.only(top: 8),
                         child: LinearProgressIndicator(),
                       ),
                    if (_searchResults.isNotEmpty)
                       Expanded(child: SearchResultsWidget(results: _searchResults, onSelect: _onPlaceSelected)),
                  ],
                ),
              ),
            ),
            
          // Active Journey Header (Dynamic Style)
          if (_state == NavState.journeyActive && _routes.isNotEmpty && _routes[_selectedRouteIndex].steps.isNotEmpty)
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F5132), 
                        borderRadius: BorderRadius.circular(16), 
                        boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 10)]
                      ),
                      child: Row(
                        children: [
                          Icon(_getTurnIcon(_routes[_selectedRouteIndex].steps[_currentStepIndex].modifier), color: Colors.white, size: 48),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(_formatDistance(_routes[_selectedRouteIndex].steps[_currentStepIndex].distance), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 24)),
                                Text(_routes[_selectedRouteIndex].steps[_currentStepIndex].instruction, style: const TextStyle(color: Colors.white, fontSize: 18), maxLines: 2, overflow: TextOverflow.ellipsis),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_currentStepIndex + 1 < _routes[_selectedRouteIndex].steps.length)
                      Container(
                        margin: const EdgeInsets.only(top: 4),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F5132),
                          borderRadius: BorderRadius.circular(8),
                          boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)]
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text('Then ', style: TextStyle(color: Colors.white, fontSize: 16)),
                            Icon(_getTurnIcon(_routes[_selectedRouteIndex].steps[_currentStepIndex+1].modifier), color: Colors.white, size: 20),
                          ],
                        ),
                      )
                  ],
                ),
              ),
            ),

          // Speed Indicator
          if (_state == NavState.journeyActive)
            Positioned(
              left: 16,
              bottom: 120,
              child: Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.grey.shade300, width: 2),
                  boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 8)]
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      _currentSpeed > 0 ? (_currentSpeed * 3.6).toStringAsFixed(0) : '0',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                    ),
                    const Text('km/h', style: TextStyle(fontSize: 10, color: Colors.grey)),
                  ],
                ),
              ),
            ),

          // Right Side Floating Buttons (Active Journey)
          if (_state == NavState.journeyActive)
            Positioned(
              right: 16,
              bottom: 200,
              child: Column(
                children: [
                  _buildMapFab(Icons.explore_outlined, () {
                    _mapController.rotate(0);
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Map oriented to North"), duration: Duration(seconds: 1)));
                  }),
                  const SizedBox(height: 12),
                  _buildMapFab(_isMuted ? Icons.volume_off : Icons.volume_up, () {
                    setState(() => _isMuted = !_isMuted);
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_isMuted ? "Voice navigation muted" : "Voice navigation unmuted"), duration: const Duration(seconds: 1)));
                  }),
                  const SizedBox(height: 12),
                  if (_routes.length > 1)
                    _buildMapFab(Icons.alt_route, () {
                      setState(() {
                        _selectedRouteIndex = (_selectedRouteIndex + 1) % _routes.length;
                        _fitMapToRoute(_routes[_selectedRouteIndex]);
                      });
                    }),
                ],
              ),
            ),
            
          // My Location Button (Idle / Planning State)
          if (_state != NavState.journeyActive && _state != NavState.journeyCompleted)
            Positioned(
              right: 16,
              bottom: _state == NavState.routeFound ? 260 : 40,
              child: FloatingActionButton(
                heroTag: 'locate_me_fab',
                backgroundColor: Colors.white,
                onPressed: _locateMe,
                child: Icon(Icons.my_location, color: Colors.blue.shade700),
              ),
            ),
            
          // Recenter Button (Active Journey)
          if (_state == NavState.journeyActive && !_autoTracking)
            Positioned(
              right: 16,
              bottom: 120,
              child: GestureDetector(
                onTap: _recenter,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 8)]
                  ),
                  child: Row(
                    children: const [
                      Icon(Icons.my_location, color: Colors.blue),
                      SizedBox(width: 8),
                      Text('Re-center', style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold)),
                    ],
                  ),
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

  IconData _getTurnIcon(String modifier) {
    switch (modifier.toLowerCase()) {
      case 'left':
      case 'sharp left':
      case 'slight left':
        return Icons.turn_left;
      case 'right':
      case 'sharp right':
      case 'slight right':
        return Icons.turn_right;
      case 'uturn':
        return Icons.u_turn_left;
      default:
        return Icons.straight;
    }
  }

  Widget _buildMapFab(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 48,
        height: 48,
        decoration: const BoxDecoration(
          color: Colors.white,
          shape: BoxShape.circle,
          boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 6)]
        ),
        child: Icon(icon, color: Colors.black87),
      ),
    );
  }

  Widget _buildTopPanel() {
    if (_state == NavState.routeFound || _state == NavState.planning) {
      return Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 12, offset: const Offset(0, 4))]
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: () {
                setState(() {
                  _state = NavState.idle;
                  _destinationPlace = null;
                  _originPlace = null;
                  _routes = [];
                  _searchResults = [];
                });
              },
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                children: [
                  SearchBarWidget(
                    hintText: _originPlace?.name ?? 'Your location',
                    prefixIcon: Icons.my_location,
                    prefixIconColor: Colors.blue.shade600,
                    showShadow: false,
                    onSearch: (q) => _search(q, forOrigin: true),
                    onClear: () {
                      setState(() => _originPlace = null);
                      _getDirections();
                    },
                  ),
                  const SizedBox(height: 8),
                  SearchBarWidget(
                    hintText: _destinationPlace?.name ?? 'Choose destination',
                    prefixIcon: Icons.location_on,
                    prefixIconColor: Colors.red.shade600,
                    showShadow: false,
                    onSearch: (q) => _search(q, forOrigin: false),
                    onClear: () => setState(() {
                      _destinationPlace = null;
                      _routes = [];
                      _state = NavState.idle;
                    }),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    } else {
      // Idle state
      return SearchBarWidget(
        hintText: 'Search here',
        onSearch: (q) => _search(q, forOrigin: false),
        onClear: () => setState(() => _searchResults = []),
      );
    }
  }

  Widget _buildBottomPanel() {
    if (_state == NavState.planning) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: const Center(child: CircularProgressIndicator()),
      );
    } else if (_state == NavState.routeFound) {
      return Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
          boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 16, offset: Offset(0,-4))]
        ),
        child: SafeArea(
          top: false,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Pull handle indicator
              Container(
                margin: const EdgeInsets.only(top: 12, bottom: 12),
                height: 4,
                width: 40,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              if (_routes.length > 1)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: _routes.asMap().entries.map((entry) {
                        final i = entry.key;
                        final route = entry.value;
                        final isSel = i == _selectedRouteIndex;
                        return GestureDetector(
                          onTap: () => setState(() { _selectedRouteIndex = i; _fitMapToRoute(route); }),
                          child: Container(
                           margin: const EdgeInsets.only(right: 12),
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            decoration: BoxDecoration(
                              color: isSel ? Colors.blue.shade50 : Colors.white,
                              border: Border.all(
                                color: isSel ? Colors.blue.shade300 : Colors.grey.shade300,
                                width: isSel ? 2 : 1,
                              ),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Column(
                              children: [
                                Text(_formatDuration(route.duration), 
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold, 
                                    fontSize: 16, 
                                    color: isSel ? Colors.blue.shade700 : Colors.black87
                                  )
                                ),
                                const SizedBox(height: 4),
                                Text(_formatDistance(route.distance), 
                                  style: TextStyle(
                                    fontSize: 13, 
                                    color: Colors.grey.shade600
                                  )
                                ),
                              ],
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ),
              Padding(
                padding: const EdgeInsets.all(24),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(_formatDuration(_routes[_selectedRouteIndex].duration), 
                            style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: Colors.green.shade700)
                          ),
                          const SizedBox(height: 4),
                          Text(_formatDistance(_routes[_selectedRouteIndex].distance), 
                            style: TextStyle(fontSize: 16, color: Colors.grey.shade600, fontWeight: FontWeight.w500)
                          ),
                        ],
                      ),
                    ),
                    ElevatedButton(
                      onPressed: _startJourney,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blueAccent.shade400,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                        elevation: 0,
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.navigation_rounded),
                          SizedBox(width: 8),
                          Text('Start', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ],
                      ),
                    )
                  ],
                ),
              )
            ],
          ),
        ),
      );
    } else if (_state == NavState.journeyActive) {
      final r = _routes[_selectedRouteIndex];
      // Updated Navigation Bottom Panel
      return Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 16, offset: Offset(0,-4))]
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        child: SafeArea(
          top: false,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              GestureDetector(
                onTap: _endJourney,
                child: Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.grey.shade300, width: 2),
                  ),
                  child: const Icon(Icons.close, color: Colors.black54, size: 28),
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Row(
                    children: [
                      Text(_formatDuration(r.duration), 
                        style: TextStyle(fontWeight: FontWeight.w800, fontSize: 32, color: Colors.orange.shade700)
                      ),
                      const SizedBox(width: 8),
                      const Icon(Icons.eco, color: Colors.green, size: 20), // Eco icon
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text('${_formatDistance(r.distance)} • ${_formatETA(r.duration)}', 
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 16, fontWeight: FontWeight.w500)
                  ),
                ],
              ),
              const SizedBox(width: 52), // Padding to balance the X button
            ],
          ),
        ),
      );
    } else if (_state == NavState.journeyCompleted) {
      return Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
        ),
        padding: const EdgeInsets.all(40),
        child: SafeArea(
          top: false,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Icon(Icons.check_circle, color: Colors.green.shade500, size: 80),
              const SizedBox(height: 24),
              const Text('You have arrived!', textAlign: TextAlign.center, style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: _endJourney,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent.shade400,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                  elevation: 0,
                ),
                child: const Text('Done', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              )
            ],
          ),
        ),
      );
    }
    return const SizedBox.shrink();
  }
}