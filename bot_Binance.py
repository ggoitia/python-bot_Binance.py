import hashlib
import hmac
import time
import requests

# ==========================================
# CONFIGURACIÓN INTEGRADA CON TUS CREDENCIALES
# ==========================================
BINANCE_API_KEY = "JuQ0FkRoKxUhEnB6fUOer6HlPeLQ9GjIodyXtPGQNOCGyqR0ipIfjN8tcKZBMbzs"
BINANCE_SECRET_KEY = "9Zfs0bZ3dKtGRG3RfK2nFlreUliQTNPCLNvQnPGCc1eViGPiP4GIIT2jkfoXBOzL"

TELEGRAM_BOT_TOKEN = "8659443549:AAEiAmQYSqNtO_8iF82QdooleY-m9iLJzdQ"
TELEGRAM_CHAT_ID = "956927958"

BASE_URL = "https://api.binance.com"


def send_telegram_alert(message: str):
    """Envía una notificación al chat de Telegram especificado."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        res_data = response.json()
        if not res_data.get("ok"):
            print(f"[Error Telegram]: {res_data.get('description')}")
        else:
            print("[Notificación enviada a Telegram con éxito]")
    except Exception as e:
        print(f"[Error de conexión con Telegram]: {e}")


def get_p2p_order_history(trade_type: str = "BUY", page: int = 1, rows: int = 10):
    """
    Consulta las órdenes P2P usando tus claves API de Binance.
    trade_type: 'BUY' o 'SELL'
    """
    endpoint = "/sapi/v1/c2c/orderMatch/listUserOrderHistory"
    timestamp = int(time.time() * 1000)

    params = {
        "tradeType": trade_type,
        "page": page,
        "rows": rows,
        "timestamp": timestamp
    }

    # Generación de firma HMAC SHA256
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(
        BINANCE_SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    params["signature"] = signature

    try:
        response = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        data = response.json()
        
        if data.get("code") == "000000":
            return data.get("data", [])
        else:
            print(f"[Error Binance API]: {data.get('message')} (Código: {data.get('code')})")
            return []
    except Exception as e:
        print(f"[Error de conexión con Binance]: {e}")
        return []


def monitor_p2p_orders():
    """Bucle principal para monitorear órdenes P2P cada 15 segundos."""
    print("🚀 Bot iniciado correctamente...")
    print("🛰️ Monitoreando órdenes P2P activas y completadas...")
    
    send_telegram_alert("🤖 *Bot Binance P2P Actualizado*\nAhora notifica aperturas, pagos recibidos y órdenes finalizadas.")
    
    # Diccionario para rastrear el último estado conocido de cada orden
    tracked_orders = {}

    while True:
        try:
            for t_type in ["BUY", "SELL"]:
                orders = get_p2p_order_history(trade_type=t_type)

                for order in orders:
                    order_number = order.get("orderNumber")
                    status = str(order.get("orderStatus"))

                    last_status = tracked_orders.get(order_number)

                    # Si el estado de la orden cambió con respecto a la última consulta
                    if status != last_status:
                        tracked_orders[order_number] = status

                        amount = order.get("amount")
                        total_price = order.get("totalPrice")
                        fiat = order.get("fiat")
                        asset = order.get("asset")
                        counterparty = order.get("counterpartNickName")

                        # Definir mensaje según el código de estado de Binance
                        if status in ["1", "TRADING"]:
                            status_msg = "🟢 *NUEVA ÓRDEN ABIERTA* (Esperando Pago)"
                        elif status in ["2", "IN_PAYMENT"]:
                            status_msg = "🟡 *PAGO NOTIFICADO* (Verificar cuenta y liberar)"
                        elif status in ["3", "COMPLETED"]:
                            status_msg = "✅ *ÓRDEN COMPLETADA / LIBERADA*"
                        elif status in ["4", "CANCELLED"]:
                            status_msg = "❌ *ÓRDEN CANCELADA*"
                        else:
                            status_msg = f"ℹ️ *CAMBIO DE ESTADO:* {status}"

                        # Solo notificar si la orden es reciente y no está en un estado ignorado inicial
                        if last_status is not None or status in ["1", "2", "TRADING", "IN_PAYMENT"]:
                            msg = (
                                f"{status_msg} ({t_type})\n"
                                f"----------------------------------------\n"
                                f"📌 *ID Órden:* `{order_number}`\n"
                                f"👤 *Cliente:* {counterparty}\n"
                                f"💵 *Monto Fiat:* {total_price} {fiat}\n"
                                f"🪙 *Cripto:* {amount} {asset}"
                            )

                            send_telegram_alert(msg)

        except Exception as e:
            print(f"[Error en bucle de monitoreo]: {e}")

        time.sleep(15)


if __name__ == "__main__":
    monitor_p2p_orders()
