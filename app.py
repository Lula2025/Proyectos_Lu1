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

# --- Sidebar de filtros ---
st.sidebar.header("🎯 Filtros")

categoria = st.sidebar.selectbox(
    "Categoría del Proyecto",
    options=["Todos"] + list(datos["Categoria_Proyecto"].unique())
)

ciclo = st.sidebar.selectbox(
    "Ciclo",
    options=["Todos"] + list(datos["Ciclo"].unique())
)

tipo_parcela = st.sidebar.selectbox(
    "Tipo de Parcela",
    options=["Todos"] + list(datos["Tipo_parcela"].unique())
)

estado = st.sidebar.selectbox(
    "Estado",
    options=["Todos"] + list(datos["Estado"].unique())
)

regimen = st.sidebar.selectbox(
    "Régimen Hídrico",
    options=["Todos"] + list(datos["Tipo_Regimen_Hidrico"].unique())
)

# --- Filtrado de datos según selecciones ---
datos_filtrados = datos.copy()

if categoria != "Todos":
    datos_filtrados = datos_filtrados[datos_filtrados["Categoria_Proyecto"] == categoria]
if ciclo != "Todos":
    datos_filtrados = datos_filtrados[datos_filtrados["Ciclo"] == ciclo]
if tipo_parcela != "Todos":
    datos_filtrados = datos_filtrados[datos_filtrados["Tipo_parcela"] == tipo_parcela]
if estado != "Todos":
    datos_filtrados = datos_filtrados[datos_filtrados["Estado"] == estado]
if regimen != "Todos":
    datos_filtrados = datos_filtrados[datos_filtrados["Tipo_Regimen_Hidrico"] == regimen]

# --- Título Principal ---
st.title("🌾 Dashboard Bitácoras Agronómicas 2012-2025")

# --- KPIs (tarjetas principales) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Bitácoras Registradas",
        value=f"{datos_filtrados.shape[0]:,}"
    )

with col2:
    st.metric(
        label="Área Total (ha)",
        value=f"{datos_filtrados['Area_total_de_la_parcela(ha)'].sum():,.2f} ha"
    )

with col3:
    if "Id_Productor" in datos_filtrados.columns:
        productores_unicos = datos_filtrados["Id_Productor"].nunique()
        st.metric(
            label="Productores",
            value=f"{productores_unicos:,}"
        )

with col4:
    if "Id_Parcela(Unico)" in datos_filtrados.columns:
        parcelas_unicas = datos_filtrados["Id_Parcela(Unico)"].nunique()
        st.metric(
            label="Parcelas",
            value=f"{parcelas_unicas:,}"
        )

st.markdown("---")

# --- Gráficas principales en dos filas ---
# Fila 1
col5, col6 = st.columns(2)

with col5:
    bitacoras_por_anio = datos_filtrados.groupby("Anio").size().reset_index(name="Bitácoras")
    fig_bitacoras = px.bar(
        bitacoras_por_anio,
        x="Anio",
        y="Bitácoras",
        title="📋 Número de Bitácoras por Año",
        color_discrete_sequence=["#1f77b4"]
    )
    st.plotly_chart(fig_bitacoras, use_container_width=True)

with col6:
    area_por_anio = datos_filtrados.groupby("Anio")["Area_total_de_la_parcela(ha)"].sum().reset_index()
    fig_area = px.bar(
        area_por_anio,
        x="Anio",
        y="Area_total_de_la_parcela(ha)",
        title="🌿 Área Total de Parcelas por Año",
        labels={"Area_total_de_la_parcela(ha)": "Área (ha)"},
        color_discrete_sequence=["#2ca02c"]
    )
    st.plotly_chart(fig_area, use_container_width=True)

# Fila 2
col7, col8 = st.columns(2)

with col7:
    if "Id_Parcela(Unico)" in datos_filtrados.columns:
        parcelas_por_anio = datos_filtrados.groupby("Anio")["Id_Parcela(Unico)"].nunique().reset_index()
        fig_parcelas = px.bar(
            parcelas_por_anio,
            x="Anio",
            y="Id_Parcela(Unico)",
            title="🌄 Número de Parcelas por Año",
            labels={"Id_Parcela(Unico)": "Parcelas"},
            color_discrete_sequence=["#9467bd"]
        )
        st.plotly_chart(fig_parcelas, use_container_width=True)

with col8:
    if "Id_Productor" in datos_filtrados.columns:
        productores_por_anio = datos_filtrados.groupby("Anio")["Id_Productor"].nunique().reset_index()
        fig_productores = px.bar(
            productores_por_anio,
            x="Anio",
            y="Id_Productor",
            title="👩‍🌾👨‍🌾 Número de Productores por Año",
            labels={"Id_Productor": "Productores"},
            color_discrete_sequence=["#ff7f0e"]
        )
        st.plotly_chart(fig_productores, use_container_width=True)

# Fila 3 (Distribución de género)
if "Genero" in datos_filtrados.columns:
    st.markdown("---")
    
    categorias_genero = ["Masculino", "Femenino", "NA.."]

    datos_genero = datos_filtrados.groupby("Genero").size().reset_index(name="Registros")
    datos_genero = datos_genero.set_index("Genero").reindex(categorias_genero, fill_value=0).reset_index()

    total_registros = datos_genero["Registros"].sum()
if "Genero" in datos_filtrados.columns:
    st.markdown("---")
    
    categorias_genero = ["Masculino", "Femenino", "NA.."]

    datos_genero = datos_filtrados.groupby("Genero").size().reset_index(name="Registros")
    datos_genero = datos_genero.set_index("Genero").reindex(categorias_genero, fill_value=0).reset_index()

    total_registros = datos_genero["Registros"].sum()
    if total_registros > 0:
        datos_genero["Porcentaje"] = (datos_genero["Registros"] / total_registros) * 100
    else:
        datos_genero["Porcentaje"] = 0

    color_map_genero = {
        "Masculino": "#2ca02c",   # verde
        "Femenino": "#ff7f0e",    # naranja
        "NA..": "#F0F0F0"         # gris claro
    }

    fig_genero = px.pie(
        datos_genero,
        names="Genero",
        values="Porcentaje",
        title="👩👨 Distribución (%) por Género",
        color="Genero",                      # <<<<<< 🔥 Agregado esto
        color_discrete_map=color_map_genero   # <<<<<< 🔥 Usa el mapa
    )

    fig_genero.update_traces(
        textinfo='percent+label',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )

    st.plotly_chart(fig_genero, use_container_width=True, key="genero")


