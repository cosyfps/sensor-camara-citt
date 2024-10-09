import cv2
import numpy as np
import tensorflow as tf

# Cargar el modelo TFLite
model_path = "test/ssd_mobilenet_v2_coco_quant_postprocess.tflite"  # Cambia esto al nombre de tu modelo
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Obtener detalles de entrada y salida
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()


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


# Iniciar la webcam
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
        # Verificar si la puntuación es mayor al umbral y si la clase es la de la botella (39)
        if (
            scores[i] > 0.1 and int(classes[i]) == 43
        ):  # Cambia 39 por el índice correcto si es diferente
            box = boxes[i]
            h, w, _ = frame.shape
            y_min, x_min, y_max, x_max = (box * np.array([h, w, h, w])).astype(int)

            # Dibujar la caja
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

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

# Liberar la webcam y cerrar ventanas
cap.release()
cv2.destroyAllWindows()
