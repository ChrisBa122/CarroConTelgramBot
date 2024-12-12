import network
from machine import Pin, PWM, ADC
import socket
import time
import utime
from machine import time_pulse_us
import _thread

# Configuración de red WiFi
ssid = "crisWifi"  # Cambia a tu SSID
password = "123456789"  # Cambia a tu contraseña

# Configuración de pines del motor
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

# Configuración de sensor de proximidad
trigger = Pin(13, Pin.OUT)
echo = Pin(32, Pin.IN)
led_proximidad = Pin(4, Pin.OUT)
buzzer_proximidad = Pin(5, Pin.OUT)

# Configuración del sensor PIR
pir = Pin(2, Pin.IN)  # GPIO 2 como entrada para el PIR
buzzer_pir = PWM(Pin(0))  # Cambia el pin según tu configuración
buzzer_pir.freq(1000)     # Frecuencia de 1 kHz para el sonido del zumbador

# Configuración del sensor LDR
ldr = ADC(Pin(34))  # Pin analógico para el LDR
ldr.atten(ADC.ATTN_11DB)  # Configurar atenuación para rango máximo
# Eliminamos la línea problemática de width()

# Variables globales para control de sensores
proximidad_detectada = False
movimiento_detectado = False
luz_detectada = False

# Función para hacer sonar el zumbador LDR
def beep_ldr(times, duration, pause):
    buzzer_ldr = Pin(21, Pin.OUT)  # Zumbador para señales de luz
    for _ in range(times):
        buzzer_ldr.on()  # Enciende el zumbador
        time.sleep(duration)
        buzzer_ldr.off()  # Apaga el zumbador
        time.sleep(pause)

# Función para medir la distancia
def medir_distancia():
    trigger.off()
    utime.sleep_us(2)
    trigger.on()
    utime.sleep_us(10)
    trigger.off()
    
    duracion = time_pulse_us(echo, 1, 30000)  # Timeout de 30 ms
    distancia = (duracion / 2) / 29.1
    return distancia

# Función para monitoreo de proximidad en un hilo separado
def monitoreo_proximidad():
    global proximidad_detectada
    while True:
        distancia = medir_distancia()
        print(f"Distancia: {distancia:.2f} cm")
        
        if distancia < 30:  # Menor a 30 cm
            proximidad_detectada = True
            led_proximidad.on()
            buzzer_proximidad.on()
        else:
            proximidad_detectada = False
            led_proximidad.off()
            buzzer_proximidad.off()
        
        utime.sleep(0.5)  # Chequeo cada 0.5 segundos

# Función para monitoreo de sensor PIR en un hilo separado
def monitoreo_pir():
    global movimiento_detectado
    while True:
        if pir.value() == 1:  # Detecta movimiento
            movimiento_detectado = True
            print("Movimiento detectado")
            buzzer_pir.duty(512)  # Activa el zumbador con 50% de duty cycle
            time.sleep(3)          # Pitido continuo durante 3 segundos
            buzzer_pir.duty(0)    # Apaga el zumbador
            print("Esperando 2 segundos...")
            time.sleep(2)          # Espera 2 segundos antes de la siguiente lectura
        else:
            movimiento_detectado = False
            buzzer_pir.duty(0)    # Asegúrate de que el zumbador esté apagado
        
        utime.sleep(0.5)  # Chequeo cada 0.5 segundos

# Función para monitoreo de sensor LDR en un hilo separado
def monitoreo_ldr():
    global luz_detectada
    while True:
        lux_value = ldr.read()  # Lee el valor de luz
        print("Nivel de luz:", lux_value)
        
        if lux_value < 1500:  # Luz baja (ajusta el valor según tu sensor)
            luz_detectada = True
            print("Luz baja detectada")
            beep_ldr(2, 1, 0.5)  # Dos pitidos sostenidos de 1 segundo
        elif lux_value > 2500:  # Luz alta (ajusta el valor según tu sensor)
            luz_detectada = True
            print("Luz alta detectada")
            beep_ldr(3, 0.2, 0.2)  # Tres pitidos rápidos
        else:
            luz_detectada = False
            # No es necesario apagar el zumbador aquí, ya lo hace beep_ldr
        
        time.sleep(3)  # Pausa antes de la siguiente lectura

