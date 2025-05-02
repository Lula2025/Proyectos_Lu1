import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

# --- Configuración inicial de la página ---
st.set_page_config(
    page_title="Dashboard Bitácoras Agronómicas",
    page_icon="🌾",
    layout="wide"
)

# --- Leer el archivo ZIP ---
archivo_zip = "Archivos.zip"
nombre_csv = "Datos_Historicos_cuenta_al26032025.csv"

try:
    with zipfile.ZipFile(archivo_zip, 'r') as z:
        with z.open(nombre_csv) as f:
            datos = pd.read_csv(f)
    st.success("Información basada en e-A. Bitácoras agronómicas 2012_1er Trimestre 2025 ")
except FileNotFoundError:
    st.error(f"Error: El archivo '{archivo_zip}' no se encontró.")
    st.stop()
except KeyError:
    st.error(f"Error: El archivo '{nombre_csv}' no está dentro del ZIP.")
    st.stop()

# --- Mostrar encabezado con imágenes ---
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    st.image("assets/cimmyt.png", use_container_width=True)
with col3:
    st.image("assets/ea.png", use_container_width=True)

# --- Preprocesamiento ---
columnas_requeridas = [
    "Anio", "Categoria_Proyecto", "Ciclo", "Estado",
    "Tipo_Regimen_Hidrico", "Tipo_parcela", "Area_total_de_la_parcela(ha)"
]
for columna in columnas_requeridas:
    if columna not in datos.columns:
        st.error(f"La columna '{columna}' no existe en el archivo CSV.")
        st.stop()

datos[columnas_requeridas] = datos[columnas_requeridas].fillna("NA")
datos["Anio"] = pd.to_numeric(datos["Anio"], errors="coerce")
datos["Area_total_de_la_parcela(ha)"] = pd.to_numeric(
    datos["Area_total_de_la_parcela(ha)"], errors="coerce"
).fillna(0)
datos = datos[(datos["Anio"] >= 2012) & (datos["Anio"] <= 2025)]

# --- Función para filtros multiselección ---
def filtro_multiselect(nombre_columna, etiqueta):
    opciones = sorted(datos[nombre_columna].unique())
    seleccion = st.sidebar.multiselect(
        etiqueta,
        options=opciones,
        default=opciones
    )
    if not seleccion:
        seleccion = opciones
    return seleccion

# --- Sidebar de filtros ---
st.sidebar.header("🎯 Filtros")
categoria = filtro_multiselect("Categoria_Proyecto", "Categoría del Proyecto")
ciclo = filtro_multiselect("Ciclo", "Ciclo")
tipo_parcela = filtro_multiselect("Tipo_parcela", "Tipo de Parcela")
estado = filtro_multiselect("Estado", "Estado")
regimen = filtro_multiselect("Tipo_Regimen_Hidrico", "Régimen Hídrico")

# --- Aplicar filtros ---
datos_filtrados = datos[
    datos["Categoria_Proyecto"].isin(categoria) &
    datos["Ciclo"].isin(ciclo) &
    datos["Tipo_parcela"].isin(tipo_parcela) &
    datos["Estado"].isin(estado) &
    datos["Tipo_Regimen_Hidrico"].isin(regimen)
]

# --- Título Principal ---
st.title("🌾 Dashboard Bitácoras Agronómicas 2012-2025")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Bitácoras Registradas", f"{datos_filtrados.shape[0]:,}")
with col2:
    st.metric("Área Total (ha)", f"{datos_filtrados['Area_total_de_la_parcela(ha)'].sum():,.2f} ha")
with col3:
    if "Id_Productor" in datos_filtrados.columns:
        st.metric("Productores", f"{datos_filtrados['Id_Productor'].nunique():,}")
with col4:
    if "Id_Parcela(Unico)" in datos_filtrados.columns:
        st.metric("Parcelas", f"{datos_filtrados['Id_Parcela(Unico)'].nunique():,}")

st.markdown("---")

# --- Gráficas principales ---
col5, col6 = st.columns(2)
with col5:
    fig = px.bar(datos_filtrados.groupby("Anio").size().reset_index(name="Bitácoras"),
                 x="Anio", y="Bitácoras", title="📋 Número de Bitácoras por Año",
                 color_discrete_sequence=["#1f77b4"])
    st.plotly_chart(fig, use_container_width=True)

with col6:
    fig = px.bar(datos_filtrados.groupby("Anio")["Area_total_de_la_parcela(ha)"].sum().reset_index(),
                 x="Anio", y="Area_total_de_la_parcela(ha)",
                 title="🌿 Área Total de Parcelas por Año",
                 labels={"Area_total_de_la_parcela(ha)": "Área (ha)"},
                 color_discrete_sequence=["#2ca02c"])
    st.plotly_chart(fig, use_container_width=True)

col7, col8 = st.columns(2)
with col7:
    if "Id_Parcela(Unico)" in datos_filtrados.columns:
        fig = px.bar(datos_filtrados.groupby("Anio")["Id_Parcela(Unico)"].nunique().reset_index(),
                     x="Anio", y="Id_Parcela(Unico)",
                     title="🌄 Número de Parcelas por Año",
                     labels={"Id_Parcela(Unico)": "Parcelas"},
                     color_discrete_sequence=["#9467bd"])
        st.plotly_chart(fig, use_container_width=True)
with col8:
    if "Id_Productor" in datos_filtrados.columns:
        fig = px.bar(datos_filtrados.groupby("Anio")["Id_Productor"].nunique().reset_index(),
                     x="Anio", y="Id_Productor",
                     title="👩‍🌾👨‍🌾 Número de Productores por Año",
                     labels={"Id_Productor": "Productores"},
                     color_discrete_sequence=["#ff7f0e"])
        st.plotly_chart(fig, use_container_width=True)

if "Genero" in datos_filtrados.columns:
    st.markdown("---")
    categorias_genero = ["Masculino", "Femenino", "NA.."]
    datos_genero = datos_filtrados.groupby("Genero").size().reset_index(name="Registros")
    datos_genero = datos_genero.set_index("Genero").reindex(categorias_genero, fill_value=0).reset_index()
    total_registros = datos_genero["Registros"].sum()
    datos_genero["Porcentaje"] = (datos_genero["Registros"] / total_registros * 100) if total_registros > 0 else 0
    color_map_genero = {"Masculino": "#2ca02c", "Femenino": "#ff7f0e", "NA..": "#F0F0F0"}
    fig = px.pie(datos_genero, names="Genero", values="Porcentaje",
                 title="👩👨 Distribución de productores(as) (%) por Género",
                 color="Genero", color_discrete_map=color_map_genero)
    fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
    st.plotly_chart(fig, use_container_width=True)
