import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

import '../features/navigation/data/nominatim_service.dart';
import '../features/navigation/models/models.dart';
import '../features/navigation/widgets/widgets.dart';

class FloodRiskMapScreen extends StatefulWidget {
  const FloodRiskMapScreen({Key? key}) : super(key: key);

  @override
  State<FloodRiskMapScreen> createState() => _FloodRiskMapScreenState();
}

class _FloodRiskMapScreenState extends State<FloodRiskMapScreen> with TickerProviderStateMixin {
  final MapController _mapController = MapController();
  final NominatimService _nominatimService = NominatimService();
  
  LatLng? _currentLocation;
  LatLng? _searchedLocation;
  bool _isLoading = true;
  String? _errorMessage;
  StreamSubscription<Position>? _positionStreamSubscription;

  List<PlaceResult> _searchResults = [];
  bool _isSearching = false;

  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    
    _startLiveLocation();
  }

  @override
  void dispose() {
    _positionStreamSubscription?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _startLiveLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        throw Exception('Location services are disabled.');
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw Exception('Location permissions denied.');
        }
      }
      if (permission == LocationPermission.deniedForever) {
        throw Exception('Location permissions permanently denied.');
      }

      LocationSettings locationSettings = const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10,
      );

      _positionStreamSubscription = Geolocator.getPositionStream(locationSettings: locationSettings).listen(
        (Position position) async {
          final latLng = LatLng(position.latitude, position.longitude);
          
          String addressStr = "Current Location";
          try {
            List<Placemark> placemarks = await Geocoding().placemarkFromCoordinates(position.latitude, position.longitude);
            if (placemarks.isNotEmpty) {
              Placemark place = placemarks.first;
              // addressStr = [place.name, place.subLocality, place.locality].where((e) => e != null && e.isNotEmpty).join(", ");
            }
          } catch (e) {
            debugPrint("Geocoding error: $e");
          }

          if (mounted) {
            setState(() {
              _currentLocation = latLng;
              if (_isLoading) {
                _isLoading = false;
                _mapController.move(latLng, 15.0);
              }
              _errorMessage = null;
            });
          }
        },
        onError: (e) {
          if (mounted) {
            setState(() {
              _errorMessage = "Live location error: $e";
              _isLoading = false;
            });
          }
        }
      );

    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _handleSearch(String query) async {
    if (query.isEmpty) {
      setState(() {
        _searchResults = [];
        _isSearching = false;
      });
      return;
    }
    setState(() => _isSearching = true);
    try {
      final results = await _nominatimService.searchPlaces(query);
      if (mounted) {
        setState(() {
          _searchResults = results;
        });
      }
    } catch (e) {
      debugPrint("Search error: $e");
    }
  }

  void _onPlaceSelected(PlaceResult place) {
    setState(() {
      _searchedLocation = place.location;
      _searchResults = [];
      _isSearching = false;
    });
    _mapController.move(place.location, 16.0);
  }

  void _centerOnUser() {
    if (_currentLocation != null) {
      _mapController.move(_currentLocation!, 15.0);
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
            options: const MapOptions(
              initialCenter: LatLng(10.0, 76.0),
              initialZoom: 6.0,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.example.floodrix',
              ),
              MarkerLayer(
                markers: [
                  if (_currentLocation != null)
                    Marker(
                      point: _currentLocation!,
                      width: 60,
                      height: 60,
                      child: AnimatedBuilder(
                        animation: _pulseController,
                        builder: (context, child) {
                          return Stack(
                            alignment: Alignment.center,
                            children: [
                              Container(
                                width: 24 + (_pulseController.value * 20),
                                height: 24 + (_pulseController.value * 20),
                                decoration: BoxDecoration(
                                  color: Colors.blue.withOpacity(0.3 - (_pulseController.value * 0.3)),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              Container(
                                width: 20,
                                height: 20,
                                decoration: BoxDecoration(
                                  color: Colors.blue.shade600,
                                  shape: BoxShape.circle,
                                  border: Border.all(color: Colors.white, width: 3),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.2),
                                      blurRadius: 6,
                                      offset: const Offset(0, 2),
                                    )
                                  ],
                                ),
                              ),
                            ],
                          );
                        },
                      ),
                    ),
                  if (_searchedLocation != null)
                    Marker(
                      point: _searchedLocation!,
                      width: 50,
                      height: 50,
                      child: const Icon(
                        Icons.location_on,
                        color: Colors.red,
                        size: 40,
                      ),
                    ),
                ],
              ),
            ],
          ),

          // Top Floating Search Bar
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              child: Column(
                children: [
                  Row(
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 8,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: IconButton(
                          icon: const Icon(Icons.arrow_back, color: Colors.black87),
                          onPressed: () {
                            if (Navigator.canPop(context)) Navigator.pop(context);
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: SearchBarWidget(
                          onSearch: _handleSearch,
                          onClear: () {
                            setState(() {
                              _searchResults = [];
                              _isSearching = false;
                              _searchedLocation = null;
                            });
                          },
                          hintText: 'Search for a place...',
                          prefixIcon: Icons.search,
                          prefixIconColor: Colors.blue.shade600,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 8,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Image.asset(
                            'assets/floodrix_logo.png',
                            fit: BoxFit.contain,
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (_isSearching && _searchResults.isNotEmpty)
                    SearchResultsWidget(
                      results: _searchResults,
                      onSelect: _onPlaceSelected,
                    ),
                ],
              ),
            ),
          ),

          // Right side Floating Action Buttons
          Positioned(
            right: 16,
            bottom: 110,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildFab(
                  icon: Icons.layers,
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Map layers coming soon")),
                    );
                  },
                ),
                const SizedBox(height: 12),
                _buildFab(
                  icon: Icons.my_location,
                  onPressed: _centerOnUser,
                  iconColor: Colors.blue.shade600,
                ),
              ],
            ),
          ),

          // Error Message
          if (_errorMessage != null)
            SafeArea(
              child: Align(
                alignment: Alignment.topCenter,
                child: Container(
                  margin: const EdgeInsets.only(top: 80),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.red.shade600,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.2),
                        blurRadius: 6,
                        offset: const Offset(0, 2),
                      ),
                    ]
                  ),
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
                  ),
                ),
              ),
            ),

          // Flood Risk Legend - Bottom Left
          Positioned(
            left: 16,
            bottom: 110,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.15),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Flood Risk Level',
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: Colors.black87),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _buildRiskBar(Colors.green.shade400, 'Low'),
                      _buildRiskBar(Colors.yellow.shade400, 'Med'),
                      _buildRiskBar(Colors.red.shade400, 'High'),
                    ],
                  ),
                ],
              ),
            ),
          ),

          if (_isLoading)
            Container(
              color: Colors.white.withOpacity(0.5),
              child: const Center(
                child: CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                ),
              ),
            ),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, -5),
            ),
          ],
        ),
        child: BottomNavigationBar(
          type: BottomNavigationBarType.fixed,
          currentIndex: 1, // Map is selected
          selectedItemColor: Colors.blue.shade700,
          unselectedItemColor: Colors.grey.shade500,
          backgroundColor: Colors.white,
          elevation: 0,
          selectedFontSize: 12,
          unselectedFontSize: 12,
          iconSize: 26,
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.home_rounded), label: 'Home'),
            BottomNavigationBarItem(icon: Icon(Icons.map_rounded), label: 'Map'),
            BottomNavigationBarItem(icon: Icon(Icons.directions_bus_rounded), label: 'Trips'),
            BottomNavigationBarItem(icon: Icon(Icons.notifications_rounded), label: 'Alerts'),
            BottomNavigationBarItem(icon: Icon(Icons.person_rounded), label: 'Profile'),
          ],
          onTap: (index) {
            if(index == 0) Navigator.pushNamedAndRemoveUntil(context, '/home_dashboard', (route) => false);
            if(index == 2) Navigator.pushNamed(context, '/my_trips');
            if(index == 3) Navigator.pushNamed(context, '/live_alerts');
            if(index == 4) Navigator.pushNamed(context, '/profile_settings');
          },
        ),
      ),
    );
  }

  Widget _buildFab({required IconData icon, required VoidCallback onPressed, Color iconColor = Colors.black87}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.15),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          customBorder: const CircleBorder(),
          onTap: onPressed,
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Icon(icon, color: iconColor, size: 26),
          ),
        ),
      ),
    );
  }

  Widget _buildRiskBar(Color color, String label) {
    return Container(
      margin: const EdgeInsets.only(right: 2),
      child: Column(
        children: [
          Container(
            width: 32,
            height: 6,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(fontSize: 10, color: Colors.grey.shade700, fontWeight: FontWeight.w600),
          )
        ],
      ),
    );
  }
}