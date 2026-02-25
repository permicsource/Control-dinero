import streamlit as st
from datetime import date
from models import Gasto
from database import crear_tabla, insertar_gasto
from analysis import resumen_por_categoria, resumen_mensual, exportar_a_excel


# Asegurar que la tabla exista
crear_tabla()

st.title("Control de Finanzas Personales")

menu = st.sidebar.selectbox(
    "Seleccione una opción",
    ["Agregar gasto", "Resumen por categoría", "Resumen mensual", "Exportar a Excel"]
)

# --------------------------
# AGREGAR GASTO
# --------------------------
if menu == "Agregar gasto":

    st.header("Agregar nuevo gasto")

    with st.form("form_gasto", clear_on_submit=True):

        fecha = st.date_input("Fecha", value=date.today())
        categoria = categoria = st.selectbox(
            "Categoría",
            ["Comida", "Bencina", "Ropa", "Arriendo", "Salud", "Deporte", "Educación", "Inversión", "Otros", "Transporte", "Ocio"]
        )
        descripcion = st.text_input("Descripción")
        monto = st.number_input("Monto", min_value=0.0, step=100.0)

        submitted = st.form_submit_button("Guardar gasto")

        if submitted:
            gasto = Gasto(fecha, categoria, descripcion, monto)
            insertar_gasto(gasto)
            st.success("✔ Gasto guardado correctamente")


# --------------------------
# RESUMEN CATEGORÍA
# --------------------------
elif menu == "Resumen por categoría":

    st.header("Resumen por categoría")
    resumen = resumen_por_categoria()

    if resumen.empty:
        st.info("No hay datos aún.")
    else:
        st.dataframe(resumen)


# --------------------------
# RESUMEN MENSUAL
# --------------------------
elif menu == "Resumen mensual":

    st.header("Resumen mensual")
    resumen = resumen_mensual()

    if resumen.empty:
        st.info("No hay datos aún.")
    else:
        st.dataframe(resumen)


# --------------------------
# EXPORTAR
# --------------------------
elif menu == "Exportar a Excel":

    st.header("Exportar datos")

    if st.button("Generar archivo Excel"):
        exportar_a_excel()
        st.success("✔ Archivo exportado como reporte_finanzas.xlsx")