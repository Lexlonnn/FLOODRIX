import 'package:flutter/material.dart';

class MyTripsScreen extends StatefulWidget {
  const MyTripsScreen({Key? key}) : super(key: key);

  @override
  State<MyTripsScreen> createState() => _MyTripsScreenState();
}

class _MyTripsScreenState extends State<MyTripsScreen> {
  bool isOngoing = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Trips', style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.grey[100],
      body: Column(
        children: [
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: GestureDetector(
                    onTap: () => setState(() => isOngoing = true),
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(color: isOngoing ? Colors.blue : Colors.transparent, borderRadius: BorderRadius.circular(24)),
                      child: Text('Ongoing', style: TextStyle(color: isOngoing ? Colors.white : Colors.grey, fontWeight: FontWeight.bold)),
                    ),
                  )
                ),
                Expanded(
                  child: GestureDetector(
                    onTap: () => setState(() => isOngoing = false),
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(color: !isOngoing ? Colors.blue : Colors.transparent, borderRadius: BorderRadius.circular(24)),
                      child: Text('Completed', style: TextStyle(color: !isOngoing ? Colors.white : Colors.grey, fontWeight: FontWeight.bold)),
                    ),
                  )
                )
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: isOngoing ? [
                _buildTripCard('Palakkad → Kochi', '4h 40m • 184 km', 'In Progress', '18% Risk', Colors.green),
              ] : [
                _buildTripCard('Thrissur → Ernakulam', '5h 10m • 210 km', 'Completed\n28 Aug 2024', '12% Risk', Colors.green),
                _buildTripCard('Kozhikode → Kochi', '4h 55m • 190 km', 'Completed\n25 Aug 2024', '35% Risk', Colors.orange),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildTripCard(String title, String subtitle, String status, String risk, Color riskColor) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: Colors.blue[50], shape: BoxShape.circle),
              child: const Icon(Icons.local_shipping, color: Colors.blue),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 4),
                  Text(subtitle, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(status, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: riskColor.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                        child: Text(risk, style: TextStyle(color: riskColor, fontSize: 12, fontWeight: FontWeight.bold)),
                      )
                    ],
                  )
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.grey)
          ],
        ),
      ),
    );
  }
}