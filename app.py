import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
import leeds_harvard_tool as lht

# --- 1. INITIALIZATION ---
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; color: #37474f; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .stInfo { background-color: #ffffff; border-left: 5px solid #009688; padding: 10px; border-radius: 5px; }
    .guide-box { background-color: #f9a825; padding: 15px; border-radius: 10px; color: white; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. BRANDED HEADER ---
header_path = "assets/Header.png"
if os.path.exists(header_path):
    st.image(header_path, use_column_width=True)

# --- 4. TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "💡 Method Guide"
])

# (Tabs 1-5 remain consistent with the previous logic for Magic Fill, Corrections, and Audit)

# --- TAB 6: METHOD GUIDE ---
with tab6:
    st.header("The Leeds Harvard Method")
    st.markdown("""
    <div class="guide-box">
    <strong>MCL Tip:</strong> References allow others to find your sources and give credit to authors. 
    Incorrect referencing can lead to plagiarism flags.
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("1. In-text Citations")
        st.write("Place these in the body of your essay whenever you use an idea.")
        st.code("(Surname, Year)")
        st.write("**Direct Quotes:** Must include a page number.")
        st.code("(Surname, Year, p. 12)")
        
    with col_b:
        st.subheader("2. The Bibliography")
        st.write("A complete list at the end of your work, in alphabetical order.")
        st.write("**Book Format:**")
        st.info("Author. (Year) Title. Edition. Place: Publisher.")
        st.write("**Website Format:**")
        st.info("Author. (Year) Title. [Online]. [Accessed Date]. Available from: URL")

    st.divider()
    st.subheader("Common MCL Standard References")
    st.write("The tool's **One-Click Correction** ensures these are always perfect:")
    st.table({
        "Source": ["Bee & Boyd", "SSSC Codes", "Equality Act", "Care Review"],
        "Correct Format": [
            "Bee, H. and Boyd, D. (2002) Life Span Development...",
            "Scottish Social Services Council (2024)...",
            "Great Britain (2010) Equality Act 2010...",
            "Independent Care Review (2021)..."
        ]
    })
