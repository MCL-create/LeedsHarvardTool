import streamlit as st
from leeds_harvard_tool import generate_reference  # this comes from your main tool

st.set_page_config(page_title="Leeds Harvard Referencing Tool", page_icon="📚", layout="centered")

st.title("📚 Leeds Harvard Referencing Checker & Guide")

st.markdown(
    """
    Use this tool to check and build Leeds Harvard references.  
    Enter the details below and the tool will show you the correct format.  
    This way you can learn how to structure your own references correctly.
    """
)

# Input fields for reference details
author = st.text_input("Author(s) (e.g., Smith, J.)")
year = st.text_input("Year (e.g., 2023)")
title = st.text_input("Title of Book/Article")
publisher = st.text_input("Publisher (if applicable)")
place = st.text_input("Place of Publication (if applicable)")

# Button to generate the reference
if st.button("Generate Reference"):
    if author and year and title:
        reference = generate_reference(author, year, title, publisher, place)
        st.success(f"✅ Your Leeds Harvard reference:\n\n{reference}")
        st.info("Tip: Compare this output with your own reference to see where you might need to amend it.")
    else:
        st.error("⚠️ Please fill in at least Author, Year, and Title.")

