# frontend/app.py
import streamlit as st
from components.sidebar import sidebar
from components.dashboard import display_dashboard
from utils.api_client import get_option_chain_data

def main():
    st.title("Options Trading Analysis App")
    instrument_name, expiry_date, side = sidebar()

    if st.button("Get Option Chain Data"):
        with st.spinner("Fetching data..."):
            data = get_option_chain_data(instrument_name, expiry_date, side)
            if data:
                display_dashboard(data)
            else:
                st.error("No data available.")

if __name__ == "__main__":
    main()
