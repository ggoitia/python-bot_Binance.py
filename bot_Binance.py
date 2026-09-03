import os
from threading import Thread
from flask import Flask

# Servidor de mantenimiento para Render (Mantiene el servicio Free activo)
app = Flask('')

@app.route('/')
def home():
    return "Bot de Binance P2P Activo y Monitoreando 24/7"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Iniciar servidor web en segundo plano
Thread(target=run_http).start()

# Determinar el tipo de operación (BUY / SELL)
trade_type = order.get('tradeType', '')  # 'BUY' o 'SELL'

# Mapeo de la orden
trade_type = order.get('tradeType', '')  # Retorna 'BUY' o 'SELL'

# EXTRAER DATOS BANCARIOS ÚNICAMENTE SI ES UNA COMPRA (BUY)
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

# MENSAJE FINAL PARA TELEGRAM
mensaje = (
    f"🚨 *NUEVA ÓRDEN P2P DETECTADA*\n\n"
    f"📌 *Orden:* `{order.get('orderNumber')}`\n"
    f"📊 *Tipo:* {'🟢 COMPRA (BUY)' if trade_type == 'BUY' else '🔴 VENTA (SELL)'}\n"
    f"🔄 *Estado:* {order.get('orderStatus')}\n"
    f"💰 *Monto Fiat:* {order.get('totalPrice')} {order.get('fiat')}\n"
    f"🪙 *Cripto:* {order.get('amount')} {order.get('asset')}\n"
    f"👤 *Contraparte:* {order.get('sellerName') if trade_type == 'BUY' else order.get('buyerName')}\n"
    f"{datos_pago_txt}"
)

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
