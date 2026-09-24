import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuración de la página
st.set_page_config(page_title="Salud Mental NL", layout="wide")

# Cargar datos
@st.cache_data
def load_data():
    # Obtener la ruta correcta del archivo
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'datos', '2024_2025_salud_mental.csv')
    
    df = pd.read_csv(csv_path)
    df = df.replace('sin valor', pd.NA)
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
    df['edad'] = pd.to_numeric(df['edad'], errors='coerce')
    
    # Convertir fecha a string para evitar errores de Arrow
    df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.stop()

# Título principal
st.title("🧠 Dashboard de Salud Mental - Nuevo León")
st.markdown("Análisis de consultas de salud mental por municipio")

# Sidebar
st.sidebar.header("Filtros")

municipio_seleccionado = st.sidebar.selectbox(
    'Municipio',
    ['Todos'] + list(df['municipio_unidad_medica'].unique())
)

if municipio_seleccionado == 'Todos':
    df_filtrado = df
else:
    df_filtrado = df[df['municipio_unidad_medica'] == municipio_seleccionado]

# KPIs principales
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Consultas", len(df_filtrado))
col2.metric("Municipios", df_filtrado['municipio_unidad_medica'].nunique())
col3.metric("Edad Promedio", f"{df_filtrado['edad'].mean():.1f} años")
col4.metric("% Femenino", f"{(df_filtrado['sexo'] == 'Femenino').sum() / len(df_filtrado) * 100:.1f}%")

# Gráficos principales
col1, col2 = st.columns(2)

# Distribución por género
fig_genero = px.pie(
    df_filtrado, 
    names='sexo', 
    title='Distribución por Género',
    color_discrete_sequence=['#FF69B4', '#4169E1', '#32CD32']
)
col1.plotly_chart(fig_genero, width='stretch')

# Distribución por edad
fig_edad = px.histogram(
    df_filtrado, 
    x='edad', 
    nbins=20,
    title='Distribución por Edad',
    color='sexo'
)
col2.plotly_chart(fig_edad, width='stretch')

# Análisis por municipio
st.subheader("Análisis por Municipio")

if municipio_seleccionado == 'Todos':
    # Comparación entre municipios
    municipio_stats = df.groupby('municipio_unidad_medica').agg({
        'edad': 'mean',
        'sexo': lambda x: (x == 'Femenino').sum() / len(x) * 100
    }).reset_index()
    municipio_stats.columns = ['municipio', 'edad_promedio', '%_femenino']
    
    fig_municipios = px.scatter(
        municipio_stats,
        x='%_femenino',
        y='edad_promedio',
        text='municipio',
        title='Municipios: Edad Promedio vs % Femenino',
        size=df.groupby('municipio_unidad_medica').size(),
        hover_name='municipio'
    )
    fig_municipios.update_traces(textposition='top center')
    st.plotly_chart(fig_municipios, width='stretch')
else:
    # Análisis detallado del municipio seleccionado
    col1, col2 = st.columns(2)
    
    # Top diagnósticos
    top_diagnosticos = df_filtrado['descripcion_enfermedad'].value_counts().head(10)
    fig_diagnosticos = px.bar(
        x=top_diagnosticos.values,
        y=top_diagnosticos.index,
        orientation='h',
        title='Top 10 Diagnósticos'
    )
    col1.plotly_chart(fig_diagnosticos, width='stretch')
    
    # Distribución por grupos de edad
    bins = [0, 12, 18, 25, 35, 50, 65, 100]
    labels = ['0-11', '12-17', '18-24', '25-34', '35-49', '50-64', '65+']
    df_filtrado = df_filtrado.copy()
    df_filtrado['grupo_edad'] = pd.cut(df_filtrado['edad'], bins=bins, labels=labels)
    
    fig_grupos = px.pie(
        df_filtrado['grupo_edad'].value_counts(),
        values=df_filtrado['grupo_edad'].value_counts().values,
        names=df_filtrado['grupo_edad'].value_counts().index,
        title='Distribución por Grupos de Edad'
    )
    col2.plotly_chart(fig_grupos, width='stretch')

# Tabla de datos detallados (sin la columna fecha problemática)
st.subheader("Datos Detallados")
columnas_mostrar = [col for col in df_filtrado.columns if col != 'fecha']
st.dataframe(df_filtrado[columnas_mostrar].describe())