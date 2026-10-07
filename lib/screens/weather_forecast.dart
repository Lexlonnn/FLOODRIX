import 'package:flutter/material.dart';
import '../api_mock.dart';

class WeatherForecastScreen extends StatefulWidget {
  const WeatherForecastScreen({Key? key}) : super(key: key);

  @override
  State<WeatherForecastScreen> createState() => _WeatherForecastScreenState();
}

class _WeatherForecastScreenState extends State<WeatherForecastScreen> {
  String selectedTab = 'Hourly';

  @override
  Widget build(BuildContext context) {
    final weather = ApiMockData.currentWeatherResponse;
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
            const Row(
              children: [
                Icon(Icons.location_on, color: Colors.blue),
                SizedBox(width: 8),
                Text('Kochi, Kerala', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
                    Text('${weather["temperature"]}°C', style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold)),
                    const Text('Moderate Rain', style: TextStyle(fontSize: 18, color: Colors.grey)),
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
            if (selectedTab == 'Hourly')
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildTimeForecast('Now', '28°', Icons.cloud),
                  _buildTimeForecast('1 PM', '27°', Icons.cloud),
                  _buildTimeForecast('2 PM', '26°', Icons.thunderstorm),
                  _buildTimeForecast('3 PM', '26°', Icons.thunderstorm),
                  _buildTimeForecast('4 PM', '25°', Icons.cloud),
                ],
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
              color: Colors.blue[50],
              child: const Center(child: Text('Bar Chart Mockup (Rainfall)')),
            )
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