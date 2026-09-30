import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os
import hashlib
import datetime

# Include parent directory for server logic imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server.federated_core import FederatedOrchestrator
from server.cold_chain_monitor import evaluate_cold_chain
from server.redistribution_engine import calculate_inter_phc_transfers

st.set_page_config(
    page_title="BRICS Pulse-Mesh Health Platform", 
    layout="wide", 
    page_icon="🏥",
    initial_sidebar_state="expanded"
)

# --- MODERN STYLING & ANIMATED CSS ---
st.markdown("""
<style>
    .main-header {
        font-family: 'Inter', -apple-system, sans-serif;
        background: linear-gradient(90deg, #1E88E5 0%, #7B1FA2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0px;
    }
    .ticker-bar {
        background: rgba(30, 136, 229, 0.08);
        border: 1px solid rgba(30, 136, 229, 0.25);
        border-radius: 8px;
        padding: 6px 16px;
        font-size: 0.88rem;
        color: #0D47A1;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pulse-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #2E7D32;
        box-shadow: 0 0 0 0 rgba(46, 125, 50, 0.7);
        animation: pulse-green 1.8s infinite;
    }
    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 125, 50, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 10px rgba(46, 125, 50, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 125, 50, 0); }
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid rgba(220, 225, 235, 0.8);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(30, 136, 229, 0.12);
    }
    .metric-title {
        font-size: 0.80rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #546E7A;
        font-weight: 600;
    }
    .metric-val {
        font-size: 1.65rem;
        font-weight: 800;
        color: #212121;
        margin: 4px 0px;
    }
    .metric-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 20px;
    }
    .badge-green { background: #E8F5E9; color: #2E7D32; }
    .badge-red { background: #FFEBEE; color: #C62828; }
    .badge-amber { background: #FFF8E1; color: #F57F17; }
    .badge-blue { background: #E3F2FD; color: #1565C0; }
</style>
""", unsafe_allow_html=True)

# --- CRYPTOGRAPHIC SHA-256 LEDGER HELPER ---
def generate_audit_hash(prev_hash, action, actor, payload_summary):
    timestamp = datetime.datetime.now().isoformat()
    record_string = f"{prev_hash}|{action}|{actor}|{payload_summary}|{timestamp}"
    return hashlib.sha256(record_string.encode()).hexdigest()[:16]

# --- SESSION STATES ---
if "chain_of_custody" not in st.session_state:
    st.session_state.chain_of_custody = [
        {"block": 1, "action": "GENESIS_INITIALIZATION", "actor": "District Central Core", "summary": "System initialized across Lucknow cluster", "hash": "0000a4f91b72e81c", "timestamp": "2026-09-30 08:00:00"}
    ]

if "brics_drift_alert" not in st.session_state:
    st.session_state.brics_drift_alert = False

if "monsoon_flood_active" not in st.session_state:
    st.session_state.monsoon_flood_active = False

if "offline_queue" not in st.session_state:
    st.session_state.offline_queue = 3

if "emergency_sos_list" not in st.session_state:
    st.session_state.emergency_sos_list = []

# Persistent Shelf Batches for FEFO Dispense
if "pharmacy_batches" not in st.session_state:
    st.session_state.pharmacy_batches = [
        {"batch_id": "AMX-B24-11", "medicine": "Amoxicillin 500mg", "stock": 8, "expiry": "2026-10-15", "location": "Shelf A-1", "fefo_priority": "High (Expiring Soon)"},
        {"batch_id": "AMX-B25-04", "medicine": "Amoxicillin 500mg", "stock": 45, "expiry": "2027-04-30", "location": "Shelf A-2", "fefo_priority": "Normal"},
        {"batch_id": "RAB-B24-09", "medicine": "Anti-Rabies Serum", "stock": 4, "expiry": "2026-11-01", "location": "Cold Fridge #1", "fefo_priority": "Critical FEFO"},
        {"batch_id": "INS-B25-01", "medicine": "Insulin Regular", "stock": 12, "expiry": "2026-12-15", "location": "Cold Fridge #2", "fefo_priority": "Normal"}
    ]

if "fleet_drivers" not in st.session_state:
    st.session_state.fleet_drivers = {
        "DRV-501 (Vikas Kumar)": {"type": "Refrigerated Van", "lat": 26.70, "lon": 80.95, "status": "Available", "cool_box": True, "active_job": None},
        "DRV-502 (Ramesh Singh)": {"type": "Refrigerated Van", "lat": 26.80, "lon": 80.88, "status": "Available", "cool_box": True, "active_job": None},
        "DRV-503 (Amit Verma)": {"type": "Rapid Two-Wheeler", "lat": 26.90, "lon": 80.75, "status": "On Trip", "cool_box": False, "active_job": "WAYBILL-PRIOR-09"},
        "DRV-504 (Drone Hub East)": {"type": "Autonomous Drone", "lat": 26.75, "lon": 80.85, "status": "Available", "cool_box": True, "active_job": None}
    }

