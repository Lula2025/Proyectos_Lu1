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
#########
# --- Sidebar de filtros encadenados ---
st.sidebar.header(" 🔽 Filtros")

if 'limpiar_filtros' not in st.session_state:
    st.session_state.limpiar_filtros = False

select_all = st.sidebar.checkbox("✅ Seleccionar todas las opciones", value=False)


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


#######

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

cambios_estados = {
    "MORELOS": "Morelos",
    "PUEBLA": "Puebla",
    "SINALOA": "Sinaloa",
    "TABASCO": "Tabasco",
    "Michoacán de Ocampo": "Michoacán",
    "Ciudad de Mexico": "Ciudad de México",
    "Veracruz de Ignacio de la Llave": "Veracruz",
    "Coahuila de Zaragoza": "Coahuila",
    
    # agrega más según necesites
}

datos_filtrados["Estado"] = datos_filtrados["Estado"].replace(cambios_estados)

with st.sidebar.expander("Estado"):
    estados = sorted(datos_filtrados["Estado"].unique())
    seleccion_estados = checkbox_list("Estado", estados, "estado")
    if seleccion_estados:
        datos_filtrados = datos_filtrados[datos_filtrados["Estado"].isin(seleccion_estados)]

# Filtro por Régimen Hídrico

cambios_regimen = {
    "RIEGO": "Riego",
    "TEMPORAL": "Temporal",
}

# Normalizar la columna correcta
datos_filtrados["Tipo_Regimen_Hidrico"] = datos_filtrados["Tipo_Regimen_Hidrico"].replace(cambios_regimen)

with st.sidebar.expander("Régimen Hídrico"):
    regimenes = sorted(datos_filtrados["Tipo_Regimen_Hidrico"].unique())
    seleccion_regimen = checkbox_list("Régimen", regimenes, "regimen")
    if seleccion_regimen:
        datos_filtrados = datos_filtrados[datos_filtrados["Tipo_Regimen_Hidrico"].isin(seleccion_regimen)]

if st.session_state.limpiar_filtros:
    st.session_state.limpiar_filtros = False




# Filtro por Año

with st.sidebar.expander("Año"):
    opciones_anio = sorted(datos_filtrados["Anio"].unique())

    # Checkbox general
    seleccionar_todos = st.checkbox("Seleccionar todos los años", value=True)

    # Crear casillas independientes para cada año
    seleccion_anio = []
    for anio in opciones_anio:
        if seleccionar_todos:
            checked = True
        else:
            checked = False

        if st.checkbox(str(anio), value=checked, key=f"anio_{anio}"):
            seleccion_anio.append(anio)

    # Filtrar datos
    if seleccion_anio:
        datos_filtrados = datos_filtrados[datos_filtrados["Anio"].isin(seleccion_anio)]




# --- Resumen de cifras totales ---
st.markdown("### Informe de acuerdo a los Datos Filtrados")

total_bitacoras = len(datos_filtrados)
total_area = datos_filtrados["Area_total_de_la_parcela(ha)"].sum()
total_parcelas = datos_filtrados["Id_Parcela(Unico)"].nunique() if "Id_Parcela(Unico)" in datos_filtrados.columns else 0
total_productores = datos_filtrados["Id_Productor"].nunique() if "Id_Productor" in datos_filtrados.columns else 0

col_r1, col_r2, col_r3, col_r4 = st.columns(4)
col_r1.metric("📋 Total de Bitácoras", f"{total_bitacoras:,}")
col_r2.metric("🌿 Área Total (ha)", f"{total_area:,.2f}")
col_r3.metric("🌄 Número de Parcelas Totales", f"{total_parcelas:,}")
col_r4.metric("👩‍🌾 Productores(as) Totales", f"{total_productores:,}")

st.markdown("---")  # Esta es la línea de separación

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
        color_discrete_map=color_map_parcela if color_arg else None,
        title="📋 Número de Bitácoras por Año"
    )

   # Forzar colores usando update_traces para asegurarnos de que las barras se pinten correctamente
    fig_bitacoras.update_traces(marker=dict(line=dict(color='black', width=1)))  # Añadir contorno para mejor visibilidad
    st.plotly_chart(fig_bitacoras, use_container_width=True)

