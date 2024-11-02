import pandas as pd
import logging
import requests
from datetime import datetime
from typing import Tuple, Optional
from fastapi import HTTPException, status

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SymbolUtilsError(Exception):
    """Base exception for symbol utils related errors"""
    pass

class SymbolNotFoundError(SymbolUtilsError):
    """Raised when symbol is not found"""
    pass

class DataFetchError(SymbolUtilsError):
    """Raised when data fetch fails"""
    pass

def validate_input_parameters(instrument_name: str, expiry_date: str, side: str) -> None:
    """
    Validate input parameters for symbol name resolution.
    
    Args:
        instrument_name: Name of the instrument
        expiry_date: Expiry date string
        side: Option type
        
    Raises:
        ValueError: If any parameter is invalid
    """
    if not instrument_name or not isinstance(instrument_name, str):
        raise ValueError("Invalid instrument name")
    
    try:
        # Validate date format
        datetime.strptime(expiry_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid expiry date format. Use YYYY-MM-DD")
    
    if side not in ['CE', 'PE']:
        raise ValueError("Side must be either 'CE' or 'PE'")

def fetch_symbol_data() -> pd.DataFrame:
    """
    Fetch symbol data from Fyers API.
    
    Returns:
        DataFrame containing symbol data
        
    Raises:
        DataFetchError: If data fetch fails
    """
    try:
        url = 'https://public.fyers.in/sym_details/NSE_FO_sym_master.json'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        script = pd.read_json(url)
        if script.empty:
            raise DataFetchError("Empty data received from Fyers API")
            
        return script.T
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch symbol data: {str(e)}", exc_info=True)
        raise DataFetchError(f"Failed to fetch symbol data: {str(e)}")
    except ValueError as e:
        logger.error(f"Failed to parse symbol data: {str(e)}", exc_info=True)
        raise DataFetchError(f"Failed to parse symbol data: {str(e)}")

def process_symbol_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process and clean symbol data.
    
    Args:
        df: Raw symbol data DataFrame
        
    Returns:
        Processed DataFrame
        
    Raises:
        DataFetchError: If processing fails
    """
    try:
        required_columns = {'optType', 'underSym', 'expiryDate', 'minLotSize'}
        if not all(col in df.columns for col in required_columns):
            raise DataFetchError("Missing required columns in symbol data")

        # Select and filter columns
        processed_df = df[list(required_columns)].copy()
        processed_df = processed_df[processed_df['optType'] != 'XX']
        
        # Convert and format dates
        processed_df['expiryDate'] = pd.to_datetime(processed_df['expiryDate'], unit='s')
        processed_df['expiryDate'] = processed_df['expiryDate'].dt.strftime('%Y-%m-%d')
        
        return processed_df
        
    except Exception as e:
        logger.error(f"Failed to process symbol data: {str(e)}", exc_info=True)
        raise DataFetchError(f"Failed to process symbol data: {str(e)}")

def get_symbol_name(
    instrument_name: str, 
    expiry_date: str, 
    side: str
) -> Tuple[str, int]:
    """
    Get symbol name and lot size based on instrument, expiry date and option type.
    
    Args:
        instrument_name: Name of the instrument (e.g. 'HDFCBANK')
        expiry_date: Expiry date in 'YYYY-MM-DD' format
        side: Option type ('CE' or 'PE')
        
    Returns:
        Tuple of (symbol_name, lot_size)
        
    Raises:
        HTTPException: If any step fails
    """
    try:
        logger.info(f"Resolving symbol for {instrument_name} expiring {expiry_date} ({side})")
        
        # Validate input parameters
        validate_input_parameters(instrument_name, expiry_date, side)
        
        # Fetch and process data
        raw_data = fetch_symbol_data()
        processed_df = process_symbol_data(raw_data)
        
        # Apply filters
        filtered_df = processed_df[
            (processed_df['underSym'] == instrument_name) & 
            (processed_df['expiryDate'] == expiry_date) & 
            (processed_df['optType'] == side)
        ]
        
        if filtered_df.empty:
            raise SymbolNotFoundError(
                f"No symbol found for {instrument_name} expiring {expiry_date} ({side})"
            )
            
        # Get the symbol name and lot size
        symbol_name = filtered_df.index[0]
        lot_size = filtered_df.loc[symbol_name, 'minLotSize']
        
        if not isinstance(lot_size, (int, float)) or lot_size <= 0:
            raise ValueError(f"Invalid lot size: {lot_size}")
            
        logger.info(f"Successfully resolved symbol: {symbol_name} (lot size: {lot_size})")
        return symbol_name, int(lot_size)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DataFetchError as e:
        logger.error(f"Data fetch error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except SymbolNotFoundError as e:
        logger.error(f"Symbol not found: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while resolving symbol"
        )