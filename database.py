#Capa de persistencia
#1. Se crea un objeto de gasto.
#2. Se abre una conexión a la .db
#3. Se ejecuta un comando SQL para insertar el gasto en la tabla.
#4. Se guardan los cambios y se cierra la conexión.

import psycopg2
import streamlit as st
from models import Gasto

def conectar():
    return psycopg2.connect(
        st.secrets["DATABASE_URL"],
        sslmode="require"
    )

def crear_tabla():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id SERIAL PRIMARY KEY,
            fecha DATE NOT NULL,
            categoria TEXT NOT NULL,
            descripcion TEXT,
            monto NUMERIC NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def insertar_gasto(gasto: Gasto):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO gastos (fecha, categoria, descripcion, monto)
        VALUES (%s, %s, %s, %s)
    """, (gasto.fecha, gasto.categoria, gasto.descripcion, gasto.monto))

    conn.commit()
    conn.close()

def obtener_todos_los_gastos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT fecha, categoria, descripcion, monto FROM gastos")
    datos = cursor.fetchall()

    conn.close()
    return datos