import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Dashboard : Visualizacion de Datos Control de Tráfico",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS (MEJORADO PARA CONTRASTE) ---
st.markdown("""
<style>
    /* Fondo General más limpio */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Encabezados brillantes */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    
    /* Tarjetas de Métricas (KPIs) */
    div[data-testid="stMetric"] {
        background-color: #1a1c24;
        border: 1px solid #2d3748;
        padding: 15px;
        border-radius: 8px;
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #00E5FF;
        transform: scale(1.02);
    }
    
    label[data-testid="stMetricLabel"] {
        color: #a0aec0 !important; /* Gris claro */
        font-size: 14px !important;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 28px !important;
    }

    /* Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #1a1c24;
        border-radius: 5px;
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2d3748;
        color: #00E5FF !important;
        border-bottom-color: #00E5FF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES ---
def parse_sumo_xml(file):
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        data = []
        for trip in root.findall('tripinfo'):
            data.append({
                "id": trip.get('id'),
                "waitingTime": float(trip.get('waitingTime')),
                "timeLoss": float(trip.get('timeLoss')),
                "duration": float(trip.get('duration'))
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error al procesar XML: {e}")
        return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.header("📂 Carga de Datos")
st.sidebar.markdown("Sube los archivos `tripinfo.xml`:")
file_static = st.sidebar.file_uploader("1. Escenario Fijo (Rojo)", type=["xml"])
file_smart = st.sidebar.file_uploader("2. Escenario IA (Verde)", type=["xml"])

# --- HEADER ---
st.title("🚦 Análisis de Impacto: Control de Tráfico Adaptativo")
st.markdown("""
Esta herramienta compara el rendimiento del **Semáforo de Ciclo Fijo** (Convencional) contra el **Controlador De Gestion Vehicular** .
""")
st.divider()

if file_static and file_smart:
    # Procesamiento
    df_static = parse_sumo_xml(file_static)
    df_smart = parse_sumo_xml(file_smart)
    
    if not df_static.empty and not df_smart.empty:
        # Etiquetas y orden
        df_static['Sistema'] = 'Fijo (Convencional)'
        df_smart['Sistema'] = 'IA (Propuesto)'
        
        # Unir y ordenar por ID para gráficas temporales
        df_static = df_static.sort_values(by="id").reset_index(drop=True)
        df_smart = df_smart.sort_values(by="id").reset_index(drop=True)
        df_combined = pd.concat([df_static, df_smart])
        
        # --- 1. KPIs (RESUMEN EJECUTIVO) ---
        col1, col2, col3, col4 = st.columns(4)
        
        wait_fix = df_static['waitingTime'].mean()
        wait_ia = df_smart['waitingTime'].mean()
        delta_wait = ((wait_ia - wait_fix) / wait_fix) * 100
        
        loss_fix = df_static['timeLoss'].mean()
        loss_ia = df_smart['timeLoss'].mean()
        delta_loss = ((loss_ia - loss_fix) / loss_fix) * 100
        
        var_fix = df_static['waitingTime'].var()
        var_ia = df_smart['waitingTime'].var()
        delta_var = ((var_ia - var_fix) / var_fix) * 100
        
        autos_fix = len(df_static)
        autos_ia = len(df_smart)
        delta_autos = autos_ia - autos_fix

        col1.metric("⏳ Tiempo Espera (Promedio)", f"{wait_ia:.2f} s", f"{delta_wait:.1f}%", delta_color="inverse")
        col2.metric("🐢 Tiempo Perdido (Promedio)", f"{loss_ia:.2f} s", f"{delta_loss:.1f}%", delta_color="inverse")
        col3.metric("📊 Varianza (Estabilidad)", f"{var_ia:.0f}", f"{delta_var:.1f}%", delta_color="inverse")
        col4.metric("🚗 Flujo Vehicular", f"{autos_ia}", f"+{delta_autos} autos")

        # --- 2. GRÁFICA DE EVOLUCIÓN (MEJORADA) ---
        st.subheader("📈 Tendencia de Congestión en el Tiempo")
        
        # Suavizado (Media Móvil)
        window_size = 50
        df_static['SmoothWait'] = df_static['waitingTime'].rolling(window=window_size).mean()
        df_smart['SmoothWait'] = df_smart['waitingTime'].rolling(window=window_size).mean()
        
        fig_trend = go.Figure()
        
        # Línea Fijo (Rojo Brillante)
        fig_trend.add_trace(go.Scatter(
            y=df_static['SmoothWait'],
            mode='lines',
            name='Fijo (Convencional)',
            line=dict(color='#ff2b2b', width=3), 
            opacity=0.9
        ))
        
        # Línea IA (Verde Neón)
        fig_trend.add_trace(go.Scatter(
            y=df_smart['SmoothWait'],
            mode='lines',
            name='IA (Propuesto)',
            line=dict(color='#00ffbf', width=3),
            opacity=0.9
        ))

        # Configuración "Dark Mode" para Plotly
        fig_trend.update_layout(
            template="plotly_dark", 
            xaxis_title="Volumen de Vehículos (Secuencia de llegada)",
            yaxis_title="Tiempo de Espera (Media Móvil 50)",
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            font=dict(size=14, color="white"), # Letra blanca y grande
            height=450,
            margin=dict(l=40, r=40, t=40, b=40),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        # --- 3. DETALLES Y GRÁFICAS ADICIONALES ---
        col_stats, col_graphs = st.columns([0.35, 0.65])
        
        with col_stats:
            st.markdown("### 📋 Estadística Descriptiva")
            
            stats = []
            for name, df in [("Fijo", df_static), ("IA", df_smart)]:
                stats.append({
                    "Sistema": name,
                    "Media": df['waitingTime'].mean(),
                    "Desv.Std": df['waitingTime'].std(),
                    "Varianza": df['waitingTime'].var(),
                    "Máximo": df['waitingTime'].max()
                })
            
            df_table = pd.DataFrame(stats).set_index("Sistema")
            
            st.dataframe(
                df_table.style.format("{:.2f}")
                .background_gradient(cmap="RdYlGn_r", subset=["Media", "Desv.Std", "Varianza", "Máximo"]),
                use_container_width=True
            )
            
            # --- CAJA DE INTERPRETACIÓN DETALLADA (NUEVA) ---
            st.markdown("""
            <div style="background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #374151;">
                <h4 style="color: #ffffff; margin:0; padding-bottom:10px;">📖 Interpretación de Métricas</h4>
                <ul style="list-style-type: none; padding: 0; margin: 0;">
                    <li style="margin-bottom: 8px;">
                        <span style="color: #00E5FF; font-weight: bold;">Media (Promedio):</span><br>
                        <span style="color: #e0e0e0; font-size: 0.9em;">Eficiencia general del sistema. Cuanto más bajo, más rápido cruzan todos.</span>
                    </li>
                    <li style="margin-bottom: 8px;">
                        <span style="color: #00E5FF; font-weight: bold;">Desviación Estándar:</span><br>
                        <span style="color: #e0e0e0; font-size: 0.9em;">Indica qué tan variables son los tiempos. Si es baja, el tráfico es predecible.</span>
                    </li>
                    <li style="margin-bottom: 8px;">
                        <span style="color: #00E5FF; font-weight: bold;">Varianza:</span><br>
                        <span style="color: #e0e0e0; font-size: 0.9em;"><b>dato.</b> Representa la estabilidad (Robustez). La IA reduce esto drásticamente al evitar colas extremas.</span>
                    </li>
                    <li style="margin-bottom: 0px;">
                        <span style="color: #00E5FF; font-weight: bold;">Máximo:</span><br>
                        <span style="color: #e0e0e0; font-size: 0.9em;">El peor escenario vivido por un conductor. Muestra la capacidad de reacción ante saturación.</span>
                    </li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_graphs:
            st.markdown("### 🔎 Análisis Profundo")
            tab1, tab2, tab3 = st.tabs(["📊 Distribución", "📦 Dispersión", "📉 Curva Demora"])
            
            # --- TAB 1: HISTOGRAMA ---
            with tab1:
                fig_hist = px.histogram(
                    df_combined, x="waitingTime", color="Sistema", 
                    barmode="overlay", nbins=40, opacity=0.7,
                    color_discrete_map={'Fijo (Convencional)': '#ff2b2b', 'IA (Propuesto)': '#00ffbf'}
                )
                fig_hist.update_layout(
                    template="plotly_dark",
                    xaxis_title="Segundos de Espera",
                    yaxis_title="Frecuencia",
                    font=dict(color="white"),
                    legend=dict(orientation="h", y=1.15, font=dict(color="white")),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            # --- TAB 2: BOXPLOT ---
            with tab2:
                fig_box = px.box(
                    df_combined, x="Sistema", y="waitingTime", color="Sistema",
                    color_discrete_map={'Fijo (Convencional)': '#ff2b2b', 'IA (Propuesto)': '#00ffbf'},
                    points="outliers" 
                )
                fig_box.update_layout(
                    template="plotly_dark",
                    yaxis_title="Tiempo de Espera (s)",
                    font=dict(color="white"),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_box, use_container_width=True)

            # --- TAB 3: CURVA ACUMULADA ---
            with tab3:
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(y=df_static['waitingTime'], mode='lines', name='Fijo', line=dict(color='#ff2b2b', width=1)))
                fig_line.add_trace(go.Scatter(y=df_smart['waitingTime'], mode='lines', name='IA', line=dict(color='#00ffbf', width=1)))
                fig_line.update_layout(
                    template="plotly_dark",
                    xaxis_title="Vehículo N°", yaxis_title="Tiempo Espera (s)",
                    font=dict(color="white"),
                    legend=dict(orientation="h", y=1.15, font=dict(color="white")),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_line, use_container_width=True)

    else:
        st.warning("⚠️ Error en los archivos. Asegúrate de que no estén vacíos.")
else:
    # Pantalla de inicio
    st.info("👋 Sube los archivos XML en la barra lateral para ver el reporte.")
