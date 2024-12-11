import network
from machine import Pin, PWM
import socket
import time
import dht11

# Configuración de red WiFi
ssid = "REDPRUEBA"  # Cambia a tu SSID
password = "Mamarre1"  # Cambia a tu contraseña

# Configuración de los pines del motor
in1 = Pin(12, Pin.OUT)
in2 = Pin(14, Pin.OUT)
in3 = Pin(26, Pin.OUT)
in4 = Pin(27, Pin.OUT)
in5 = Pin(33, Pin.OUT)
in6 = Pin(15, Pin.OUT)
in7 = Pin(18, Pin.OUT)
in8 = Pin(19, Pin.OUT)

en_a = PWM(Pin(25), freq=500)
en_a2 = PWM(Pin(21), freq=500)
en_b = PWM(Pin(22), freq=500)
en_b2 = PWM(Pin(23), freq=500)

en_a.duty(1023)  # Ciclo de trabajo máximo (motor habilitado)
en_a2.duty(1023)
en_b.duty(1023)
en_b2.duty(1023)

# Configuración del sensor DHT11 y el LED RGB
dht_sensor = dht.DHT11(Pin(4))  # DHT11 conectado al pin GPIO4
led_r = PWM(Pin(32), freq=500)
led_g = PWM(Pin(5), freq=500)
led_b = PWM(Pin(16), freq=500)

led_r.duty(0)  # Apagar LEDs inicialmente
led_g.duty(0)
led_b.duty(0)

# Configuración inicial
def stop_motors():
    in1.off()
    in2.off()
    in3.off()
    in4.off()
    in5.off()
    in6.off()
    in7.off()
    in8.off()

stop_motors()

# Conexión WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print("Conectando a la red WiFi...")
    while not wlan.isconnected():
        time.sleep(1)

    print("Conexión exitosa")
    print("Dirección IP:", wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

ip = connect_wifi()

# Servidor HTTP
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("Servidor corriendo en:", addr)

    while True:
        cl, addr = s.accept()
        print("Cliente conectado desde:", addr)
        request = cl.recv(1024).decode('utf-8')
        print("Solicitud HTTP:", request)

        # Procesar comandos de la App Inventor
        if '/btnForward' in request:
            # Todos los motores hacia adelante
            in1.on()
            in2.off()
            in3.on()
            in4.off()
            in5.on()
            in6.off()
            in7.on()
            in8.off()
        elif '/btnBack' in request:
            # Atrás
            in1.off()
            in2.on()
            in3.off()
            in4.on()
            in5.off()
            in6.on()
            in7.off()
            in8.on()
        elif '/btnLeft' in request:
            # Izquierda
            in1.on()
            in2.off()
            in3.on()
            in4.off()
            in5.off()
            in6.on()
            in7.on()
            in8.off()
        elif '/btnRight' in request:
            # Derecha
            in1.off()
            in2.on()
            in3.off()
            in4.off()
            in5.on()
            in6.off()
            in7.off()
            in8.off()
        elif '/btnStop' in request:
            # Detener
            stop_motors()
        elif '/readDHT' in request:
            # Leer el sensor DHT11
            try:
                dht_sensor.measure()
                temp = dht_sensor.temperature()
                hum = dht_sensor.humidity()
                response = f"HTTP/1.1 200 OK\n\nTemperatura: {temp} C\nHumedad: {hum}%"
            except Exception as e:
                response = f"HTTP/1.1 500 Internal Server Error\n\nError al leer el sensor: {e}"
            cl.send(response)
            cl.close()
            continue
        elif '/setLED?' in request:
            # Controlar el LED RGB
            try:
                r = int(request.split('r=')[1].split('&')[0])
                g = int(request.split('g=')[1].split('&')[0])
                b = int(request.split('b=')[1].split(' ')[0])

                led_r.duty(r)
                led_g.duty(g)
                led_b.duty(b)
                response = "HTTP/1.1 200 OK\n\nLED configurado"
            except Exception as e:
                response = f"HTTP/1.1 400 Bad Request\n\nError al configurar el LED: {e}"
            cl.send(response)
            cl.close()
            continue

        # Responder a la solicitud HTTP
        response = "HTTP/1.1 200 OK\n\nControl recibido"
        cl.send(response)
        cl.close()

start_server()