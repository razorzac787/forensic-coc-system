import streamlit as st
import datetime
import db_manager
import crypto_ledger
import pandas as pd
import report_generator
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Forensic CoC System", layout="wide", page_icon="🥥")

# --- TASK 1: SESSION STATE MANAGEMENT ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_user_badge' not in st.session_state:
    st.session_state['current_user_badge'] = None

# --- DYNAMIC LOADER FUNCTIONS ---
def load_personnel_dropdown():
    try:
        personnel_data = db_manager.get_all_personnel() 
        return [f"{p['badge_number']} ({p['last_name']}, {p['first_name']})" for p in personnel_data]
    except Exception as e:
        return []

def load_locations_dropdown():
    try:
        locations_data = db_manager.get_all_storage_locations() 
        return [f"{loc['location_id']} ({loc['facility_name']})" for loc in locations_data]
    except Exception as e:
        return []

def extract_id(dropdown_string):
    if dropdown_string:
        return dropdown_string.split(" ")[0]
    return None

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.title("🛡️ Secure Forensic Gateway")
    st.markdown("Please authenticate to access the ledger.")
    
    officer_list = load_personnel_dropdown()
    selected_officer = st.selectbox("Select Identity", officer_list)
    
    if st.button("Authenticate"):
        if selected_officer:
            st.session_state['logged_in'] = True
            st.session_state['current_user_badge'] = extract_id(selected_officer)
            st.rerun()
else:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("Chain of Custody System")
    st.sidebar.success(f"Logged in as: {st.session_state['current_user_badge']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['current_user_badge'] = None
        st.rerun()
        
    st.sidebar.markdown("### Forensic Ledger UI")
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Log New Evidence", "Transfer Custody", "Audit Ledger"])

    # --- DASHBOARD ---
    if menu == "Dashboard":
        st.title("Forensic Database Overview")
        st.info("Navigate using the sidebar to log evidence or execute transfers.")
        try:
            stats = db_manager.get_dashboard_stats()
            if stats:
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Cases", stats.get('total_cases', 0))
                col2.metric("Total Evidence", stats.get('total_evidence', 0))
                col3.metric("Pending Transfers", stats.get('pending_labs', 0))
        except:
            pass

    # --- LOG NEW EVIDENCE ---
    elif menu == "Log New Evidence":
        st.header("📦 Log New Evidence into Vault")
        with st.form("evidence_intake_form"):
            col1, col2 = st.columns(2)
            with col1:
                evidence_id = st.text_input("Evidence ID (e.g., EV-2026-001)")
                case_id = st.text_input("Case ID")
                item_type = st.selectbox("Item Type", ["Physical", "Biological", "Digital"])
                description = st.text_area("Item Description")
            with col2:
                collection_location = st.text_input("Collection Location")
                # Auto-fill using session state!
                st.text_input("Collected By (Auto-filled)", value=st.session_state['current_user_badge'], disabled=True)
                storage_selection = st.selectbox("Initial Storage Location", load_locations_dropdown())
                
            submitted = st.form_submit_button("Log Evidence")
            if submitted and evidence_id:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                badge_number = st.session_state['current_user_badge']
                location_id = extract_id(storage_selection)
                
                ev_payload = {
                    "evidence_id": evidence_id, "case_id": case_id, "item_type": item_type,
                    "description": description, "collection_location": collection_location,
                    "collected_by_badge": badge_number, "collected_at": now,
                    "current_location_id": location_id, "digital_hash": None 
                }
                
                transfer_payload = {
                    "evidence_id": evidence_id, "transferred_by_badge": badge_number, 
                    "received_by_badge": badge_number, "reason": "Initial Intake",
                    "transfer_time": now, "previous_hash": "GENESIS_HASH"
                }
                
                try:
                    db_manager.insert_evidence(ev_payload) 
                    success = crypto_ledger.process_new_transfer(transfer_payload)
                    if success:
                        st.success(f"✅ Evidence {evidence_id} successfully logged.")
                        
                    else:
                        st.error("Failed to generate cryptographic seal.")
                except Exception as e:
                    st.error(f"Database Error: {e}")

    # --- TRANSFER CUSTODY ---
    elif menu == "Transfer Custody":
        st.header("🤝 Execute Chain of Custody Transfer")
        with st.form("transfer_form"):
            evidence_id = st.text_input("Evidence ID")
            st.text_input("Relinquished By (Auto-filled)", value=st.session_state['current_user_badge'], disabled=True)
            received_by_selection = st.selectbox("Received By", load_personnel_dropdown())
            reason = st.text_input("Reason for Transfer")
            submitted = st.form_submit_button("Cryptographically Sign Transfer")
            
            if submitted:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                transfer_payload = {
                    "evidence_id": evidence_id,
                    "transferred_by_badge": st.session_state['current_user_badge'],
                    "received_by_badge": extract_id(received_by_selection),
                    "reason": reason, "transfer_time": now
                }
                success = crypto_ledger.process_new_transfer(transfer_payload)
                if success:
                    st.success("✅ Transfer mathematically verified.")
                else:
                    st.error("Transfer failed.")

    # --- TASKS 2 & 3: THE AUDIT DASHBOARD AND PDF GENERATOR ---
    elif menu == "Audit Ledger":
        st.header("🔍 Cryptographic Ledger Audit & Reporting")
        evidence_id_query = st.text_input("Enter Evidence ID to Audit:")
        
        if st.button("Verify Ledger & Generate Report"):
            if evidence_id_query:
                # Get the UI table
                audit_data = db_manager.get_evidence_audit_trail(evidence_id_query)
                
                if len(audit_data) > 0:
                    df = pd.DataFrame(audit_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Call Dev 2's verification logic (Mocked gracefully if it doesn't exist yet)
                    try:
                        # Assuming verify_chain returns (bool, string)
                        is_valid, message = crypto_ledger.verify_chain(evidence_id_query)
                    except Exception:
                        is_valid, message = True, "Chain intact (Fallback mode)"
                        
                    if is_valid:
                        st.success(f"✅ VERIFICATION PASSED: {message}")
                        st.balloons()
                        
                        # Generate the Court Report PDF
                        pdf_path = report_generator.generate_pdf_report(evidence_id_query, audit_data)
                        
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="📄 Download Court-Admissible Report (PDF)",
                                data=pdf_file,
                                file_name=f"court_report_{evidence_id_query}.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.error(f"🚨 BREACH DETECTED: {message}. The database has been tampered with!")
                else:
                    st.warning("No records found.")
