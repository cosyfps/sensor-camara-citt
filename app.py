from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = "database/citt.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Ruta para obtener todos los conteos de tráfico
@app.route("/traffic_counts", methods=["GET"])
def get_traffic_counts():
    conn = get_db_connection()
    counts = conn.execute("SELECT * FROM traffic_counts").fetchall()
    conn.close()

    traffic_counts = [dict(row) for row in counts]
    return jsonify(traffic_counts)


@app.route("/traffic_counts", methods=["GET"])
def get_entry_exit():
    conn = get_db_connection()
    counts = conn.execute(
        "SELECT exit_count, entry_count FROM traffic_counts"
    ).fetchall()
    conn.close()

    traffic_counts = [dict(row) for row in counts]
    return jsonify(traffic_counts)


# Ruta para agregar un nuevo conteo
@app.route("/traffic_counts", methods=["POST"])
def add_traffic_count():
    data = request.get_json()
    exit_count = data.get("exit_count")
    entry_count = data.get("entry_count")

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO traffic_counts (exit_count, entry_count) VALUES (?, ?)",
        (exit_count, entry_count),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Conteo agregado exitosamente"}), 201


# Ruta para obtener un conteo específico por ID
@app.route("/traffic_counts/<int:id>", methods=["GET"])
def get_traffic_count(id):
    conn = get_db_connection()
    count = conn.execute("SELECT * FROM traffic_counts WHERE id = ?", (id,)).fetchone()
    conn.close()

    if count is None:
        return jsonify({"message": "Conteo no encontrado"}), 404

    return jsonify(dict(count))


if __name__ == "__main__":
    app.run(debug=True)