with col6:
    area_por_anio = datos_filtrados.groupby(["Anio", "Tipo_parcela"])["Area_total_de_la_parcela(ha)"].sum().reset_index() if seleccion_tipos_parcela else datos_filtrados.groupby("Anio")["Area_total_de_la_parcela(ha)"].sum().reset_index()
    fig_area = px.bar(
        area_por_anio,
        x="Anio",
        y="Area_total_de_la_parcela(ha)",
        color="Tipo_parcela" if seleccion_tipos_parcela else None,
        color_discrete_map=color_map_parcela if seleccion_tipos_parcela else None,
        title="🌿 Área Total de Parcelas por Año ",
        labels={"Area_total_de_la_parcela(ha)": "Área (ha)"}
    )
    # Forzar colores usando update_traces para asegurar la correcta aplicación del color
    fig_area.update_traces(marker=dict(line=dict(color='black', width=1)))  # Añadir contorno
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
            color_discrete_map=color_map_parcela if seleccion_tipos_parcela else None,
            title="🌄 Número de Parcelas por Año",
            labels={"Id_Parcela(Unico)": "Parcelas"}
        )
        # Forzar colores usando update_traces para asegurar la correcta aplicación del color
        fig_parcelas.update_traces(marker=dict(line=dict(color='black', width=1)))  # Añadir contorno
        st.plotly_chart(fig_parcelas, use_container_width=True)

with col8:
    if "Id_Productor" in datos_filtrados.columns:
        productores_por_anio = datos_filtrados.groupby(["Anio", "Tipo_parcela"])["Id_Productor"].nunique().reset_index() if seleccion_tipos_parcela else datos_filtrados.groupby("Anio")["Id_Productor"].nunique().reset_index()
        fig_productores = px.bar(
            productores_por_anio,
            x="Anio",
            y="Id_Productor",
            color="Tipo_parcela" if seleccion_tipos_parcela else None,
            color_discrete_map=color_map_parcela if seleccion_tipos_parcela else None,
            title="👩‍🌾👨‍🌾 Número de Productores por Año",
            labels={"Id_Productor": "Productores"}
        )
        # Forzar colores usando update_traces para asegurar la correcta aplicación del color
        fig_productores.update_traces(marker=dict(line=dict(color='black', width=1)))  # Añadir contorno
        st.plotly_chart(fig_productores, use_container_width=True)


# --- Gráfico de distribución por género ---
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
        title="👩👨 Distribución Total de Productores(as) por Género",
        color="Genero",
        color_discrete_map=color_map_genero
    )

    fig_genero.update_traces(
        textinfo='percent',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )

    st.plotly_chart(fig_genero, use_container_width=True)


