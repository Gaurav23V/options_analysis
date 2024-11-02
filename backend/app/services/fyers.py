from fyers_apiv3 import fyersModel
import requests
import time
import json
import os
import pandas as pd
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FyersServiceError(Exception):
    """Base exception for FyersService related errors"""
    pass

class AuthenticationError(FyersServiceError):
    """Raised when authentication fails"""
    pass

class TokenRefreshError(FyersServiceError):
    """Raised when token refresh fails"""
    pass

class OptionChainError(FyersServiceError):
    """Raised when option chain data fetch fails"""
    pass

class FyersService:
    BASE_URL = "https://api.fyers.in"
    
    def __init__(self):
        try:
            self.client_id = settings.FYERS_CLIENT_ID
            self.client_id_hash = settings.FYERS_CLIENT_ID_HASH
            self.refresh_token = settings.FYERS_REFRESH_TOKEN
            self.pin = settings.FYERS_PIN
            self.access_token = settings.FYERS_ACCESS_TOKEN
            self.token_expires_at = settings.FYERS_TOKEN_EXPIRES_AT

            if not all([self.client_id, self.client_id_hash, self.refresh_token, self.pin]):
                raise AuthenticationError("Missing required credentials in settings")

            self.fyers = fyersModel.FyersModel(
                client_id=self.client_id, 
                token=self.access_token,
                is_async=False, 
                log_path=""
            )
            
            self.authenticate()
            
        except Exception as e:
            logger.error(f"Failed to initialize FyersService: {str(e)}", exc_info=True)
            raise FyersServiceError(f"Service initialization failed: {str(e)}")

    def authenticate(self) -> None:
        """Authenticate with Fyers API"""
        try:
            current_time = time.time()
            logger.info(f"Checking token status - Current time: {current_time}, Expires at: {self.token_expires_at}")
            
            if not self.access_token or current_time >= float(self.token_expires_at):
                logger.info("Access token missing or expired, initiating refresh...")
                self.refresh_access_token()
            else:
                logger.info("Access token is valid, initializing FyersModel...")
                self.fyers = fyersModel.FyersModel(
                    client_id=self.client_id, 
                    token=self.access_token, 
                    is_async=False
                )
                
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}", exc_info=True)
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")

    def refresh_access_token(self) -> None:
        """Refresh the access token"""
        logger.info("Initiating access token refresh...")
        
        try:
            url = 'https://api-t1.fyers.in/api/v3/validate-refresh-token'
            headers = {'Content-Type': 'application/json'}
            data = {
                'grant_type': 'refresh_token',
                'appIdHash': self.client_id_hash,
                'refresh_token': self.refresh_token,
                'pin': self.pin
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raises HTTPError for bad responses
            
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode API response: {response.text}")
                raise TokenRefreshError(f"Invalid JSON response: {str(e)}")

            if not response_data.get("access_token"):
                raise TokenRefreshError("No access token in response")

            self.access_token = response_data["access_token"]
            expires_in = response_data.get("expires_in", 86400)
            self.token_expires_at = time.time() + expires_in - 60

            self.save_tokens()
            
            logger.info("Access token refreshed successfully")
            self.fyers = fyersModel.FyersModel(
                client_id=self.client_id, 
                token=self.access_token, 
                is_async=False
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed during token refresh: {str(e)}", exc_info=True)
            raise TokenRefreshError(f"Failed to refresh token: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
            raise TokenRefreshError(f"Token refresh failed: {str(e)}")

    def save_tokens(self) -> None:
        """Save tokens to settings and .env file"""
        try:
            settings.FYERS_ACCESS_TOKEN = self.access_token
            settings.FYERS_TOKEN_EXPIRES_AT = str(int(self.token_expires_at))

            self.update_env_file({
                "FYERS_ACCESS_TOKEN": self.access_token,
                "FYERS_TOKEN_EXPIRES_AT": str(int(self.token_expires_at))
            })
            logger.info("Tokens saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save tokens: {str(e)}", exc_info=True)
            raise FyersServiceError(f"Failed to save tokens: {str(e)}")

    def update_env_file(self, new_vars: Dict[str, str]) -> None:
        """Update the .env file with new variables"""
        try:
            env_vars = {}
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        if line.strip() and '=' in line:
                            key, value = line.strip().split('=', 1)
                            env_vars[key] = value

            env_vars.update(new_vars)

            with open('.env', 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
                    
            logger.info(".env file updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update .env file: {str(e)}", exc_info=True)
            raise FyersServiceError(f"Failed to update .env file: {str(e)}")
    
    def get_option_chain(self, symbol: str, strike_count: int) -> Optional[pd.DataFrame]:
        """
        Get option chain data for a symbol
        
        Args:
            symbol (str): The symbol to get option chain for
            strike_count (int): Number of strikes to fetch
            
        Returns:
            Optional[pd.DataFrame]: DataFrame containing option chain data
            
        Raises:
            OptionChainError: If failed to fetch or process option chain data
        """
        try:
            logger.info(f"Fetching option chain for {symbol} with {strike_count} strikes")
            
            if not symbol or not isinstance(strike_count, int):
                raise ValueError("Invalid symbol or strike_count")

            data = {
                "symbol": symbol,
                "strikecount": strike_count,
                "timestamp": ""
            }

            response = self.fyers.optionchain(data=data)
            
            if response.get("s") != "ok":
                error_msg = response.get("message", "Unknown error")
                raise OptionChainError(f"API returned error: {error_msg}")

            data = response.get("data", {})
            if not data or "optionsChain" not in data:
                raise OptionChainError("No options chain data in response")

            options_chain_df = pd.DataFrame(data["optionsChain"])
            
            # Apply filters and transformations
            options_chain_df = options_chain_df[options_chain_df['ask'] != 0]
            options_chain_df = options_chain_df[['ask', 'bid', 'option_type', 'strike_price', 'symbol']]
            options_chain_df = options_chain_df.iloc[1:]
            
            logger.info(f"Successfully retrieved option chain data for {symbol}")
            return options_chain_df
            
        except (KeyError, ValueError, pd.errors.EmptyDataError) as e:
            logger.error(f"Data processing error for {symbol}: {str(e)}", exc_info=True)
            raise OptionChainError(f"Failed to process option chain data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting option chain for {symbol}: {str(e)}", exc_info=True)
            raise OptionChainError(f"Failed to get option chain: {str(e)}")