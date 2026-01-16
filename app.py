import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
import leeds_harvard_tool as lht

# --- INITIALIZATION ---
if 'bibliography' not in st.session_state: 
    st.session_state.bibliography = []

st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; } 
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    .method-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #009688; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide & Instructions", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: RESTORED GUIDE ---
with tabs[0]:
    st.title("🎓 Leeds Harvard Referencing Guide")
    
    with st.container():
        st.markdown("""
        <div class="method-box">
        <h3>What is the Leeds Harvard Method?</h3>
        <p>The Leeds Harvard style is an <strong>Author-Date</strong> system. It requires two parts:</p>
        <ul>
            <li><strong>In-text citations:</strong> Brief details in brackets within your essay (e.g., <em>Adams, 1906</em>).</li>
            <li><strong>Bibliography:</strong> A complete list of all sources at the end of your work, arranged alphabetically.</li>
        </ul>
        <p><strong>Core Format:</strong> Family name, INITIAL(S). Year. <em>Title (italics)</em>. Edition. Place: Publisher.</p>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("🚀 How to Use This Tool")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown("""
        **1. Input Sources**
        Use the Book, Journal, or Website tabs. You can search by title or enter details manually.
        
        **2. Bibliography Tab**
        Review your list. Click **'One-Click Correction'** to ensure Scottish Social Care legislation meets Gold Standards.
        """)
    with col_i2:
        st.markdown("""
        **3. Smart Audit**
        Upload your essay (.docx). The tool checks if your in-text citations match your bibliography and flags missing page numbers in quotes.
        
        **4. Glossary**
        Check definitions for plagiarism, paraphrasing, and secondary citations.
        """)
    
    st.divider()
    st.subheader("📚 Examples")
    st.code("Adams, A.D. 1906. Electric transmission of water power. New York: McGraw.")
    st.code("Finch, E. and Fafinski, S. 2015. Legal skills. 5th ed. Oxford: Oxford University Press.")

# --- TAB 5: BIBLIOGRAPHY ---
with tabs[4]:
    st.header("Bibliography Management")
    if st.session_state.bibliography:
        if st.button("🪄 One-Click Gold Standard Correction"):
            st.session_state.bibliography = lht.apply_one_click_corrections(st.session_state.bibliography)
            st.rerun()
        
        # Word Export with Printable Guide logic
        doc = Document()
        doc.add_heading('MCL Referencing: Quick Desk Guide', 0)
        doc.add_paragraph("In-text: (Author, Year) | Quote: (Author, Year, p. X)")
        doc.add_page_break()
        doc.add_heading('Bibliography', 1)
        st.session_state.bibliography.sort()
        for ref in st.session_state.bibliography:
            doc.add_paragraph(ref).style.font.size = Pt(11)
        
        buf = BytesIO(); doc.save(buf)
        st.download_button("📥 Download Bibliography & Printable Guide", buf.getvalue(), "MCL_References.docx")
        st.divider()
        for r in st.session_state.bibliography: st.info(r)
    else:
        st.warning("Add sources in the other tabs to build your list!")

# --- TAB 6: SMART AUDIT ---
with tabs[5]:
    st.header("🔍 Smart Essay Audit")
    up = st.file_uploader("Upload your Essay (.docx)", type="docx")
    if up and st.button("Run Audit"):
        doc = Document(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        results = []
        for i, p in enumerate(doc.paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
            for c in cites:
                clean_cite = lht.clean_text(c)
                matched = any(clean_cite in cb or cb in clean_cite for cb in clean_bib if cb)
                
                # Enhanced feedback logic
                feedback = "Verified" if matched else "⚠️ Not in Bibliography"
                if '"' in p.text and not any(x in c.lower() for x in ["p.", "page"]):
                    feedback = "⚠️ Quote: Missing page number (p. X)"
                    matched = False
                
                results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if matched else "❌", "Feedback": feedback})
        st.table(results)

# --- TAB 7: GLOSSARY ---
with tabs[6]:
    st.header("📚 Academic Glossary")
    st.markdown("""
    **Plagiarism:** Presenting someone else's work or ideas as your own.
    **Paraphrasing:** Rewriting ideas in your own words (still needs a citation).
    **Direct Quote:** Exact words (requires "marks" and page numbers).
    **Secondary Citation:** Citing a source mentioned in another source (e.g., Smith cited in Jones).
    """)
