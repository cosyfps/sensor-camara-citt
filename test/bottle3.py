import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2
import gi
import os

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

# Cargar el modelo TFLite
model_path = "/home/botella/Modelos/ssd_mobilenet_v2_coco_quant_postprocess.tflite"  # Cambia esto al nombre de tu modelo
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Obtener detalles de entrada y salida
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Cargar la imagen de fondo
background_path = "/home/botella/background.jpg"
background = cv2.imread(background_path)

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

        # Establecer la imagen de fondo
        self.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))
        self.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1))

        # Cargar la imagen de fondo como pixbuf y redimensionarla para llenar toda la ventana
        self.background_pixbuf = GdkPixbuf.Pixbuf.new_from_file(background_path)
        screen = self.get_screen()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        self.background_pixbuf = self.background_pixbuf.scale_simple(screen_width, screen_height, GdkPixbuf.InterpType.BILINEAR)
        self.set_app_paintable(True)
        self.connect("draw", self.on_draw)

        self.show_all()

    def on_draw(self, widget, cr):
        Gdk.cairo_set_source_pixbuf(cr, self.background_pixbuf, 0, 0)
        cr.paint()

    def update_label(self, message):
        self.label.set_text(message)

    def update_image(self, frame):
        # Convertir la imagen de OpenCV a GdkPixbuf
        height, width, channels = frame.shape
        row_stride = width * channels
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(frame.tobytes(), GdkPixbuf.Colorspace.RGB, False, 8, width, height, row_stride)
        self.image.set_from_pixbuf(pixbuf)

    def on_close_button_clicked(self, widget):
        self.close()
        Gtk.main_quit()

    def on_destroy(self, widget):
        Gtk.main_quit()

# Iniciar la Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

# Iniciar la ventana GTK
window = FullscreenWindow()

# Contador para las imágenes guardadas
image_counter = 0

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
    else:
        window.update_label("Esperando detección de botella...")

    window.update_image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    # Procesar eventos de GTK
    while Gtk.events_pending():
        Gtk.main_iteration()

# Liberar la Picamera2
picam2.stop()
cv2.destroyAllWindows()
