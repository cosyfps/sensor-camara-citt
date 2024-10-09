import cv2
import numpy as np
import tensorflow as tf
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
camera_config = camera.create_still_configuration(
    main={"size": (1980, 1024)}, lores={"size": (640, 480)}, display="lores"
)
camera.configure(camera_config)

# Directorio donde se guardarán las fotos
foto_dir = "/home/botella/"

# Cargar el modelo TFLite
model_path = "test/ssd_mobilenet_v2_coco_quant_postprocess.tflite"  # Cambia esto al nombre de tu modelo
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Obtener detalles de entrada y salida
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()


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


# Función para procesar la imagen
def process_frame(frame):
    input_shape = input_details[0]["shape"]

    # Redimensionar la imagen
    frame_resized = cv2.resize(frame, (input_shape[2], input_shape[1]))

    # Convertir la imagen a tipo UINT8
    input_data = np.clip(frame_resized, 0, 255).astype(np.uint8)

    # Expandir dimensiones para la entrada
    input_data = np.expand_dims(input_data, axis=0)

    # Ejecutar el modelo
    interpreter.set_tensor(input_details[0]["index"], input_data)
    interpreter.invoke()

    # Obtener resultados
    boxes = interpreter.get_tensor(output_details[0]["index"])[
        0
    ]  # coordenadas de las cajas
    classes = interpreter.get_tensor(output_details[1]["index"])[
        0
    ]  # clases de los objetos
    scores = interpreter.get_tensor(output_details[2]["index"])[
        0
    ]  # puntuaciones de confianza

    return boxes, classes, scores


# Iniciar el bucle principal
try:
    while True:
        distancia = medir_distancia()
        print(f"Distancia: {distancia} cm")

        # Si la distancia es menor a 40 cm, toma una foto y procesa la imagen
        if distancia < 40:
            tomar_foto()

            # Captura de video para la detección de objetos
            cap = cv2.VideoCapture(0)

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("No se puede acceder a la cámara.")
                    break

                # Procesar la imagen y obtener detección
                boxes, classes, scores = process_frame(frame)

                # Dibujar las detecciones en el marco
                for i in range(len(scores)):
                    print(
                        f"Clase: {int(classes[i])}, Puntuacion: {scores[i]:.2f}"
                    )  # Para depuración
                    # Verificar si la puntuación es mayor al umbral y si la clase es la de la botella (43)
                    if (
                        scores[i] > 0.1 and int(classes[i]) == 43
                    ):  # Asegúrate de que 43 sea el índice correcto
                        box = boxes[i]
                        h, w, _ = frame.shape
                        y_min, x_min, y_max, x_max = (
                            box * np.array([h, w, h, w])
                        ).astype(int)

                        # Dibujar la caja
                        cv2.rectangle(
                            frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2
                        )

                        # Etiquetar con la clase
                        label = f"Botella, Score: {scores[i]:.2f}"
                        cv2.putText(
                            frame,
                            label,
                            (x_min, y_min - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (255, 0, 0),
                            2,
                        )

                # Mostrar el resultado
                cv2.imshow("Object Detection", frame)

                # Cambiar la tecla para salir del bucle a Esc (27 es el código ASCII para Esc)
                if cv2.waitKey(1) & 0xFF == 27:  # 27 es el código ASCII para Esc
                    break

            # Liberar la cámara de video
            cap.release()
            cv2.destroyAllWindows()

        time.sleep(1)

except KeyboardInterrupt:
    print("Detenido por el usuario.")
finally:
    GPIO.cleanup()
