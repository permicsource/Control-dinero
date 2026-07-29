import pandas as pd
from datetime import date, timedelta
from database import conectar, insertar_historial_inversion
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

#
#
#
#
#
#
#
#
# Obtiene el capital acumulado hasta la fecha de una categoría
# Por ahora no se está usando.

#def obtener_capital_categoria(categoria, fecha):

    conn = conectar()

    query = """
        SELECT SUM(monto) AS capital
        FROM distribucion_ahorro
        WHERE categoria = %s
        AND DATE(fecha_registro) <= %s
    """

    df = pd.read_sql(
        query,
        conn,
        params=(categoria, fecha)
    )

    conn.close()

    if df.empty or pd.isna(df.loc[0, "capital"]):
        return 0.0

    return float(df.loc[0, "capital"])

# Lee la tabla objetivos y devuelve un df con las columnas del query
#Es la unica funcion que devuelve un df

def obtener_objetivos():

    conn = conectar()

    query = """
        SELECT categoria,
               tipo,
               meta,
               tasa_interes
        FROM objetivos
        ORDER BY categoria
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df

# Lee historial_inversiones y devuelve un diccionario con la ultima fotografía disponible
#para una categoria

def obtener_historial_anterior(categoria, fecha):

    conn = conectar()

    query = """
        SELECT
            fecha,
            capital,
            rentabilidad,
            valor_total
        FROM historial_inversiones
        WHERE categoria = %s
        AND fecha < %s
        ORDER BY fecha DESC
        LIMIT 1
    """

    df = pd.read_sql(
        query,
        conn,
        params=(categoria, fecha)
    )

    conn.close()

    if df.empty:
        return None

    return df.iloc[0].to_dict()

#Calcula liquidez según la foto del dia anterior recibe el objetivo (categoria mas taza), el capital actual y calcula la rentabilidad
#solo calcula no guarda nada.

def calcular_liquidez(objetivo, capital_actual, fecha):

    categoria = objetivo["categoria"]
    tasa_anual = float(objetivo["tasa_interes"])

    historial = obtener_historial_anterior(
        categoria,
        fecha
    )

    # Primera fotografía
    if historial is None:

        return {
            "categoria": categoria,
            "capital_aportado": capital_actual,
            "rentabilidad": 0.0,
            "valor_total": capital_actual
        }

    capital_anterior = float(historial["capital"])
    rentabilidad_anterior = float(historial["rentabilidad"])
    valor_anterior = float(historial["valor_total"])

    aporte_dia = capital_actual - capital_anterior

    tasa_diaria = (tasa_anual / 100) / 365

    interes_dia = valor_anterior * tasa_diaria

    rentabilidad = rentabilidad_anterior + interes_dia

    valor_total = valor_anterior + interes_dia + aporte_dia

    return {
        "categoria": categoria,
        "capital_aportado": capital_actual,
        "rentabilidad": rentabilidad,
        "valor_total": valor_total
    }

# Lee historial inversiones y devuelve el último dia que proceso el motor (ultimo dia que entre a la app)
#para calcular los intereses de los dias que no se calcularon.

def obtener_ultima_fecha_historial():

    conn = conectar()

    query = """
        SELECT MAX(fecha) AS ultima_fecha
        FROM historial_inversiones
    """

    df = pd.read_sql(query, conn)

    conn.close()

    if pd.isna(df.loc[0, "ultima_fecha"]):
        return None

    return df.loc[0, "ultima_fecha"]


# Lee distribucion_ahorro, y devuelve la fecha donde comenzó la inversión
#si no hay nada devuelve None

def obtener_primer_aporte():

    conn = conectar()

    query = """
        SELECT MIN(DATE(fecha_registro)) AS primer_aporte
        FROM distribucion_ahorro
    """

    df = pd.read_sql(query, conn)

    conn.close()

    if pd.isna(df.loc[0, "primer_aporte"]):
        return None

    return df.loc[0, "primer_aporte"]



# Lee distribucion_ahorro y devuelve un diccionario con el total de los aportes hasta la fecha para cada categoria
# solo aportes no incluye intereses

def obtener_capitales(fecha):

    conn = conectar()

    query = """
        SELECT
            categoria,
            SUM(monto) AS capital
        FROM distribucion_ahorro
        WHERE DATE(fecha_registro) <= %s
        GROUP BY categoria
    """

    df = pd.read_sql(query, conn, params=(fecha,))

    conn.close()

    capitales = {}

    for _, fila in df.iterrows():

        capitales[fila["categoria"]] = float(fila["capital"])

    return capitales


#MOTOR V6
# No calcula solo llama al resto de las funciones
#
def actualizar_historial_inversiones():

    ultima_fecha = obtener_ultima_fecha_historial()

    if ultima_fecha is None:

        fecha_actualizar = obtener_primer_aporte()

    else:

        fecha_actualizar = ultima_fecha + timedelta(days=1)

    if fecha_actualizar is None:
        return

    hoy = date.today()

    while fecha_actualizar <= hoy:

        objetivos = obtener_objetivos()

        # Una sola consulta SQL para todas las categorías de este día
        capitales = obtener_capitales(fecha_actualizar)

        for _, objetivo in objetivos.iterrows():

            categoria = objetivo["categoria"]

            capital_actual = capitales.get(categoria, 0.0)

            if objetivo["tipo"] == "Liquidez":

                resultado = calcular_liquidez(
                    objetivo,
                    capital_actual,
                    fecha_actualizar
                )

            else:

                # Se implementará cuando agreguemos ETFs
                continue

            insertar_historial_inversion(
                fecha=fecha_actualizar,
                categoria=resultado["categoria"],
                capital=resultado["capital_aportado"],
                rentabilidad=resultado["rentabilidad"],
                valor_total=resultado["valor_total"]
            )

        fecha_actualizar += timedelta(days=1)

#
#
#
#
#
#
#
#
#
# Comprueba que las inversiones y sus intereses esten actualizados, de no ser asi 
#actualiza los dias faltantes, la idea es que se corra autimaticamnete al abrir el módulo de inversiones.



def actualizar_historial_si_es_necesario():

    ultima_fecha = obtener_ultima_fecha_historial()

    if ultima_fecha == date.today():

        return ultima_fecha, False

    actualizar_historial_inversiones()

    return date.today(), True


# Entrega un df con los datos de la ultima fotografía
#Se usa para mostrar y graficar en la interfaz


def obtener_estado_actual():

    conn = conectar()

    query = """
        SELECT
            h.categoria,
            o.tipo,
            o.meta,
            h.capital,
            h.rentabilidad,
            h.valor_total
        FROM historial_inversiones h
        INNER JOIN objetivos o
            ON h.categoria = o.categoria
        WHERE h.fecha = (
            SELECT MAX(fecha)
            FROM historial_inversiones
        )
        ORDER BY o.tipo, h.categoria
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df

