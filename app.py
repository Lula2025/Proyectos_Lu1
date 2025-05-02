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

# --- Sidebar de filtros ---
st.sidebar.markdown("""
###  Filtros  ⚗️
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M3 4H21V6L14 13V19L10 21V13L3 6V4Z" fill="#4CAF50"/>
  <path d="M14 13L21 6V4H3V6L10 13V21L14 19V13Z" stroke="#2E7D32" stroke-width="1.5"/>
</svg>
""", unsafe_allow_html=True)  

if 'limpiar_filtros' not in st.session_state:
    st.session_state.limpiar_filtros = False

datos_filtrados = datos.copy()

# Función auxiliar para manejar checkboxes con opción de limpiar
def checkbox_list(label, opciones, prefix):
    seleccionadas = []
    seleccionar_todos = st.checkbox(f"Seleccionar todos en {label}", key=f"select_all_{prefix}")
    for o in opciones:
        default_value = seleccionar_todos if not st.session_state.limpiar_filtros else False
        key_name = f"{prefix}_{str(o)}"
        checked = st.checkbox(str(o), value=default_value, key=key_name)
        if checked:
            seleccionadas.append(o)
    return seleccionadas

# Filtro por Categoría del Proyecto y Proyecto (subcategoría)
with st.sidebar.expander("Categoría del Proyecto"):
    categorias = sorted(datos["Categoria_Proyecto"].unique())
    categoria_seleccionada = st.selectbox("Selecciona una categoría", ["Todas"] + categorias)

    if categoria_seleccionada != "Todas":
        proyectos = sorted(datos[datos["Categoria_Proyecto"] == categoria_seleccionada]["Proyecto"].unique())

        proyectos_seleccionados = []

        # Si solo hay un proyecto, lo seleccionamos automáticamente
        if len(proyectos) == 1:
            proyectos_seleccionados = proyectos
        else:
            seleccionar_todos_proyectos = st.checkbox("Seleccionar todos los proyectos")
            for proyecto in proyectos:
                valor_default = seleccionar_todos_proyectos if not st.session_state.limpiar_filtros else False
                key_name = f"proyecto_{str(proyecto)}"
                if st.checkbox(str(proyecto), value=valor_default, key=key_name):
                    proyectos_seleccionados.append(proyecto)

        datos_filtrados = datos_filtrados[
            (datos_filtrados["Categoria_Proyecto"] == categoria_seleccionada) &
            (datos_filtrados["Proyecto"].isin(proyectos_seleccionados))
        ]

# Filtro por Ciclo (opciones dinámicas)
with st.sidebar.expander("Ciclo"):
    ciclos_disponibles = sorted(datos_filtrados["Ciclo"].unique())
    seleccion_ciclos = checkbox_list("Ciclo", ciclos_disponibles, "ciclo")
    if seleccion_ciclos:
        datos_filtrados = datos_filtrados[datos_filtrados["Ciclo"].isin(seleccion_ciclos)]

# Filtro por Tipo de Parcela (opciones dinámicas)
with st.sidebar.expander("Tipo de Parcela"):
    tipos_parcela_disponibles = sorted(datos_filtrados["Tipo_parcela"].unique())
    seleccion_tipos_parcela = checkbox_list("Tipo Parcela", tipos_parcela_disponibles, "parcela")
    if seleccion_tipos_parcela:
        datos_filtrados = datos_filtrados[datos_filtrados["Tipo_parcela"].isin(seleccion_tipos_parcela)]

# Filtro por Estado (opciones dinámicas)
with st.sidebar.expander("Estado"):
    estados_disponibles = sorted(datos_filtrados["Estado"].unique())
    seleccionar_todos_estados = st.checkbox("Seleccionar todos los estados", key="select_all_estados")
    seleccion_estados = []
    for estado in estados_disponibles:
        key_estado = f"estado_{estado}"
        valor_default = seleccionar_todos_estados if not st.session_state.limpiar_filtros else False
        if st.checkbox(estado, value=valor_default, key=key_estado):
            seleccion_estados.append(estado)
    if seleccion_estados:
        datos_filtrados = datos_filtrados[datos_filtrados["Estado"].isin(seleccion_estados)]

