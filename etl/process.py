"""
ETL (Extract, Transform, Load) - Proceso unificado de datos.
Combina datos de Shopify y MercadoLibre en una base de datos SQLite.
"""
import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DATABASE_PATH
from extraction.shopify_extractor import extract_shopify
from extraction.mercadolibre_extractor import extract_mercadolibre


def init_database():
    """Inicializa la base de datos SQLite con el schema necesario."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            order_id INTEGER,
            external_order_id TEXT UNIQUE,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            status TEXT,
            fulfillment_status TEXT,
            customer_name TEXT,
            customer_email TEXT,
            total_amount REAL,
            subtotal REAL,
            shipping_amount REAL,
            tax_amount REAL,
            currency TEXT,
            products TEXT,
            items_count INTEGER,
            payment_method TEXT,
            shipping_address TEXT,
            date DATE,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_platform ON orders(platform)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_date ON orders(date)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at ON orders(created_at)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"Base de datos inicializada: {DATABASE_PATH}")


def load_to_database(df):
    """Carga DataFrame a SQLite, evitando duplicados."""
    if df.empty:
        print("DataFrame vacío, nada que cargar.")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    # Insertar ignorando duplicados
    df.to_sql("orders", conn, if_exists="append", index=False)
    
    # Eliminar duplicados (mantener el más reciente)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM orders
        WHERE rowid NOT IN (
            SELECT MAX(rowid)
            FROM orders
            GROUP BY external_order_id
        )
    """)
    
    conn.commit()
    inserted = cursor.rowcount
    conn.close()
    
    print(f"Datos cargados: {inserted} nuevas órdenes")


def get_unified_data(days=30):
    """Obtiene datos unificados de los últimos N días."""
    conn = sqlite3.connect(DATABASE_PATH)
    
    query = f"""
        SELECT * FROM orders
        WHERE created_at >= datetime('now', '-{days} days')
        ORDER BY created_at DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["date"] = pd.to_datetime(df["date"]).dt.date
    
    return df


def get_summary_stats(days=30):
    """Obtiene estadísticas resumidas."""
    conn = sqlite3.connect(DATABASE_PATH)
    
    query = f"""
        SELECT 
            platform,
            COUNT(*) as total_orders,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value,
            SUM(items_count) as total_items
        FROM orders
        WHERE created_at >= datetime('now', '-{days} days')
        GROUP BY platform
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def get_daily_sales(days=30):
    """Obtiene ventas diarias por plataforma."""
    conn = sqlite3.connect(DATABASE_PATH)
    
    query = f"""
        SELECT 
            date(created_at) as date,
            platform,
            COUNT(*) as orders,
            SUM(total_amount) as revenue
        FROM orders
        WHERE created_at >= datetime('now', '-{days} days')
        GROUP BY date(created_at), platform
        ORDER BY date
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    
    return df


def get_top_products(days=30, limit=10):
    """Obtiene productos más vendidos."""
    conn = sqlite3.connect(DATABASE_PATH)
    
    query = f"""
        SELECT 
            products,
            SUM(items_count) as quantity_sold,
            SUM(total_amount) as revenue,
            COUNT(*) as times_ordered
        FROM orders
        WHERE created_at >= datetime('now', '-{days} days')
        GROUP BY products
        ORDER BY quantity_sold DESC
        LIMIT {limit}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def run_etl(days_back=30):
    """Ejecuta el proceso ETL completo."""
    print("=" * 50)
    print("INICIANDO PROCESO ETL")
    print("=" * 50)
    
    init_database()
    
    print("\n[1/2] Extrayendo datos de Shopify...")
    df_shopify = extract_shopify(days_back)
    
    print("\n[2/2] Extrayendo datos de MercadoLibre...")
    df_ml = extract_mercadolibre(days_back)
    
    if not df_shopify.empty:
        load_to_database(df_shopify)
    
    if not df_ml.empty:
        load_to_database(df_ml)
    
    print("\n" + "=" * 50)
    print("PROCESO ETL COMPLETADO")
    print("=" * 50)
    
    return get_unified_data(days_back)


if __name__ == "__main__":
    run_etl()
