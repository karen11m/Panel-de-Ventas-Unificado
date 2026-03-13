# Panel de Ventas Unificado 📊

Dashboard centralizado que unifica datos de **Shopify** y **MercadoLibre**.

## 🚀 Instalación

```bash
# 1. Clonar el proyecto
cd Panel-de-Ventas-Unificado

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 4. Instalar dependencias
pip install -r requirements.txt
```

---

## 🔐 CONFIGURAR CREDENCIALES

### 🛒 SHOPIFY

1. Ve a tu **Shopify Admin**
2. **Settings > Apps and sales channels > Develop apps**
3. Click **"Create an app"** → Nombre: `Panel Ventas`
4. Click **Configure Admin API scopes**
5. Selecciona: `read_orders` y `read_products`
6. Click **Save** → **Install app**
7. **COPIA EL ACCESS TOKEN** (solo se muestra una vez)

### 🛍️ MERCADO LIBRE (Colombia)

1. Ve a https://developers.mercadolibre.com.co
2. Inicia sesión con tu cuenta de MercadoLibre
3. **Mis Apps > + Crear aplicación**
4. Completa:
   - Nombre: `Panel Ventas`
   - URL callback: `http://localhost`
   - Productos: selecciona `orders_v2`
5. Guarda y copia **App ID** (Client ID) y **Client Secret**

#### Obtener Refresh Token

```bash
# 1. Copia tu CLIENT_ID y SECRET en el archivo .env

# 2. Abre esta URL en tu navegador (reemplaza TU_CLIENT_ID):
https://auth.mercadolibre.com.co/authorization?response_type=code&client_id=TU_CLIENT_ID&redirect_uri=http://localhost

# 3. Autoriza y copia el código de la URL (lo que está después de code=)

# 4. Ejecuta:
python get_ml_token.py TU_CODIGO

# 5. Copia el REFRESH_TOKEN resultante al .env
```

---

## ⚙️ Configurar .env

Edita el archivo `.env` con tus credenciales reales:

```env
SHOPIFY_SHOP_NAME=mitienda.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxx

ML_CLIENT_ID=1234567890123456
ML_CLIENT_SECRET=AbCdEfGh...
ML_REFRESH_TOKEN=TG-xxx...
```

---

## ▶️ EJECUTAR

```bash
# Extraer datos (una vez)
python -m etl.process

# Iniciar dashboard
streamlit run dashboard/app.py
```

El dashboard se abre en: http://localhost:8501

---

## ☁️ DEPLOY EN NUBE (Opcional)

### Railway
1. Sube a GitHub
2. Crea proyecto en Railway
3. Agrega variables de entorno (Settings > Variables)
4. Start command: `streamlit run dashboard/app.py --server.port $PORT`

### Render
1. Conecta tu repositorio
2. Build: `pip install -r requirements.txt`
3. Start: `streamlit run dashboard/app.py --server.port $PORT`

---

## 📁 Estructura

```
├── src/config.py           # Configuración
├── extraction/             # Extractores API
│   ├── shopify_extractor.py
│   └── mercadolibre_extractor.py
├── etl/process.py          # ETL + Base de datos
├── dashboard/app.py       # Dashboard Streamlit
├── data/                  # SQLite database
├── .env                   # Tus credenciales
└── requirements.txt
```