# Filtro por Régimen Hídrico (opciones dinámicas)
with st.sidebar.expander("Régimen Hídrico"):
    regimenes_disponibles = sorted(datos_filtrados["Tipo_Regimen_Hidrico"].unique())
    seleccion_regimen = checkbox_list("Régimen", regimenes_disponibles, "regimen")
    if seleccion_regimen:
        datos_filtrados = datos_filtrados[datos_filtrados["Tipo_Regimen_Hidrico"].isin(seleccion_regimen)]

# Resetear estado después de aplicar filtros
if st.session_state.limpiar_filtros:
    st.session_state.limpiar_filtros = False

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
    color_arg = "Tipo_parcela" if seleccion_tipos_parcela else None
    bitacoras_por_anio = datos_filtrados.groupby(["Anio", "Tipo_parcela"]).size().reset_index(name="Bitácoras") if color_arg else datos_filtrados.groupby("Anio").size().reset_index(name="Bitácoras")
    fig_bitacoras = px.bar(
        bitacoras_por_anio,
        x="Anio",
        y="Bitácoras",
        color=color_arg,
        title="📋 Número de Bitácoras por Año"
    )
    st.plotly_chart(fig_bitacoras, use_container_width=True)

with col6:
    area_por_anio = datos_filtrados.groupby(["Anio", "Tipo_parcela"])["Area_total_de_la_parcela(ha)"].sum().reset_index() if seleccion_tipos_parcela else datos_filtrados.groupby("Anio")["Area_total_de_la_parcela(ha)"].sum().reset_index()
    fig_area = px.bar(
        area_por_anio,
        x="Anio",
        y="Area_total_de_la_parcela(ha)",
        color="Tipo_parcela" if seleccion_tipos_parcela else None,
        title="🌿 Área Total de Parcelas por Año",
        labels={"Area_total_de_la_parcela(ha)": "Área (ha)"}
    )
    st.plotly_chart(fig_area, use_container_width=True)

col7, col8 = st.columns(2)

with col7:
    if "Id_Parcela(Unico)" in datos_filtrados.columns:
        parcelas_por_anio = datos_filtrados.groupby(["Anio", "Tipo_parcela"])["Id_Parcela(Unico)"].nunique().reset_index() if seleccion_tipos_parcela else datos_filtrados.groupby("Anio")["Id_Parcela(Unico)"].nunique().reset_index()
        fig_parcelas = px.bar(
            parcelas_por_anio,
            x="Anio",
            y="Id_Parcela(Unico)",
            color="Tipo_parcela" if seleccion_tipos_parcela else None,
            title="🌄 Número de Parcelas por Año",
            labels={"Id_Parcela(Unico)": "Parcelas"}
        )
        st.plotly_chart(fig_parcelas, use_container_width=True)

with col8:
    if "Id_Productor" in datos_filtrados.columns:
        productores_por_anio = datos_filtrados.groupby(["Anio", "Tipo_parcela"])["Id_Productor"].nunique().reset_index() if seleccion_tipos_parcela else datos_filtrados.groupby("Anio")["Id_Productor"].nunique().reset_index()
        fig_productores = px.bar(
            productores_por_anio,
            x="Anio",
            y="Id_Productor",
            color="Tipo_parcela" if seleccion_tipos_parcela else None,
            title="👩‍🌾👨‍🌾 Número de Productores por Año",
            labels={"Id_Productor": "Productores"}
        )
        st.plotly_chart(fig_productores, use_container_width=True)

# Distribución por género
if "Genero" in datos_filtrados.columns:
    st.markdown("---")
    datos_filtrados["Genero"] = datos_filtrados["Genero"].fillna("NA..")
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
