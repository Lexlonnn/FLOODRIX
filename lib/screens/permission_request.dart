import 'package:flutter/material.dart';

class PermissionRequestScreen extends StatefulWidget {
  const PermissionRequestScreen({Key? key}) : super(key: key);

  @override
  State<PermissionRequestScreen> createState() => _PermissionRequestScreenState();
}

class _PermissionRequestScreenState extends State<PermissionRequestScreen> {
  bool locEnabled = true;
  bool notifEnabled = true;
  bool bgLocEnabled = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
        elevation: 0,
        backgroundColor: Colors.white,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Enable Permissions', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
            const SizedBox(height: 32),
            _buildPermissionItem('Location', 'To show your live location and provide real-time alerts', Icons.location_on, Colors.green, locEnabled, (val) => setState(() => locEnabled = val)),
            const Divider(height: 32),
            _buildPermissionItem('Notifications', 'To send flood alerts and route updates', Icons.notifications, Colors.redAccent, notifEnabled, (val) => setState(() => notifEnabled = val)),
            const Divider(height: 32),
            _buildPermissionItem('Background Location', 'To track your trip even when the app is in background', Icons.security, Colors.purple, bgLocEnabled, (val) => setState(() => bgLocEnabled = val)),
            const Spacer(),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/home_dashboard'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                backgroundColor: Colors.blue[700]
              ),
              child: const Text('Continue', style: TextStyle(fontSize: 16, color: Colors.white)),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildPermissionItem(String title, String subtitle, IconData icon, Color iconColor, bool switchValue, Function(bool) onChanged) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: iconColor.withOpacity(0.1), shape: BoxShape.circle),
          child: Icon(icon, color: iconColor),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        ),
        Switch(value: switchValue, onChanged: onChanged, activeColor: Colors.blue),
      ],
    );
  }
}