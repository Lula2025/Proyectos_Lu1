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
    st.success("Información basada en e-A. Bitácoras agronómicas 2012_1er Trimestre 2025")
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
    st.image("assets/filtro_verde.png", use_container_width=True)

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
### <span style='vertical-align:middle;'>Filtros</span>
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" style="vertical-align:middle;" fill="none" viewBox="0 0 24 24">
  <path fill="#2196F3" d="M3 4h18v2l-7 7v7l-4 2v-9L3 6V4z"/>
  <path stroke="#0D47A1" stroke-width="1.5" d="M3 4h18v2l-7 7v7l-4 2v-9L3 6V4z"/>
</svg>
""", unsafe_allow_html=True)

if 'limpiar_filtros' not in st.session_state:
    st.session_state.limpiar_filtros = False

select_all = st.sidebar.checkbox("✅ Seleccionar todas las opciones", value=False)

datos_filtrados = datos.copy()

# Botón seleccionar/deseleccionar todos
st.sidebar.markdown("### Selección general")
seleccionar_todo_global = st.sidebar.checkbox("Seleccionar/Deseleccionar todos")

datos_filtrados = datos.copy()

# Función auxiliar para manejar checkboxes con ocultación de opciones inválidas
def checkbox_list(label, opciones, prefix, disponibles_actuales):
    seleccionadas = []
    seleccionar_todos = seleccionar_todo_global or st.checkbox(f"Seleccionar todos en {label}", key=f"select_all_{prefix}")
    if disponibles_actuales:
        for o in disponibles_actuales:
            key_name = f"{prefix}_{str(o)}"
            checked = st.checkbox(
                str(o),
                value=seleccionar_todos,
                key=key_name
            )
            if checked:
                seleccionadas.append(o)
    else:
        st.markdown(f"*Sin opciones disponibles en {label}*")
    return seleccionadas

# Filtro por Categoría del Proyecto y Proyecto (subcategoría)
with st.sidebar.expander("Categoría del Proyecto"):
    categorias = sorted(datos["Categoria_Proyecto"].unique())
    categoria_seleccionada = st.selectbox("Selecciona una categoría", ["Todas"] + categorias)

    if categoria_seleccionada != "Todas":
        proyectos = sorted(datos_filtrados[datos_filtrados["Categoria_Proyecto"] == categoria_seleccionada]["Proyecto"].unique())
        proyectos_seleccionados = []

        if len(proyectos) == 1:
            proyectos_seleccionados = proyectos
            st.markdown(f"**Proyecto único seleccionado automáticamente:** {proyectos[0]}")
            datos_filtrados = datos_filtrados[
                (datos_filtrados["Categoria_Proyecto"] == categoria_seleccionada) &
                (datos_filtrados["Proyecto"] == proyectos[0])
            ]
        elif proyectos:
            seleccionar_todos_proyectos = seleccionar_todo_global or st.checkbox("Seleccionar todos los proyectos", key="select_all_proyectos")
            for proyecto in proyectos:
                key_name = f"proyecto_checkbox_{str(proyecto)}"
                if st.checkbox(str(proyecto), value=seleccionar_todos_proyectos, key=key_name):
                    proyectos_seleccionados.append(proyecto)

            datos_filtrados = datos_filtrados[
                (datos_filtrados["Categoria_Proyecto"] == categoria_seleccionada) &
                (datos_filtrados["Proyecto"].isin(proyectos_seleccionados))
            ]
        else:
            st.markdown("*Sin proyectos disponibles*")

# Filtro por Ciclo
if not datos_filtrados.empty:
    with st.sidebar.expander("Ciclo"):
        ciclos_validos = sorted(datos["Ciclo"].unique())
        disponibles = sorted(datos_filtrados["Ciclo"].unique())
        seleccion_ciclos = checkbox_list("Ciclo", ciclos_validos, "ciclo", disponibles)
        if seleccion_ciclos:
            datos_filtrados = datos_filtrados[datos_filtrados["Ciclo"].isin(seleccion_ciclos)]

# Filtro por Tipo de Parcela
if not datos_filtrados.empty:
    with st.sidebar.expander("Tipo de Parcela"):
        tipos_validos = sorted(datos["Tipo_parcela"].unique())
        disponibles = sorted(datos_filtrados["Tipo_parcela"].unique())
        seleccion_tipos_parcela = checkbox_list("Tipo Parcela", tipos_validos, "parcela", disponibles)
        if seleccion_tipos_parcela:
            datos_filtrados = datos_filtrados[datos_filtrados["Tipo_parcela"].isin(seleccion_tipos_parcela)]

# Filtro por Estado
if not datos_filtrados.empty:
    with st.sidebar.expander("Estado"):
        estados_validos = sorted(datos["Estado"].unique())
        disponibles = sorted(datos_filtrados["Estado"].unique())
        seleccion_estados = checkbox_list("Estado", estados_validos, "estado", disponibles)
        if seleccion_estados:
            datos_filtrados = datos_filtrados[datos_filtrados["Estado"].isin(seleccion_estados)]

# Filtro por Régimen Hídrico
if not datos_filtrados.empty:
    with st.sidebar.expander("Régimen Hídrico"):
        regimenes_validos = sorted(datos["Tipo_Regimen_Hidrico"].unique())
        disponibles = sorted(datos_filtrados["Tipo_Regimen_Hidrico"].unique())
        seleccion_regimen = checkbox_list("Régimen", regimenes_validos, "regimen", disponibles)
        if seleccion_regimen:
            datos_filtrados = datos_filtrados[datos_filtrados["Tipo_Regimen_Hidrico"].isin(seleccion_regimen)]

# --- Título Principal ---
st.title("🌾 Dashboard Bitácoras Agronómicas 2012-2025")

if datos_filtrados.empty:
    st.warning("⚠️ No hay datos disponibles para los filtros seleccionados. Selecciona al menos una opción en los filtros.")
    st.stop()

# Ejemplo de visualización reactiva
grafico = px.histogram(
    datos_filtrados,
    x="Estado",
    color="Tipo_parcela",
    title="Distribución de parcelas por Estado y Tipo",
    barmode="group"
)
st.plotly_chart(grafico, use_container_width=True)


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


    st.plotly_chart(fig_genero, use_container_width=True)
