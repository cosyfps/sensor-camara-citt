import sqlite3
import datetime


def insert_traffic_counts(exit_count, entry_count):
    conn = sqlite3.connect("database/citt.db")
    c = conn.cursor()

    # Obtener la hora local del sistema
    local_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Insertar datos
    c.execute(
        "INSERT INTO traffic_counts (timestamp, exit_count, entry_count) VALUES (?, ?, ?)",
        (local_timestamp, exit_count, entry_count),
    )
    conn.commit()
    conn.close()


def query_traffic_counts():
    conn = sqlite3.connect("database/citt.db")
    c = conn.cursor()

    # Consultar todos los datos
    c.execute("SELECT * FROM traffic_counts")
    rows = c.fetchall()

    for row in rows:
        print(f"ID: {row[0]}, Timestamp: {row[1]}, Entrada: {row[2]}, Salida: {row[3]}")

    conn.close()
