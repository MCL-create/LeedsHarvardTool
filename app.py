import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

# Applying MCL Brand Palette from provided swatch
st.markdown(f"""
    <style>
    /* Background and Text */
    .stApp {{ background-color: #e6f7f8; color: #37474f; }}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #dff7f9; 
        border-radius: 4px;
        color: #008080;
    }}
    .stTabs [aria-selected="true"] {{ 
        background-color: #009688 !important; 
        color: white !important; 
    }}
    
    /* Button Styling (Deep Turquoise) */
    div.stButton > button:first-child {{
        background-color: #009688;
        color: white;
        border: none;
        border-radius: 5px;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background-color: #00796b;
        border: 1px solid #f9a825; /* Golden Yellow Accent on hover */
    }}
    
    /* Table & Alert Styling */
    .stAlert {{ border-left: 5px solid #f9a825; }}
    </style>
""", unsafe_allow_html=True)

# Persistent Memory for Bibliography
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

# --- TAB 1-3: REFERENCE GENERATORS ---
# (Logic remains same as before but using the new theme)
with tab1:
    st.header("Book Reference")
    with st.form("book_form"):
        # Form logic here...
        st.form_submit_button("Add to List")

# --- TAB 5: ESSAY AUDIT (FUNCTIONAL FIX) ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    # Using a unique key for the uploader prevents "freezing"
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx", key="mcl_audit_uploader")
    
    if uploaded_file is not None:
        # We wrap this in a spinner to show the user it is working
        with st.spinner("MCL Tool is analyzing your citations..."):
            doc = Document(uploaded_file)
            full_text = " ".join([p.text for p in doc.paragraphs])
            cites = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', full_text)
            
            if cites:
                st.subheader(f"Found {len(cites)} Potential Citations")
                bib_lower = " ".join(st.session_state.bibliography).lower()
                
                audit_data = []
                for c in sorted(list(set(cites))):
                    # Simplified name check
                    name_check = c.split(',')[0].split(' ')[0].lower()
                    status = "✅ Matched" if name_check in bib_lower else "⚠️ Missing"
                    audit_data.append({"Citation": f"({c})", "Status": status})
                
                st.table(audit_data)
                
                # Output Report
                report = "MCL AUDIT REPORT\n" + "-"*20 + "\n"
                for item in audit_data:
                    report += f"{item['Status']}: {item['Citation']}\n"
                
                st.download_button("📥 Download Report", report, "Audit_Report.txt", key="audit_dl")
            else:
                st.info("No citations detected. Please ensure your citations use brackets, e.g. (Smith, 2024).")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #37474f; font-size: 0.9em;'>"
    f"© 2026 Macmillan Centre for Learning.<br>"
    f"<a href='https://www.macmillancentreforlearning.co.uk/home-2/' style='color: #0288d1;'>Go to Macmillan Centre for Learning</a>"
    f"</div>", 
    unsafe_allow_html=True
)
