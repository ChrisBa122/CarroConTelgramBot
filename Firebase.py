import network
import time
from machine import Pin
import urequests
import ujson

# Configuración Wi-Fi
SSID = 'crisWifi'  # Cambiar por nombre de red
PASSWORD = '123456789'  # Cambiar por contraseña de red

# Configuración Firebase
FIREBASE_PROJECT = "carrito-sensores"
FIREBASE_URL = f"https://{FIREBASE_PROJECT}.firebaseio.com/sensor_pir"
FIREBASE_NODE = ".json"  # Nodo raíz en Firebase

# Configuración del sensor PIR
PIR_PIN = 13  # Pin donde está conectado el sensor PIR
pir = Pin(PIR_PIN, Pin.IN)

# Función para conectar a Wi-Fi
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print("Conectando a Wi-Fi...")
    intentos = 0
    while not wlan.isconnected():
        time.sleep(1)
        intentos += 1
        if intentos > 10:
            print("No se pudo conectar a Wi-Fi")
            machine.reset()  # Reinicia el dispositivo si no logra conectarse
    
    print("Conexión Wi-Fi establecida:", wlan.ifconfig())

# Función para enviar datos a Firebase
def enviar_datos_firebase(datos):
    try:
        # Preparar solicitud PUT a Firebase
        headers = {'Content-Type': 'application/json'}
        url = f"{FIREBASE_URL}{FIREBASE_NODE}"
        
        # Convertir datos a JSON
        payload = ujson.dumps(datos)
        
        # Enviar solicitud
        respuesta = urequests.put(url, headers=headers, data=payload)
        
        print("Datos enviados correctamente")
        respuesta.close()
    except Exception as e:
        print(f"Error al enviar datos: {e}")

# Función principal
def main():
    # Conectar a Wi-Fi
    conectar_wifi()
    
    print("Iniciando monitoreo de sensor PIR...")
    
    while True:
        # Leer estado del sensor PIR
        movimiento = pir.value()
        
        # Preparar datos para enviar
        datos = {
            "estado": "Detectado" if movimiento else "Sin movimiento",
            "timestamp": time.time()
        }
        
        # Enviar datos a Firebase
        enviar_datos_firebase(datos)
        
        # Mostrar estado por consola
        print(f"Estado: {datos['estado']}")
        
        # Esperar antes de la próxima lectura
        time.sleep(1)

# Ejecutar el programa principal
if __name__ == '__main__':
    main()
