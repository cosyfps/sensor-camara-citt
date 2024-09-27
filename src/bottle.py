import cv2
import numpy as np
import threading

# Cargar la red YOLO
net = cv2.dnn.readNet("src/test/yolov3.weights", "src/test/yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Cargar la lista de clases
with open("src/test/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Captura de video
cap = cv2.VideoCapture(0)

# Variable para almacenar el frame
frame = None
running = True

def capture_frames():
    global frame
    while running:
        ret, f = cap.read()
        if ret:
            frame = f

# Iniciar el hilo de captura
threading.Thread(target=capture_frames, daemon=True).start()

while True:
    if frame is None:
        continue

    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outputs = net.forward(output_layers)

    boxes, confidences, class_ids = [], [], []

    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5 and classes[class_id] == "bottle":
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    print(f"Detecciones encontradas: {len(boxes)}")

    # Aplicar Non-Maxima Suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # Manejar los índices de manera adecuada
    if len(indices) > 0:  # Asegúrate de que hay índices para procesar
        for i in indices.flatten() if isinstance(indices, np.ndarray) else indices[0]:
            box = boxes[i]
            x, y, w, h = box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, str(classes[class_ids[i]]), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    cv2.imshow("Deteccion de Botellas", frame)

    k = cv2.waitKey(1) & 0xFF
    if k == 27:  # Esc para salir
        running = False
        break

cap.release()
cv2.destroyAllWindows()
