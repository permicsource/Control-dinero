#Capa de persistencia
#1. Se crea un objeto de gasto.
#2. Se abre una conexión a la .db
#3. Se ejecuta un comando SQL para insertar el gasto en la tabla.
#4. Se guardan los cambios y se cierra la conexión.

import sqlite3
from models import Gasto

DB_PATH = "/tmp/control_dinero.db"

#En lugar de escribir la ruta cada vez, se define como una constante.
def conectar():
    return sqlite3.connect(DB_PATH)

#Función para crear la tabla de gastos si no existe. Se ejecuta al iniciar la aplicación.
def crear_tabla():
    conn = conectar()
    cursor = conn.cursor()
#Se ejecuta un comando SQL para crear la tabla "gastos" con las columnas necesarias. Si la tabla ya existe, no hace nada.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descripcion TEXT,
            monto REAL NOT NULL
        )
    """)
#Confirma y guarda los cambios en la base de datos, luego cierra la conexión.
    conn.commit()
    conn.close()

#Función para guardar nuevo gasto.
def insertar_gasto(gasto: Gasto):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO gastos (fecha, categoria, descripcion, monto)
        VALUES (?, ?, ?, ?)
    """, (gasto.fecha.isoformat(), gasto.categoria, gasto.descripcion, gasto.monto))

    conn.commit()
    conn.close()

#Obtiene todos los gastos almacenados en la base de datos. Devuelve Tuplas.
def obtener_todos_los_gastos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT fecha, categoria, descripcion, monto FROM gastos")
    datos = cursor.fetchall()

    conn.close()
    return datos