import streamlit as st
from datetime import datetime

def sidebar():
    st.sidebar.header("Input Parameters")
    
    # Replace selectbox with text input
    instrument_name = st.sidebar.text_input("Instrument")
    
    # Show example instruments below the input
    st.sidebar.text("Eg: FEDERALBNK, TATACHEM, NIFTY")
    
    expiry_date = st.sidebar.date_input("Expiry Date", min_value=datetime.now())
    expiry_date_str = expiry_date.strftime("%Y-%m-%d")
    side = st.sidebar.selectbox("Option Side", ["PE", "CE"])
    
    return instrument_name, expiry_date_str, side