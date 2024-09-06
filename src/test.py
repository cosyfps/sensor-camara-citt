# Instalar Librerias
import cv2
import numpy as np
import sqlite3

# Deteccion de Caras con el Archivo .xml
faceDetect=cv2.CascadeClassifier('haarcascade_frontalface_default.xml');  # Re-dirigimos al archivo .xml
cam=cv2.VideoCapture(0);                               # 0 para la camara por defecto del sistema

# Conectar a la base de datos
def insertOrUpdate(Id,Name,Age,Gen):                    # Funcion para la base de datos SQLite3
    conn=sqlite3.connect("database/sqlite.db")                   # Conexion hacia la base de datos SQLite3 de reconocimiento 
    cmd="SELECT * FROM Personas WHERE ID="+str(Id)      # Creamos una Query para identificar a la persona por su ID
    cursor=conn.execute(cmd)                            # Ejecutamos la Query con este cursor 
    isRecordExist=0                                     # Si no se esta Ejecutando el Programa no se guardaran datos
    for row in cursor:      
        isRecordExist=1                                 # Si se ejecuta el Programa se empiezan a guardar los datos
    
    if(isRecordExist==1):
        conn.execute("UPDATE Personas SET Name=? WHERE id=?", (Name,Id,))   # Si se ejecuta actualizamos el Nombre y ID de la Persona
        conn.execute("UPDATE Personas SET Age=? WHERE id=?",(Age, Id))
        conn.execute("UPDATE Personas SET Gen=? WHERE id=?", (Gen,Id,))
    else:
        conn.execute("INSERT INTO Personas(Id,Name,Age,Gen) Values(?,?,?,?)", (Id, Name, Age, Gen))     # Si se termina de ejecutar insertamos esos datos en la tabla Persona
    
    conn.commit()       # Hacemos un commit a los cambios 
    conn.close()        # Terminamos la conexion de la base de datos SQLite3


# Insertar una Persona indentificada  por medio de parametros
Id=input('User Id:')
Name=input('User Name:')
Age=input('User Age:')
Gen=input('User Gender:')

insertOrUpdate(Id,Name,Age,Gen)     # Insertamos los datos hacia la funcion que crea la conexion con la base de datos SQLite3 por medio de parametros

# Deteccion de Caras en las Camaras 
sampleNum=0         # Asumimos que no hay ningun sample
while(True):
    ret,img=cam.read();                                    # Abrimos la camara por defecto del Sistema
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)              # Cambiamos la imagen de tama;o y la convertimos en color Gris
    faces=faceDetect.detectMultiScale(gray,1.3,5);         # Escalamos las caras 
    for(x,y,w,h) in faces:                                 
        sampleNum=sampleNum+1;                             # Si se detecta una cara incrementa el numero del sample
        cv2.imwrite("review/User."+str(Id)+"."+str(sampleNum)+".jpg",gray[y:y+h,x:x+w])       # Si se detecta una cara sera registrada en la carpeta review/ en formato .jpg
        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)     # Creamos un rectangulo para identificar que caras detecta la camara
        cv2.waitKey(400);                                  # Delay de la camara en segundos
        cv2.imshow("Face",img);                            # Muestra las caras detectadas en la camara
        cv2.waitKey(1);

        if(sampleNum > 50):                                # Si los samples son > a 50 se rompe el bucle While 
            break;

cam.release()
cv2.destroyAllWindows()                                    # Cerramos la camara
        