from machine import Pin
import network
import camera
import urequests
import time

# Configuración Wi-Fi
SSID = 'REDPRUEBA'  # Cambiar por nombre de la red
PASSWORD = 'Mamarre1'  # Cambiar por contraseña de red

# Configuración de Firebase
FIREBASE_URL = "https://esp32-3beea-default-rtdb.firebaseio.com/"
NODE_NAME = "pir_status.json"

# Configuración de Telegram
BOT_TOKEN = "7875017203:AAEiuwC5SozcAmBWsnNaVsh_icyeD4dyrAw"
CHAT_ID = "6889877465"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

# Configuración del sensor PIR
PIR_PIN = 13  # Cambiar al pin donde conectaste el PIR
pir = Pin(PIR_PIN, Pin.IN)

# Conexión Wi-Fi
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Conectando a Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(1)
    print("Conexión Wi-Fi establecida:", wlan.ifconfig())

# Inicializar la cámara
def inicializar_camara():
    camera.init(0, format=camera.JPEG)
    print("Cámara inicializada.")

# Tomar una foto con la cámara
def tomar_foto():
    print("Tomando foto...")
    camera.framesize(camera.FRAME_QVGA)  # Ajuste de resolución
    foto = camera.capture()
    with open('imagen.jpg', 'wb') as f:
        f.write(foto)
    print("Foto tomada.")
    return 'imagen.jpg'

# Enviar estado a Firebase
def enviar_estado_firebase(movimiento):
    try:
        url = FIREBASE_URL + NODE_NAME
        headers = {"Content-Type": "application/json"}
        data = {"movimiento": movimiento, "timestamp": time.time()}
        response = urequests.put(url, headers=headers, json=data)
        print("Estado enviado a Firebase:", response.text)
        response.close()
    except Exception as e:
        print("Error al enviar estado a Firebase:", e)

# Enviar foto a Telegram
def enviar_foto_telegram():
    with open('imagen.jpg', 'rb') as img_file:
        foto = img_file.read()

    # Crear el cuerpo de la solicitud multipart/form-data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    cuerpo = (
        "--" + boundary + "\r\n" +
        "Content-Disposition: form-data; name=\"chat_id\"\r\n\r\n" +
        CHAT_ID + "\r\n" +
        "--" + boundary + "\r\n" +
        "Content-Disposition: form-data; name=\"photo\"; filename=\"imagen.jpg\"\r\n" +
        "Content-Type: image/jpeg\r\n\r\n"
    ).encode('utf-8') + foto + "\r\n--" + boundary + "--\r\n".encode('utf-8')

    headers = {
        "Content-Type": "multipart/form-data; boundary=" + boundary
    }

    try:
        response = urequests.post(TELEGRAM_URL, data=cuerpo, headers=headers)
        if response.status_code == 200:
            print("Foto enviada a Telegram con éxito.")
        else:
            print("Error al enviar la foto:", response.text)
    except Exception as e:
        print("Error al intentar enviar la foto:", e)

# Script principal
def main():
    conectar_wifi()
    inicializar_camara()
    print("Sistema iniciado. Detectando movimiento...")

    while True:
        if pir.value() == 1:  # Detecta movimiento
            print("¡Movimiento detectado!")
            enviar_estado_firebase("Detectado")
            foto_path = tomar_foto()
            enviar_foto_telegram()
        else:
            print("Sin movimiento.")
            enviar_estado_firebase("Sin movimiento")
        time.sleep(1)  # Espera 1 segundo entre lecturas

# Iniciar el programa
main()