# Función para detener motores
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

# Iniciar hilos de monitoreo de sensores
_thread.start_new_thread(monitoreo_proximidad, ())
_thread.start_new_thread(monitoreo_pir, ())
_thread.start_new_thread(monitoreo_ldr, ())

# Servidor HTTP con control de proximidad, movimiento y luz
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
        
        # Verificar condiciones de los sensores
        if proximidad_detectada or movimiento_detectado or luz_detectada:
            stop_motors()  # Detener motores si hay un obstáculo, movimiento o condición de luz
            response = "HTTP/1.1 200 OK\n\nSensor detectado. Movimiento detenido."
        else:
            # Procesamiento de comandos de movimiento
            if '/btnForward' in request:
                # Adelante
                in1.on(); in2.off()
                in3.on(); in4.off()
                in5.on(); in6.off()
                in7.on(); in8.off()
            elif '/btnBack' in request:
                # Atrás
                in1.off(); in2.on()
                in3.off(); in4.on()
                in5.off(); in6.on()
                in7.off(); in8.on()
            elif '/btnLeft' in request:
                # Izquierda
                in1.off(); in2.on()
                in3.on(); in4.off()
                in5.off(); in6.on()
                in7.on(); in8.off()
            elif '/btnRight' in request:
                # Derecha
                in1.on(); in2.off()
                in3.off(); in4.on()
                in5.on(); in6.off()
                in7.off(); in8.on()
            elif '/btnStop' in request:
                # Detener
                stop_motors()
            
            response = "HTTP/1.1 200 OK\n\nControl recibido"
        
        cl.send(response)
        cl.close()

start_server()
import network
from machine import Pin, PWM, ADC
import socket
import time
import utime
from machine import time_pulse_us
import _thread

# Configuración de red WiFi
ssid = "crisWifi"  # Cambia a tu SSID
password = "123456789"  # Cambia a tu contraseña

# Configuración de pines del motor
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

# Configuración de sensor de proximidad
trigger = Pin(13, Pin.OUT)
echo = Pin(32, Pin.IN)
led_proximidad = Pin(4, Pin.OUT)
buzzer_proximidad = Pin(5, Pin.OUT)

# Configuración del sensor PIR
pir = Pin(2, Pin.IN)  # GPIO 2 como entrada para el PIR
buzzer_pir = PWM(Pin(0))  # Cambia el pin según tu configuración
buzzer_pir.freq(1000)     # Frecuencia de 1 kHz para el sonido del zumbador

# Configuración del sensor LDR
ldr = ADC(Pin(34))  # Pin analógico para el LDR
ldr.atten(ADC.ATTN_11DB)  # Configurar atenuación para rango máximo
# Eliminamos la línea problemática de width()

# Variables globales para control de sensores
proximidad_detectada = False
movimiento_detectado = False
luz_detectada = False

# Función para hacer sonar el zumbador LDR
def beep_ldr(times, duration, pause):
    buzzer_ldr = Pin(21, Pin.OUT)  # Zumbador para señales de luz
    for _ in range(times):
        buzzer_ldr.on()  # Enciende el zumbador
        time.sleep(duration)
        buzzer_ldr.off()  # Apaga el zumbador
        time.sleep(pause)

# Función para medir la distancia
def medir_distancia():
    trigger.off()
    utime.sleep_us(2)
    trigger.on()
    utime.sleep_us(10)
    trigger.off()
    
    duracion = time_pulse_us(echo, 1, 30000)  # Timeout de 30 ms
    distancia = (duracion / 2) / 29.1
    return distancia

