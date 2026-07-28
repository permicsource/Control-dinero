import pandas as pd
from datetime import date
from database import conectar
import psycopg2
from io import BytesIO


#Extrae los datos de la base de datos y los convierte en un df.
def obtener_dataframe():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM gastos", conn)
    conn.close()

    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["mes"] = df["fecha"].dt.to_period("M")

    return df

#Agrupa los gastos por categoría y suma el monto total de cada una

def resumen_por_categoria(mes, anio):
    conn = conectar()

    query = """
        SELECT categoria, SUM(monto) as total
        FROM gastos
        WHERE EXTRACT(MONTH FROM fecha) = %s
          AND EXTRACT(YEAR FROM fecha) = %s
        GROUP BY categoria
        ORDER BY total DESC;
    """

    df = pd.read_sql(query, conn, params=(mes, anio))
    conn.close()
    return df


#Función para obtener el resumen mensual total. Suma todos los gastos del mes seleccionado.

def resumen_mensual(mes, anio):
    conn = conectar()

    query = """
        SELECT SUM(monto) as total_mes
        FROM gastos
        WHERE EXTRACT(MONTH FROM fecha) = %s
          AND EXTRACT(YEAR FROM fecha) = %s;
    """

    df = pd.read_sql(query, conn, params=(mes, anio))
    conn.close()
    return df


#Exporta los datos en excel.
def exportar_a_excel():
    conn = conectar()

    df = pd.read_sql("""
        SELECT fecha, categoria, descripcion, monto
        FROM gastos
        ORDER BY fecha
    """, conn)

    conn.close()

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Gastos")

    output.seek(0)

    return output

    
    
#Función para gráfica de barras stacked.


def evolucion_mensual(anio):
    conn = conectar()

    query = """
        SELECT 
            EXTRACT(MONTH FROM fecha) AS mes,
            categoria,
            SUM(monto) AS total
        FROM gastos
        WHERE EXTRACT(YEAR FROM fecha) = %s
        GROUP BY mes, categoria
        ORDER BY mes;
    """

    df = pd.read_sql(query, conn, params=(anio,))
    conn.close()
    return df

#Función para mostrar los últimos gastos registrados.

def ultimos_gastos(n=3):
    conn = conectar()
    query = """
        SELECT fecha, categoria, descripcion, monto
        FROM gastos
        ORDER BY fecha DESC, id DESC
        LIMIT %s;
    """
    df = pd.read_sql(query, conn, params=(n,))
    conn.close()
    return df

#Función para mostrar los gastos de una categoría específica en un mes y año determinados.

def gastos_por_categoria(mes, anio, categoria):
    conn = conectar()

    query = """
        SELECT fecha, descripcion, monto
        FROM gastos
        WHERE EXTRACT(MONTH FROM fecha) = %s
          AND EXTRACT(YEAR FROM fecha) = %s
          AND categoria = %s
        ORDER BY fecha DESC;
    """

    df = pd.read_sql(query, conn, params=(mes, anio, categoria))
    conn.close()
    return df

#Función para guardar el sueldo mensual en la base de datos.


def guardar_sueldo(fecha_inicio, sueldo):
    conn = conectar()
    cursor = conn.cursor()

    query = """
        INSERT INTO sueldos (fecha_inicio, sueldo)
        VALUES (%s, %s);
    """

    cursor.execute(query, (fecha_inicio, sueldo))
    conn.commit()
    conn.close()

#Función para obtener el sueldo vigente en una fecha determinada.

def obtener_sueldo(fecha):
    conn = conectar()
    cursor = conn.cursor()

    query = """
        SELECT sueldo
        FROM sueldos
        WHERE fecha_inicio <= %s
        ORDER BY fecha_inicio DESC
        LIMIT 1;
    """

    cursor.execute(query, (fecha,))
    resultado = cursor.fetchone()

    conn.close()

    return resultado[0] if resultado else None


#Función para obtener ingresos adicionales

def obtener_ingresos_extra(mes, anio):

    conn = conectar()

    query = """
        SELECT SUM(monto) AS total
        FROM ingresos_extra
        WHERE EXTRACT(MONTH FROM fecha)=%s
        AND EXTRACT(YEAR FROM fecha)=%s
    """

    df = pd.read_sql(query,conn,params=(mes,anio))

    conn.close()

    return df


# Funcion para obtener la distribución de ahorro de un mes pasado

def obtener_distribucion(periodo):

    conn = conectar()

    query = """
        SELECT categoria, monto
        FROM distribucion_ahorro
        WHERE periodo = %s
        ORDER BY categoria;
    """

    df = pd.read_sql(query, conn, params=(periodo,))

    conn.close()

    return df


# Funcion para comprobar que el ahorro del mes ya fue distribuido
def periodo_distribuido(periodo):

    df = obtener_distribucion(periodo)

    return not df.empty


# DE AQUI PARA ABAJO SE AÑADEN FUNCIONES QUE DEVUELVEN FLOATS Y NO DF'S
#AHORA SOLO LAS ESTOY USANDO EN EL MODULO DE DISTRIBUCION DE AHORRO
#ALGUNAS FUNCIONES TIENEN EL MISMO NOMBRE QUE LAS QUE DEVUELVE DF, ACA TODAS TERMINAN EN _
#LUEGO REEMPLAZAR EN EL RESTO DE MODULOS PARA QUE SEA MAS SIMPLE
#ACA SE DEBERIAN HACER TODOS LOS CALCULOS, Y NO CALCULAR NADA EN APP.PY


#Devuelve float con el sueldo vigente se ese mes

def obtener_sueldo_(fecha):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        SELECT sueldo
        FROM sueldos
        WHERE fecha_inicio <= %s
        ORDER BY fecha_inicio DESC
        LIMIT 1;
    """

    cursor.execute(query, (fecha,))
    resultado = cursor.fetchone()

    conn.close()

    if resultado is None:
        return 0.0

    return float(resultado[0])



#Devuelve float con ingresos extra del mes

def obtener_ingresos_extra_(mes, anio):

    conn = conectar()

    query = """
        SELECT SUM(monto) AS total
        FROM ingresos_extra
        WHERE EXTRACT(MONTH FROM fecha) = %s
        AND EXTRACT(YEAR FROM fecha) = %s
    """

    df = pd.read_sql(query, conn, params=(mes, anio))

    conn.close()

    if df.empty or pd.isna(df.loc[0, "total"]):
        return 0.0

    return float(df.loc[0, "total"])

#Devuelve gastos del mes para el periodo seleccionado

def obtener_gastos_mes_(mes, anio):

    conn = conectar()

    query = """
        SELECT SUM(monto) AS total
        FROM gastos
        WHERE EXTRACT(MONTH FROM fecha) = %s
        AND EXTRACT(YEAR FROM fecha) = %s
    """

    df = pd.read_sql(query, conn, params=(mes, anio))

    conn.close()

    if df.empty or pd.isna(df.loc[0, "total"]):
        return 0.0

    return float(df.loc[0, "total"])


# Calcula el ahorro del mes con las funciones anteriores, devuelve float 

def obtener_ahorro_mes_(mes, anio):

    fecha = date(anio, mes, 1)

    sueldo = obtener_sueldo_(fecha)
    ingresos_extra = obtener_ingresos_extra_(mes, anio)
    gastos = obtener_gastos_mes_(mes, anio)

    ingresos = sueldo + ingresos_extra
    ahorro = ingresos - gastos

    return ingresos, gastos, ahorro