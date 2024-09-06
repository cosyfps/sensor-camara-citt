import sqlite3


def create_database():
    conn = sqlite3.connect("database/citt.db")
    c = conn.cursor()

    # Crear la tabla si no existe
    c.execute(
        """CREATE TABLE IF NOT EXISTS traffic_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    exit_count INTEGER,
                    entry_count INTEGER
                )"""
    )

    c.execute(
        """CREATE TABLE IF NOT EXISTS traffic_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    exit_count INTEGER,
                    entry_count INTEGER
                )"""
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
