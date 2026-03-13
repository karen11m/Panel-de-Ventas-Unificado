"""
Dashboard Streamlit - Panel de Ventas Unificado.
Muestra métricas de Shopify y MercadoLibre en tiempo real.
"""
import sys
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DASHBOARD_CONFIG, DATABASE_PATH
from etl.process import get_unified_data, get_summary_stats, get_daily_sales, get_top_products, run_etl

st.set_page_config(
    page_title=DASHBOARD_CONFIG["title"],
    page_icon="📊",
    layout="wide",
)

CURRENCY_SYMBOL = {"ARS": "$", "MXN": "$", "BRL": "R$", "USD": "US$"}
CURRENCY = DASHBOARD_CONFIG.get("currency", "ARS")
SYMBOL = CURRENCY_SYMBOL.get(CURRENCY, "$")


@st.cache_data(ttl=3600)
def load_data(days):
    """Carga datos con caché de 1 hora."""
    return get_unified_data(days)


@st.cache_data(ttl=3600)
def load_stats(days):
    """Carga estadísticas."""
    return get_summary_stats(days)


@st.cache_data(ttl=3600)
def load_daily_sales(days):
    """Carga ventas diarias."""
    return get_daily_sales(days)


@st.cache_data(ttl=3600)
def load_top_products(days):
    """Carga productos top."""
    return get_top_products(days)


def format_currency(value):
    """Formatea valor monetario."""
    return f"{SYMBOL} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    st.title(f"📊 {DASHBOARD_CONFIG['title']}")
    st.markdown("---")
    
    # Sidebar - Controles
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        days = st.slider("Período (días)", 7, 90, 30)
        
        st.markdown("---")
        
        if st.button("🔄 Actualizar datos", type="primary"):
            with st.spinner("Actualizando datos..."):
                run_etl(days_back=days)
                st.cache_data.clear()
            st.success("¡Datos actualizados!")
        
        st.markdown("---")
        st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Cargar datos
    df = load_data(days)
    stats = load_stats(days)
    daily = load_daily_sales(days)
    products = load_top_products(days)
    
    if df.empty:
        st.warning("⚠️ No hay datos disponibles. Configura las credenciales API y actualiza.")
        
        with st.expander("📋 Instrucciones de configuración"):
            st.markdown("""
            ### Configuración requerida
            
            1. **Shopify**: Obtén tu Access Token en Shopify Admin > Settings > Apps and sales channels > Develop apps
            2. **MercadoLibre**: Crea una app en https://developers.mercadolibre.com.ar
            
            Luego configura las variables de entorno:
            """)
            st.code("""
export SHOPIFY_ACCESS_TOKEN="tu_token_shopify"
export ML_CLIENT_ID="tu_client_id"
export ML_CLIENT_SECRET="tu_client_secret"  
export ML_REFRESH_TOKEN="tu_refresh_token"
            """, bash)
        return
    
    # Métricas principales
    total_orders = len(df)
    total_revenue = df["total_amount"].sum()
    avg_order = df["total_amount"].mean()
    total_items = df["items_count"].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Pedidos Totales", f"{total_orders:,}")
    with col2:
        st.metric("Ingresos Totales", format_currency(total_revenue))
    with col3:
        st.metric("Ticket Promedio", format_currency(avg_order))
    with col4:
        st.metric("Productos Vendidos", f"{total_items:,}")
    
    st.markdown("---")
    
    # Gráficos
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Ingresos por Plataforma")
        
        if not stats.empty:
            fig_data = pd.DataFrame({
                "Plataforma": stats["platform"],
                "Ingresos": stats["total_revenue"],
            })
            st.bar_chart(fig_data.set_index("Plataforma"), horizontal=True)
    
    with col_right:
        st.subheader("🛒 Pedidos por Plataforma")
        
        if not stats.empty:
            fig_orders = pd.DataFrame({
                "Plataforma": stats["platform"],
                "Pedidos": stats["total_orders"],
            })
            st.bar_chart(fig_orders.set_index("Plataforma"), horizontal=True)
    
    st.markdown("---")
    
    # Ventas diarias
    st.subheader("📅 Ventas Diarias")
    
    if not daily.empty:
        pivot_daily = daily.pivot(index="date", columns="platform", values="revenue").fillna(0)
        st.line_chart(pivot_daily)
    
    st.markdown("---")
    
    # Productos más vendidos
    col_products, col_table = st.columns([1, 1])
    
    with col_products:
        st.subheader("🏆 Top Productos")
        
        if not products.empty:
            products_display = products.copy()
            products_display["revenue"] = products_display["revenue"].apply(format_currency)
            st.dataframe(
                products_display[["products", "quantity_sold", "revenue"]].head(5),
                hide_index=True,
                use_container_width=True,
            )
    
    with col_table:
        st.subheader("📋 Últimos Pedidos")
        
        recent = df[["external_order_id", "platform", "date", "total_amount", "status"]].head(10)
        recent["total_amount"] = recent["total_amount"].apply(format_currency)
        recent["date"] = pd.to_datetime(recent["date"]).dt.strftime("%d/%m/%Y")
        st.dataframe(recent, hide_index=True, use_container_width=True)
    
    # Detalle por plataforma
    st.markdown("---")
    st.subheader("📊 Detalle por Plataforma")
    
    tab1, tab2 = st.tabs(["📦 Shopify", "🛍️ MercadoLibre"])
    
    with tab1:
        shopify_df = df[df["platform"] == "Shopify"]
        if not shopify_df.empty:
            st.write(f"**Pedidos:** {len(shopify_df)} | **Ingresos:** {format_currency(shopify_df['total_amount'].sum())}")
            st.dataframe(
                shopify_df[["external_order_id", "date", "customer_name", "total_amount", "status"]].head(10),
                hide_index=True,
            )
        else:
            st.info("No hay pedidos de Shopify")
    
    with tab2:
        ml_df = df[df["platform"] == "MercadoLibre"]
        if not ml_df.empty:
            st.write(f"**Pedidos:** {len(ml_df)} | **Ingresos:** {format_currency(ml_df['total_amount'].sum())}")
            st.dataframe(
                ml_df[["external_order_id", "date", "customer_name", "total_amount", "status"]].head(10),
                hide_index=True,
            )
        else:
            st.info("No hay pedidos de MercadoLibre")


if __name__ == "__main__":
    main()