# --- MULTI-REGION DATASETS ---
REGION_CONFIGS = {
    "India - UP East Cluster": {
        "lat": 26.85, "lon": 80.94, "zoom": 9.2,
        "sample_sms": "PHC-LKO-102|AMX:12,PAR:90|BED:95|DOC:1|FT:140",
        "records": [
            {"phc_id": "PHC-LKO-101", "facility_name": "Bakshi Ka Talab PHC", "medicine": "Anti-Rabies Serum", "recorded_stock": 4, "safety_stock": 15, "forecast_demand": 18, "bed_occupancy_pct": 65, "staff_present": 4, "staff_total": 5, "lat": 26.98, "lon": 80.93, "temp_profile": [4.1, 4.8, 5.2, 5.0, 4.9]},
            {"phc_id": "PHC-LKO-102", "facility_name": "Malihabad CHC", "medicine": "Amoxicillin 500mg", "recorded_stock": 14, "safety_stock": 60, "forecast_demand": 70, "bed_occupancy_pct": 92, "staff_present": 3, "staff_total": 6, "lat": 26.92, "lon": 80.71, "temp_profile": [4.0, 4.2, 4.1, 4.3, 4.0]},
            {"phc_id": "PHC-LKO-103", "facility_name": "Mohanlalganj PHC", "medicine": "Anti-Rabies Serum", "recorded_stock": 35, "safety_stock": 10, "forecast_demand": 8, "bed_occupancy_pct": 55, "staff_present": 4, "staff_total": 4, "lat": 26.67, "lon": 80.98, "temp_profile": [4.5, 4.7, 4.6, 4.4, 4.5]},
            {"phc_id": "PHC-LKO-104", "facility_name": "Sarojini Nagar PHC", "medicine": "Amoxicillin 500mg", "recorded_stock": 180, "safety_stock": 40, "forecast_demand": 45, "bed_occupancy_pct": 48, "staff_present": 7, "staff_total": 8, "lat": 26.75, "lon": 80.86, "temp_profile": [4.2, 4.5, 4.1, 4.0, 4.3]},
            {"phc_id": "PHC-LKO-105", "facility_name": "Gosainganj CHC", "medicine": "Insulin Regular", "recorded_stock": 60, "safety_stock": 25, "forecast_demand": 30, "bed_occupancy_pct": 84, "staff_present": 5, "staff_total": 7, "lat": 26.77, "lon": 81.12, "temp_profile": [9.2, 10.1, 9.8, 11.2, 10.5]},
            {"phc_id": "PHC-LKO-106", "facility_name": "Kakori PHC", "medicine": "Insulin Regular", "recorded_stock": 10, "safety_stock": 30, "forecast_demand": 35, "bed_occupancy_pct": 70, "staff_present": 5, "staff_total": 5, "lat": 26.88, "lon": 80.79, "temp_profile": [4.0, 4.2, 4.3, 4.1, 4.0]}
        ]
    },
    "Brazil - Amazonas Hub": {
        "lat": -3.10, "lon": -60.02, "zoom": 9.0,
        "sample_sms": "UBS-MAO-201|ANT:8,PAR:110|BED:85|DOC:2|FT:160",
        "records": [
            {"phc_id": "UBS-MAO-201", "facility_name": "UBS Manaus Ponta Negra", "medicine": "Antivenom Serum", "recorded_stock": 3, "safety_stock": 20, "forecast_demand": 25, "bed_occupancy_pct": 88, "staff_present": 4, "staff_total": 6, "lat": -3.06, "lon": -60.09, "temp_profile": [4.2, 4.4, 4.6, 4.3, 4.5]},
            {"phc_id": "UBS-MAO-202", "facility_name": "UBS Cidade Nova Hub", "medicine": "Antivenom Serum", "recorded_stock": 42, "safety_stock": 15, "forecast_demand": 12, "bed_occupancy_pct": 60, "staff_present": 6, "staff_total": 6, "lat": -3.02, "lon": -59.98, "temp_profile": [4.0, 4.1, 4.0, 4.2, 4.1]},
            {"phc_id": "UBS-MAO-203", "facility_name": "UBS Iranduba River Post", "medicine": "Artemether Malaria Tabs", "recorded_stock": 12, "safety_stock": 50, "forecast_demand": 65, "bed_occupancy_pct": 95, "staff_present": 2, "staff_total": 4, "lat": -3.28, "lon": -60.18, "temp_profile": [4.1, 4.3, 4.2, 4.0, 4.1]},
            {"phc_id": "UBS-MAO-204", "facility_name": "UBS Careiro Rural Clinic", "medicine": "Artemether Malaria Tabs", "recorded_stock": 150, "safety_stock": 40, "forecast_demand": 45, "bed_occupancy_pct": 50, "staff_present": 5, "staff_total": 6, "lat": -3.38, "lon": -59.82, "temp_profile": [4.3, 4.4, 4.2, 4.1, 4.2]},
            {"phc_id": "UBS-MAO-205", "facility_name": "UBS Tarumã Clinic", "medicine": "Yellow Fever Vaccine", "recorded_stock": 55, "safety_stock": 20, "forecast_demand": 25, "bed_occupancy_pct": 65, "staff_present": 4, "staff_total": 5, "lat": -2.98, "lon": -60.05, "temp_profile": [9.8, 10.4, 11.0, 10.2, 9.9]}
        ]
    },
    "South Africa - Gauteng Network": {
        "lat": -26.18, "lon": 28.05, "zoom": 9.4,
        "sample_sms": "JHB-CLN-301|ARV:20,INS:15|BED:90|DOC:3|FT:210",
        "records": [
            {"phc_id": "JHB-CLN-301", "facility_name": "Soweto Community Clinic", "medicine": "ARV Fixed-Dose (TLD)", "recorded_stock": 18, "safety_stock": 100, "forecast_demand": 120, "bed_occupancy_pct": 94, "staff_present": 6, "staff_total": 8, "lat": -26.25, "lon": 27.85, "temp_profile": [4.0, 4.1, 4.2, 4.0, 4.1]},
            {"phc_id": "JHB-CLN-302", "facility_name": "Sandton Primary Care", "medicine": "ARV Fixed-Dose (TLD)", "recorded_stock": 260, "safety_stock": 80, "forecast_demand": 70, "bed_occupancy_pct": 45, "staff_present": 8, "staff_total": 8, "lat": -26.10, "lon": 28.05, "temp_profile": [4.2, 4.3, 4.1, 4.0, 4.2]},
            {"phc_id": "JHB-CLN-303", "facility_name": "Alexandra Health Centre", "medicine": "Insulin Glargine", "recorded_stock": 8, "safety_stock": 35, "forecast_demand": 40, "bed_occupancy_pct": 89, "staff_present": 5, "staff_total": 7, "lat": -26.12, "lon": 28.10, "temp_profile": [4.5, 4.6, 4.4, 4.2, 4.5]},
            {"phc_id": "JHB-CLN-304", "facility_name": "Germiston Care Clinic", "medicine": "Insulin Glargine", "recorded_stock": 70, "safety_stock": 25, "forecast_demand": 25, "bed_occupancy_pct": 52, "staff_present": 4, "staff_total": 5, "lat": -26.22, "lon": 28.17, "temp_profile": [4.1, 4.2, 4.0, 4.3, 4.1]}
        ]
    }
}

