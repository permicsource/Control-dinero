import streamlit as st
import datetime
import calendar
import pandas as pd
from datetime import date
from models import Gasto, IngresoExtra
from database import crear_tabla, insertar_gasto, insertar_ingreso_extra, insertar_distribucion
from analysis import (resumen_por_categoria,
                      resumen_mensual,
                      evolucion_mensual,
                      exportar_a_excel,
                      ultimos_gastos,
                      gastos_por_categoria,
                      obtener_sueldo,
                      guardar_sueldo,
                      obtener_ingresos_extra,
                      obtener_distribucion,
                      periodo_distribuido,
                      obtener_sueldo_,
                      obtener_ingresos_extra_,
                      obtener_gastos_mes_,
                      obtener_ahorro_mes_
                      )

#Config pag
#_


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
    ["Agregar gasto", "Resumen mensual", "Análisis", "Exportar a Excel", "Ingresos", "Distribución ahorro"]
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
        monto = st.number_input("Monto", min_value=0, step=100, format="%d")

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
# RESUMEN MENSUAL
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
        sueldo_actual_f = float(sueldo_actual)
        df_ingresos = obtener_ingresos_extra(mes, anio)

        ingresos_extra = (
            float(df_ingresos.iloc[0]["total"])
            if not df_ingresos.empty
            and df_ingresos.iloc[0]["total"] is not None
            else 0.0
        )

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
        col_tabla, col_espacio, col_status, col_grafico = st.columns([1.1, 0.3, 1, 2.1])

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
            total_ingresos = sueldo_actual_f + ingresos_extra
            ahorro_mes = total_ingresos - total_gastado

            if sueldo_actual is not None:
                st.metric("Sueldo", f"${sueldo_actual_f:,.0f}")
                st.metric("Ingresos extra", f"${ingresos_extra:,.0f}")
                st.metric("Total Gastado", f"${total_gastado:,.0f}")
                st.metric("Ahorro", f"${ahorro_mes:,.0f}", delta=f"${ahorro_mes:,.0f}")

        with col_grafico:
            st.subheader("Distribución")
            
            # Preparación de datos para el gráfico
            etiquetas = list(resumen_cat["categoria"])
            valores = [float(v) for v in resumen_cat["total"]]
            
            # Cálculo del ahorro para el gráfico
            if total_ingresos > sum(valores):
                ahorro_grafico = total_ingresos - sum(valores)
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
        categoria_sel = st.selectbox(" ", opciones)

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

    anio_analisis = st.selectbox(" ", [2024, 2025, 2026], index=2)

    df_raw = evolucion_mensual(anio_analisis)

    if df_raw.empty:
        st.info(f"No hay datos registrados para el año {anio_analisis}.")
    else:
        df_evolucion = df_raw.pivot(index="mes", columns="categoria", values="total").fillna(0)
        gastos_mensuales = df_evolucion.sum(axis=1) 
        
        datos_analisis = []
        ahorro_acumulado = 0
        
        # --- FILTRO DE RANGO DE MESES (SÓLO MESES CERRADOS Y DESDE EL INICIO REAL) ---
        if anio_analisis == anio_actual:
            meses_a_procesar = mes_actual - 1  # Hasta el mes anterior cerrado
            # CORRECCIÓN: Si es 2026, empezamos en Marzo (3). Si no, en Enero (1).
            mes_inicio = 3 if anio_analisis == 2026 else 1 
        elif anio_analisis < anio_actual:
            meses_a_procesar = 12
            mes_inicio = 1
        else:
            meses_a_procesar = 0
            mes_inicio = 1

        # El bucle ahora inicia en 'mes_inicio' en lugar de fijarse siempre en 1
        for mes_num in range(mes_inicio, meses_a_procesar + 1):
            gasto_del_mes = gastos_mensuales.get(float(mes_num), 0.0)
            
            fecha_mes = date(anio_analisis, mes_num, 1)
            sueldo_mes = obtener_sueldo(fecha_mes)
            sueldo_mes = float(sueldo_mes) if sueldo_mes else 0.0

            df_ingresos = obtener_ingresos_extra(mes_num, anio_analisis)

            ingresos_extra = (
                float(df_ingresos.iloc[0]["total"])
                if not df_ingresos.empty
                and df_ingresos.iloc[0]["total"] is not None
                else 0.0
            )

            total_ingresos = sueldo_mes + ingresos_extra

            ahorro_mes = total_ingresos - gasto_del_mes
            ahorro_acumulado += ahorro_mes
            
            datos_analisis.append({
                "Mes": meses[mes_num-1],
                "Ingresos totales": total_ingresos,
                "Sueldo": sueldo_mes,
                "Gastos": gasto_del_mes,
                "Ingresos extra": ingresos_extra,
                "Ahorro": ahorro_mes,
                "Ahorro Acumulado": ahorro_acumulado,
                "Tasa de Ahorro (%)": (ahorro_mes / total_ingresos * 100) if total_ingresos > 0 else 0
            })

        if not datos_analisis:
            st.warning("No hay meses completamente terminados para mostrar en este periodo todavía.")
        else:
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
        for col in ["Ingresos totales", "Sueldo", "Ingresos extra", "Gastos", "Ahorro", "Ahorro Acumulado"]:
            df_mostrar[col] = df_mostrar[col].apply(lambda x: f"${x:,.0f}")
        df_mostrar["Tasa de Ahorro (%)"] = df_mostrar["Tasa de Ahorro (%)"].apply(lambda x: f"{x:.1f}%")
        
        st.table(df_mostrar.set_index("Mes"))


        # =====================================================================
        # PROYECCIÓN DE AHORRO
        # =====================================================================
        st.markdown("---")
        st.subheader("Proyección Financiera")
        
        st.markdown(
            f"Ahorro promedio mensual actual: "
            f"**${promedio_ahorro_mensual:,.0f}**.  "
        )

        # Slider interactivo para seleccionar de 1 a 60 meses (5 años)
        meses_proyeccion = st.slider("Proyección:", min_value=1, max_value=60, value=12, step=1)

        # Cálculos predictivos lineales
        nuevo_ahorro_proyectado = promedio_ahorro_mensual * meses_proyeccion
        patrimonio_total_estimado = ahorro_acumulado + nuevo_ahorro_proyectado

        # Visualización de métricas estimadas
        col_p1, col_p2, col_p3 = st.columns(3)
        
        col_p1.metric(
            label=f"Ahorro Nuevo Est. ({meses_proyeccion} meses)", 
            value=f"${nuevo_ahorro_proyectado:,.0f}"
        )
        col_p2.metric(
            label="Tu Base Actual", 
            value=f"${ahorro_acumulado:,.0f}",
            help="Este es el total acumulado real que llevas guardado hasta el último mes cerrado."
        )
        col_p3.metric(
            label="Total Estimado Final", 
            value=f"${patrimonio_total_estimado:,.0f}",
            help="La suma de lo que ya tienes hoy más el ahorro proyectado."
        )
