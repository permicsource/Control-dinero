import streamlit as st
import datetime
import calendar
from datetime import date
from models import Gasto
from database import crear_tabla, insertar_gasto
from analysis import resumen_por_categoria, resumen_mensual, evolucion_mensual, exportar_a_excel, ultimos_gastos, gastos_por_categoria, obtener_sueldo, guardar_sueldo
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
    ["Agregar gasto", "Resumen mensual", "Análisis", "Exportar a Excel", "Sueldos"]
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
    
    
    st.subheader("Últimos gastos ingresados")

    df_ultimos = ultimos_gastos(3)

    if not df_ultimos.empty:
        st.dataframe(df_ultimos)
    else:
        st.info("Aún no hay gastos registrados.")


# --------------------------
# RESUMEN CATEGORÍA
# --------------------------

elif menu == "Resumen mensual":
    st.header("Resumen mensual")

    col1, col2 = st.columns(2)

    with col1:
        anio = st.selectbox("Año", [2026], index=0)
        mes_nombre = st.selectbox("Mes", meses, index=mes_actual - 1)
        mes = meses.index(mes_nombre) + 1

        fecha_consulta = date(anio, mes, 1)
        sueldo_actual = obtener_sueldo(fecha_consulta)

    resumen_cat = resumen_por_categoria(mes, anio)
    resumen_mes = resumen_mensual(mes, anio)

    col_tabla, col_resumen = st.columns([2, 1])

    with col_tabla:
        if resumen_cat.empty:
            st.info("No hay datos para este mes.")
        else:
            st.subheader("Gasto por categoría")
            # Mostramos la tabla general de gastos sin índice para que sea más limpia
            st.dataframe(resumen_cat, hide_index=True, use_container_width=True)

    with col_resumen:
        st.subheader("Estado Financiero")
        
        # Obtenemos el total gastado de forma segura
        total_gastado = 0.0
        if not resumen_mes.empty and resumen_mes.iloc[0]["total_mes"] is not None:
            total_gastado = float(resumen_mes.iloc[0]["total_mes"])
        
        st.metric("Total gastado", f"${total_gastado:,.0f}")

        if sueldo_actual is not None:
            sueldo_actual_f = float(sueldo_actual)
            st.metric("Sueldo del mes", f"${sueldo_actual_f:,.0f}")
            
            # Cálculo de ahorro
            ahorro_mes = sueldo_actual_f - total_gastado
            st.metric("Ahorro del mes", f"${ahorro_mes:,.0f}", delta=f"${ahorro_mes:,.0f}")
        else:
            st.info("No hay sueldo registrado.")

    # ---------------------------------------------------------
    # ÚNICO GRÁFICO: Distribución Total del Ingreso
    # ---------------------------------------------------------
    if not resumen_cat.empty and sueldo_actual and sueldo_actual > 0:
        st.markdown("---")
        st.subheader("Distribución total del ingreso")
        
        # Preparamos los datos para el gráfico
        etiquetas = list(resumen_cat["categoria"])
        valores = list(resumen_cat["total"])
        
        total_gasto_real = sum(valores) # Usamos sum() nativo de Python para evitar errores
        ahorro_real = float(sueldo_actual) - total_gasto_real
        
        if ahorro_real > 0:
            etiquetas.append("Ahorro")
            valores.append(ahorro_real)
        
        fig = {
            "data": [{
                "labels": etiquetas,
                "values": valores,
                "type": "pie",
                "hole": .4, # Estilo Donut
                "textinfo": "label+percent"
            }],
            "layout": {"title": "Gastos vs Ahorro"}
        }
        st.plotly_chart(fig)

    # ---------------------------------------------------------
    # DETALLE POR CATEGORÍA (Oculto por defecto y sin decimales)
    # ---------------------------------------------------------
    if not resumen_cat.empty:
        st.markdown("---")
        st.subheader("🔍 Detalle por categoría")
        
        # Opción neutra para que no cargue nada al inicio
        opciones = ["Seleccione una categoría..."] + list(resumen_cat["categoria"].unique())
        categoria_sel = st.selectbox("¿De qué categoría quieres ver los gastos?", opciones)

        if categoria_sel != "Seleccione una categoría...":
            df_detalle = gastos_por_categoria(mes, anio, categoria_sel)
            
            if not df_detalle.empty:
                # Limpiamos decimales: convertimos a float y redondeamos a entero
                df_detalle["monto"] = df_detalle["monto"].astype(float).round(0).astype(int) #[cite: 39]
                
                # Mostramos la tabla optimizada
                st.dataframe(df_detalle, use_container_width=True, hide_index=True) #[cite: 43]
            else:
                st.warning("No hay registros para esta categoría.")

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

# --------------------------
# Sueldos
# --------------------------    

elif menu == "Sueldos":

    st.header("Actualizar sueldo")

    nuevo_sueldo = st.number_input("Nuevo sueldo", min_value=0.0)

    if st.button("Guardar nuevo sueldo"):
        guardar_sueldo(date.today(), nuevo_sueldo)
        st.success("Sueldo actualizado")