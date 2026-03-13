"""
Extractor de datos de Shopify.
 Requiere: Shopify Admin API Access Token
 Documentación: https://shopify.dev/docs/admin-api
"""
import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import SHOPIFY_CONFIG, DATABASE_PATH

SHOPIFY_API_URL = f"https://{SHOPIFY_CONFIG['shop_name']}/admin/api/{SHOPIFY_CONFIG['api_version']}"

HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_CONFIG["access_token"],
    "Content-Type": "application/json",
}


def get_orders(status="any", limit=250, created_at_min=None):
    """Obtiene órdenes de Shopify con paginación."""
    orders = []
    url = f"{SHOPIFY_API_URL}/orders.json?status={status}&limit={limit}"
    
    if created_at_min:
        url += f"&created_at_min={created_at_min}"
    
    while url:
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Error Shopify: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        orders.extend(data.get("orders", []))
        
        # Paginación
        link_header = response.headers.get("Link", "")
        url = None
        if "next" in link_header:
            for part in link_header.split(","):
                if "rel=\"next\"" in part:
                    url = part.split(";")[0].strip("<> ")
                    break
    
    return orders


def transform_order(order):
    """Transforma una orden de Shopify al formato unificado."""
    total_price = float(order.get("total_price", 0))
    subtotal = float(order.get("subtotal_price", 0))
    shipping = float(order.get("total_shipping_price_set", {}).get("shop_money", {}).get("amount", 0))
    tax = float(order.get("total_tax", 0))
    
    line_items = order.get("line_items", [])
    products = [item.get("name") for item in line_items]
    quantity = sum(item.get("quantity", 0) for item in line_items)
    
    return {
        "platform": "Shopify",
        "order_id": order.get("id"),
        "external_order_id": order.get("name"),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at"),
        "status": order.get("financial_status"),
        "fulfillment_status": order.get("fulfillment_status"),
        "customer_name": f"{order.get('customer', {}).get('first_name', '')} {order.get('customer', {}).get('last_name', '')}".strip(),
        "customer_email": order.get("customer", {}).get("email"),
        "total_amount": total_price,
        "subtotal": subtotal,
        "shipping_amount": shipping,
        "tax_amount": tax,
        "currency": order.get("currency"),
        "products": ", ".join(products),
        "items_count": quantity,
        "payment_method": order.get("gateway", "N/A"),
        "shipping_address": f"{order.get('shipping_address', {}).get('address1', '')} {order.get('shipping_address', {}).get('city', '')}".strip(),
        "raw_data": str(order),
    }


def extract_shopify(days_back=30):
    """Extrae todas las órdenes de Shopify de los últimos N días."""
    print(f"Extrayendo datos de Shopify...")
    
    created_at_min = (datetime.now() - timedelta(days=days_back)).isoformat()
    orders = get_orders(created_at_min=created_at_min)
    
    print(f"Órdenes encontradas: {len(orders)}")
    
    if not orders:
        return pd.DataFrame()
    
    df = pd.DataFrame([transform_order(order) for order in orders])
    
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    
    print(f"Datos de Shopify extraídos: {len(df)} órdenes")
    return df


if __name__ == "__main__":
    df = extract_shopify()
    print(df.head())
