import pandas as pd
import requests
import logging
from typing import Tuple, Optional
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.fyers import FyersService, FyersServiceError
from app.utils.symbol_utils import get_symbol_name

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalculationError(Exception):
    """Base exception for calculation related errors"""
    pass

class MarginCalculationError(CalculationError):
    """Raised when margin calculation fails"""
    pass

class DataProcessingError(CalculationError):
    """Raised when data processing fails"""
    pass

def validate_input_parameters(instrument_name: str, expiry_date: str, side: str) -> None:
    """Validate input parameters for option chain calculations"""
    if not instrument_name or not isinstance(instrument_name, str):
        raise ValueError("Invalid instrument name")
        
    if not expiry_date or not isinstance(expiry_date, str):
        raise ValueError("Invalid expiry date")
        
    if side not in ['CE', 'PE']:
        raise ValueError("Side must be either 'CE' or 'PE'")

def get_highest_option_prices(
    options_chain_df: pd.DataFrame, 
    instrument_name: str, 
    side: str
) -> pd.DataFrame:
    """
    Get highest option prices for either PE bid or CE ask based on side parameter.
    
    Args:
        options_chain_df: DataFrame containing option chain data
        instrument_name: Name of the instrument
        side: 'PE' for put options or 'CE' for call options
        
    Returns:
        DataFrame with filtered and processed option prices
        
    Raises:
        DataProcessingError: If processing fails
    """
    try:
        logger.info(f"Processing option prices for {instrument_name} ({side})")
        
        if options_chain_df.empty:
            raise DataProcessingError("Empty options chain data")
            
        required_columns = {'option_type', 'ask', 'bid'}
        if not all(col in options_chain_df.columns for col in required_columns):
            raise DataProcessingError("Missing required columns in options chain data")

        # Filter by option type
        filtered_df = options_chain_df[options_chain_df['option_type'] == side].copy()
        
        if filtered_df.empty:
            raise DataProcessingError(f"No data found for option type {side}")

        # Set bid/ask values
        filtered_df['bid/ask'] = filtered_df.apply(
            lambda row: row['ask'] if side == 'CE' else row['bid'], 
            axis=1
        )

        # Clean up and add instrument name
        filtered_df = filtered_df.drop(columns=['ask', 'bid'])
        filtered_df['instrument_name'] = instrument_name

        logger.info(f"Successfully processed option prices for {instrument_name}")
        return filtered_df
        
    except Exception as e:
        logger.error(f"Error processing option prices: {str(e)}", exc_info=True)
        raise DataProcessingError(f"Failed to process option prices: {str(e)}")

def get_option_chain_data(
    instrument_name: str, 
    expiry_date: str, 
    side: str
) -> Tuple[pd.DataFrame, int]:
    """
    Fetch and process option chain data.
    
    Args:
        instrument_name: Name of the instrument
        expiry_date: Expiry date string
        side: Option type ('CE' or 'PE')
        
    Returns:
        Tuple of (processed DataFrame, lot size)
        
    Raises:
        HTTPException: If any step fails
    """
    try:
        logger.info(f"Fetching option chain data for {instrument_name} expiring {expiry_date}")
        
        # Validate input parameters
        validate_input_parameters(instrument_name, expiry_date, side)
        
        # Get symbol and lot size
        symbol, lot_size = get_symbol_name(instrument_name, expiry_date, side)
        strike_count = 40

        # Initialize FyersService and fetch data
        fyers_service = FyersService()
        options_chain_data = fyers_service.get_option_chain(symbol, strike_count)
        
        if options_chain_data is None or options_chain_data.empty:
            raise DataProcessingError("No option chain data received")

        # Process the data
        result_df = get_highest_option_prices(options_chain_data, instrument_name, side)
        
        logger.info(f"Successfully retrieved option chain data for {instrument_name}")
        return result_df, lot_size
        
    except FyersServiceError as e:
        logger.error(f"Fyers service error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Fyers service error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DataProcessingError as e:
        logger.error(f"Data processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

def calculate_margin_and_premium(df: pd.DataFrame, lot_size: int) -> pd.DataFrame:
    """
    Calculate margin and premium for option positions.
    
    Args:
        df: DataFrame containing option data
        lot_size: Size of each lot
        
    Returns:
        DataFrame with added margin and premium columns
        
    Raises:
        MarginCalculationError: If margin calculation fails
    """
    try:
        logger.info("Calculating margin and premium")
        
        if df.empty:
            raise MarginCalculationError("Empty DataFrame provided")
            
        if not isinstance(lot_size, int) or lot_size <= 0:
            raise ValueError("Invalid lot size")

        result_df = df.copy()
        result_df['margin'] = 0.0
        result_df['premium'] = 0.0
        
        url = "https://api.fyers.in/api/v2/span_margin"
        headers = {
            "Authorization": f"{settings.FYERS_CLIENT_ID}:{settings.FYERS_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        for idx, row in result_df.iterrows():
            try:
                payload = {
                    "data": [{
                        "symbol": row['symbol'],
                        "qty": lot_size,
                        "side": -1,
                        "type": 2,
                        "productType": "INTRADAY",
                        "limitPrice": 0.0,
                        "stopLoss": 0.0
                    }]
                }
                
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                margin_data = response.json()
                
                if not margin_data.get('data', {}).get('total'):
                    logger.warning(f"No margin data received for symbol {row['symbol']}")
                    continue
                    
                result_df.at[idx, 'margin'] = margin_data['data']['total']
                
                # Calculate premium
                if 'bid/ask' in row:
                    result_df.at[idx, 'premium'] = row['bid/ask'] * lot_size
                else:
                    result_df.at[idx, 'premium'] = row.get('last_traded_price', 0) * lot_size
                    
            except requests.RequestException as e:
                logger.error(f"API error for symbol {row['symbol']}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Calculation error for symbol {row['symbol']}: {str(e)}")
                continue

        logger.info("Successfully calculated margin and premium")
        return result_df
        
    except ValueError as e:
        logger.error(f"Invalid input error: {str(e)}", exc_info=True)
        raise MarginCalculationError(f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Margin calculation error: {str(e)}", exc_info=True)
        raise MarginCalculationError(f"Failed to calculate margin: {str(e)}")