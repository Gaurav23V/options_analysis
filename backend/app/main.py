# backend/app/main.py
from fastapi import FastAPI
from app.routers import option_chain  # Change to absolute import
from app.core.config import settings  # Change to absolute import
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Options Trading Analysis API",
    version="1.0.0",
    description="API for fetching option chain data and calculating margins and premiums."
)

# Include routers
app.include_router(option_chain.router, prefix="/api/v1")

# You can add middleware or exception handlers here if needed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)