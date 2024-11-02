from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from pandas.errors import EmptyDataError
import pandas as pd
from app.utils.calculations import get_option_chain_data, calculate_margin_and_premium

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class OptionChainError(Exception):
    """Base exception for option chain related errors"""
    pass

class InvalidParameterError(OptionChainError):
    """Raised when input parameters are invalid"""
    pass

class DataFetchError(OptionChainError):
    """Raised when there's an error fetching option chain data"""
    pass

def validate_parameters(instrument_name: str, expiry_date: str, side: str) -> None:
    """Validate input parameters"""
    if not instrument_name or not isinstance(instrument_name, str):
        raise InvalidParameterError("Invalid instrument name")
    
    # Validate expiry date format
    try:
        datetime.strptime(expiry_date, '%Y-%m-%d')
    except ValueError:
        raise InvalidParameterError("Invalid expiry date format. Use YYYY-MM-DD")
    
    if side.upper() not in ['CE', 'PE']:
        raise InvalidParameterError("Side must be either 'CE' or 'PE'")

@router.get("/option-chain", 
    response_model=List[Dict[str, Any]],
    responses={
        200: {"description": "Successfully retrieved option chain data"},
        400: {"description": "Invalid parameters"},
        404: {"description": "Data not found"},
        500: {"description": "Internal server error"}
    })
def option_chain(instrument_name: str, expiry_date: str, side: str):
    """
    Get option chain data for specified instrument and expiry date.
    
    Args:
        instrument_name (str): Name of the instrument
        expiry_date (str): Expiry date in YYYY-MM-DD format
        side (str): Option type (CE/PE)
        
    Returns:
        List[Dict]: List of option chain records
    """
    request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    logger.info(f"Request {request_id} - Processing option chain request for {instrument_name}, {expiry_date}, {side}")
    
    try:
        # Validate input parameters
        validate_parameters(instrument_name, expiry_date, side)
        
        # Fetch option chain data
        data, lot_size = get_option_chain_data(instrument_name, expiry_date, side)
        if data.empty:
            raise DataFetchError("No data found for the specified parameters")
            
        # Calculate margin and premium
        data = calculate_margin_and_premium(data, lot_size)
        
        # Select required columns
        result_data = data[['instrument_name', 'strike_price', 'option_type', 'bid/ask', 'margin', 'premium']]
        
        response_data = result_data.to_dict(orient='records')
        logger.info(f"Request {request_id} - Successfully processed option chain request")
        
        return response_data
        
    except InvalidParameterError as e:
        logger.error(f"Request {request_id} - Invalid parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except DataFetchError as e:
        logger.error(f"Request {request_id} - Data fetch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    except EmptyDataError as e:
        logger.error(f"Request {request_id} - Empty data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data available for the specified parameters"
        )
        
    except Exception as e:
        logger.error(f"Request {request_id} - Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request"
        )