# Función para monitoreo de proximidad en un hilo separado
def monitoreo_proximidad():
    global proximidad_detectada
    while True:
        distancia = medir_distancia()
        print(f"Distancia: {distancia:.2f} cm")
        
        if distancia < 30:  # Menor a 30 cm
            proximidad_detectada = True
            led_proximidad.on()
            buzzer_proximidad.on()
        else:
            proximidad_detectada = False
            led_proximidad.off()
            buzzer_proximidad.off()
        
        utime.sleep(0.5)  # Chequeo cada 0.5 segundos

# Función para monitoreo de sensor PIR en un hilo separado
def monitoreo_pir():
    global movimiento_detectado
    while True:
        if pir.value() == 1:  # Detecta movimiento
            movimiento_detectado = True
            print("Movimiento detectado")
            buzzer_pir.duty(512)  # Activa el zumbador con 50% de duty cycle
            time.sleep(3)          # Pitido continuo durante 3 segundos
            buzzer_pir.duty(0)    # Apaga el zumbador
            print("Esperando 2 segundos...")
            time.sleep(2)          # Espera 2 segundos antes de la siguiente lectura
        else:
            movimiento_detectado = False
            buzzer_pir.duty(0)    # Asegúrate de que el zumbador esté apagado
        
        utime.sleep(0.5)  # Chequeo cada 0.5 segundos

# Función para monitoreo de sensor LDR en un hilo separado
def monitoreo_ldr():
    global luz_detectada
    while True:
        lux_value = ldr.read()  # Lee el valor de luz
        print("Nivel de luz:", lux_value)
        
        if lux_value < 1500:  # Luz baja (ajusta el valor según tu sensor)
            luz_detectada = True
            print("Luz baja detectada")
            beep_ldr(2, 1, 0.5)  # Dos pitidos sostenidos de 1 segundo
        elif lux_value > 2500:  # Luz alta (ajusta el valor según tu sensor)
            luz_detectada = True
            print("Luz alta detectada")
            beep_ldr(3, 0.2, 0.2)  # Tres pitidos rápidos
        else:
            luz_detectada = False
            # No es necesario apagar el zumbador aquí, ya lo hace beep_ldr
        
        time.sleep(3)  # Pausa antes de la siguiente lectura

# Función para detener motores
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

# Iniciar hilos de monitoreo de sensores
_thread.start_new_thread(monitoreo_proximidad, ())
_thread.start_new_thread(monitoreo_pir, ())
_thread.start_new_thread(monitoreo_ldr, ())

# Servidor HTTP con control de proximidad, movimiento y luz
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
        
        # Verificar condiciones de los sensores
        if proximidad_detectada or movimiento_detectado or luz_detectada:
            stop_motors()  # Detener motores si hay un obstáculo, movimiento o condición de luz
            response = "HTTP/1.1 200 OK\n\nSensor detectado. Movimiento detenido."
        else:
            # Procesamiento de comandos de movimiento
            if '/btnForward' in request:
                # Adelante
                in1.on(); in2.off()
                in3.on(); in4.off()
                in5.on(); in6.off()
                in7.on(); in8.off()
            elif '/btnBack' in request:
                # Atrás
                in1.off(); in2.on()
                in3.off(); in4.on()
                in5.off(); in6.on()
                in7.off(); in8.on()
            elif '/btnLeft' in request:
                # Izquierda
                in1.off(); in2.on()
                in3.on(); in4.off()
                in5.off(); in6.on()
                in7.on(); in8.off()
            elif '/btnRight' in request:
                # Derecha
                in1.on(); in2.off()
                in3.off(); in4.on()
                in5.on(); in6.off()
                in7.off(); in8.on()
            elif '/btnStop' in request:
                # Detener
                stop_motors()
            
            response = "HTTP/1.1 200 OK\n\nControl recibido"
        
        cl.send(response)
        cl.close()

start_server()
