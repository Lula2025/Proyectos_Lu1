import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import unicodedata
import geopandas as gpd
import plotly.graph_objects as go


# --- Configuración inicial de la página ---
st.set_page_config(
    page_title="Dashboard Bitácoras Agronómicas",
    page_icon="🌾",
    layout="wide"
)

# --- Función para normalizar texto ---
def normalizar_texto(texto):
    if pd.isna(texto):
        return texto
    texto_norm = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto_norm.strip().capitalize()


# --- Leer el archivo ZIP ---
archivo_zip = "Archivos.2.zip"
nombre_csv = "Datos_Historicos_cuenta_actualizacion_23_24_30052025.2.csv"

try:
    with zipfile.ZipFile(archivo_zip, 'r') as z:
        with z.open(nombre_csv) as f:
            datos = pd.read_csv(f)
    st.success("Información basada en e-Agrology. Bitácoras agronómicas configuradas durante el año 2012 al 2do Trimestre 2025 ")
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
    "Tipo_Regimen_Hidrico", "Tipo_parcela", "Area_total_de_la_parcela(ha)", "Proyecto"
]
for columna in columnas_requeridas:
    if columna not in datos.columns:
        st.error(f"La columna '{columna}' no existe en el archivo CSV.")
        st.stop()
    datos[columna] = datos[columna].fillna("NA" if datos[columna].dtype == "object" else 0)

# Convertir columnas categóricas a string
columnas_categoricas = ["Categoria_Proyecto", "Ciclo", "Estado", "Tipo_Regimen_Hidrico", "Tipo_parcela", "Proyecto"]
for col in columnas_categoricas:
    datos[col] = datos[col].astype(str)

datos["Anio"] = pd.to_numeric(datos["Anio"], errors="coerce")
datos["Area_total_de_la_parcela(ha)"] = pd.to_numeric(
    datos["Area_total_de_la_parcela(ha)"], errors="coerce"
).fillna(0)

datos = datos[(datos["Anio"] >= 2012) & (datos["Anio"] <= 2025)]

# --- Crear mapa de colores fijo para Tipo_parcela ---
color_map_parcela = {
    "Área de Impacto": "#87CEEB",   # azul  
    "Área de extensión": "#2ca02c",  # Verde
    "Módulo": "#d62728" ,           # Rojo
}



    

# --- Preprocesamiento ---
columnas_requeridas = [
    "Anio", "Categoria_Proyecto", "Ciclo", "Estado",
    "Tipo_Regimen_Hidrico", "Tipo_parcela", "Area_total_de_la_parcela(ha)", "Proyecto"
]
for columna in columnas_requeridas:
    if columna not in datos.columns:
        st.error(f"La columna '{columna}' no existe en el archivo CSV.")
        st.stop()
    datos[columna] = datos[columna].fillna("NA" if datos[columna].dtype == "object" else 0)

# Convertir columnas categóricas a string
columnas_categoricas = ["Categoria_Proyecto", "Ciclo", "Estado", "Tipo_Regimen_Hidrico", "Tipo_parcela", "Proyecto"]
for col in columnas_categoricas:
    datos[col] = datos[col].astype(str)

datos["Anio"] = pd.to_numeric(datos["Anio"], errors="coerce")
datos["Area_total_de_la_parcela(ha)"] = pd.to_numeric(
    datos["Area_total_de_la_parcela(ha)"], errors="coerce"
).fillna(0)

# Acotar rango de años válidos
datos = datos[(datos["Anio"] >= 2012) & (datos["Anio"] <= 2025)]

# --- Crear mapa de colores fijo para Tipo_parcela ---
color_map_parcela = {
    "Área de Impacto": "#87CEEB",   # Azul
    "Área de extensión": "#2ca02c", # Verde
    "Módulo": "#d62728",            # Rojo
}

# --- Inicializar filtros ---
filtros_dict = {}

# --- Filtro Año (checkboxes con selección de los últimos 2 años por defecto) ---
ultimos_anios = sorted(datos["Anio"].dropna().unique())[-2:]

def checkbox_list(label, opciones, seleccion_previa=None):
    """Retorna lista de opciones seleccionadas con checkboxes."""
    st.sidebar.markdown(f"**{label}**")
    if seleccion_previa is None:
        seleccion_previa = opciones.copy()
    seleccionadas = []
    for o in opciones:
        default_value = o in seleccion_previa
        if st.sidebar.checkbox(str(o), value=default_value, key=f"{label}_{o}"):
            seleccionadas.append(o)
    return seleccionadas

opciones_anio = sorted(datos["Anio"].dropna().unique())
seleccion_anio = checkbox_list("Año", opciones_anio, seleccion_previa=ultimos_anios)
datos_filtrados = datos[datos["Anio"].isin(seleccion_anio)]

# --- Filtros encadenados (solo columnas que existen) ---
columnas_filtro = ["HUB_Agroecológico", "Categoria_Proyecto", "Proyecto", "Ciclo",
                   "Tipo_parcela", "Estado", "Tipo de sistema"]

def filtro_multiselect(columna, label):
    if columna not in datos_filtrados.columns:
        st.warning(f"El filtro '{label}' no está disponible (columna no existe).")
        return []
    opciones = sorted(datos_filtrados[columna].dropna().unique())
    seleccion = st.sidebar.multiselect(label, opciones, default=opciones)
    return seleccion

for col in columnas_filtro:
    seleccion = filtro_multiselect(col, col.replace("_", " "))
    if seleccion:
        datos_filtrados = datos_filtrados[datos_filtrados[col].isin(seleccion)]
    filtros_dict[col] = seleccion

