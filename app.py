import streamlit as st
import datetime
import calendar
from datetime import date
from models import Gasto
from database import crear_tabla, insertar_gasto
from analysis import resumen_por_categoria, resumen_mensual, evolucion_mensual, exportar_a_excel

#Config pag

st.set_page_config(
    page_title="Money Saver",
    page_icon="assets/icon.png",
    layout="centered"
)

#Fecha Hoy
hoy = datetime.date.today()
mes_actual = hoy.month
anio_actual = hoy.year

# Lista nombres de meses
meses = [
    "Enero", "Febrero", "Marzo", "Abril",
    "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Asegurar que la tabla exista
if "db_initialized" not in st.session_state:
    crear_tabla()
    st.session_state.db_initialized = True

st.title("Money Saver")

menu = st.sidebar.selectbox(
    "Seleccione una opción",
    ["Agregar gasto", "Resumen mensual", "Análisis", "Exportar a Excel"]
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

elif menu == "Resumen mensual":

    st.header("Resumen mensual")

    col1, col2 = st.columns(2)

    with col1:
        anio = st.selectbox("Año", [2026], index=0)
        mes_nombre = st.selectbox(
            "Mes",
            meses,
            index=mes_actual - 1
        )

        # Convertir nombre a número
        mes = meses.index(mes_nombre) + 1

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



# --------------------------
# ANALISIS
# --------------------------

elif menu == "Análisis":

    st.header("Evolución mensual de gastos")

    anio = st.selectbox("Año", [2026], index=0)

    df_evolucion = evolucion_mensual(anio)

    if df_evolucion.empty:
        st.info("No hay datos para este año.")
    else:
        # Pivotear datos para stacked bar
        df_pivot = df_evolucion.pivot(
            index="mes",
            columns="categoria",
            values="total"
        ).fillna(0)

        # Ordenar meses
        df_pivot = df_pivot.sort_index()

        meses = [
            "Enero", "Febrero", "Marzo", "Abril",
            "Mayo", "Junio", "Julio", "Agosto",
            "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        df_pivot.index = [meses[int(m)-1] for m in df_pivot.index]


        import plotly.graph_objects as go

        fig = go.Figure()

        for categoria in df_pivot.columns:
            fig.add_trace(go.Bar(
                x=df_pivot.index,
                y=df_pivot[categoria],
                name=categoria,
                hovertemplate=f"{categoria}: %{{y}}<extra></extra>"
            ))
            

        fig.update_layout(
            barmode='stack',
            xaxis_title="Mes",
            yaxis_title="Total gastado",
            legend_title="Categoría",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

# --------------------------
# EXPORTAR
# --------------------------
elif menu == "Exportar a Excel":

    st.header("Exportar datos")

    if st.button("Generar archivo Excel"):
        exportar_a_excel()
        st.success("✔ Archivo exportado como reporte_finanzas.xlsx")