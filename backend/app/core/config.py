from pydantic_settings import BaseSettings
from pydantic.error_wrappers import ValidationError
import os

class Settings(BaseSettings):
    FYERS_CLIENT_ID: str
    FYERS_CLIENT_ID_HASH: str
    FYERS_ACCESS_TOKEN: str
    FYERS_REFRESH_TOKEN: str
    FYERS_PIN: str
    api_host: str
    api_port: int
    environment: str
    FYERS_TOKEN_EXPIRES_AT: int  # Added this line

    class Config:
        env_file = ".env"

try:
    settings = Settings()
except ValidationError as e:
    print(f"Error loading settings: {e}")