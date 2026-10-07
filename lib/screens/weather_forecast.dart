import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import '../core/config/env.dart';
import '../core/network/dio_client.dart';
import '../core/location/location_service.dart';

class WeatherForecastScreen extends StatefulWidget {
  const WeatherForecastScreen({Key? key}) : super(key: key);

  @override
  State<WeatherForecastScreen> createState() => _WeatherForecastScreenState();
}

class _WeatherForecastScreenState extends State<WeatherForecastScreen> {
  String selectedTab = 'Hourly';
  bool _isLoading = true;
  Map<String, dynamic>? _currentWeather;
  List<dynamic>? _forecast;

  @override
  void initState() {
    super.initState();
    _fetchWeather();
  }

  Future<void> _fetchWeather() async {
    try {
      final loc = await LocationService().getCurrentLocation();
      LatLng position = loc;

      final currentRes = await DioClient.instance.get(
        '${Env.apiBaseUrl}/api/v1/weather/current',
        queryParameters: {'latitude': position.latitude, 'longitude': position.longitude}
      );
      
      final forecastRes = await DioClient.instance.get(
        '${Env.apiBaseUrl}/api/v1/weather/forecast',
        queryParameters: {'latitude': position.latitude, 'longitude': position.longitude}
      );

      setState(() {
        _currentWeather = currentRes.data;
        _forecast = forecastRes.data['forecast'];
        _isLoading = false;
      });
    } catch (e) {
      print('Failed to fetch weather: $e');
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Weather Forecast', style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else if (_currentWeather != null) ...[
              const Row(
                children: [
                  Icon(Icons.location_on, color: Colors.blue),
                  SizedBox(width: 8),
                  Text('Current Location', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 32),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.cloud, color: Colors.blue, size: 80),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${_currentWeather!["temperature_c"]}°C', style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold)),
                      Text('${_currentWeather!["condition"]}', style: const TextStyle(fontSize: 18, color: Colors.grey)),
                    ],
                  )
                ],
              ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildTab('Hourly'),
                _buildTab('Daily'),
                _buildTab('7 Days'),
              ],
            ),
            const SizedBox(height: 24),
            if (selectedTab == 'Hourly' && _forecast != null)
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: _forecast!.map((f) {
                    IconData icon = Icons.cloud;
                    if (f['risk_indicator'] == 'HIGH') icon = Icons.thunderstorm;
                    if (f['risk_indicator'] == 'MODERATE') icon = Icons.water_drop;
                    
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12.0),
                      child: _buildTimeForecast(f['time'], '${f['rainfall']} mm', icon),
                    );
                  }).toList(),
                ),
              )
            else
              const Padding(
                padding: EdgeInsets.all(24.0),
                child: Text('Data not mocked for this tab', style: TextStyle(color: Colors.grey)),
              ),
            const SizedBox(height: 32),
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('Rainfall Forecast', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold))
            ),
            const SizedBox(height: 16),
            Container(
              height: 150,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(12)
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_currentWeather != null) ...[
                    Text('1-Hour Rainfall: ${_currentWeather!["rainfall_1h"]} mm', style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text('6-Hour Rainfall: ${_currentWeather!["rainfall_6h"]} mm', style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text('24-Hour Rainfall: ${_currentWeather!["rainfall_24h"]} mm', style: const TextStyle(fontWeight: FontWeight.bold)),
                  ]
                ],
              ),
            ),
            ]
          ],
        ),
      ),
    );
  }

  Widget _buildTab(String title) {
    final bool selected = selectedTab == title;
    return GestureDetector(
      onTap: () => setState(() => selectedTab = title),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? Colors.blue : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(title, style: TextStyle(color: selected ? Colors.white : Colors.black, fontWeight: FontWeight.bold)),
      ),
    );
  }

  Widget _buildTimeForecast(String time, String temp, IconData icon) {
    return Column(
      children: [
        Text(time, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Icon(icon, color: Colors.blue),
        const SizedBox(height: 8),
        Text(temp, style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}