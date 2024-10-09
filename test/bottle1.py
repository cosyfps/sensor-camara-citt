import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2

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

    # Expandir dimensiones para la entrada
    input_data = np.expand_dims(input_data, axis=0)

    # Verificar si las dimensiones coinciden con las esperadas
    if input_data.shape != tuple(input_shape):
        raise ValueError(f"Dimension mismatch: expected {input_shape}, but got {input_data.shape}")

    # Ejecutar el modelo
    interpreter.set_tensor(input_details[0]["index"], input_data)
    interpreter.invoke()

    # Obtener resultados
    boxes = interpreter.get_tensor(output_details[0]["index"])[0]  # coordenadas de las cajas
    classes = interpreter.get_tensor(output_details[1]["index"])[0]  # clases de los objetos
    scores = interpreter.get_tensor(output_details[2]["index"])[0]  # puntuaciones de confianza

    return boxes, classes, scores

# Iniciar la Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

while True:
    frame = picam2.capture_array()

    # Procesar la imagen y obtener detección
    try:
        boxes, classes, scores = process_frame(frame)
    except ValueError as e:
        print(e)
        continue

    # Dibujar las detecciones en el marco
    for i in range(len(scores)):
        print(f"Clase: {int(classes[i])}, Puntuacion: {scores[i]:.2f}")  # Para depuración
        # Verificar si la puntuación es mayor al umbral y si la clase es la de la botella (43)
        if scores[i] > 0.1 and int(classes[i]) == 43:  # Cambia 43 por el índice correcto si es diferente
            box = boxes[i]
            h, w, _ = frame.shape
            y_min, x_min, y_max, x_max = (box * np.array([h, w, h, w])).astype(int)

            # Dibujar la caja
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

            # Etiquetar con la clase
            label = f"Botella, Score: {scores[i]:.2f}"
            cv2.putText(frame, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Mostrar el resultado
    cv2.imshow("Object Detection", frame)

    # Cambiar la tecla para salir del bucle a Esc (27 es el código ASCII para Esc)
    if cv2.waitKey(1) & 0xFF == 27:  # 27 es el código ASCII para Esc
        break

# Liberar la Picamera2 y cerrar ventanas
picam2.stop()
cv2.destroyAllWindows()