# --- Gráfico de evolución de productores por género a lo largo de los años ---
if "Genero" in datos_filtrados.columns and "Anio" in datos_filtrados.columns:
    st.markdown("###")

    # Normalizar valores de género
    datos_filtrados["Genero"] = datos_filtrados["Genero"].fillna("NA..")
    datos_filtrados["Genero"] = datos_filtrados["Genero"].replace({
        "Hombre": "Masculino",
        "Mujer": "Femenino",
        "NA": "NA.."
    })

    # Agrupar por año y género
    productores_genero_anio = datos_filtrados.groupby(["Anio", "Genero"])["Id_Productor"].nunique().reset_index(name="Cantidad")

    # Calcular total de productores por año
    totales_anio = productores_genero_anio.groupby("Anio")["Cantidad"].sum().reset_index(name="Total")
    productores_genero_anio = productores_genero_anio.merge(totales_anio, on="Anio")

    # Calcular porcentaje por año
    productores_genero_anio["Porcentaje"] = (productores_genero_anio["Cantidad"] / productores_genero_anio["Total"] * 100).round(1)

    # Asignar emojis a cada género
    emoji_genero = {
        "Femenino": "👩 Mujeres",
        "Masculino": "👨 Hombres",
        "NA..": "❔ Sin dato"
    }
    productores_genero_anio["Genero_Emoji"] = productores_genero_anio["Genero"].map(emoji_genero)

    # Crear gráfico de barras apiladas por porcentaje
    fig_genero_pct = px.bar(
        productores_genero_anio,
        x="Anio",
        y="Porcentaje",
        color="Genero_Emoji",
        title="📊 Porcentaje de Productores(as) por Género y Año",
        labels={"Porcentaje": "% del total por año"},
        color_discrete_map={
            "👨 Hombres": "#2ca02c",
            "👩 Mujeres": "#ff7f0e",
            "❔ Sin dato": "#F0F0F0"
        },
        text=productores_genero_anio["Porcentaje"].astype(str) + "%"
    )

 # Configurar diseño del gráfico
    fig_genero_pct.update_layout(
        barmode="stack",
        yaxis_tickformat=".1f",
        yaxis_title="Porcentaje (%)",
        xaxis_title="Año",
        legend_title="Género",
        height=600,
        width=700,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    # Posicionar los textos dentro de las barras
    fig_genero_pct.update_traces(textposition="inside")

    # Mostrar el gráfico
    st.plotly_chart(fig_genero_pct, use_container_width=True)


####



########



st.markdown("---")  # Línea de separación

# --- Recuento por Año, Categoría y Proyecto ---
conteo_mix = (
    datos_filtrados
    .groupby(["Anio", "Categoria_Proyecto", "Proyecto"])
    .size()
    .reset_index(name="Registros")
)

# Total por año
total_anual = conteo_mix.groupby("Anio")["Registros"].sum().reset_index(name="Total")

# Calcular porcentaje del total por año
conteo_mix = conteo_mix.merge(total_anual, on="Anio")
conteo_mix["Porcentaje"] = (conteo_mix["Registros"] / conteo_mix["Total"] * 100).round(1)

# Obtener el proyecto dominante por año
proyecto_max = (
    conteo_mix.loc[conteo_mix.groupby("Anio")["Porcentaje"].idxmax()]
    .set_index("Anio")["Proyecto"]
)

# Crear tabla con MultiIndex (Categoria -> Proyecto) como columnas
conteo_pivot = conteo_mix.pivot_table(
    index="Anio",
    columns=["Categoria_Proyecto", "Proyecto"],
    values="Porcentaje",
    fill_value=0
)

# Insertar "Numero de Bitacoras" al inicio
conteo_pivot.insert(0, "🔢 Numero de Bitacoras ", total_anual.set_index("Anio")["Total"])

# Insertar "Proyecto Dominante" justo después (posición 1)
conteo_pivot.insert(1, "🏆 Proyecto Dominante", proyecto_max)


# Convertir todos los valores a texto sin símbolo % (solo valores numéricos)
tabla_final = conteo_pivot.copy()

for col in tabla_final.columns:
    if col == "🔢 Numero de Bitacoras ":
        # Mantener como entero
        tabla_final[col] = tabla_final[col].apply(lambda x: int(x) if pd.notnull(x) else x)
    elif tabla_final[col].dtype in [float, int]:
        # Redondear a dos decimales
        tabla_final[col] = tabla_final[col].apply(lambda x: round(x, 2) if pd.notnull(x) else x)



# --- Crear copia de la tabla con columnas modificadas ---
tabla_tooltip = tabla_final.copy()


# Mostrar tabla final sin % en ningún valor
st.markdown("### 📋 Número de Bitácoras y Distribución(%) por Proyecto y Categoría, por Año")
st.dataframe(tabla_final.reset_index(), use_container_width=False, height=min(600, 40 * len(tabla_final)))




# --- Tabla de porcentajes por año y categoría del proyecto ---
st.markdown("### 📋 Distribución(%) por Categoría del Proyecto, por Año")

# Agrupar por año y categoría
conteo = datos_filtrados.groupby(["Anio", "Categoria_Proyecto"]).size().reset_index(name="Registros")

# Calcular total por año
conteo["Total_Anio"] = conteo.groupby("Anio")["Registros"].transform("sum")

# Calcular porcentaje
conteo["Porcentaje"] = (conteo["Registros"] / conteo["Total_Anio"] * 100)

# Pivotear para mostrar cada categoría como columna
tabla_pct = conteo.pivot_table(
    index="Anio",
    columns="Categoria_Proyecto",
    values="Porcentaje",
    fill_value=0
)

# Redondear a 2 decimales y convertir a string con % para presentación
tabla_pct = tabla_pct.round(2)

# Resetear índice para que 'Anio' sea una columna normal
tabla_pct = tabla_pct.reset_index()

# Mostrar tabla sin scroll horizontal (adaptada al contenido)
st.dataframe(tabla_pct, use_container_width=False, height=min(600, 40 * len(tabla_pct)))


# --- Tabla pivote: Número único de productores por género, proyecto y año ---
if {"Id_Productor", "Genero", "Proyecto", "Anio"}.issubset(datos_filtrados.columns):
    st.markdown("### 📊 Número Único de Productores(as)")

    # Normalizar valores de género
    datos_filtrados["Genero"] = datos_filtrados["Genero"].fillna("n/a").replace({
        "Hombre": "Masculino",
        "Mujer": "Femenino",
        "NA": "n/a",
        "NA..": "n/a"
    })

    # Tabla base con conteo único de productores
    tabla_base = (
        datos_filtrados
        .groupby(["Proyecto", "Anio", "Genero"])["Id_Productor"]
        .nunique()
        .reset_index()
    )

    # Crear tabla pivote
    tabla_pivote = tabla_base.pivot_table(
        index=["Proyecto", "Anio"],
        columns="Genero",
        values="Id_Productor",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Grand Total"
    ).reset_index()

    # Mostrar tabla pivote
    st.dataframe(tabla_pivote, use_container_width=True)



# --- Preparar datos ---
datos_filtrados["Latitud"] = pd.to_numeric(datos_filtrados["Latitud"], errors="coerce")
datos_filtrados["Longitud"] = pd.to_numeric(datos_filtrados["Longitud"], errors="coerce")
datos_geo = datos_filtrados.dropna(subset=["Latitud", "Longitud"])

# Agrupar por coordenadas y Tipo de sistema
parcelas_geo = (
    datos_geo.groupby(["Latitud", "Longitud", "Tipo de sistema"])["Id_Parcela(Unico)"]
    .nunique()
    .reset_index(name="Parcelas")
)

# --- Sidebar filtro por Tipo de sistema ---
with st.sidebar.expander("Tipo de sistema"):
    opciones_sistema = sorted(datos_filtrados["Tipo de sistema"].dropna().unique())

    # Checkbox para seleccionar todos
    seleccionar_todos_sistema = st.checkbox("Seleccionar todos los sistemas", value=True)

    seleccion_sistema = []
    for sistema in opciones_sistema:
        if seleccionar_todos_sistema:
            checked = True
        else:
            checked = False

        if st.checkbox(sistema, value=checked, key=f"sistema_{sistema}"):
            seleccion_sistema.append(sistema)

# Aplicar filtro dinámico por Tipo de sistema
if seleccion_sistema:
    parcelas_geo = parcelas_geo[parcelas_geo["Tipo de sistema"].isin(seleccion_sistema)]



# --- Definir centro y límites para México ---
mexico_center = {"lat": 23.0, "lon": -102.0}  # Centro aproximado de México
lat_range = [14.5, 32.7]  # Sur a Norte
lon_range = [-118.5, -86.7]  # Oeste a Este

# --- Crear mapa interactivo ---
fig_mapa_geo = px.scatter_mapbox(
    parcelas_geo,
    lat="Latitud",
    lon="Longitud",
    size="Parcelas",
    color="Tipo de sistema",   # <- cambio aquí
    hover_name="Tipo de sistema",  # <- cambio aquí
    hover_data={"Latitud": True, "Longitud": True, "Parcelas": True},
    mapbox_style="carto-positron",
    center=mexico_center,
    zoom=4.5,
    height=700,
    width=700,
    title="📍 Distribución Geográfica de Parcelas por Tipo de Sistema"
)

# Ajustar tamaño máximo de los puntos
fig_mapa_geo.update_traces(marker=dict(sizemode="area", sizeref=2, sizemin=5))

# Limitar visualización al rango de México
fig_mapa_geo.update_layout(
    mapbox=dict(
        center=mexico_center,
        zoom=4.5,
        bearing=0,
        pitch=0,
    ),
    margin={"l":0,"r":0,"t":50,"b":0}
)

# Mostrar mapa en Streamlit
st.plotly_chart(fig_mapa_geo, use_container_width=True)



# -----------------------------------
# --- Crear DataFrame con número de parcelas por estado según el filtro activo ---
parcelas_estado = datos_filtrados.groupby("Estado").agg({
    "Id_Parcela(Unico)": "nunique"
}).reset_index().rename(columns={"Id_Parcela(Unico)": "Parcelas"})

# --- Coordenadas aproximadas para el centro de cada estado ---
centros_estados = {
    "Aguascalientes": {"lat": 21.885, "lon": -102.291},
    "Baja California": {"lat": 30.840, "lon": -115.283},
    "Baja California Sur": {"lat": 26.049, "lon": -111.666},
    "Campeche": {"lat": 19.830, "lon": -90.534},
    "Chiapas": {"lat": 16.756, "lon": -93.116},
    "Chihuahua": {"lat": 28.632, "lon": -106.069},
    "Ciudad de México": {"lat": 19.432, "lon": -99.133},
    "Coahuila": {"lat": 27.058, "lon": -101.706},
    "Colima": {"lat": 19.243, "lon": -103.724},
    "Durango": {"lat": 24.027, "lon": -104.653},
    "Guanajuato": {"lat": 21.019, "lon": -101.257},
    "Guerrero": {"lat": 17.551, "lon": -99.503},
    "Hidalgo": {"lat": 20.091, "lon": -98.762},
    "Jalisco": {"lat": 20.659, "lon": -103.349},
    "México": {"lat": 19.345, "lon": -99.837},
    "Michoacán": {"lat": 19.566, "lon": -101.706},
    "Morelos": {"lat": 18.681, "lon": -99.101},
    "Nayarit": {"lat": 21.751, "lon": -104.845},
    "Nuevo León": {"lat": 25.675, "lon": -100.318},
    "Oaxaca": {"lat": 17.073, "lon": -96.726},
    "Puebla": {"lat": 19.041, "lon": -98.206},
    "Querétaro": {"lat": 20.588, "lon": -100.389},
    "Quintana Roo": {"lat": 19.181, "lon": -88.479},
    "San Luis Potosí": {"lat": 22.156, "lon": -100.985},
    "Sinaloa": {"lat": 25.172, "lon": -107.479},
    "Sonora": {"lat": 29.297, "lon": -110.330},
    "Tabasco": {"lat": 17.840, "lon": -92.618},
    "Tamaulipas": {"lat": 23.747, "lon": -98.525},
    "Tlaxcala": {"lat": 19.318, "lon": -98.237},
    "Veracruz": {"lat": 19.173, "lon": -96.134},
    "Yucatán": {"lat": 20.709, "lon": -89.094},
    "Zacatecas": {"lat": 22.770, "lon": -102.583}
}

# --- Agregar columnas de latitud y longitud ---
parcelas_estado["Latitud"] = parcelas_estado["Estado"].map(lambda x: centros_estados.get(x, {}).get("lat", 23.0))
parcelas_estado["Longitud"] = parcelas_estado["Estado"].map(lambda x: centros_estados.get(x, {}).get("lon", -102.0))

# --- Crear mapa de burbujas interactivo ---
fig_estado = px.scatter_mapbox(
    parcelas_estado,
    lat="Latitud",
    lon="Longitud",
    size="Parcelas",
    color="Parcelas",
    hover_name="Estado",
    hover_data={"Parcelas": True, "Latitud": False, "Longitud": False},  
    size_max=6,  # círculos pequeños
    color_continuous_scale="Plasma",
    zoom=4.5,
    center={"lat": 23.0, "lon": -102.0},
    mapbox_style="carto-positron",
    title="📍 Número de Parcelas Atendidas por Estado"
)

# --- Ajuste dinámico de escala de colores ---
cmin = parcelas_estado["Parcelas"].min()
cmax = parcelas_estado["Parcelas"].max()

# Dividir la leyenda en 5–6 intervalos para mayor diversidad de colores
step = max(1, (cmax - cmin) // 6)

fig_estado.update_traces(
    marker=dict(
        sizemode="area",
        sizeref=30,  # controlar tamaño de círculos
        sizemin=1,
        color=parcelas_estado["Parcelas"],
        cmin=cmin,
        cmax=cmax,
        showscale=True
    ),
    text=parcelas_estado["Parcelas"],  
    textposition="top center"
)

# --- Leyenda y layout general ---
fig_estado.update_layout(
    margin={"l":0,"r":0,"t":50,"b":0},
    height=700,
    coloraxis_colorbar=dict(
        title="Parcelas",
        tickvals=list(range(cmin, cmax + step, step)),
        ticktext=[f"{v//1000}k" for v in range(cmin, cmax + step, step)]
    )
)

# --- Mostrar en Streamlit ---
st.plotly_chart(fig_estado, use_container_width=True)
