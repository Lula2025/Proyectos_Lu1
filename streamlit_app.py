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

# --- Leer el archivo ZIo ---
archivo_zip = "Archivos.zip"
nombre_csv = "Datos_Historicos_cuenta_al26032025.csv"

try:
    with zipfile.ZipFile(archivo_zip, 'r') as z:
        with z.open(nombre_csv) as f:
            datos = pd.read_csv(f)
    st.success("Información basada en e-Agrology. Bitácoras agronómicas 2012_1er Trimestre 2025 ")
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

# --- Sidebar de filtros encadenados ---
st.sidebar.header(" 🔽 Filtros")

if 'limpiar_filtros' not in st.session_state:
    st.session_state.limpiar_filtros = False

select_all = st.sidebar.checkbox("✅ Seleccionar todas las opciones", value=False)

# Función auxiliar para manejar checkboxes múltiples
def checkbox_list(label, opciones, prefix):
    seleccionadas = []
    for o in opciones:
        default_value = select_all if not st.session_state.limpiar_filtros else False
        key_name = f"{prefix}_{str(o)}"
        if st.checkbox(str(o), value=default_value, key=key_name):
            seleccionadas.append(o)
    return seleccionadas

# Inicializar con todos los datos
datos_filtrados = datos.copy()

# Filtro por Categoría del Proyecto y Proyecto
with st.sidebar.expander("Categoría del Proyecto"):
    categorias = sorted(datos_filtrados["Categoria_Proyecto"].unique())
    categoria_seleccionada = st.selectbox("Selecciona una categoría", ["Todas"] + categorias)

    if categoria_seleccionada != "Todas":
        datos_filtrados = datos_filtrados[datos_filtrados["Categoria_Proyecto"] == categoria_seleccionada]
        proyectos = sorted(datos_filtrados["Proyecto"].unique())
        seleccionar_todos_proyectos = st.checkbox("Seleccionar todos los proyectos")

        proyectos_seleccionados = []
        for proyecto in proyectos:
            valor_default = seleccionar_todos_proyectos if not st.session_state.limpiar_filtros else False
            key_name = f"proyecto_{str(proyecto)}"
            if st.checkbox(str(proyecto), value=valor_default, key=key_name):
                proyectos_seleccionados.append(proyecto)

        if proyectos_seleccionados:
            datos_filtrados = datos_filtrados[datos_filtrados["Proyecto"].isin(proyectos_seleccionados)]

# Filtro por Ciclo
with st.sidebar.expander("Ciclo"):
    ciclos = sorted(datos_filtrados["Ciclo"].unique())
    seleccion_ciclos = checkbox_list("Ciclo", ciclos, "ciclo")
    if seleccion_ciclos:
        datos_filtrados = datos_filtrados[datos_filtrados["Ciclo"].isin(seleccion_ciclos)]

# Filtro por Tipo de Parcela
with st.sidebar.expander("Tipo de Parcela"):
    tipos_parcela = sorted(datos_filtrados["Tipo_parcela"].unique())
    seleccion_tipos_parcela = checkbox_list("Tipo Parcela", tipos_parcela, "parcela")
    if seleccion_tipos_parcela:
        datos_filtrados = datos_filtrados[datos_filtrados["Tipo_parcela"].isin(seleccion_tipos_parcela)]

# Filtro por Estado
with st.sidebar.expander("Estado"):
    estados = sorted(datos_filtrados["Estado"].unique())
    seleccion_estados = checkbox_list("Estado", estados, "estado")
    if seleccion_estados:
        datos_filtrados = datos_filtrados[datos_filtrados["Estado"].isin(seleccion_estados)]

# Filtro por Régimen Hídrico
with st.sidebar.expander("Régimen Hídrico"):
    regimenes = sorted(datos_filtrados["Tipo_Regimen_Hidrico"].unique())
    seleccion_regimen = checkbox_list("Régimen", regimenes, "regimen")
    if seleccion_regimen:
        datos_filtrados = datos_filtrados[datos_filtrados["Tipo_Regimen_Hidrico"].isin(seleccion_regimen)]

# Resetear estado después de aplicar filtros
if st.session_state.limpiar_filtros:
    st.session_state.limpiar_filtros = False

# --- Gráfico de distribución por género ---
import plotly.express as px

if "Genero" in datos_filtrados.columns:
    st.markdown("---")
    datos_filtrados["Genero"] = datos_filtrados["Genero"].fillna("NA..")
    categorias_genero = ["Masculino", "Femenino", "NA.."]
    datos_genero = datos_filtrados.groupby("Genero").size().reset_index(name="Registros")
    datos_genero = datos_genero.set_index("Genero").reindex(categorias_genero, fill_value=0).reset_index()

    total_registros = datos_genero["Registros"].sum()
    datos_genero["Porcentaje"] = (datos_genero["Registros"] / total_registros * 100) if total_registros > 0 else 0

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
