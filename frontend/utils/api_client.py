# frontend/utils/api_client.py
import requests
import os
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")

def get_option_chain_data(instrument_name, expiry_date, side):
    try:
        url = f"{BACKEND_URL}/option-chain"
        params = {
            'instrument_name': instrument_name,
            'expiry_date': expiry_date,
            'side': side
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None
