import streamlit as st
import datetime
import calendar
import pandas as pd
from datetime import date
from models import Gasto
from database import crear_tabla, insertar_gasto
from analysis import resumen_por_categoria, resumen_mensual, evolucion_mensual, exportar_a_excel, ultimos_gastos, gastos_por_categoria, obtener_sueldo, guardar_sueldo
#Config pag

st.set_page_config(
    page_title="Money Saver",
    page_icon="assets/icon.png",
    layout="wide"
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

    # 1. Selección de fecha y obtención de sueldo
    col_fecha1, col_fecha2 = st.columns(2)
    with col_fecha1:
        anio = st.selectbox("Año", [2026], index=0)
        mes_nombre = st.selectbox("Mes", meses, index=mes_actual - 1)
        mes = meses.index(mes_nombre) + 1
        
        fecha_consulta = date(anio, mes, 1)
        sueldo_actual = obtener_sueldo(fecha_consulta)

    # Obtención de datos desde la base de datos
    resumen_cat = resumen_por_categoria(mes, anio)
    resumen_mes = resumen_mensual(mes, anio)

    if resumen_cat.empty:
        st.info("No hay datos para este mes.")
    else:
        # 2. Layout de tres columnas para la parte superior
        st.markdown("---")
        # 1. Definimos 4 columnas en lugar de 3. 
        # La segunda columna [0.5] servirá de "margen" o aire.
        # [Tabla, Espaciador, Estado, Gráfico]
        col_tabla, col_espacio, col_status, col_grafico = st.columns([1.1, 0.4, 1, 2.1])

        with col_tabla:
            st.subheader("Gasto por categoría")
            resumen_cat_fmt = resumen_cat.copy()
            resumen_cat_fmt["total"] = resumen_cat_fmt["total"].astype(float).round(0).astype(int)
            st.dataframe(resumen_cat_fmt, hide_index=True, use_container_width=True)

        with col_espacio:
            # Esta columna se queda vacía, funciona como un margen ajustable
            st.write("") 

        with col_status:
            st.subheader("Estado")
            total_gastado = float(resumen_mes.iloc[0]["total_mes"]) if not resumen_mes.empty and resumen_mes.iloc[0]["total_mes"] else 0.0

            if sueldo_actual is not None:
                sueldo_actual_f = float(sueldo_actual)
                st.metric("Sueldo", f"${sueldo_actual_f:,.0f}")
                st.metric("Total Gastado", f"${total_gastado:,.0f}")
                ahorro_mes = sueldo_actual_f - total_gastado
                st.metric("Ahorro", f"${ahorro_mes:,.0f}", delta=f"${ahorro_mes:,.0f}")

        with col_grafico:
            st.subheader("Distribución")
            
            # Preparación de datos para el gráfico
            etiquetas = list(resumen_cat["categoria"])
            valores = [float(v) for v in resumen_cat["total"]]
            
            # Cálculo del ahorro para el gráfico
            if sueldo_actual and float(sueldo_actual) > sum(valores):
                ahorro_grafico = float(sueldo_actual) - sum(valores)
                etiquetas.append("Ahorro")
                valores.append(ahorro_grafico)
            
            fig = {
                "data": [{
                    "labels": etiquetas,
                    "values": valores,
                    "type": "pie",
                    "hole": .4,
                    "textinfo": "label+percent"
                }],
                "layout": {"margin": dict(t=0, b=0, l=0, r=0), "height": 300}
            }
            st.plotly_chart(fig, use_container_width=True)

    # 3. Detalle por categoría al final (oculto por defecto y sin decimales)
    if not resumen_cat.empty:
        st.markdown("---")
        st.subheader("Detalle por categoría")
        
        opciones = ["Seleccionar categoría"] + list(resumen_cat["categoria"].unique())
        categoria_sel = st.selectbox("¿De qué categoría quieres ver los gastos?", opciones)

        if categoria_sel != "Seleccionar categoría":
            df_detalle = gastos_por_categoria(mes, anio, categoria_sel)
            
            if not df_detalle.empty:
                # Eliminación de los 4 ceros decimales (.0000) de PostgreSQL
                df_detalle["monto"] = df_detalle["monto"].astype(float).round(0).astype(int)
                st.dataframe(df_detalle, use_container_width=True, hide_index=True)
            else:
                st.warning("No hay registros detallados.")

# --------------------------
# ANALISIS
# --------------------------

elif menu == "Análisis":
    st.header("Análisis de Evolución Financiera")

    anio_analisis = st.selectbox("Seleccione el año para el análisis", [2024, 2025, 2026], index=2)

    # 1. Obtener datos base
    df_raw = evolucion_mensual(anio_analisis)

    if df_raw.empty:
        st.info(f"No hay datos registrados para el año {anio_analisis}.")
    else:
        # --- CORRECCIÓN AQUÍ: Pivotar para que las columnas sean solo números ---
        # Transformamos: mes, categoria, total -> Mes como índice, Categorías como columnas
        df_evolucion = df_raw.pivot(index="mes", columns="categoria", values="total").fillna(0)
        
        # Ahora el sum(axis=1) sumará solo los montos de cada categoría por mes
        gastos_mensuales = df_evolucion.sum(axis=1) 
        
        # 2. Calcular Ingresos y Ahorros por mes
        datos_analisis = []
        ahorro_acumulado = 0
        
        for mes_num in range(1, 13):
            # Obtener gasto del mes (ahora el índice es el número de mes)
            gasto_del_mes = gastos_mensuales.get(float(mes_num), 0.0)
            
            fecha_mes = date(anio_analisis, mes_num, 1)
            sueldo_mes = obtener_sueldo(fecha_mes)
            sueldo_mes = float(sueldo_mes) if sueldo_mes else 0.0
            
            if sueldo_mes > 0 or gasto_del_mes > 0:
                ahorro_mes = sueldo_mes - gasto_del_mes
                ahorro_acumulado += ahorro_mes
                
                datos_analisis.append({
                    "Mes": meses[mes_num-1],
                    "Ingresos": sueldo_mes,
                    "Gastos": gasto_del_mes,
                    "Ahorro": ahorro_mes,
                    "Ahorro Acumulado": ahorro_acumulado,
                    "Tasa de Ahorro (%)": (ahorro_mes / sueldo_mes * 100) if sueldo_mes > 0 else 0
                })

        df_analisis = pd.DataFrame(datos_analisis)

        # --------------------------
        # MÉTRICAS ANUALES (Resumen rápido)
        # --------------------------
        st.subheader(f"Resumen Anual {anio_analisis}")
        m1, m2, m3, m4 = st.columns(4)
        
        total_ahorrado_anio = df_analisis["Ahorro"].sum()
        promedio_ahorro_mensual = df_analisis["Ahorro"].mean()
        tasa_ahorro_promedio = df_analisis["Tasa de Ahorro (%)"].mean()

        m1.metric("Total Ahorrado", f"${total_ahorrado_anio:,.0f}")
        m2.metric("Promedio Mensual", f"${promedio_ahorro_mensual:,.0f}")
        m3.metric("Tasa de Ahorro Media", f"{tasa_ahorro_promedio:.1f}%")
        m4.metric("Ahorro Acumulado Final", f"${ahorro_acumulado:,.0f}")

        st.markdown("---")

        # --------------------------
        # GRÁFICOS
        # --------------------------
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("Gastos por Categoría")
            # Tu gráfico de barras original (mejorado)
            import plotly.graph_objects as go
            fig_bar = go.Figure()
            for cat in df_evolucion.columns:
                fig_bar.add_trace(go.Bar(
                    x=[meses[int(m)-1] for m in df_evolucion.index],
                    y=df_evolucion[cat],
                    name=cat
                ))
            fig_bar.update_layout(barmode='stack', height=400, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            st.subheader("Evolución del Ahorro Acumulado")
            # Nuevo gráfico de línea para el acumulado
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=df_analisis["Mes"],
                y=df_analisis["Ahorro Acumulado"],
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#2ecc71', width=3),
                name="Acumulado"
            ))
            fig_line.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_line, use_container_width=True)

        # --------------------------
        # TABLAS DE DATOS
        # --------------------------
        st.markdown("---")
        st.subheader("Tabla Comparativa Mensual")
        
        # Formatear la tabla para mostrar sin decimales y con separador de miles
        df_mostrar = df_analisis.copy()
        for col in ["Ingresos", "Gastos", "Ahorro", "Ahorro Acumulado"]:
            df_mostrar[col] = df_mostrar[col].apply(lambda x: f"${x:,.0f}")
        df_mostrar["Tasa de Ahorro (%)"] = df_mostrar["Tasa de Ahorro (%)"].apply(lambda x: f"{x:.1f}%")
        
        st.table(df_mostrar.set_index("Mes"))

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