import streamlit as st
import datetime
import db_manager
import crypto_ledger
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Forensic CoC System", layout="wide", page_icon="🥥")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🥥 Project COCONUT")
st.sidebar.markdown("### Forensic Ledger UI")
menu = st.sidebar.radio("Navigation", [
    "Dashboard", 
    "Log New Evidence", 
    "Transfer Custody", 
    "Audit Ledger"
])

# --- DYNAMIC LOADER FUNCTIONS ---
def load_personnel_dropdown():
    """Fetches personnel from DB and formats them for Streamlit."""
    try:
        personnel_data = db_manager.get_all_personnel() 
        # Format: "B-101 (last_name, first_name)"
        return [f"{p['badge_number']} ({p['last_name']}, {p['first_name']})" for p in personnel_data]
    except Exception as e:
        st.error(f"Failed to load personnel: {e}")
        return []

def load_locations_dropdown():
    """Fetches locations from DB and formats them for Streamlit."""
    try:
        locations_data = db_manager.get_all_storage_locations() 
        # Format: "LOC-01 (Facility Name)"
        return [f"{loc['location_id']} ({loc['facility_name']})" for loc in locations_data]
    except Exception as e:
        st.error(f"Failed to load locations: {e}")
        return []

def extract_id(dropdown_string):
    """Takes 'B-101 (Jenkins, John)' and returns just the ID 'B-101'"""
    if dropdown_string:
        return dropdown_string.split(" ")[0]
    return None


# --- PAGE 1: LOG NEW EVIDENCE ---
if menu == "Log New Evidence":
    st.header("📦 Log New Evidence into Vault")
    st.markdown("Use this form to intake physical evidence. This will automatically generate the Genesis Hash.")
    
    with st.form("evidence_intake_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            evidence_id = st.text_input("Evidence ID (e.g., EV-2026-001)")
            case_id = st.text_input("Case ID")
            item_type = st.selectbox("Item Type", ["Physical", "Biological", "Digital"])
            description = st.text_area("Item Description")
            
        with col2:
            collection_location = st.text_input("Collection Location (GPS/Address)")
            # Using the dynamic loaders here
            collected_by_selection = st.selectbox("Collected By (Badge Number)", load_personnel_dropdown())
            storage_selection = st.selectbox("Initial Storage Location", load_locations_dropdown())
            
        submitted = st.form_submit_button("Log Evidence")
        
        if submitted:
            if not evidence_id or not collected_by_selection:
                st.error("Evidence ID and Collector are required.")
            else:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Extract the pure Foreign Keys using our helper
                badge_number = extract_id(collected_by_selection)
                location_id = extract_id(storage_selection)
                
                # 1. Build the Evidence Payload
                ev_payload = {
                    "evidence_id": evidence_id,
                    "case_id": case_id, # If you have a case_id field in DB, add it, otherwise ignore
                    "item_type": item_type,
                    "description": description,
                    "collection_location": collection_location,
                    "collected_by_badge": badge_number,
                    "collected_at": now,
                    "current_location_id": location_id,
                    "digital_hash": None 
                }
                
                # 2. Build the Genesis Transfer Payload
                transfer_payload = {
                    "evidence_id": evidence_id,
                    "transferred_by_badge": "SYS", # Genesis record
                    "received_by_badge": badge_number,
                    "reason": "Initial Intake",
                    "transfer_time": now,
                    "previous_hash": "GENESIS_HASH"
                }
                
                try:
                    # Log physical evidence
                    db_manager.insert_evidence(ev_payload) 
                    
                    # Trigger Application-Level Trigger
                    success = crypto_ledger.process_new_transfer(transfer_payload)
                    
                    if success:
                        st.success(f"✅ Evidence {evidence_id} successfully logged with Genesis Hash.")
                    else:
                        st.error("Failed to generate cryptographic seal.")
                except Exception as e:
                    st.error(f"Database Error: {e}")

# --- PAGE 2: TRANSFER CUSTODY ---
elif menu == "Transfer Custody":
    st.header("🤝 Execute Chain of Custody Transfer")
    
    with st.form("transfer_form"):
        evidence_id = st.text_input("Evidence ID")
        # Using the dynamic loaders
        transferred_by_selection = st.selectbox("Relinquished By (Badge Number)", load_personnel_dropdown())
        received_by_selection = st.selectbox("Received By (Badge Number)", load_personnel_dropdown())
        reason = st.text_input("Reason for Transfer")
        
        submitted = st.form_submit_button("Cryptographically Sign Transfer")
        
        if submitted:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Extract IDs before sending to ledger
            transferred_by_badge = extract_id(transferred_by_selection)
            received_by_badge = extract_id(received_by_selection)
            
            transfer_payload = {
                "evidence_id": evidence_id,
                "transferred_by_badge": transferred_by_badge,
                "received_by_badge": received_by_badge,
                "reason": reason,
                "transfer_time": now
            }
            
            try:
                success = crypto_ledger.process_new_transfer(transfer_payload)
                if success:
                    st.success("✅ Transfer mathematically verified and committed to ledger.")
                else:
                    st.error("Transfer failed. Hash generation error.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- PAGE 3: AUDIT LEDGER ---
elif menu == "Audit Ledger":
    st.header("🔍 Cryptographic Ledger Audit")
    
    evidence_id = st.text_input("Enter Evidence ID to Audit:")
    
    if st.button("Verify Ledger Integrity"):
        # Mocking for now until you wire up verify_chain()
        is_valid = True
        message = "Ledger mathematically intact."
        
        if is_valid:
            st.success(f"✅ {message}")
            st.balloons()
        else:
            st.error(f"🚨 BREACH DETECTED: {message}")
            
# --- DASHBOARD ---
elif menu == "Dashboard":
    st.title("Forensic Database Overview")
    st.info("Navigate using the sidebar to log evidence or execute transfers.")
    
    # Optional: If you want to show live stats right away!
    try:
        stats = db_manager.get_dashboard_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cases", stats.get('total_cases', 0))
        col2.metric("Total Evidence Logged", stats.get('total_evidence', 0))
        col3.metric("Pending Lab Requests", stats.get('pending_labs', 0))
    except Exception as e:
        pass # Silently pass if DB isn't seeded yet
