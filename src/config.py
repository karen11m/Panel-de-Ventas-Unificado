"""
Configuración centralizada del Panel de Ventas Unificado.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SHOPIFY_CONFIG = {
    "shop_name": os.environ.get("SHOPIFY_SHOP_NAME", "tu-tienda.myshopify.com"),
    "access_token": os.environ.get("SHOPIFY_ACCESS_TOKEN", ""),
    "api_version": "2024-01",
}

MERCADO_LIBRE_CONFIG = {
    "client_id": os.environ.get("ML_CLIENT_ID", ""),
    "client_secret": os.environ.get("ML_CLIENT_SECRET", ""),
    "refresh_token": os.environ.get("ML_REFRESH_TOKEN", ""),
    "access_token": os.environ.get("ML_ACCESS_TOKEN", ""),
    "site_id": "MCO",  # Colombia: MCO, Argentina: MLA, México: MLM, Brasil: MLB
}

DATABASE_PATH = DATA_DIR / "ventas.db"

SCHEDULE = {
    "enabled": True,
    "hour": 6,
    "timezone": "America/Bogota",
}

DASHBOARD_CONFIG = {
    "title": "Panel de Ventas Unificado",
    "currency": "COP",
    "date_format": "%d/%m/%Y",
}