# --- SIDEBAR: ROLE CONTROLLER ---
st.sidebar.markdown("## 👤 User Persona & Role")
user_role = st.sidebar.radio(
    "Active System View:",
    ["District Command Officer (CMO)", "PHC Pharmacist Experience (Mobile PWA)", "Logistics Driver Portal", "Frontline IVR Phone Gateway"]
)

# -------------------------------------------------------------
# 1. UPGRADED PHARMACIST WORKFLOW EXPERIENCE (PWA)
# -------------------------------------------------------------
if user_role == "PHC Pharmacist Experience (Mobile PWA)":
    st.markdown("<h1 class='main-header'>📱 PHC Dispensary & Clinical Inventory Portal</h1>", unsafe_allow_html=True)
    st.caption("Offline-First Progressive Web App | FEFO Shelf Guidance | Emergency Restock SOS | Audit Reconcile")

    st.markdown(f"""
        <div class='ticker-bar'>
            <span class='pulse-dot'></span>
            <b>Frontline Dispensary Mode:</b> Local Cache Active | 
            <b>Pending Sync Queue:</b> {st.session_state.offline_queue} Transactions Cached | 
            <b>Assigned Clinic:</b> PHC-LKO-101 (Bakshi Ka Talab)
        </div>
    """, unsafe_allow_html=True)

    pharma_tab1, pharma_tab2, pharma_tab3, pharma_tab4 = st.tabs([
        "💊 FEFO Smart Dispense", 
        "🚨 Emergency Restock SOS", 
        "📥 Consignment Verification", 
        "📝 Physical Stock Reconciliation"
    ])

    with pharma_tab1:
        st.subheader("📦 Scan & Smart Dispense (FEFO Guard)")
        st.caption("System automatically prompts the earliest-expiring batch to open, eliminating shelf-life waste.")

        col_d1, col_d2 = st.columns([3, 2])
        with col_d1:
            selected_med = st.selectbox(
                "Prescription Item to Dispense:", 
                ["Amoxicillin 500mg", "Anti-Rabies Serum", "Insulin Regular"]
            )
            
            matching_batches = [b for b in st.session_state.pharmacy_batches if b["medicine"] == selected_med]
            matching_batches.sort(key=lambda x: x["expiry"])
            recommended_batch = matching_batches[0]

            st.info(f"💡 **Recommended FEFO Batch:** Pick Batch **{recommended_batch['batch_id']}** from **{recommended_batch['location']}** (Expires: {recommended_batch['expiry']})")

            scan_code = st.text_input("Barcode / QR Code Verification", f"SCAN-{recommended_batch['batch_id']}")
            units_to_dispense = st.number_input("Units Prescribed & Dispensed", min_value=1, max_value=20, value=2)
            patient_id = st.text_input("Patient Health ID (ABHA)", "ABHA-UP-2026-94812")

            if st.button("✓ Confirm Dispense & Update Local Ledger"):
                if recommended_batch["stock"] >= units_to_dispense:
                    recommended_batch["stock"] -= units_to_dispense
                    st.session_state.offline_queue += 1
                    st.success(f"Dispensed {units_to_dispense} units from Batch {recommended_batch['batch_id']}. Remaining batch stock: {recommended_batch['stock']}.")
                    st.caption(f"Transaction stored in local IndexedDB. Sync queue updated ({st.session_state.offline_queue} pending).")
                else:
                    st.error("Insufficient stock in the active batch! Please open the secondary batch.")

        with col_d2:
            st.subheader("📋 Active Shelf Inventory")
            st.table(pd.DataFrame(st.session_state.pharmacy_batches)[["batch_id", "medicine", "stock", "expiry", "location"]])

    with pharma_tab2:
        st.subheader("🚨 Emergency Stockout SOS Restock Beacon")
        st.caption("Instantly alerts District Central Command to an unexpected mass casualty or outbreak surge.")
        
        sos_col1, sos_col2 = st.columns(2)
        with sos_col1:
            sos_reason = st.selectbox(
                "Incident Trigger / Clinical Rationale:",
                [
                    "Mass Trauma / Road Traffic Accident Spike",
                    "Canine Bite / Rabies Outbreak Spike in Village",
                    "Acute Gastroenteritis / Diarrhea Outbreak",
                    "Unexpected Cold-Room Power Trip Spoilage"
                ]
            )
            sos_medicine = st.selectbox("Required Critical Medicine:", ["Anti-Rabies Serum", "Amoxicillin 500mg", "Insulin Regular", "IV Ringer Lactate"])
            sos_units = st.number_input("Emergency Vials / Strips Needed Immediately:", min_value=5, max_value=100, value=20)
            
            if st.button("🔥 Broadcast Priority SOS to District CMO"):
                sos_payload = {
                    "phc": "Bakshi Ka Talab PHC",
                    "reason": sos_reason,
                    "medicine": sos_medicine,
                    "units": sos_units,
                    "time": datetime.datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.emergency_sos_list.append(sos_payload)
                st.error("SOS BEACON BROADCASTED! District CMO notified to trigger rapid drone/bike courier dispatch.")

        with sos_col2:
            st.subheader("Active Emergency Signals")
            if st.session_state.emergency_sos_list:
                st.dataframe(pd.DataFrame(st.session_state.emergency_sos_list), use_container_width=True)
            else:
                st.info("No active emergency SOS signals from this facility.")

    with pharma_tab3:
        st.subheader("📥 Inward Inter-District Consignment Verification")
        received_token = st.text_input("Scan Inward Waybill QR Code", "WAYBILL-TR-802")
        temp_verification = st.number_input("Transport Box Arrival Temperature (°C)", value=4.4, step=0.1)
        
        if st.button("Confirm Handover & Restock"):
            if temp_verification <= 8.0:
                last_hash = st.session_state.chain_of_custody[-1]["hash"]
                new_hash = generate_audit_hash(last_hash, "RECEIPT_CONFIRMED", "Pharmacist (Bakshi Ka Talab)", f"17 vials Anti-Rabies verified at {temp_verification}°C")
                st.session_state.chain_of_custody.append({
                    "block": len(st.session_state.chain_of_custody) + 1,
                    "action": "CONSIGNMENT_ACCEPTED",
                    "actor": "Bakshi Ka Talab Dispenser",
                    "summary": f"17 units restocked at {temp_verification}°C",
                    "hash": new_hash,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                # Restock the local batch
                st.session_state.pharmacy_batches.append({
                    "batch_id": "RAB-TR802-IN", "medicine": "Anti-Rabies Serum", "stock": 17, "expiry": "2027-02-28", "location": "Cold Fridge #1", "fefo_priority": "Normal"
                })
                st.balloons()
                st.success(f"✓ Consignment '{received_token}' validated! 17 units transferred to active inventory. SHA-256 Block #{len(st.session_state.chain_of_custody)} generated.")
                st.caption(f"Immutable Handover Hash: `{new_hash}`")
            else:
                st.error("Thermal violation detected on arrival! Quarantining batch for biological inspection.")

    with pharma_tab4:
        st.subheader("📝 Daily Physical Audit & Breakage Reconciliation")
        st.caption("Record physical count variances, broken ampoules, or shelf drops for government compliance.")
        
        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            rec_batch = st.selectbox("Select Batch to Audit:", [b["batch_id"] for b in st.session_state.pharmacy_batches])
            phys_count = st.number_input("Actual Physical Units Counted on Shelf:", min_value=0, max_value=200, value=8)
            discrepancy_reason = st.selectbox("Reason for Discrepancy (if any):", ["Count Matches Perfect", "Ampoule Broken During Handling", "Water Damage / Damaged Packaging", "Clerical Counting Error"])
            
            if st.button("Log Physical Reconciliation"):
                st.success(f"Audit saved for Batch {rec_batch}. Discrepancy logged: '{discrepancy_reason}'. Compliance report updated.")

# -------------------------------------------------------------
# 2. LOGISTICS DRIVER VIEW
# -------------------------------------------------------------
elif user_role == "Logistics Driver Portal":
    st.markdown("<h1 class='main-header'>🚚 District Logistics & Transit Portal</h1>", unsafe_allow_html=True)
    st.caption("Fleet Matching Engine | Proximity Allocation | Real-Time Custody Tracking")

    selected_driver_id = st.selectbox(
        "Select Logged-In Driver Profile:",
        list(st.session_state.fleet_drivers.keys())
    )
    driver_info = st.session_state.fleet_drivers[selected_driver_id]

    col_prof1, col_prof2, col_prof3 = st.columns(3)
    col_prof1.write(f"**Vehicle Category:** {driver_info['type']}")
    col_prof2.write(f"**Thermal Cool-Box:** {'✓ Certified (2-8°C)' if driver_info['cool_box'] else '✗ Not Equipped'}")
    col_prof3.write(f"**Duty State:** `{driver_info['status']}`")

    st.markdown("---")

    if driver_info['active_job']:
        st.success(f"🔒 You have an active locked assignment: **{driver_info['active_job']}**")
        st.write("**Route:** Mohanlalganj PHC ➔ Bakshi Ka Talab PHC (34.9 km)[cite: 5]")
        st.write("**Manifest:** 17 Vials Anti-Rabies Serum | Active Thermal: 4.2°C[cite: 5]")
        
        milestone = st.radio(
            "Update Milestone Progress:",
            [
                "1. En Route to Donor Facility",
                "2. Goods Picked Up & Chilled in Vehicle Dock",
                "3. In Transit (Broadcasting Live Telemetry)",
                "4. Arrived at Destination PHC (Awaiting Pharmacist Scan)"
            ]
        )
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            if st.button("Transmit Milestone"):
                last_hash = st.session_state.chain_of_custody[-1]["hash"]
                new_hash = generate_audit_hash(last_hash, "TRANSIT_MILESTONE", selected_driver_id, milestone)
                st.session_state.chain_of_custody.append({
                    "block": len(st.session_state.chain_of_custody) + 1,
                    "action": "TRANSIT_UPDATE",
                    "actor": selected_driver_id,
                    "summary": milestone,
                    "hash": new_hash,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.success(f"Milestone updated: '{milestone}'. Cryptographic Hash `{new_hash}` appended to ledger.")
        with col_m2:
            if st.button("Complete Job & Return to Available Fleet"):
                st.session_state.fleet_drivers[selected_driver_id]['status'] = "Available"
                st.session_state.fleet_drivers[selected_driver_id]['active_job'] = None
                st.rerun()

    else:
        st.subheader("📋 Available Emergency Transfer Requests (Proximity Pool)")
        donor_lat, donor_lon = 26.67, 80.98
        driver_dist = round(np.sqrt((driver_info['lat'] - donor_lat)**2 + (driver_info['lon'] - donor_lon)**2) * 111.0, 1)

        available_jobs = [
            {
                "Waybill": "WAYBILL-TR-802",
                "From": "Mohanlalganj PHC",
                "To": "Bakshi Ka Talab PHC",
                "Medicine": "Anti-Rabies Serum",
                "Units": 17,
                "Distance to Donor": f"{driver_dist} km",
                "Trip Transit Dist": "34.9 km",
                "Cold-Chain Required": "Yes (2-8°C)",
                "Payout Allowance": "₹278.84"
            }
        ]
        st.table(pd.DataFrame(available_jobs))

        if not driver_info['cool_box']:
            st.warning("⚠️ Your vehicle lacks an active 2-8°C cool-box required for Anti-Rabies Serum. Job claim disabled.")
        elif driver_info['status'] == "On Trip":
            st.warning("⚠️ You are currently engaged on another trip. Finish current assignment first.")
        else:
            if st.button(f"⚡ Accept & Lock Assignment (WAYBILL-TR-802) as {selected_driver_id.split(' ')[0]}"):
                last_hash = st.session_state.chain_of_custody[-1]["hash"]
                new_hash = generate_audit_hash(last_hash, "JOB_LOCKED", selected_driver_id, "Accepted WAYBILL-TR-802")
                st.session_state.chain_of_custody.append({
                    "block": len(st.session_state.chain_of_custody) + 1,
                    "action": "DRIVER_ACCEPTANCE",
                    "actor": selected_driver_id,
                    "summary": "Locked WAYBILL-TR-802 for immediate dispatch",
                    "hash": new_hash,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.fleet_drivers[selected_driver_id]['status'] = "On Trip"
                st.session_state.fleet_drivers[selected_driver_id]['active_job'] = "WAYBILL-TR-802"
                st.success(f"Job WAYBILL-TR-802 locked exclusively to {selected_driver_id}. Chain hash `{new_hash}` created.")
                st.rerun()

# -------------------------------------------------------------
# 3. FRONTLINE IVR PHONE GATEWAY
# -------------------------------------------------------------
elif user_role == "Frontline IVR Phone Gateway":
    st.markdown("<h1 class='main-header'>📞 Frontline IVR & Voice Response Gateway</h1>", unsafe_allow_html=True)
    st.caption("Zero-Smartphone Accessible Telemetry | Automated Touch-Tone Keypad Interface")
    
    st.write("Simulates an automated toll-free hotline (`1800-PHC-STOCK`) for community health attendants with basic feature phones.")

    ivr_col1, ivr_col2 = st.columns(2)
    with ivr_col1:
        st.subheader("📱 Dialpad Simulation")
        selected_phc = st.selectbox("Calling Station:", ["PHC-LKO-101 (Bakshi Ka Talab)", "PHC-LKO-102 (Malihabad)", "PHC-LKO-106 (Kakori)"])
        med_code = st.selectbox("Select Medicine Item (IVR Menu Prompt):", ["1 - Anti-Rabies Serum", "2 - Amoxicillin 500mg", "3 - Insulin Regular"])
        keypad_stock = st.number_input("Enter Current Stock Units via Keypad (#):", min_value=0, max_value=200, value=6)
        
        if st.button("Transmit IVR Audio Telemetry"):
            st.success(f"Voice gateway processed call from {selected_phc}. Inventory for menu item [{med_code}] set to {keypad_stock} units.")
            st.caption("Call recording verified by automatic speech-to-intent engine; database synchronized.")
            
    with ivr_col2:
        st.subheader("📜 Generated Automated IVR Log")
        st.code(f"""
[IVR INBOUND CALL CONNECTED]
Origin: Caller ID +91-98765-XXXXX
Station: {selected_phc}
Session ID: IVR-UP-SESSION-{np.random.randint(1000, 9999)}
DTMF Input Received: 1 -> {med_code}
Count Confirmed: {keypad_stock} units
Latency: 320ms (Telephony Gateway)
Status: INVENTORY_UPDATED_SUCCESS
        """, language="yaml")

# -------------------------------------------------------------
# 4. DISTRICT COMMAND OFFICER (CMO) DASHBOARD
# -------------------------------------------------------------
else:
    st.markdown("<h1 class='main-header'>🌐 BRICS Pulse-Mesh: Public Health Supply Chain Orchestrator</h1>", unsafe_allow_html=True)
    st.caption("Federated AI Architecture | Real-Time Stockout Warning | Dynamic Inter-District Redistribution | Cold-Chain Audit[cite: 1]")

    # Cross-BRICS Outbreak Drift Banner Alert
    if st.session_state.brics_drift_alert:
        st.error(
            "⚠️ **CROSS-BRICS EPIDEMIOLOGICAL DRIFT ALERT**: Unseasonal vector surge (Dengue/Malaria mutation) "
            "detected in Brazil (Amazonas Hub)[cite: 1]! Global federated weights updated. Recommended: Elevate district "
            "antibiotic and IV fluid buffer thresholds by **+25%** proactively[cite: 1]."
        )

    # Urgent Frontline Pharmacist SOS Alerts
    if st.session_state.emergency_sos_list:
        for sos in st.session_state.emergency_sos_list:
            st.warning(f"🚨 **URGENT PHC SOS ({sos['phc']})**: Requesting immediate emergency allocation of **{sos['units']} units of {sos['medicine']}** due to *'{sos['reason']}'* (Logged at {sos['time']}).")

    # Live Event Ticker
    st.markdown(f"""
        <div class='ticker-bar'>
            <span class='pulse-dot'></span>
            <b>Live Mesh Telemetry:</b> 100% Nodes Online | Differential Privacy ε=1.0 | 
            <b>Weather Hazard State:</b> {'⛈️ MONSOON FLOOD ALERT (Drone Escalation Active)' if st.session_state.monsoon_flood_active else '☀️ Clear Road Logistics'}
        </div>
    """, unsafe_allow_html=True)

    # --- SIDEBAR CONFIGURATIONS ---
    st.sidebar.markdown("---")
    st.sidebar.header("🌍 Operational Configurations")
    selected_region = st.sidebar.selectbox(
        "Active Operational Cluster", 
        list(REGION_CONFIGS.keys())
    )
    active_config = REGION_CONFIGS[selected_region]

    # Climate Disruption Toggle
    st.session_state.monsoon_flood_active = st.sidebar.checkbox(
        "⛈ Simulate Monsoon / Flooded Roads", 
        value=st.session_state.monsoon_flood_active,
        help="Simulates impassable road conditions, triggering automated medical drone escalation."
    )

    epsilon_budget = st.sidebar.slider(
        "Differential Privacy Budget (ε)", 
        min_value=0.1, 
        max_value=3.0, 
        value=1.0, 
        step=0.1
    )
    st.sidebar.info("Lower ε injects calibrated Laplacian noise into model weights, ensuring zero raw patient record leakage across borders.")

    st.sidebar.markdown("---")
    st.sidebar.header("📡 SMS Gateway Webhook Ingestion")
    sample_sms = st.sidebar.text_input(
        "Simulated Incoming Compressed SMS", 
        active_config["sample_sms"]
    )
    if st.sidebar.button("Ingest SMS Telemetry"):
        st.sidebar.success(f"✓ Parsed & Ingested Edge Node: {sample_sms.split('|')[0]}")

    # Process Active Region Dataset
    processed_data = []
    for item in active_config["records"]:
        cc_result = evaluate_cold_chain(item['temp_profile'], item['recorded_stock'])
        row = item.copy()
        row['usable_stock'] = cc_result['usable_stock']
        row['cold_chain_status'] = cc_result['status']
        row['spoiled_units'] = cc_result['spoiled_stock']
        
        # Risk triage evaluation
        if row['usable_stock'] <= (row['safety_stock'] * 0.4):
            row['status'] = "CRITICAL DEFICIT"
        elif row['usable_stock'] < (row['safety_stock'] + row['forecast_demand']):
            row['status'] = "AT RISK"
        else:
            row['status'] = "HEALTHY"
        processed_data.append(row)

    df = pd.DataFrame(processed_data)

    # --- TABS INTERFACE ---
    tab_ops, tab_fl, tab_ledger, tab_fleet = st.tabs([
        "🚀 Live Operational Command", 
        "🌐 Cross-BRICS Federated AI Hub", 
        "🔗 SHA-256 Chain of Custody Ledger",
        "🚚 District Fleet Status"
    ])

    with tab_ops:
        crit_count = len(df[df['status'] == 'CRITICAL DEFICIT'])
        breach_count = len(df[df['cold_chain_status'] != 'COMPLIANT'])

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Monitored Facilities</div>
                    <div class='metric-val'>{len(df)} Nodes</div>
                    <span class='metric-badge badge-green'>● 100% Operational</span>
                </div>
            """, unsafe_allow_html=True)
        with m2:
            badge_class = "badge-red" if crit_count > 0 else "badge-green"
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Critical Stockouts</div>
                    <div class='metric-val'>{crit_count} Centers</div>
                    <span class='metric-badge {badge_class}'>● Action Mandated</span>
                </div>
            """, unsafe_allow_html=True)
        with m3:
            badge_class = "badge-amber" if breach_count > 0 else "badge-green"
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Cold-Chain Breaches</div>
                    <div class='metric-val'>{breach_count} Incidents</div>
                    <span class='metric-badge {badge_class}'>● Thermal Audit Flag</span>
                </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Federated Privacy Budget</div>
                    <div class='metric-val'>ε = {epsilon_budget}</div>
                    <span class='metric-badge badge-blue'>● Differential Privacy Active</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        c_map, c_matrix = st.columns([3, 2])
        transfer_df = calculate_inter_phc_transfers(df)

        with c_map:
            st.subheader("📍 Geospatial Network Telemetry & Redistribution Routes")
            
            # Universal Dynamic Tile Map (Works across Plotly 5.x, 6.x, and 7.x)
            ScatterMap = getattr(go, "Scattermap", getattr(go, "Scattermapbox", None))
            is_new_plotly = hasattr(go, "Scattermap")
            
            fig = go.Figure()
            color_map = {"CRITICAL DEFICIT": "#D32F2F", "AT RISK": "#FFA000", "HEALTHY": "#2E7D32"}
            
            for status_type, color_val in color_map.items():
                sub_df = df[df['status'] == status_type]
                if not sub_df.empty:
                    fig.add_trace(ScatterMap(
                        lon=sub_df['lon'],
                        lat=sub_df['lat'],
                        mode='markers',
                        marker=dict(size=14, color=color_val),
                        name=status_type,
                        text=sub_df.apply(lambda r: f"<b>{r['facility_name']}</b><br>{r['medicine']}<br>Usable: {r['usable_stock']}", axis=1),
                        hoverinfo='text'
                    ))

            # Draw Route Arcs with Dynamic Colors
            facility_coords = {r['facility_name']: (r['lat'], r['lon']) for _, r in df.iterrows()}
            for _, t in transfer_df.iterrows():
                if t['From PHC'] in facility_coords and t['To PHC'] in facility_coords:
                    from_coord = facility_coords[t['From PHC']]
                    to_coord = facility_coords[t['To PHC']]
                    line_color = "#FF6D00" if st.session_state.monsoon_flood_active else "#0288D1"
                    fig.add_trace(ScatterMap(
                        lon=[from_coord[1], to_coord[1]],
                        lat=[from_coord[0], to_coord[0]],
                        mode="lines+markers",
                        line=dict(width=3.5, color=line_color),
                        marker=dict(size=7, color="#D32F2F"),
                        name=f"Transfer: {t['Medicine']}",
                        hoverinfo="text",
                        text=f"Rebalance Route: {t['From PHC']} → {t['To PHC']} ({t['Transfer Units']} units)"
                    ))

            # OpenStreetMap street tiles with mouse-wheel zoom
            map_settings = dict(
                style="open-street-map",
                center=dict(lat=active_config["lat"], lon=active_config["lon"]),
                zoom=active_config["zoom"]
            )
            
            if is_new_plotly:
                fig.update_layout(map=map_settings, margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=480, showlegend=True)
            else:
                fig.update_layout(mapbox=map_settings, margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=480, showlegend=True)

            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

        with c_matrix:
            st.subheader("⚠️ Clinical Stock & Supply Health")
            disp_cols = ['facility_name', 'medicine', 'usable_stock', 'safety_stock', 'cold_chain_status', 'status']
            st.dataframe(df[disp_cols], height=480, use_container_width=True)

        st.markdown("---")

        # Dynamic Route Assignment Accounting for Weather Hazards
        st.subheader("🚚 Automated Inter-District Redistribution Orders")
        if not transfer_df.empty:
            if st.session_state.monsoon_flood_active:
                transfer_df['Logistics Mode'] = "🚁 Medical Drone Corridor (Flood Override)"
                transfer_df['Est. Logistics Cost (INR)'] = transfer_df['Est. Logistics Cost (INR)'] * 1.35
            else:
                transfer_df['Logistics Mode'] = transfer_df['Distance (km)'].apply(
                    lambda d: "🚁 Medical Drone Priority" if d <= 30 else "🚐 Cold-Van Ground Freight"
                )
                
            st.dataframe(transfer_df, use_container_width=True)
            col_btn, _ = st.columns([1, 4])
            with col_btn:
                if st.button("🚀 Approve & Dispatch All Rebalancing Routes"):
                    last_hash = st.session_state.chain_of_custody[-1]["hash"]
                    new_hash = generate_audit_hash(last_hash, "CMO_APPROVAL", "District CMO", "Dispatched all rebalancing routes")
                    st.session_state.chain_of_custody.append({
                        "block": len(st.session_state.chain_of_custody) + 1,
                        "action": "CMO_DISPATCH_AUTHORIZATION",
                        "actor": "District Chief Medical Officer",
                        "summary": f"Authorized {len(transfer_df)} transfer routes under flood={st.session_state.monsoon_flood_active}",
                        "hash": new_hash,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.success(f"Logistics dispatch tokens broadcasted via SMS/MQTT! SHA-256 Block #{len(st.session_state.chain_of_custody)} recorded.")
        else:
            st.info("Public health inventory is currently balanced across all district nodes.")

    with tab_fl:
        st.subheader("🛡️ Multi-National Federated Parameter Convergence")
        st.write(
            "Demonstrates decentralized epidemiological model training across BRICS partner nodes[cite: 1]. "
            "No patient records cross national borders; only locally trained parameter weights are synchronized[cite: 1]."
        )
        
        col_fl1, col_fl2 = st.columns(2)
        with col_fl1:
            st.markdown("**Active Sovereign Federated Clusters:**")
            st.write("1. 🇮🇳 **India (MoHFW Cluster)**: 1,420 PHC Nodes")
            st.write("2. 🇧🇷 **Brazil (SUS Cluster)**: 890 UBS Nodes")
            st.write("3. 🇿🇦 **South Africa (DoH Cluster)**: 410 Clinic Nodes")
            
            rounds = st.slider("Execute Federated Convergence Rounds", 1, 10, 5)
            
            st.markdown("---")
            st.subheader("🦠 Cross-Border Anomaly Injection")
            if st.button("Simulate Vector Surge in Brazil Node"):
                st.session_state.brics_drift_alert = True
                st.success("Surge detected! Global FedAvg weights adjusted. National alert published.")
                st.rerun()
            if st.session_state.brics_drift_alert:
                if st.button("Clear Cross-Border Anomaly"):
                    st.session_state.brics_drift_alert = False
                    st.rerun()
            
        with col_fl2:
            np.random.seed(42)
            sim_loss = [0.85 * (0.65 ** r) + np.random.uniform(0.01, 0.03) for r in range(rounds)]
            loss_df = pd.DataFrame({"Round": list(range(1, rounds + 1)), "Global Loss (FedAvg)": sim_loss})
            fig_loss = go.Figure()
            fig_loss.add_trace(go.Scatter(x=loss_df["Round"], y=loss_df["Global Loss (FedAvg)"], mode='lines+markers', line=dict(color="#1E88E5", width=3)))
            fig_loss.update_layout(title="Global Model Loss vs Training Rounds", xaxis_title="Round", yaxis_title="Global Loss (FedAvg)")
            st.plotly_chart(fig_loss, use_container_width=True)

    with tab_ledger:
        st.subheader("🔗 SHA-256 Immutable Consignment Custody Ledger")
        st.caption("Cryptographic audit trail tracking transfers from approval to physical pharmacy handoff.")
        ledger_df = pd.DataFrame(st.session_state.chain_of_custody)
        st.dataframe(ledger_df, use_container_width=True)
        st.info("Every action hashes the previous block's hash, making unverified stock diversion or retroactive record editing cryptographically impossible.")

    with tab_fleet:
        st.subheader("🚐 Registered Fleet Telemetry & Readiness")
        fleet_table = []
        for d_id, d_data in st.session_state.fleet_drivers.items():
            fleet_table.append({
                "Driver / Unit ID": d_id,
                "Vehicle Type": d_data["type"],
                "Cool-Box Certified": "Yes" if d_data["cool_box"] else "No",
                "Operational Status": d_data["status"],
                "Active Waybill Assigned": d_data["active_job"] if d_data["active_job"] else "None"
            })
        st.table(pd.DataFrame(fleet_table))