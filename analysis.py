import pandas as pd
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
def resumen_por_categoria():
    df = obtener_dataframe()

    if df.empty:
        return df

    return df.groupby("categoria")["monto"].sum().sort_values(ascending=False)

#Agrupa los gastos por mes y suma el monto total de cada uno
def resumen_mensual():
    df = obtener_dataframe()

    if df.empty:
        return df

    return df.groupby("mes")["monto"].sum().sort_index()

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