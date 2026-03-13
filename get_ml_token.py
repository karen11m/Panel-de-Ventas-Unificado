"""
Script para obtener refresh_token de MercadoLibre.

PASOS:
1. Ejecuta este script con tu CODE de autorización
2. Copia el REFRESH_TOKEN que aparece
3. Agrégalo a tu archivo .env

Uso: python get_ml_token.py TU_CODIGO
"""
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path
import os

# Cargar credenciales
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

CLIENT_ID = os.environ.get("ML_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ML_CLIENT_SECRET", "")

if len(sys.argv) < 2:
    print("❌ Error: Falta el código de autorización")
    print("\nPASO 1: Ve a esta URL (reemplaza TU_CLIENT_ID):")
    print(f"https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri=http://localhost")
    print("\nPASO 2: Copia el código de la URL resultante")
    print("\nPASO 3: Ejecuta:")
    print(f"python get_ml_token.py TU_CODIGO")
    sys.exit(1)

CODE = sys.argv[1]

url = "https://api.mercadolibre.com/oauth/token"
data = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": CODE,
    "redirect_uri": "https://mlpanel2.loca.lt",
}

print("Obteniendo tokens...")
response = requests.post(url, data=data)
result = response.json()

if "refresh_token" in result:
    print("="*50)
    print("SUCCESS! Copia este REFRESH_TOKEN:")
    print("="*50)
    print(result.get('refresh_token'))
    print("="*50)
else:
    print("ERROR:", result)
