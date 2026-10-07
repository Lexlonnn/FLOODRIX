# FLOODRIX

### Predict. Protect. Deliver.

> AI-powered flood prediction and resilient logistics routing for Kerala.

FLOODRIX is an intelligent logistics decision-support platform designed to predict the probability of flooding along a vehicle's route and use that prediction to make safer, more reliable logistics decisions.

Instead of simply showing historically flood-prone areas, FLOODRIX learns from **historical flood events and the environmental conditions under which flooding occurred**. It combines this learned knowledge with current and forecast weather conditions to estimate the probability of flooding at specific locations along a planned or ongoing route.

The predicted flood risk is then combined with logistics information such as route geometry, estimated arrival time, cargo type, delivery deadlines, and road closures to recommend the safest practical route.

---

## 🚨 Problem

Kerala's transportation network is frequently affected by:

- Flooding
- Waterlogging
- Heavy rainfall
- Landslides
- Road closures
- Traffic disruptions
- Delivery delays

For logistics operators, the problem is not simply knowing that an area is historically flood-prone.

The real question is:

> **"Will this particular road be affected by flooding when my vehicle reaches it?"**

Traditional navigation systems primarily optimize for distance and travel time. FLOODRIX introduces **predicted flood risk as a routing factor**.

---

# 💡 Core Concept

FLOODRIX is built around a historical-event-driven flood prediction pipeline.

```text
Historical Flood Events
          +
Historical Weather Conditions
          +
Flood-Prone Areas
          +
Terrain / Geographic Factors
          ↓
   Machine Learning Model
          ↓
  Flood Probability Model
          ↓
Current + Forecast Weather
          ↓
Flood Probability Along Route
          ↓
Logistics Risk Engine
          ↓
GO / REROUTE / WAIT
