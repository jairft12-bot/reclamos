import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =======================
# Configuración del archivo Excel
# =======================
EXCEL_PATH = r"C:\Users\HOME\Desktop\PROCESOS\jair.xlsx"
if not os.path.exists(EXCEL_PATH):
    st.error(f"No se encontró el archivo en: {EXCEL_PATH}")
    st.stop()

@st.cache_data
def load_data():
    return pd.read_excel(EXCEL_PATH, engine="openpyxl")

df = load_data()

# =======================
# Configuración página y tema oscuro
# =======================
st.set_page_config(layout="wide", page_title="Dashboard Clínica Viva")
tema_oscuro = st.sidebar.checkbox("Tema oscuro", value=False)
bg_color = "#1e1e1e" if tema_oscuro else "#ffffff"
text_color = "#ffffff" if tema_oscuro else "#3498db"
card_bg = "#2e2e2e" if tema_oscuro else "#ffffff"

# =======================
# Header con logo grande y título
# =======================
logo_path = r"C:\Users\HOME\Desktop\PROCESOS\logo.png"
header_col1, header_col2 = st.columns([1,6])

with header_col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)  # Logo grande

with header_col2:
    st.markdown(f"""
        <div style='display:flex; align-items:center; height:100%;'>
            <h1 style='color:{text_color}; margin:0;'>📊 Dashboard de Reclamos - Clínica Viva</h1>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"<hr style='border:2px solid {text_color}'>", unsafe_allow_html=True)

# =======================
# Sidebar filtros (corregido)
# =======================
st.sidebar.header("Filtros")

def filtro(columna, nombre):
    if columna in df.columns:
        # Solo valores únicos, limpios y ordenados
        valores_unicos = df[columna].dropna().astype(str).str.strip().unique()
        valores_unicos.sort()
        return st.sidebar.selectbox(
            nombre,
            ["Todos"] + list(valores_unicos)
        )
    return "Todos"

estado_final = filtro("ESTADO FINAL", "Estado Final")
dni = filtro("DOCUMENTO", "Documento")
paciente = filtro("PACIENTE", "Paciente")
canal = filtro("CANALES DE ATENCIÓN", "Canal de Atención")

# Filtro por fecha
if "FECHA DEL INCIDENTE" in df.columns:
    fecha_inicio, fecha_fin = st.sidebar.date_input(
        "Rango de Fecha del Incidente",
        value=[df["FECHA DEL INCIDENTE"].min().date(), df["FECHA DEL INCIDENTE"].max().date()]
    )

# =======================
# Filtrar dataset
# =======================
df_filtered = df.copy()
if estado_final != "Todos": df_filtered = df_filtered[df_filtered["ESTADO FINAL"].str.strip() == estado_final]
if dni != "Todos": df_filtered = df_filtered[df_filtered["DOCUMENTO"].astype(str).str.strip() == dni]
if paciente != "Todos": df_filtered = df_filtered[df_filtered["PACIENTE"].astype(str).str.strip() == paciente]
if canal != "Todos": df_filtered = df_filtered[df_filtered["CANALES DE ATENCIÓN"].astype(str).str.strip() == canal]
if "FECHA DEL INCIDENTE" in df.columns:
    df_filtered = df_filtered[(df_filtered["FECHA DEL INCIDENTE"] >= pd.to_datetime(fecha_inicio)) &
                              (df_filtered["FECHA DEL INCIDENTE"] <= pd.to_datetime(fecha_fin))]

# =======================
# KPIs dinámicos
# =======================
total_casos = len(df_filtered)
total_cerrados = (df_filtered["ESTADO FINAL"].str.upper()=="CERRADA").sum() if "ESTADO FINAL" in df_filtered.columns else 0
total_activos = (df_filtered["ESTADO FINAL"].str.upper()=="ACTIVA").sum() if "ESTADO FINAL" in df_filtered.columns else 0
porc_cerrados = total_cerrados/total_casos*100 if total_casos>0 else 0
porc_activos = total_activos/total_casos*100 if total_casos>0 else 0

if "TIEMPO DE RESPUESTA(DIAS)" in df_filtered.columns:
    tiempos = pd.to_numeric(df_filtered["TIEMPO DE RESPUESTA(DIAS)"], errors="coerce").dropna()
    tiempo_promedio = tiempos.mean() if not tiempos.empty else 0
else:
    tiempo_promedio = 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📌 Total Casos", f"{total_casos}", "")
col2.metric("✅ Casos Cerrados", f"{total_cerrados}", f"{porc_cerrados:.0f}%")
col3.metric("🕒 Casos Activos", f"{total_activos}", f"{porc_activos:.0f}%")
col4.metric("⚖️ % Cerrados vs Activos", f"{porc_cerrados:.0f}% / {porc_activos:.0f}%", "")
col5.metric("⏳ Tiempo Promedio de Resolución (días)", f"{tiempo_promedio:.1f}")

# =======================
# Función para gráficos
# =======================
def chart_card(title, fig):
    st.markdown(f"<div style='border-radius:15px;padding:15px;background:{card_bg};box-shadow:0 4px 15px rgba(0,0,0,0.1);margin-bottom:15px;'>"
                f"<h3 style='color:{text_color};text-align:center;'>{title}</h3>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =======================
# Fila 1: Estado Final, Canales, Documento
# =======================
fila1 = st.columns(3)

with fila1[0]:
    if "ESTADO FINAL" in df_filtered.columns:
        fig_estado = px.histogram(df_filtered, x="ESTADO FINAL", color="ESTADO FINAL",
                                  color_discrete_map={"CERRADA":"green","ACTIVA":"orange"},
                                  text_auto=True, labels={"ESTADO FINAL":"Estado Final"})
        fig_estado.update_layout(paper_bgcolor=bg_color, plot_bgcolor=bg_color, font_color=text_color)
        chart_card("📊 Casos por Estado Final", fig_estado)

with fila1[1]:
    if "CANALES DE ATENCIÓN" in df_filtered.columns:
        df_canal = df_filtered["CANALES DE ATENCIÓN"].value_counts().reset_index()
        df_canal.columns = ["CANALES DE ATENCIÓN","COUNT"]
        fig_canal = px.bar(df_canal, x="CANALES DE ATENCIÓN", y="COUNT", text="COUNT",
                           labels={"CANALES DE ATENCIÓN":"Canal","COUNT":"Cantidad"},
                           color="COUNT", color_continuous_scale="Blues")
        fig_canal.update_layout(paper_bgcolor=bg_color, plot_bgcolor=bg_color, font_color=text_color)
        chart_card("📞 Canales de Atención", fig_canal)

with fila1[2]:
    if "TIPO DE DOCUMENTO" in df_filtered.columns:
        df_doc = df_filtered["TIPO DE DOCUMENTO"].value_counts().reset_index()
        df_doc.columns = ["DOCUMENTO","COUNT"]
        fig_doc = px.bar(df_doc, x="DOCUMENTO", y="COUNT", text="COUNT",
                         labels={"DOCUMENTO":"Tipo","COUNT":"Cantidad"})
        fig_doc.update_layout(paper_bgcolor=bg_color, plot_bgcolor=bg_color, font_color=text_color)
        chart_card("🪪 Distribución por Documento", fig_doc)

# =======================
# Fila 2: Tiempo de Respuesta
# =======================
fila2 = st.columns(2)

with fila2[0]:
    if "TIEMPO DE RESPUESTA(DIAS)" in df_filtered.columns and not tiempos.empty:
        fig_hist = px.histogram(tiempos, nbins=20, labels={"value":"Días"}, color_discrete_sequence=["#3498db"])
        fig_hist.update_layout(paper_bgcolor=bg_color, plot_bgcolor=bg_color, font_color=text_color)
        chart_card("⏱️ Distribución de Tiempos de Respuesta", fig_hist)

with fila2[1]:
    if "TIEMPO DE RESPUESTA(DIAS)" in df_filtered.columns and not tiempos.empty:
        df_freq = tiempos.value_counts().reset_index()
        df_freq.columns = ["Días","Cantidad"]
        df_freq = df_freq.sort_values("Días")
        fig_bar = px.bar(df_freq, x="Días", y="Cantidad", text="Cantidad", color="Cantidad",
                         color_continuous_scale="Oranges")
        fig_bar.update_layout(paper_bgcolor=bg_color, plot_bgcolor=bg_color, font_color=text_color)
        chart_card("📊 Reclamos por Tiempo de Respuesta", fig_bar)

# =======================
# Fila 3: Pie Grupo de Días
# =======================
if "TIEMPO DE RESPUESTA(DIAS)" in df_filtered.columns and not tiempos.empty:
    grupos = pd.cut(tiempos, bins=[-1,3,15,float("inf")], labels=["<4 días","4-15 días",">15 días"])
    df_grupos = grupos.value_counts().reset_index()
    df_grupos.columns = ["Grupo","Cantidad"]
    fig_pie = px.pie(df_grupos, names="Grupo", values="Cantidad", hole=0.4,
                     color_discrete_sequence=["#3498db","#f39c12","#e74c3c"])
    fig_pie.update_traces(textinfo="percent+label", marker=dict(line=dict(color=bg_color, width=2)))
    fig_pie.update_layout(paper_bgcolor=bg_color, plot_bgcolor=bg_color, font_color=text_color)
    chart_card("📌 Reclamos por Grupo de Días", fig_pie)
   # =======================
# Evolución de Reclamos por Mes (área azul + línea amarilla)
# =======================
if "FECHA DEL INCIDENTE" in df_filtered.columns and "ESTADO FINAL" in df_filtered.columns:
    df_filtered['FECHA DEL INCIDENTE'] = pd.to_datetime(df_filtered['FECHA DEL INCIDENTE'])
    
    # Agrupar por mes y estado
    df_grouped = df_filtered.groupby([df_filtered['FECHA DEL INCIDENTE'].dt.to_period('M'), 'ESTADO FINAL']).size().reset_index(name='Cantidad')
    df_grouped['FECHA_DEL_INCIDENTE'] = df_grouped['FECHA DEL INCIDENTE'].dt.to_timestamp()

    # Separar por estado y eliminar meses sin reclamos
    df_cerrada = df_grouped[df_grouped['ESTADO FINAL'] == 'CERRADA']
    df_activa  = df_grouped[df_grouped['ESTADO FINAL'] == 'ACTIVA']

    # Crear figura vacía
    import plotly.graph_objects as go
    fig_time = go.Figure()

    # Área azul (CERRADA)
    fig_time.add_trace(go.Scatter(
        x=df_cerrada['FECHA_DEL_INCIDENTE'],
        y=df_cerrada['Cantidad'],
        mode='lines+markers',
        name='CERRADA',
        line=dict(color='#1f77b4', width=4, shape='spline'),
        marker=dict(size=10, line=dict(width=2, color='white')),
        fill='tozeroy',  # área sombreada
        hovertemplate='%{x|%b %Y}: %{y} reclamos<extra></extra>'
    ))

    # Línea amarilla (ACTIVA) solo donde hay reclamos
    fig_time.add_trace(go.Scatter(
        x=df_activa['FECHA_DEL_INCIDENTE'],
        y=df_activa['Cantidad'],
        mode='lines+markers',
        name='ACTIVA',
        line=dict(color='#ffcc00', width=4, shape='spline'),
        marker=dict(size=10, line=dict(width=2, color='white')),
        hovertemplate='%{x|%b %Y}: %{y} reclamos<extra></extra>'
    ))

    # Layout estilo presentación ejecutiva
    fig_time.update_layout(
        title='📈 Evolución de Reclamos por Mes',
        title_x=0.5,
        title_font_size=20,
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(family='Arial, sans-serif', size=12, color=text_color),
        xaxis=dict(showgrid=False, showline=True, linecolor=text_color, tickfont=dict(size=12, color=text_color)),
        yaxis=dict(showgrid=False, showline=True, linecolor=text_color, tickfont=dict(size=12, color=text_color), rangemode='tozero'),
        legend=dict(title='Estado Final', title_font=dict(size=14), font=dict(size=12)),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    chart_card("📈 Evolución de Reclamos por Mes", fig_time)
