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

# --- MOCK HELPER FUNCTIONS ---
# Note for the Team: You need to add these to db_manager.py to dynamically populate the dropdowns 
def get_personnel_list():
    # Example: return ["B-101 (Det. Jenkins)", "B-102 (Tech Davis)"]
    return ["B-101", "B-102", "B-103"] 

def get_storage_locations():
    # Example: return ["LOC-01 (Deep Freezer)", "LOC-02 (Locker A)"]
    return ["LOC-01", "LOC-02", "LOC-03"]

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
            collected_by_badge = st.selectbox("Collected By (Badge Number)", get_personnel_list())
            current_location_id = st.selectbox("Initial Storage Location", get_storage_locations())
            
        submitted = st.form_submit_button("Log Evidence")
        
        if submitted:
            if not evidence_id or not case_id:
                st.error("Evidence ID and Case ID are required.")
            else:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 1. Build the Evidence Payload
                ev_payload = {
                    "evidence_id": evidence_id,
                    "case_id": case_id,
                    "item_type": item_type,
                    "description": description,
                    "collection_location": collection_location,
                    "collected_by_badge": collected_by_badge,
                    "collected_at": now,
                    "current_location_id": current_location_id,
                    "digital_hash": None # Handled later for digital evidence
                }
                
                # 2. Build the Genesis Transfer Payload
                transfer_payload = {
                    "evidence_id": evidence_id,
                    "transferred_by_badge": "SYSTEM", # Genesis record
                    "received_by_badge": collected_by_badge,
                    "reason": "Initial Intake",
                    "transfer_time": now,
                    "previous_hash": "GENESIS_HASH"
                }
                
                try:
                    # Execute DB Insert
                    # Note: db_manager needs an insert_evidence function!
                    # db_manager.insert_evidence(ev_payload) 
                    
                    # Trigger Application-Level Trigger [cite: 177, 185]
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
        transferred_by_badge = st.selectbox("Relinquished By (Badge Number)", get_personnel_list())
        received_by_badge = st.selectbox("Received By (Badge Number)", get_personnel_list())
        reason = st.text_input("Reason for Transfer")
        
        submitted = st.form_submit_button("Cryptographically Sign Transfer")
        
        if submitted:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # The payload expected by crypto_ledger.process_new_transfer [cite: 70, 71, 72]
            transfer_payload = {
                "evidence_id": evidence_id,
                "transferred_by_badge": transferred_by_badge,
                "received_by_badge": received_by_badge,
                "reason": reason,
                "transfer_time": now
                # previous_hash and current_hash are handled by process_new_transfer [cite: 71, 72]
            }
            
            try:
                # Bind directly to the crypto_ledger 
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
        # Note: You will need a verify_chain() function in your crypto_ledger
        # is_valid, message = crypto_ledger.verify_chain(evidence_id)
        
        # Mocking for the UI demonstration
        is_valid = True
        message = "Ledger mathematically intact."
        
        if is_valid:
            st.success(f"✅ {message}")
            st.balloons()
            
            # Note: Integrate your get_full_chain_of_custody here [cite: 147]
            # records = db_manager.get_full_chain_of_custody(evidence_id)
            # if records:
            #     df = pd.DataFrame(records)
            #     st.dataframe(df)
        else:
            st.error(f"🚨 BREACH DETECTED: {message}")
            
# --- DASHBOARD (Placeholder) ---
elif menu == "Dashboard":
    st.title("Forensic Database Overview")
    st.info("Navigate using the sidebar to log evidence or execute transfers.")
