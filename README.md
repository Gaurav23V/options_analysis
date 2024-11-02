# Option Chain Data Processing API

## Overview

The Option Chain Data Processing API is a FastAPI-based backend application designed to handle option chain data processing for the Indian financial markets. It integrates with the Fyers options chain API to fetch real-time option chain data and performs specific financial calculations related to options trading. Users can input an instrument name (e.g., NIFTY or FEDERALBNK), an expiry date, and an option type (either Put Options "PE" or Call Options "CE"). Based on this input, the API retrieves relevant option chain information, calculates the highest bid or ask prices, and computes additional financial metrics such as margin requirements and premium earned.

This application serves as a powerful tool for traders and financial analysts who need to process and analyze options data efficiently, providing essential insights for informed decision-making in options trading strategies.

## Features

- **Fetch Option Chain Data**: Retrieves option chain data for a specified instrument and expiry date.
- **Calculate Highest Option Prices**: Determines the highest bid price for put options (PE) or the highest ask price for call options (CE) at each strike price.
- **Financial Calculations**: Computes additional financial metrics, including margin requirements and premium earned for each option contract.
- **User-Friendly API**: Provides easy-to-use endpoints for frontend integration.
- **Robust Error Handling**: Implements comprehensive error checking and validation to ensure reliable performance.
- **Secure Authentication**: Integrates with the Fyers API using secure token management.

## Technical Stack

**Backend:**

- Python
- FastAPI
- Uvicorn
- Pandas
- Requests
- Fyers API (fyers-apiv3)
- python-dotenv
- Pydantic
- pydantic-settings

**Frontend:**

- Streamlit
- Pandas
- Requests
- Matplotlib
- Plotly

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/gaurav23v/options_analysis.git
   cd options_analysis
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Backend Dependencies**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install Frontend Dependencies**

   ```bash
   cd frontend
   pip install -r requirements.txt
   cd ..
   ```

5. **Setup Environment Variables**

   - Create a `.env` file in the `backend` directory with the necessary configuration (see the Configuration section).

6. **Run the Application**

   - **Backend:**

     ```bash
     uvicorn app.main:app --reload
     ```

   - **Frontend:**

     ```bash
     cd frontend
     streamlit run app.py
     ```

## Configuration

The application requires specific environment variables and API keys to function correctly. Create a `.env` file in the `backend` directory with the following content:

```ini
# Fyers API Credentials
FYERS_CLIENT_ID=your_fyers_client_id
FYERS_CLIENT_ID_HASH=sha256(fyers_client_id:fyers_secret_key)
FYERS_PIN=XXXX
FYERS_SECRET_KEY=your_fyers_secret_key
FYERS_REDIRECT_URI=your_fyers_redirect_uri

# Authentication Tokens (will be managed by the application)
FYERS_ACCESS_TOKEN=
FYERS_REFRESH_TOKEN=
FYERS_TOKEN_EXPIRES_AT=0 #(will be updated by the application)

# Application Settings
API_HOST=localhost
API_PORT=8000
ENVIRONMENT=development  # or 'production'
```

- **FYERS_CLIENT_ID**: Your Fyers API client ID.
- **FYERS_SECRET_KEY**: Your Fyers API secret key.
- **FYERS_REDIRECT_URI**: Your redirect URI registered with Fyers.
- **FYERS_ACCESS_TOKEN**: Will be auto-populated after authentication.
- **FYERS_REFRESH_TOKEN**: Will be auto-populated after authentication.
- **API_HOST**: The host where the API will run (default: localhost).
- **API_PORT**: The port on which the API will listen (default: 8000).
- **ENVIRONMENT**: The application environment (development or production).

## API Documentation

### **Endpoint**: `/option-chain`

- **Method**: `GET`
- **Description**: Fetches option chain data for the specified instrument, expiry date, and option type, and returns processed data including the highest option prices, margin requirements, and premium earned.

#### **Parameters**

- **instrument_name**: `string` (required)
  - The name of the instrument (e.g., "NIFTY", "BANKNIFTY").
- **expiry_date**: `string` (required)
  - The expiry date of the options in `YYYY-MM-DD` format.
- **side**: `string` (required)
  - The option type: "CE" for Call Options or "PE" for Put Options.

#### **Response**

- **Status Code**: `200 OK`
- **Content**: JSON
  - **strike_price**: `float` - The strike price of the option.
  - **highest_bid_ask_price**: `float` - The highest bid price for PE or the highest ask price for CE.
  - **margin_required**: `float` - The margin required for selling the option.
  - **premium_earned**: `float` - The premium earned from selling the option.

### **Functionality Overview**

1. **Authentication**

   - The API uses the `FyersService` class to manage authentication with the Fyers API.
   - Tokens are refreshed automatically when expired.

2. **Data Retrieval**

   - Fetches the option chain data for the specified instrument and expiry date.
   - Utilizes the `get_option_chain()` method from the Fyers API integration service.

3. **Data Processing**

   - Filters the option chain data based on the selected side (PE or CE).
   - Calculates the highest bid price (for PE) or highest ask price (for CE) for each strike price.
   - Uses the `get_highest_option_prices()` function from the calculations module.

