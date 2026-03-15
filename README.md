# SmartGate WMS: Dynamic Dock-to-Rack Optimizer
### IECU Hackathon 2026 | Official Submission

## Overview
SmartGate WMS is a backend logic system that optimizes the interaction between external logistics (trucks) and internal automation (MDR/ASRS). 

## How It Works
1. **Pre-Booking:** Trucks submit manifests via a web portal.
2. **Smart Slotting:** The system assigns a Dock (1-25) based on the shortest path to the cargo's storage class.
3. **Cascading Flow:** Sensors trigger the "Sliding Effect," moving pallets forward only when a dock gap is created.
4. **Accuracy Gate:** Automated weight and ID verification before final loading.

## IE Principles Applied
- **Lean Waste Reduction:** Minimized Motion & Transport.
- **JIT (Just-In-Time):** Synchronized truck arrival with pallet arrival.
- **Sustainability:** ZPA motor control for energy efficiency.

## 🛠Tech Stack (Conceptual)
- **Backend:** Python/Node.js for Gate Assignment Logic.
- **WMS:** SQL Database for SKU Class Management.
- **Hardware Interface:** PLC-based triggers for MDR Zonal Accumulation.

---
**Competition:** Chula Engineering IECU Hackathon 2026
