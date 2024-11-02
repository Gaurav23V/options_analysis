# components/right_sidebar.py
import streamlit as st

def right_documentation_sidebar():
    with st.sidebar:
        # Using columns to create space between left and right sidebars
        # This pushes our documentation to the right
        col1, col2 = st.columns([2, 10])
        
        with col2:
            st.markdown("# 📚 Documentation")
            
            with st.expander("Overview", expanded=True):
                st.markdown("""
                This application provides real-time options chain data analysis 
                and visualization. The project repository is available at 
                [GitHub](https://github.com/Gaurav23V/options_analysis).
                """)
            
            with st.expander("Input Parameters"):
                st.markdown("""
                ### Required Inputs
                - **Instrument Name**: Select the trading instrument
                - **Expiry Date**: Choose the options expiry date
                - **Side**: Select PE (Put) or CE (Call) options
                """)
            
            with st.expander("Data Flow"):
                st.markdown("""
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
                """)
            
            with st.expander("Backend Structure"):
                st.markdown("""
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
                """)
            
            with st.expander("Processing Steps"):
                st.markdown("""
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
                """)
            
            with st.expander("Security & Error Handling"):
                st.markdown("""
                ### Security Features
                - Automatic token refresh mechanism
                - Input validation at multiple levels
                - Secure API integration
                
                ### Error Handling
                - Comprehensive input validation
                - Logging at each processing step
                - User-friendly error messages
                """)