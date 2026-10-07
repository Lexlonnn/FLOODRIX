import 'package:flutter/material.dart';
import '../api_mock.dart';

class PlanTripScreen extends StatefulWidget {
  const PlanTripScreen({Key? key}) : super(key: key);

  @override
  State<PlanTripScreen> createState() => _PlanTripScreenState();
}

class _PlanTripScreenState extends State<PlanTripScreen> {
  String cargoType = 'perishable';
  TimeOfDay? selectedTime;

  @override
  void initState() {
    super.initState();
    cargoType = ApiMockData.planRouteRequest["cargo_type"];
  }

  Future<void> _selectTime(BuildContext context) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (picked != null && picked != selectedTime) {
      setState(() {
        selectedTime = picked;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Plan Your Trip', style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildInputField('From', 'Palakkad, Kerala', Icons.location_on, Colors.blue),
            const SizedBox(height: 16),
            _buildInputField('To', 'Kochi, Kerala', Icons.location_on, Colors.red),
            const SizedBox(height: 24),
            const Text('Cargo Type', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300),
                borderRadius: BorderRadius.circular(8)
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: cargoType,
                  isExpanded: true,
                  items: const [
                    DropdownMenuItem(value: 'perishable', child: Text('Fruits & Vegetables (Perishable)')),
                    DropdownMenuItem(value: 'electronics', child: Text('Electronics')),
                    DropdownMenuItem(value: 'general', child: Text('General Cargo')),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => cargoType = val);
                  },
                ),
              ),
            ),
            const SizedBox(height: 24),
            const Text('Departure Time', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            GestureDetector(
              onTap: () => _selectTime(context),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8)
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(selectedTime == null ? 'Now' : selectedTime!.format(context)),
                    const Icon(Icons.calendar_today, color: Colors.grey, size: 20)
                  ],
                ),
              ),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/route_options'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue[700],
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
              ),
              child: const Text('Find Safe Routes', style: TextStyle(color: Colors.white, fontSize: 16)),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildInputField(String label, String hint, IconData icon, Color iconColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        TextField(
          controller: TextEditingController(text: hint),
          decoration: InputDecoration(
            prefixIcon: Icon(icon, color: iconColor),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            contentPadding: const EdgeInsets.symmetric(vertical: 14)
          ),
        )
      ],
    );
  }
}