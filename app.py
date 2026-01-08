import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #e6f7f8; color: #37474f; }}
    .stTabs [aria-selected="true"] {{ background-color: #009688 !important; color: white !important; }}
    div.stButton > button {{ background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }}
    .mcl-explanation {{ background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #f9a825; margin: 20px 0; }}
    .success-card {{ background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #c3e6cb; }}
    </style>
""", unsafe_allow_html=True)

if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. HEADER ---
img_path = "assets/Header.png"
if os.path.exists(img_path):
    st.image(img_path, use_column_width=True)

# --- 3. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"
])

# --- TAB 1: BOOK (Preserved & Active) ---
with tab1:
    st.header("Book Reference")
    with st.form("book_active", clear_on_submit=True):
        auth = st.text_input("Authors", key="k_b_auth")
        yr = st.text_input("Year", key="k_b_yr")
        tit = st.text_input("Title", key="k_b_tit")
        if st.form_submit_button("Add Reference"):
            if auth and yr and tit:
                res = generate_book_reference([a.strip() for a in auth.split(",")], yr, tit, "", "", "")
                st.session_state.bibliography.append(res)
                st.success("Reference Saved!")

# --- TAB 5: AUDIT WITH SUCCESS CELEBRATION ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx", key="mcl_final_audit")
    
    if uploaded_file:
        if st.button("Run Audit", key="run_final_audit"):
            doc = Document(uploaded_file)
            text = " ".join([p.text for p in doc.paragraphs])
            cites = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', text)
            
            if cites:
                bib_low = " ".join(st.session_state.bibliography).lower()
                results = []
                missing_count = 0
                
                for c in sorted(list(set(cites))):
                    name = c.split(',')[0].split(' ')[0].lower()
                    found = name in bib_low
                    if not found: missing_count += 1
                    results.append({"Citation": f"({c})", "Status": "✅ Matched" if found else "⚠️ Missing"})
                
                st.table(results)

                # --- SUCCESS SCREEN ---
                if missing_count == 0:
                    st.balloons()
                    st.markdown("""
                        <div class="success-card">
                        <h2>🎉 Perfect Match!</h2>
                        <p>All in-text citations were found in your bibliography. Your academic referencing is spot on!</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    # Educational Feedback (Preserved)
                    st.markdown(f"""
                        <div class="mcl-explanation">
                        <h4>💡 Fixing {missing_count} Missing Items</h4>
                        <p>Check your <b>Spelling</b> and ensure you added these to the <b>Bibliography</b> tab before auditing.</p>
                        </div>
                    """, unsafe_allow_html=True)

                # Report Download (Preserved)
                report = "MCL AUDIT REPORT\n" + "="*20 + "\n"
                for r in results: report += f"[{r['Status']}] {r['Citation']}\n"
                st.download_button("📥 Download Report", report, "MCL_Audit.txt", key="dl_final")