# Funcion para obtener historial a usar en los graficos

def obtener_historial(tipo=None, categoria=None):

    conn = conectar()

    query = """
        SELECT
            h.fecha,
            h.categoria,
            o.tipo,
            h.capital,
            h.rentabilidad,
            h.valor_total
        FROM historial_inversiones h
        INNER JOIN objetivos o
            ON h.categoria = o.categoria
    """

    params = []

    filtros = []

    if tipo is not None:

        filtros.append("o.tipo = %s")
        params.append(tipo)

    if categoria is not None:

        filtros.append("h.categoria = %s")
        params.append(categoria)

    if filtros:

        query += " WHERE " + " AND ".join(filtros)

    query += """
        ORDER BY
            h.fecha,
            h.categoria
    """

    df = pd.read_sql(
        query,
        conn,
        params=params
    )

    conn.close()

    return df

#Para hacer el grafico de capital vs patrimonio (Evolucion del patrimonio)
#grafico de dos lineas


def obtener_evolucion_patrimonio():

    df = obtener_historial()

    df = (
        df.groupby("fecha")[["capital", "rentabilidad", "valor_total"]]
        .sum()
        .reset_index()
    )

    return df

# Para graficar el stacked area chart

def obtener_composicion_patrimonio():

    df = obtener_historial()

    df = df.pivot_table(

        index="fecha",

        columns="categoria",

        values="valor_total",

        aggfunc="sum",

        fill_value=0

    )

    return df.reset_index()

#Para obtener el progreso de los objetivos y graficar las barras

def obtener_progreso_objetivos():

    df = obtener_estado_actual()

    df["progreso"] = df["valor_total"] / df["meta"]

    return df

#Para obtener tabla resumen de las inversiones

def obtener_resumen_inversiones():

    df = obtener_estado_actual()

    df["progreso"] = (
        df["valor_total"] /
        df["meta"]
    ) * 100

    return df