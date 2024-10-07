import RPi.GPIO as GPIO
import time
from picamera2 import Picamera2, Preview
import os

# Configuración del GPIO
GPIO.setmode(GPIO.BCM)
TRIG = 27  # Pin TRIG del sensor
ECHO = 17  # Pin ECHO del sensor
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Inicializar la cámara fuera del bucle
camera = Picamera2()
camera_config = camera.create_still_configuration(main={"size": (1980, 1024)}, lores={"size": (640, 480)}, display="lores")
camera.configure(camera_config)

# Directorio donde se guardarán las fotos
foto_dir = '/home/botella/'

# Función para medir distancia
def medir_distancia():
    # Enviar pulso al TRIG
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Medir el tiempo de retorno del pulso en ECHO
    while GPIO.input(ECHO) == 0:
        inicio_pulso = time.time()

    while GPIO.input(ECHO) == 1:
        fin_pulso = time.time()

    # Calcular la distancia en cm
    duracion_pulso = fin_pulso - inicio_pulso
    distancia = duracion_pulso * 17150
    distancia = round(distancia, 2)

    return distancia

# Función para obtener el nombre de la siguiente foto
def obtener_nombre_foto():
    numero_foto = 1
    while os.path.exists(f"{foto_dir}foto{numero_foto}.jpg"):
        numero_foto += 1
    return f"{foto_dir}foto{numero_foto}.jpg"

# Función para tomar una foto
def tomar_foto():
    nombre_foto = obtener_nombre_foto()
    camera.start_preview(Preview.QTGL)
    camera.start()
    time.sleep(2)  # Espera para ajustar enfoque y exposición
    camera.capture_file(nombre_foto)
    camera.stop_preview()  # Detener la vista previa después de la captura
    camera.stop()  # Detener la cámara para liberar recursos
    print(f"Foto tomada y guardada como {nombre_foto}.")

try:
    while True:
        distancia = medir_distancia()
        print(f"Distancia: {distancia} cm")

        # Si la distancia es menor a 10 cm (ajusta según lo necesites), toma una foto
        if distancia < 40:
            tomar_foto()
        time.sleep(1)

except KeyboardInterrupt:
    print("Detenido por el usuario.")
    GPIO.cleanup()