# --------------------------
# DISTRIBUCIÓN DE AHORRO
# --------------------------

elif menu == "Distribución ahorro":

    st.header("Distribución ahorro")

    st.subheader("Seleccionar período")

    anio = st.selectbox(
        "Año",
        [2026, 2027],
        index=0
    )

    mes = st.selectbox("Mes", meses)

    mes_numero = meses.index(mes) + 1

    periodo = date(anio, mes_numero, 1)

    if periodo_distribuido(periodo):

        st.success("Este mes ya fue distribuido.")

        st.dataframe(
            obtener_distribucion(periodo),
            use_container_width=True
        )

        st.stop()

    ingresos, gastos, ahorro = obtener_ahorro_mes_(mes_numero, anio)

    st.subheader("Resumen del mes")

    col1, col2, col3 = st.columns(3)

    col1.metric("Ingresos", f"${ingresos:,.0f}")
    col2.metric("Gastos", f"${gastos:,.0f}")
    col3.metric("Ahorro disponible", f"${ahorro:,.0f}")

    if ahorro <= 0:

        st.warning("No existe ahorro disponible para distribuir.")

        st.stop()

    categorias = [
        "Largo plazo",
        "Fondo emergencia",
        "Bicicleta",
        "Botas Montaña",
        "Magister"
    ]

    st.subheader("Distribución del ahorro")

    distribucion = {}

    for categoria in categorias:

        monto = st.number_input(
            categoria,
            min_value=0,
            value=0,
            step=1000,
            key=f"dist_{categoria}"
        )

        distribucion[categoria] = monto

    total_distribuido = sum(distribucion.values())

    st.metric(
        "Total distribuido",
        f"${total_distribuido:,.0f}"
    )

    diferencia = ahorro - total_distribuido

    if diferencia > 0:

        st.warning(
            f"Faltan ${diferencia:,.0f} por distribuir."
        )

    elif diferencia < 0:

        st.error(
            f"Te excediste en ${abs(diferencia):,.0f}."
        )

    else:

        st.success("Distribución completa.")


    guardar = st.button(
        "Guardar distribución",
        disabled=(diferencia != 0)
    )

    if guardar:

        insertar_distribucion(
            periodo,
            distribucion
        )

        st.success("Distribución guardada correctamente.")

        st.rerun()

# --------------------------
# EXPORTAR
# --------------------------
elif menu == "Exportar a Excel":

    st.header("Exportar datos")

    excel = exportar_a_excel()

    st.download_button(
        label="📥 Descargar Excel",
        data=excel,
        file_name=f"reporte_finanzas_{hoy}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --------------------------
# Ingresos
# --------------------------    

elif menu == "Ingresos":

    st.header("Ingresos")

    nuevo_sueldo = st.number_input("Nuevo sueldo", min_value=0, format="%d")

    if st.button("Guardar nuevo sueldo"):
        guardar_sueldo(date.today(), nuevo_sueldo)
        st.success("Sueldo actualizado")

    st.divider()

    st.subheader("Agregar ingreso extra")

    with st.form("form_ingreso"):

        fecha = st.date_input(
            "Fecha",
            value=date.today(),
            key="fecha_ingreso"
        )

        tipo = st.selectbox(
            "Tipo",
            [
                "Bono",
                "Reembolso",
                "Interés",
                "Otro"
            ]
        )

        descripcion = st.text_input("Descripción")

        monto = st.number_input(
            "Monto",
            min_value=0,
            step=1000,
            key="monto_ingreso",
            format="%d"
        )

        submitted = st.form_submit_button("Guardar ingreso")

        if submitted:

            ingreso = IngresoExtra(fecha, tipo, descripcion, monto)
            insertar_ingreso_extra(ingreso)
            
            st.success("Ingreso guardado correctamente")