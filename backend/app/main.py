from contextlib import asynccontextmanager

from app.routes.transactions import router as transaction_router

from app.routes.dashboard import router as dashboard_router

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.connection import engine, Base, get_db
from app.models.transaction import Transaction


# Initialize database tables
@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title="FinSight AI API",
    description="AI-Powered Cash Flow Forecasting System",
    version="1.0.0",
    lifespan=lifespan
)


# React frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(transaction_router)
app.include_router(dashboard_router)

@app.get("/")
def home():

    return {
        "message": "Welcome to FinSight AI Backend",
        "status": "Running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.get("/db-check")
def database_check(db: Session = Depends(get_db)):

    db.execute(text("SELECT 1"))

    return {
        "database": "Connected successfully",
        "database_name": "finsight_db"
    }