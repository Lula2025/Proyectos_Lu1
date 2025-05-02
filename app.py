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
    if datos[columna].dtype == "object":
        datos[columna] = datos[columna].fillna("NA")
    else:
        datos[columna] = datos[columna].fillna(0)

datos["Anio"] = pd.to_numeric(datos["Anio"], errors="coerce")
datos["Area_total_de_la_parcela(ha)"] = pd.to_numeric(
    datos["Area_total_de_la_parcela(ha)"], errors="coerce"
).fillna(0)

datos = datos[(datos["Anio"] >= 2012) & (datos["Anio"] <= 2025)]

# --- Sidebar de filtros ---
st.sidebar.header("🌟 Filtros")

limpiar = st.sidebar.button("❌ Limpiar todos los filtros")

select_all = st.sidebar.checkbox("✅ Seleccionar todas las opciones", value=False)

datos_filtrados = datos.copy()

# Filtro por Categoría
with st.sidebar.expander("Categoría del Proyecto"):
    categorias = sorted(datos["Categoria_Proyecto"].unique())
    seleccion_categorias = [c for c in categorias if st.checkbox(c, value=select_all, key=f"cat_{c}")]
    if seleccion_categorias:
        datos_filtrados = datos_filtrados[datos_filtrados["Categoria_Proyecto"].isin(seleccion_categorias)]

# Filtro por Ciclo
with st.sidebar.expander("Ciclo"):
    ciclos = sorted(datos["Ciclo"].unique())
    seleccion_ciclos = [c for c in ciclos if st.checkbox(c, value=select_all, key=f"ciclo_{c}")]
    if seleccion_ciclos:
        datos_filtrados = datos_filtrados[datos_filtrados["Ciclo"].isin(seleccion_ciclos)]

# Filtro por Tipo de Parcela
with st.sidebar.expander("Tipo de Parcela"):
    tipos_parcela = sorted(datos["Tipo_parcela"].unique())
    seleccion_tipos_parcela = [t for t in tipos_parcela if st.checkbox(t, value=select_all, key=f"parcela_{t}")]
    if seleccion_tipos_parcela:
        datos_filtrados = datos_filtrados[datos_filtrados["Tipo_parcela"].isin(seleccion_tipos_parcela)]

# Filtro por Estado
with st.sidebar.expander("Estado"):
    estados = sorted(datos["Estado"].unique())
    seleccion_estados = [e for e in estados if st.checkbox(e, value=select_all, key=f"estado_{e}")]
    if seleccion_estados:
        datos_filtrados = datos_filtrados[datos_filtrados["Estado"].isin(seleccion_estados)]

# Filtro por Régimen Hídrico
with st.sidebar.expander("Régimen Hídrico"):
    regimenes = sorted(datos["Tipo_Regimen_Hidrico"].unique())
    seleccion_regimen = [r for r in regimenes if st.checkbox(r, value=select_all, key=f"regimen_{r}")]
    if seleccion_regimen:
        datos_filtrados = datos_filtrados[datos_filtrados["Tipo_Regimen_Hidrico"].isin(seleccion_regimen)]

# --- Título Principal ---
st.title("🌾 Dashboard Bitácoras Agronómicas 2012-2025")

if datos_filtrados.empty:
    st.warning("⚠️ No hay datos disponibles para los filtros seleccionados. Selecciona al menos una opción en los filtros.")
    st.stop()

# --- KPIs ---
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

# --- Gráficas principales ---
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

# Distribución por género
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
        "Masculino": "#2ca02c",
        "Femenino": "#ff7f0e",
        "NA..": "#F0F0F0"
    }

    fig_genero = px.pie(
        datos_genero,
        names="Genero",
        values="Registros",
        title="👩👨 Distribución de productores(as) por Género",
        color="Genero",
        color_discrete_map=color_map_genero
    )

    fig_genero.update_traces(
        textinfo='value',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )

    st.plotly_chart(fig_genero, use_container_width=True)
