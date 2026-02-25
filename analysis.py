import pandas as pd
from database import conectar
import psycopg2
from database import conectar

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


#def resumen_mensual():
#    df = obtener_dataframe()
#
#    if df.empty:
#        return df
#
#    return df.groupby("mes")["monto"].sum().sort_index()

#Exporta los datos en excel.
def exportar_a_excel(nombre_archivo="reporte_finanzas.xlsx"):
    df = obtener_dataframe()

    if df.empty:
        print("No hay datos para exportar.")
        return

    with pd.ExcelWriter(nombre_archivo) as writer:
        df.to_excel(writer, sheet_name="Datos", index=False)

        resumen_cat = df.groupby("categoria")["monto"].sum()
        resumen_cat.to_excel(writer, sheet_name="Resumen_Categorias")

        resumen_mes = df.groupby("mes")["monto"].sum()
        resumen_mes.to_excel(writer, sheet_name="Resumen_Mensual")

    print(f"Archivo exportado como {nombre_archivo}")