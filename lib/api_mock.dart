
class ApiMockData {
  static const Map<String, dynamic> planRouteRequest = {
    "origin": {"latitude": 10.7867, "longitude": 76.6548},
    "destination": {"latitude": 9.9312, "longitude": 76.2673},
    "cargo_type": "perishable",
    "departure_time": "2026-10-07T11:00:00+05:30"
  };

  static const Map<String, dynamic> planRouteResponse = {
    "recommended_route": {
      "route_id": "R1",
      "distance_km": 178.4,
      "base_eta_minutes": 265,
      "risk_score": 0.21,
      "risk_level": "LOW",
      "eta_best_minutes": 265,
      "eta_worst_minutes": 310
    },
    "alternatives": [
      {
        "route_id": "R2",
        "distance_km": 184.2,
        "base_eta_minutes": 280,
        "risk_score": 0.12,
        "risk_level": "LOW",
        "eta_best_minutes": 280,
        "eta_worst_minutes": 300
      }
    ],
    "decision": "R1"
  };

  static const Map<String, dynamic> singleLocationFloodPrediction = {
    "latitude": 10.0159,
    "longitude": 76.3419,
    "rainfall_1h": 18.4,
    "rainfall_6h": 62.7,
    "rainfall_24h": 141.2,
    "elevation": 12.5,
    "historical_flood_frequency": 0.72,
    "flood_zone": 1
  };

  static const Map<String, dynamic> currentWeatherResponse = {
    "latitude": 10.01,
    "longitude": 76.34,
    "rainfall_1h": 12.4,
    "rainfall_6h": 43.8,
    "rainfall_24h": 112.2,
    "temperature": 27.4,
    "weather_code": 65
  };
  
  static const Map<String, dynamic> activeAlertsResponse = {
    "alerts": [
      {
        "id": "ALT001",
        "type": "FLOOD_RISK",
        "severity": "HIGH",
        "title": "High flood probability ahead",
        "message": "High flood probability detected 8 km ahead.",
        "latitude": 10.12,
        "longitude": 76.34
      }
    ]
  };
}
