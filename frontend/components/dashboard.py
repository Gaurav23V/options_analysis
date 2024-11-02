# frontend/components/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

def display_dashboard(data):
    df = pd.DataFrame(data)
    st.subheader("Option Chain Data")
    st.dataframe(df)
