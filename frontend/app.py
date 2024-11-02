import streamlit as st
from components.sidebar import sidebar
from components.dashboard import display_dashboard
from utils.api_client import get_option_chain_data

def display_documentation():
    """Display the documentation section."""
    with st.expander("📚 Documentation", expanded=True):
        st.markdown("""
        # About This Options Trading Analysis App
        
        ## Overview
        This application provides real-time options chain data analysis and visualization. The project repository is available at [GitHub](https://github.com/Gaurav23V/options_analysis).
        
        ## How It Works
        
        ### 1. Input Parameters
        - **Instrument Name**: Select the trading instrument
        - **Expiry Date**: Choose the options expiry date
        - **Side**: Select PE (Put) or CE (Call) options
        
        ### 2. Data Flow Architecture
        ```mermaid
        graph TD
            A[Frontend] --> B[/option-chain Endpoint/]
            B --> C[Input Validation]
            C --> D[Symbol Resolution]
            D --> E[Broker API Integration]
            E --> F[Data Processing]
            F --> G[Premium Calculation]
            G --> A
        ```
        
        ### 3. Key Components
        
        #### Backend Structure
        ```
        app/
        ├── core/
        │   └── config.py         # Configuration settings
        ├── services/
        │   └── fyers.py         # Broker API integration
        ├── utils/
        │   ├── calculations.py  # Options calculations
        │   └── symbol_utils.py  # Symbol utilities
        └── routes/
            └── option_chain.py  # API endpoints
        ```
        
        ### 4. Processing Steps
        1. **Symbol Resolution**
           - Fetches symbol data from broker API
           - Filters based on instrument name, expiry date, and option type
        
        2. **Data Retrieval**
           - Validates access tokens
           - Auto-refreshes expired tokens
           - Fetches option chain data using resolved symbol
        
        3. **Calculations**
           - Processes option chain data
           - Calculates margins based on lot size
           - Computes premiums using bid/ask prices
        
        ### 5. Security Features
        - Automatic token refresh mechanism
        - Input validation at multiple levels
        - Secure API integration
        
        ### 6. Error Handling
        - Comprehensive input validation
        - Logging at each processing step
        - User-friendly error messages
        """)

def main():
    st.set_page_config(
        page_title="Options Trading Analysis App",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("Options Trading Analysis App")
        instrument_name, expiry_date, side = sidebar()

        if st.button("Get Option Chain Data"):
            with st.spinner("Fetching data..."):
                data = get_option_chain_data(instrument_name, expiry_date, side)
                if data:
                    display_dashboard(data)
                else:
                    st.error("No data available.")
    
    # Display documentation in the right column
    with col2:
        display_documentation()

if __name__ == "__main__":
    main()