#!/usr/bin/env python3
"""Simple Streamlit test app"""

import streamlit as st

st.title("🧪 Streamlit Connection Test")
st.write("If you can see this, Streamlit is working correctly!")
st.success("✅ Server connection is functional")

# Test basic functionality
if st.button("Test Button"):
    st.balloons()
    st.write("🎉 Button clicked successfully!")

st.info("This is a simple test to verify Streamlit server connectivity.")