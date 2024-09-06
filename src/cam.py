import sys
import os

from data_operations import (
    insert_traffic_counts,
)  # Importar la función para insertar datos
import cv2

# Agregar el directorio raíz al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración de las cámaras
cap1 = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Usar DirectShow para la cámara 1 (Salida)
cap2 = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Usar DirectShow para la cámara 2 (Entrada)

cap1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Inicializar VideoWriter para guardar los videos con MJPEG
fourcc1 = cv2.VideoWriter_fourcc(*"MJPG")  # Utiliza el códec MJPEG para archivos .avi
out1 = cv2.VideoWriter("output1.avi", fourcc1, 20.0, (640, 480))
out2 = cv2.VideoWriter("output2.avi", fourcc1, 20.0, (640, 480))

# Clasificadores para detección de rostro
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Obtener dimensiones del frame de la cámara 1
w1 = int(cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
h1 = int(cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Obtener dimensiones del frame de la cámara 2
w2 = int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
h2 = int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Parámetros para las líneas de conteo
line_up1_position = (
    4  # Cambia este valor para ajustar la línea de conteo en la cámara 1 (salida)
)
line_up2_position = (
    1.5  # Cambia este valor para ajustar la línea de conteo en la cámara 2 (entrada)
)

# Coordenadas para las líneas de conteo
line_up1 = int(line_up1_position * (h1 / 5))
line_up2 = int(line_up2_position * (h2 / 5))

# Asegurarse de que las coordenadas de las líneas estén dentro del rango del frame
line_up1 = max(0, min(line_up1, h1 - 1))
line_up2 = max(0, min(line_up2, h2 - 1))

# Diccionarios para almacenar las posiciones anteriores de los rostros
previous_faces1 = {}
previous_faces2 = {}

# Inicializar contadores de entradas y salidas
entry_count = 0
exit_count = 0

# Valores anteriores para comparación
prev_exit_count = 0
prev_entry_count = 0

while cap1.isOpened() and cap2.isOpened():
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()

    if not ret1 or not ret2:
        print("Error: No se puede capturar el frame.")
        break

    # Procesar frame de la cámara 1 (salida)
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    faces1 = face_cascade.detectMultiScale(gray1, 1.3, 5)

    frame_with_lines1 = frame1.copy()
    # Dibujar línea de salida (azul)
    cv2.line(frame_with_lines1, (0, line_up1), (w1, line_up1), (255, 0, 0), 2)

    current_faces1 = {}

    for i, (x, y, w, h) in enumerate(faces1):
        center_x, center_y = x + w // 2, y + h // 2
        current_faces1[i] = center_y

        # Dibujar rectángulo y punto en el centro del rostro
        cv2.rectangle(frame_with_lines1, (x, y), (x + w, y + h), (255, 0, 0), 5)
        cv2.circle(
            frame_with_lines1, (center_x, center_y), 5, (0, 255, 0), -1
        )  # Punto verde en el centro

        # Verificar si un rostro cruzó la línea hacia arriba (salida)
        if i in previous_faces1:
            if previous_faces1[i] < line_up1 and center_y >= line_up1:
                exit_count += 1

    previous_faces1 = current_faces1

    # Mostrar el conteo en el frame de salida de la cámara 1
    cv2.putText(
        frame_with_lines1,
        f"Salidas: {exit_count}",
        (10, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 0),
        2,
    )
    cv2.imshow("CAMARA SALIDA 1", frame_with_lines1)

    # Guardar el frame de la cámara 1
    out1.write(frame_with_lines1)

    # Procesar frame de la cámara 2 (entrada)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    faces2 = face_cascade.detectMultiScale(gray2, 1.3, 5)

    frame_with_lines2 = frame2.copy()
    # Dibujar línea de entrada (roja)
    cv2.line(frame_with_lines2, (0, line_up2), (w2, line_up2), (0, 0, 255), 2)

    current_faces2 = {}

    for i, (x, y, w, h) in enumerate(faces2):
        center_x, center_y = x + w // 2, y + h // 2
        current_faces2[i] = center_y

        # Dibujar rectángulo y punto en el centro del rostro
        cv2.rectangle(frame_with_lines2, (x, y), (x + w, y + h), (255, 0, 0), 5)
        cv2.circle(
            frame_with_lines2, (center_x, center_y), 5, (0, 255, 0), -1
        )  # Punto verde en el centro

        # Verificar si un rostro cruzó la línea hacia arriba (entrada)
        if i in previous_faces2:
            if previous_faces2[i] < line_up2 and center_y >= line_up2:
                entry_count += 1

    previous_faces2 = current_faces2

    # Mostrar el conteo en el frame de entrada de la cámara 2
    cv2.putText(
        frame_with_lines2,
        f"Entradas: {entry_count}",
        (10, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2,
    )
    cv2.imshow("CAMARA ENTRADA 2", frame_with_lines2)

    # Guardar el frame de la cámara 2
    out2.write(frame_with_lines2)

    # Salir si se presiona 'esc'
    k = cv2.waitKey(30) & 0xFF
    if k == 27:  # Esc key to stop
        break

# Liberar recursos
cap1.release()
cap2.release()
out1.release()
out2.release()
cv2.destroyAllWindows()

# Insertar los datos en la base de datos
insert_traffic_counts(exit_count, entry_count)
