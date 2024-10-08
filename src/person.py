import numpy as np
import cv2

cap = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

while True:
    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for x, y, w, h in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 5)
        roi_gray = gray[y : y + w, x : x + w]
        roi_color = frame[y : y + h, x : x + w]

    cv2.imshow("Entrada", frame)

    k = cv2.waitKey(30) & 0xFF
    if k == 27:  
        break

cap.release()
cv2.destroyAllWindows()
