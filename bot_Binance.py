import os
import time
import requests
import hmac
import hashlib
from threading import Thread
from flask import Flask

# ==========================================
# 1. SERVIDOR DE MANTENIMIENTO PARA RENDER
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot de Binance P2P Activo y Monitoreando 24/7"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 2. CONFIGURACIÓN DE APIS (DESDE ENTORNO)
# ==========================================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://api.binance.com"

# ==========================================
# 3. FUNCIONES AUXILIARES
# ==========================================
def enviar_telegram(mensaje):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Error: No se han configurado las credenciales de Telegram en Render.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Error enviando a Telegram: {response.text}")
    except Exception as e:
        print(f"Error de conexión al enviar a Telegram: {e}")

def generar_firma(query_string, secret):
    return hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def obtener_ordenes_activas():
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        print("⚠️ Error: No se han configurado las claves API de Binance en Render.")
        return []

    endpoint = "/sapi/v1/c2c/orderMatch/listUserOrderHistory"
    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}"
    signature = generar_firma(query_string, BINANCE_SECRET_KEY)
    
    headers = {'X-MBX-APIKEY': BINANCE_API_KEY}
    url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Error en API Binance: {response.text}")
            return []
    except Exception as e:
        print(f"Error de conexión con Binance: {e}")
        return []

# ==========================================
# 4. BUCLE DE MONITOREO Y PROCESAMIENTO
# ==========================================
def procesar_orden(order):
    trade_type = order.get('tradeType', '')  # 'BUY' o 'SELL'
    contraparte = order.get('sellerName') if trade_type == 'BUY' else order.get('buyerName')

    # Extraer datos bancarios únicamente si es COMPRA (BUY)
    datos_pago_txt = ""
    if trade_type == 'BUY':
        pay_methods = order.get('payMethods', [])
        if pay_methods:
            datos_pago_txt = "\n🏦 *DATOS BANCARIOS DEL VENDEDOR:*\n"
            for pm in pay_methods:
                nombre_metodo = pm.get('payType', 'N/A')
                campos = pm.get('fields', [])
                
                detalles_pm = []
                for field in campos:
                    fieldName = field.get('fieldName', '')
                    fieldValue = field.get('fieldContent', '')
                    if fieldValue:
                        detalles_pm.append(f"  • *{fieldName}:* `{fieldValue}`")
                
                info_extra = "\n".join(detalles_pm) if detalles_pm else "  • Sin detalles adicionales"
                datos_pago_txt += f"\n💳 *Método:* {nombre_metodo}\n{info_extra}\n"
        else:
            datos_pago_txt = "\n💳 *Método de pago:* No especificado en la orden\n"

    # Formatear el mensaje final para Telegram
    mensaje = (
        f"🚨 *ACTUALIZACIÓN DE ÓRDEN P2P*\n\n"
        f"📌 *Orden:* `{order.get('orderNumber')}`\n"
        f"📊 *Tipo:* {'🟢 COMPRA' if trade_type == 'BUY' else '🔴 VENTA'}\n"
        f"🔄 *Estado:* {order.get('orderStatus')}\n"
        f"💰 *Monto Fiat:* {order.get('totalPrice')} {order.get('fiat')}\n"
        f"🪙 *Cripto:* {order.get('amount')} {order.get('asset')}\n"
        f"👤 *Contraparte:* {contraparte}\n"
        f"{datos_pago_txt}"
    )

    enviar_telegram(mensaje)

def monitorear_binance():
    print("🚀 Iniciando bucle de monitoreo P2P...")
    ordenes_procesadas = set()

    while True:
        try:
            ordenes = obtener_ordenes_activas()
            for order in ordenes:
                order_id = order.get('orderNumber')
                status = order.get('orderStatus')
                clave_orden = f"{order_id}_{status}"

                # Enviar notificación solo si hay un cambio de estado en la orden
                if clave_orden not in ordenes_procesadas:
                    procesar_orden(order)
                    ordenes_procesadas.add(clave_orden)

        except Exception as e:
            print(f"⚠️ Error en la consulta: {e}")

        time.sleep(10)  # Revisa cada 10 segundos

# ==========================================
# 5. PUNTO DE ENTRADA (EJECUCIÓN)
# ==========================================
if __name__ == "__main__":
    # Iniciar servidor web en segundo plano para Render
    Thread(target=run_http, daemon=True).start()
    
    # Iniciar monitoreo continuo
    monitorear_binance()
