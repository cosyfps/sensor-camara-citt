import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# Cargar el modelo TFLite
model_path = "/home/botella/Modelos/ssd_mobilenet_v2_coco_quant_postprocess.tflite"  # Cambia esto al nombre de tu modelo
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Obtener detalles de entrada y salida
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

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

    # Verificar si las dimensiones coinciden con las esperadas
    if input_data.shape[-1] != input_shape[-1]:
        input_data = cv2.cvtColor(input_data, cv2.COLOR_RGB2BGR)

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
        self.connect("destroy", Gtk.main_quit)
        self.set_default_size(800, 600)
        self.fullscreen()

        self.label = Gtk.Label(label="Esperando detección de botella...")
        self.label.set_name("label")
        self.add(self.label)

        self.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))
        self.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1))

        self.show_all()

    def update_label(self, message):
        self.label.set_text(message)

# Iniciar la Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

# Iniciar la ventana GTK
window = FullscreenWindow()

# Loop principal para la detección
while True:
    frame = picam2.capture_array()

    # Procesar la imagen y obtener detección
    try:
        boxes, classes, scores = process_frame(frame)
    except ValueError as e:
        print(e)
        continue

    # Verificar si se detecta una botella
    detected = False
    for i in range(len(scores)):
        if scores[i] > 0.1 and int(classes[i]) == 43:  # Cambia 43 por el índice correcto si es diferente
            detected = True
            break

    # Actualizar el mensaje en la ventana
    if detected:
        window.update_label("¡Botella detectada!")
    else:
        window.update_label("Esperando detección de botella...")

    # Procesar eventos de GTK
    while Gtk.events_pending():
        Gtk.main_iteration()

# Liberar la Picamera2
picam2.stop()
cv2.destroyAllWindows()
