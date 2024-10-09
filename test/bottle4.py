import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2
import RPi.GPIO as GPIO
import gi
import os
import time
import signal
import threading

# Configurar GTK
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf

# Configurar el sensor de proximidad
TRIG_PIN = 23
ECHO_PIN = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Cargar el modelo TFLite
model_path = "/home/botella/Modelos/ssd_mobilenet_v2_coco_quant_postprocess.tflite"  # Cambia esto al nombre de tu modelo
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Obtener detalles de entrada y salida
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Cargar la imagen de fondo
background_path = "/home/botella/background.jpg"  # Cambia esto al nombre de tu archivo de fondo
background = cv2.imread(background_path)
background = cv2.resize(background, (640, 480))  # Ajustar el tamaño del fondo si es necesario

# Función para procesar la imagen
def process_frame(frame):
    input_shape = input_details[0]["shape"]

    # Redimensionar la imagen y convertirla a RGB si es necesario
    frame_resized = cv2.resize(frame, (input_shape[2], input_shape[1]))
    if len(frame_resized.shape) == 2:  # Convertir a RGB si la imagen es en escala de grises
        frame_resized = cv2.cvtColor(frame_resized, cv2.COLOR_GRAY2RGB)
    elif frame_resized.shape[2] == 4:  # Convertir a RGB si la imagen tiene canal alfa
        frame_resized = cv2.cvtColor(frame_resized, cv2.COLOR_BGRA2RGB)

    # Normalizar la imagen si se requiere por el modelo
    if input_details[0]['dtype'] == np.float32:
        input_data = np.array(frame_resized, dtype=np.float32) / 255.0
    else:
        input_data = np.clip(frame_resized, 0, 255).astype(np.uint8)

    # Expandir dimensiones para la entrada
    input_data = np.expand_dims(input_data, axis=0)

    # Ejecutar el modelo
    interpreter.set_tensor(input_details[0]["index"], input_data)
    interpreter.invoke()

    # Obtener resultados
    boxes = interpreter.get_tensor(output_details[0]["index"])[0]  # coordenadas de las cajas
    classes = interpreter.get_tensor(output_details[1]["index"])[0]  # clases de los objetos
    scores = interpreter.get_tensor(output_details[2]["index"])[0]  # puntuaciones de confianza

    return boxes, classes, scores

# Crear la ventana GTK en pantalla completa
class FullscreenWindow(Gtk.Window):
    def __init__(self):
        super(FullscreenWindow, self).__init__()
        self.set_title("Detección de Botellas")
        self.connect("destroy", self.on_destroy)
        self.set_default_size(800, 600)
        self.fullscreen()

        # Contenedor principal
        vbox = Gtk.VBox(spacing=10)
        self.add(vbox)

        # Imagen y etiqueta
        self.image = Gtk.Image()
        self.label = Gtk.Label(label="Esperando detección de botella...")
        self.label.set_name("label")

        vbox.pack_start(self.image, True, True, 0)
        vbox.pack_start(self.label, False, False, 0)

        # Botón para cerrar la aplicación
        self.button = Gtk.Button(label="Cerrar Aplicación")
        self.button.connect("clicked", self.on_close_button_clicked)
        vbox.pack_start(self.button, False, False, 0)

        self.show_all()

    def update_label(self, message):
        self.label.set_text(message)

    def update_image(self, frame):
        # Convertir la imagen de OpenCV a GdkPixbuf
        height, width, channels = frame.shape
        row_stride = width * channels
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(frame.tobytes(), GdkPixbuf.Colorspace.RGB, False, 8, width, height, row_stride)
        self.image.set_from_pixbuf(pixbuf)

    def on_close_button_clicked(self, widget):
        self.on_destroy(widget)

    def on_destroy(self, widget):
        print("Cerrando la aplicación...")
        if picam2:
            picam2.stop()
        try:
            GPIO.cleanup()
        except RuntimeWarning:
            pass
        cv2.destroyAllWindows()
        Gtk.main_quit()
        os._exit(0)

# Función para medir la distancia usando el sensor ultrasónico
def medir_distancia():
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()

    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()

    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2
    return distance

# Manejador de señal para limpiar los recursos al interrumpir el script
def signal_handler(sig, frame):
    print("\nInterrupción detectada, limpiando recursos...")
    if picam2:
        picam2.stop()
    try:
        GPIO.cleanup()
    except RuntimeWarning:
        pass
    cv2.destroyAllWindows()
    Gtk.main_quit()
    os._exit(0)

# Registrar el manejador de señales
signal.signal(signal.SIGINT, signal_handler)

# Iniciar la Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

# Iniciar la ventana GTK
def iniciar_gtk():
    window = FullscreenWindow()
    Gtk.main()

gtk_thread = threading.Thread(target=iniciar_gtk)
gtk_thread.daemon = True
gtk_thread.start()

# Contador para las imágenes guardadas
image_counter = 0

# Loop principal para la detección
def main_loop():
    global image_counter
    try:
        while True:
            # Medir la distancia con el sensor ultrasónico
            distancia = medir_distancia()
            print(f"Distancia medida: {distancia:.2f} cm")

            # Actualizar el mensaje en la ventana con la distancia medida
            window.update_label(f"Distancia medida: {distancia:.2f} cm")

            # Procesar la imagen solo si el sensor de proximidad detecta un objeto a menos de 40 cm
            if distancia <= 40:
                frame = picam2.capture_array()

                # Combinar el fondo con la imagen de la cámara
                frame = cv2.addWeighted(background, 0.5, frame, 0.5, 0)

                # Procesar la imagen y obtener detección
                try:
                    boxes, classes, scores = process_frame(frame)
                except ValueError as e:
                    print(e)
                    continue

                # Verificar si se detecta una botella
                detected = False
                for i in range(len(scores)):
                    if scores[i] > 0.5 and int(classes[i]) == 43:  # Cambia 43 por el índice correcto si es diferente
                        detected = True
                        box = boxes[i]
                        h, w, _ = frame.shape
                        y_min, x_min, y_max, x_max = (box * np.array([h, w, h, w])).astype(int)
                        # Dibujar la caja
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
                        # Guardar la imagen con la detección
                        image_path = f"/home/botella/botella_detectada_{image_counter}.jpg"
                        cv2.imwrite(image_path, frame)
                        image_counter += 1
                        break

                # Actualizar el mensaje y la imagen en la ventana
                if detected:
                    window.update_label("¡Botella detectada!")
                window.update_image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    finally:
        if picam2:
            picam2.stop()
        try:
            GPIO.cleanup()
        except RuntimeWarning:
            pass
        cv2.destroyAllWindows()

# Ejecutar el bucle principal en el hilo principal
main_loop()
