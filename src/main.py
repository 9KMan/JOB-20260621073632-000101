// src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth, invoices, purchase_orders, delivery_notes, matches
from src.database import engine, Base
from src.config import get_settings

settings = get_settings()

app = FastAPI(
    title="FinaRo - AP Automation Core Engine",
    description="3-Way Matching Engine (Invoice × Delivery Note × Purchase Order)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(purchase_orders.router, prefix="/api/v1/purchase-orders", tags=["Purchase Orders"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(delivery_notes.router, prefix="/api/v1/delivery-notes", tags=["Delivery Notes"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["Matching"])


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FinaRo AP Automation"}


@app.get("/")
async def root():
    return {
        "service": "FinaRo AP Automation Core Engine",
        "version": "1.0.0",
        "docs": "/docs"
    }
