import streamlit as st
from datetime import date
from models import Gasto
from database import crear_tabla, insertar_gasto
from analysis import resumen_por_categoria, resumen_mensual, exportar_a_excel


# Asegurar que la tabla exista
if "db_initialized" not in st.session_state:
    crear_tabla()
    st.session_state.db_initialized = True

st.title("Money Saver")

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

    col1, col2 = st.columns(2)

    with col1:
        anio = st.selectbox("Año", [2024, 2025, 2026], index=1)
        mes = st.selectbox(
            "Mes",
            list(range(1, 13)),
            format_func=lambda x: [
                "Enero","Febrero","Marzo","Abril","Mayo","Junio",
                "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
            ][x-1]
        )

    resumen_cat = resumen_por_categoria(mes, anio)
    resumen_mes = resumen_mensual(mes, anio)

    col_tabla, col_resumen = st.columns([2,1])

    with col_tabla:
        if resumen_cat.empty:
            st.info("No hay datos para este mes.")
        else:
            st.subheader("Gasto por categoría")
            st.dataframe(resumen_cat)

            st.subheader("Distribución porcentual")
            st.plotly_chart({
                "data": [{
                    "labels": resumen_cat["categoria"],
                    "values": resumen_cat["total"],
                    "type": "pie"
                }]
            })

    with col_resumen:
        st.subheader("Total del mes")

        if resumen_mes.iloc[0]["total_mes"] is not None:
            total = resumen_mes.iloc[0]["total_mes"]
            st.metric("Total gastado", f"${total:,.0f}")
        else:
            st.metric("Total gastado", "$0")



#elif menu == "Resumen por categoría":
#
#    st.header("Resumen por categoría")
#    resumen = resumen_por_categoria()
#
#    if resumen.empty:
#        st.info("No hay datos aún.")
#    else:
#        st.dataframe(resumen)


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