# --- Cultivo(s) (manteniendo clasificación múltiple) ---
def clasificar_cultivo_multiple(texto):
    texto = str(texto).lower()
    categorias = []
    if "maíz" in texto or "maiz" in texto:
        categorias.append("Maíz")
    if "trigo" in texto:
        categorias.append("Trigo")
    if "avena" in texto:
        categorias.append("Avena")
    if "cebada" in texto:
        categorias.append("Cebada")
    if "frijol" in texto:
        categorias.append("Frijol")
    if not categorias:
        categorias.append("Otros")
    return categorias

if "Cultivo(s)" in datos_filtrados.columns:
    datos_filtrados["Cultivo_Categorizado"] = datos_filtrados["Cultivo(s)"].apply(clasificar_cultivo_multiple)
    opciones_cultivo = ["Maíz", "Trigo", "Avena", "Cebada", "Frijol", "Otros"]
    seleccion_cultivos = st.sidebar.multiselect("Cultivo(s)", opciones_cultivo, default=opciones_cultivo)
    datos_filtrados = datos_filtrados[
        datos_filtrados["Cultivo_Categorizado"].apply(lambda cats: any(c in seleccion_cultivos for c in cats))
    ]
    filtros_dict["Cultivo(s)"] = seleccion_cultivos

# --- Mostrar filtros aplicados ---
st.markdown("### Filtros Aplicados")
filtros_texto = []

# Año
if seleccion_anio:
    filtros_texto.append(f"**Año:** {', '.join(str(a) for a in seleccion_anio)}")
else:
    filtros_texto.append("**Año:** Todos")

# Otros filtros
for nombre, seleccion in filtros_dict.items():
    if seleccion:
        filtros_texto.append(f"**{nombre}:** {', '.join(str(s) for s in seleccion)}")
    else:
        filtros_texto.append(f"**{nombre}:** Todos")

st.markdown(",  ".join(filtros_texto))

# --- Resumen de cifras totales según filtros ---
st.markdown("### 📊 Resumen de Datos Filtrados")

# Total de bitácoras
total_bitacoras = len(datos_filtrados)

# Total de área
total_area = datos_filtrados["Area_total_de_la_parcela(ha)"].sum()

# Total de parcelas únicas
total_parcelas = datos_filtrados["Id_Parcela(Unico)"].nunique() if "Id_Parcela(Unico)" in datos_filtrados.columns else 0

# Total de productores únicos
total_productores = datos_filtrados["Id_Productor"].nunique() if "Id_Productor" in datos_filtrados.columns else 0

# Mostrar métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("📋 Total de Bitácoras", f"{total_bitacoras:,}")
col2.metric("🌿 Área Total (ha)", f"{total_area:,.2f}")
col3.metric("🌄 Número de Parcelas Totales", f"{total_parcelas:,}")
col4.metric("👩‍🌾 Productores(as) Totales", f"{total_productores:,}")

st.markdown("---")

# --- Gráficas ---
import plotly.express as px

# 1️⃣ Bitácoras por tipo de parcela
if not datos_filtrados.empty and "Tipo_parcela" in datos_filtrados.columns:
    bitacoras_tipo = datos_filtrados.groupby("Tipo_parcela")["Id_Parcela(Unico)"].nunique().reset_index(name="Parcelas")
    fig_bitacoras = px.bar(
        bitacoras_tipo,
        x="Tipo_parcela",
        y="Parcelas",
        color="Tipo_parcela",
        title="📋 Número de Parcelas por Tipo de Parcela"
    )
    st.plotly_chart(fig_bitacoras, use_container_width=True)

# 2️⃣ Área total por tipo de parcela
if not datos_filtrados.empty and "Tipo_parcela" in datos_filtrados.columns:
    area_tipo = datos_filtrados.groupby("Tipo_parcela")["Area_total_de_la_parcela(ha)"].sum().reset_index()
    fig_area = px.bar(
        area_tipo,
        x="Tipo_parcela",
        y="Area_total_de_la_parcela(ha)",
        color="Tipo_parcela",
        title="🌿 Área Total por Tipo de Parcela"
    )
    st.plotly_chart(fig_area, use_container_width=True)

# --- Mapa de parcelas ---
st.markdown("### 📍 Distribución de Parcelas")
if not datos_filtrados.empty and {"Latitud","Longitud"}.issubset(datos_filtrados.columns):
    datos_mapa = datos_filtrados.dropna(subset=["Latitud","Longitud"])
    if not datos_mapa.empty:
        # Reducir decimales para agrupar puntos cercanos
        datos_mapa["Latitud_r"] = datos_mapa["Latitud"].round(4)
        datos_mapa["Longitud_r"] = datos_mapa["Longitud"].round(4)

        # Contar parcelas por ubicación
        mapa_parcelas = (
            datos_mapa.groupby(["Latitud_r", "Longitud_r", "Tipo_parcela"])
            .agg(Num_Parcelas=("Id_Parcela(Unico)", "nunique"))
            .reset_index()
        )

        fig_mapa = px.scatter_mapbox(
            mapa_parcelas,
            lat="Latitud_r",
            lon="Longitud_r",
            size="Num_Parcelas",
            color="Tipo_parcela",
            hover_name="Tipo_parcela",
            hover_data={"Num_Parcelas": True},
            zoom=4,
            mapbox_style="carto-positron",
            title="📍 Parcelas según Filtros"
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.info("No hay datos de latitud/longitud para mostrar en el mapa.")
else:
    st.info("Las columnas 'Latitud' y 'Longitud' no existen en los datos filtrados.")