4. **Financial Calculations**

   - Computes the margin required for selling each option using the `calculate_margin_and_premium()` function.
     - Margin requirements are fetched from the broker's API based on the option contract. The default quantity for margin calculation is set as the lot size provided by the broker API
   - Calculates the premium earned by multiplying the highest bid/ask price by the lot size for each option.

5. **Response Generation**

   - Constructs a response containing all the calculated fields.
   - Ensures data integrity and error handling throughout the process.

## Usage Examples

### **API Call Example**

**Request**

```http
GET /option-chain?instrument_name=NIFTY&expiry_date=2023-12-28&side=PE HTTP/1.1
Host: localhost:8000
Content-Type: application/json
```

**Response**

```json
[
  {
    "strike_price": 19000,
    "highest_bid_ask_price": 150.5,
    "margin_required": 120000,
    "premium_earned": 112875
  },
  {
    "strike_price": 19100,
    "highest_bid_ask_price": 160.0,
    "margin_required": 125000,
    "premium_earned": 120000
  },
  ...
]
```

### **Frontend Integration**

In the frontend Streamlit application:

```python
import streamlit as st
import requests
import pandas as pd

# User inputs
instrument_name = st.text_input("Instrument Name", "NIFTY")
expiry_date = st.date_input("Expiry Date")
side = st.selectbox("Option Type", ["PE", "CE"])

# Fetch data
response = requests.get(
    "http://localhost:8000/option-chain",
    params={
        "instrument_name": instrument_name,
        "expiry_date": expiry_date.strftime("%Y-%m-%d"),
        "side": side
    }
)

data = response.json()
df = pd.DataFrame(data)

# Display data
st.dataframe(df)
```

## AI Assistance Documentation

During the development of this application, AI tools were leveraged in several key areas:

1. **Understanding Financial Concepts**
   - AI tools assisted in comprehending complex financial terminologies and concepts related to options trading, ensuring accurate implementation of financial calculations.

2. **Architectural Design**
   - AI provided guidance in designing a robust and scalable architecture for the application, helping to outline the project structure and determine the best practices for integration and modularization.

3. **Debugging and Logging Mechanisms**
   - AI tools were utilized to implement effective debugging strategies during development.
   - Assisted in setting up comprehensive logging mechanisms to enhance error handling and facilitate easier maintenance.

4. **Code Optimization**
   - AI recommendations were followed to improve code structure, enhance readability, and optimize performance after the core functionality was implemented.

5. **And generation of this README as well**

## Testing

To ensure the reliability and accuracy of the Option Chain Data Processing API, the following testing strategies can be employed:

1. **Unit Testing**

   - Test individual functions such as `get_highest_option_prices()` and `calculate_margin_and_premium()` with predefined inputs and validate the outputs.
   - Mock external API calls to the Fyers API to test the application logic without relying on live data.

2. **Integration Testing**

   - Test the full API endpoint `/option-chain` with various valid and invalid inputs to ensure it behaves as expected.
   - Verify the authentication flow with the Fyers API, including token refresh mechanisms.

3. **Performance Testing**

   - Assess the API's performance with large datasets to ensure it handles high volumes of data efficiently.
   - Use tools like Apache JMeter or Locust to simulate multiple concurrent requests.

4. **Error Handling Testing**

   - Intentionally cause errors (e.g., invalid parameters, expired tokens) to ensure the API responds with appropriate error messages and status codes.
   - Check that sensitive information is not exposed in error responses.

5. **User Acceptance Testing**

   - Validate the frontend and backend integration by simulating user interactions through the Streamlit application.
   - Ensure the data displayed to the user matches the expected results based on known inputs.

6. **Regression Testing**

   - After updates or changes to the codebase, run a suite of tests to confirm that existing functionality remains unaffected.

## Error Handling

The application implements comprehensive error handling to ensure robustness and reliability:

1. **Custom Exception Classes**

   - **FyersServiceError**: Handles errors related to the Fyers API integration.
   - **OptionChainError**: Manages errors during option chain data retrieval and processing.
   - **CalculationError**: Catches exceptions in financial calculations.
   - **SymbolUtilsError**: Handles issues with symbol resolution and validation.

2. **HTTP Response Codes**

   - **400 Bad Request**: Returned when the client provides invalid parameters or malformed requests.
   - **401 Unauthorized**: Indicates authentication failures with the Fyers API.
   - **404 Not Found**: When the requested data is not available.
   - **500 Internal Server Error**: For unexpected server-side errors.
   - **503 Service Unavailable**: When external services (like the Fyers API) are unreachable.

3. **Validation and Sanitization**

   - Input parameters are validated using Pydantic models.
   - Ensures that dates, instrument names, and option types conform to expected formats.

4. **Logging**

   - Errors are logged with detailed stack traces for debugging.
   - Logs include timestamps and unique request identifiers for traceability.

5. **User Feedback**

   - Error responses provide meaningful messages to help users understand and rectify issues.
   - Sensitive information is not exposed in error messages to maintain security.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Thank you for exploring the Option Chain Data Processing API. Contributions, suggestions, and feedback are welcome to enhance the functionality and reliability of this application.