#Capa de persistencia
#1. Se crea un objeto de gasto.
#2. Se abre una conexión a la .db
#3. Se ejecuta un comando SQL para insertar el gasto en la tabla.
#4. Se guardan los cambios y se cierra la conexión.

import psycopg2
import streamlit as st
from models import Gasto, IngresoExtra

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingresos_extra (
            id SERIAL PRIMARY KEY,
            fecha DATE NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT,
            monto NUMERIC NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distribucion_ahorro (
            id SERIAL PRIMARY KEY,
            periodo DATE NOT NULL,
            categoria TEXT NOT NULL,
            monto NUMERIC NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def insertar_ingreso_extra(ingreso: IngresoExtra):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ingresos_extra
        (fecha, tipo, descripcion, monto)
        VALUES (%s,%s,%s,%s)
    """,
    (
        ingreso.fecha,
        ingreso.tipo,
        ingreso.descripcion,
        ingreso.monto
    ))

    conn.commit()
    conn.close()


def insertar_distribucion(periodo, distribucion):

    conn = conectar()
    cursor = conn.cursor()

    try:

        for categoria, monto in distribucion.items():

            if monto > 0:

                cursor.execute("""
                    INSERT INTO distribucion_ahorro
                    (periodo, categoria, monto)
                    VALUES (%s, %s, %s)
                """, (periodo, categoria, monto))

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()

