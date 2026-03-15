# SmartGate WMS: Dynamic Dock-to-Rack Optimizer
### IECU Hackathon 2026 | Official Submission

## Overview
SmartGate WMS is a backend logic system that optimizes the interaction between external logistics (trucks) and internal automation (MDR/ASRS). 

---

## How It Works
1. **Pre-Booking:** Trucks submit manifests via a web portal.
2. **Smart Slotting:** The system assigns a Dock (1-25) based on the shortest path to the cargo's storage class.
3. **Cascading Flow:** Sensors trigger the "Sliding Effect," moving pallets forward only when a dock gap is created.
4. **Accuracy Gate:** Automated weight and ID verification before final loading.

---

##  Factory Workflow: The "East-to-West" Flow

Our warehouse operates on a **Linear Throughput Model**, ensuring items move in a single direction to prevent backtracking and congestion.

### 1. Inbound & Induction (East Side)
* **Arrival & Unload:** Cargo arrives at the **2m Dock Doors**. The WMS analyzes the truck manifest and assigns the truck to the specific dock closest to its designated storage rack (minimizing travel distance).
* **Staging & Quality Check:** Items are moved into the **5m Staging Area**. They are placed on **"Slave Pallets"** (standardized totes) to ensure the MDR rollers can grip them reliably.
* **Digital Tagging:** Every item is scanned. The WMS decides its **"Class" (1, 2, 3, or 4)** based on turnover speed, which determines its vertical and horizontal storage location.

### 2. Vertical Storage & Zonal Accumulation
* **Loading:** The **East AS/RS Elevator** carries the cargo to the assigned vertical floor.
* **Hold State (ZPA):** Once on the rack, "TSA-style" sensors detect if the lane is empty and zip the item to the innermost available spot. 
* **Energy Efficiency:** If the lane is full, the MDR motors shut off. The item sits in a **"Sleeping"** state, consuming zero energy until a space opens up on the West side.

### 3. Outbound & The "Sliding" Effect (West Side)
* **Pick Request:** A customer order triggers the **West Side Gate**.
* **The "Sliding" Effect:** As the West-most pallet moves out, sensors detect the opening and automatically **"slide"** the next pallet forward one zone. This cascading flow keeps items ready for immediate dispatch.
* **Descent & Final Sort:** The pallet descends via the **West Elevator** and travels down a braked slope to the staging area. Items are consolidated, pallet-wrapped, and loaded into outgoing trucks.

---

## IE Principles Applied
- **Lean Waste Reduction:** Minimized Motion & Transport.
- **JIT (Just-In-Time):** Synchronized truck arrival with pallet arrival.
- **Sustainability:** ZPA motor control for energy efficiency.

---

## Tech Stack (Conceptual)
- **Backend:** Python/Node.js for Gate Assignment Logic.
- **WMS:** SQL Database for SKU Class Management.
- **Hardware Interface:** PLC-based triggers for MDR Zonal Accumulation.

---
**Competition:** Chula Engineering IECU Hackathon 2026
