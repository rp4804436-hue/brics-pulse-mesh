# 🌐 BRICS Pulse-Mesh: Public Health Supply Chain Orchestrator

An end-to-end, resilient health resource management and federated AI platform built for Primary Health Centres (PHCs). Designed to eliminate medicine stock-outs, forecast supply demand, enforce thermal cold-chain safety, and automate inter-district redistribution across BRICS member nations without compromising patient data sovereignty.

---

## 🚀 Key Architectural Pillars

- **Real-Time Network Telemetry:** Live tracking of medicine inventories, bed occupancy, and medical staff attendance across multi-tier public health facilities.
- **Predictive Demand Forecasting:** 7-day multi-variable consumption projections modeling daily footfall, historical burn rate, and seasonal epidemiological indicators.
- **Dynamic Inter-District Rebalancing:** Autonomous Minimum-Cost Network Flow solver pairing deficit clinics with nearest surplus hubs via road and drone transit corridors.
- **Zero-Connectivity Edge Resilience:** Offline-first edge nodes powered by local SQLite/IndexedDB caching, supported by 140-character compressed SMS and touch-tone IVR fallback gateways.
- **IoT Cold-Chain Thermal Auditing:** Automated biological shelf-life degradation tracking for temperature-sensitive biologics (Insulin, Anti-Rabies Serum).
- **Frontline PWA Experience:** In-browser barcode scanning, First-Expired First-Out (FEFO) dispensing guidance, physical discrepancy reconciliation, and one-tap emergency SOS beaconing.
- **Cryptographic Chain of Custody:** SHA-256 hash-linked immutable ledger logging custody handoffs between CMO authorization, driver transit, and recipient restocking.
- **Cross-BRICS Federated Learning:** Decentralized Federated Averaging (FedAvg) with Laplacian Differential Privacy ($\epsilon$-budgeting) allowing cross-border outbreak trend learning without raw electronic health record (EHR) transmission.

---

## 📁 Repository Structure

```text
brics_pulse_mesh/
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation
├── edge_node/
│   └── local_client.py         # Rural PHC edge storage & SMS encoder
├── server/
│   ├── federated_core.py       # FedAvg & Differential Privacy engine
│   ├── redistribution_engine.py# Inter-district routing & transfer solver
│   └── cold_chain_monitor.py   # IoT thermal breach & degradation tracker
└── dashboard/
    └── app.py                  # Full-stack Streamlit command interface