# API package init
from . import (
    rag_routes, 
    chat_routes, 
    prescription_routes,
    amu_routes,
    mrl_routes,
    risk_routes,
    database_routes
)

__all__ = [
    "rag_routes", 
    "chat_routes", 
    "prescription_routes", 
    "amu_routes",
    "mrl_routes", 
    "risk_routes",
    "database_routes"
]