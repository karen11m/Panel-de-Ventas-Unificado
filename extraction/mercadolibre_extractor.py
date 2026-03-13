"""
Extractor de datos de MercadoLibre.
 Requiere: OAuth de MercadoLibre (client_id, client_secret, refresh_token)
 Documentación: https://developers.mercadolibre.com.ar/es_ar/autenticacion-y-autorizacion
"""
import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import MERCADO_LIBRE_CONFIG

ML_API_URL = f"https://api.mercadolibre.com"


def get_access_token():
    """Obtiene token de acceso."""
    import os
    from dotenv import load_dotenv
    from pathlib import Path
    
    BASE_DIR = Path(__file__).parent.parent
    load_dotenv(BASE_DIR / ".env")
    
    access_token_env = os.environ.get("ML_ACCESS_TOKEN", "")
    if access_token_env:
        print("Usando access_token directo del .env")
        return access_token_env
    
    config = MERCADO_LIBRE_CONFIG
    
    if not config.get("refresh_token"):
        print("No hay refresh_token configurado")
        return None
    
    url = f"{ML_API_URL}/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "refresh_token": config["refresh_token"],
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code != 200:
        print(f"Error obteniendo token: {response.status_code} - {response.text}")
        return None
    
    return response.json().get("access_token")


def get_orders(access_token, status=None, limit=100):
    """Obtiene órdenes de MercadoLibre."""
    orders = []
    offset = 0
    
    url = f"{ML_API_URL}/orders/search"
    params = {
        "seller": "me",
        "limit": limit,
        "offset": offset,
    }
    
    if status:
        params["status"] = status
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    while True:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error MercadoLibre: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        results = data.get("results", [])
        orders.extend(results)
        
        if len(results) < limit:
            break
        
        offset += limit
        params["offset"] = offset
    
    return orders


def get_order_detail(access_token, order_id):
    """Obtiene detalles completos de una orden."""
    url = f"{ML_API_URL}/orders/{order_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    return None


def transform_order(order, access_token):
    """Transforma una orden de MercadoLibre al formato unificado."""
    order_id = order.get("id")
    
    # Obtener detalles completos para更多信息
    detail = order
    if order_id:
        full_detail = get_order_detail(access_token, order_id)
        if full_detail:
            detail = full_detail
    
    payments = detail.get("payments", [])
    total_paid = sum(float(p.get("transaction_amount", 0)) for p in payments)
    
    shipping = detail.get("shipping", {})
    shipping_cost = float(shipping.get("shipping_cost", 0) or 0)
    
    buyer = detail.get("buyer", {})
    nickname = buyer.get("nickname", "N/A")
    email = buyer.get("email", "N/A")
    
    line_items = detail.get("order_items", [])
    products = [item.get("item", {}).get("title", "") for item in line_items]
    quantity = sum(item.get("quantity", 1) for item in line_items)
    
    status_mapping = {
        "paid": "paid",
        "pending": "pending",
        "in_process": "in_process",
        "confirmed": "confirmed",
        "shipped": "shipped",
        "delivered": "delivered",
        "cancelled": "cancelled",
    }
    
    return {
        "platform": "MercadoLibre",
        "order_id": order_id,
        "external_order_id": f"ML{order_id}",
        "created_at": detail.get("date_created"),
        "updated_at": detail.get("last_updated"),
        "status": status_mapping.get(detail.get("status"), detail.get("status")),
        "fulfillment_status": shipping.get("status", "N/A"),
        "customer_name": nickname,
        "customer_email": email,
        "total_amount": total_paid,
        "subtotal": total_paid - shipping_cost,
        "shipping_amount": shipping_cost,
        "tax_amount": 0,
        "currency": detail.get("currency_id", "COP"),
        "products": ", ".join(products),
        "items_count": quantity,
        "payment_method": payments[0].get("payment_type", "N/A") if payments else "N/A",
        "shipping_address": f"{detail.get('shipping', {}).get('receiver_address', {}).get('address_line', '')}".strip(),
        "raw_data": str(detail),
    }


def extract_mercadolibre(days_back=30):
    """Extrae todas las órdenes de MercadoLibre de los últimos N días."""
    print(f"Extrayendo datos de MercadoLibre...")
    
    access_token = get_access_token()
    if not access_token:
        print("No se pudo obtener token de acceso")
        return pd.DataFrame()
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Estados a buscar
    statuses = ["paid", "confirmed", "shipped", "delivered"]
    all_orders = []
    
    for status in statuses:
        orders = get_orders(access_token, status=status)
        
        # Filtrar por fecha
        for order in orders:
            order_date = datetime.fromisoformat(order.get("date_created").replace("Z", "+00:00"))
            if order_date >= cutoff_date:
                all_orders.append(order)
    
    print(f"Órdenes encontradas: {len(all_orders)}")
    
    if not all_orders:
        return pd.DataFrame()
    
    df = pd.DataFrame([transform_order(order, access_token) for order in all_orders])
    
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    
    print(f"Datos de MercadoLibre extraídos: {len(df)} órdenes")
    return df


if __name__ == "__main__":
    df = extract_mercadolibre()
    print(df.head())
