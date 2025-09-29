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

# ----------------------------
# --- Preprocesamiento ---
# ----------------------------
columnas_requeridas = [
    "Anio", "Categoria_Proyecto", "Ciclo", "Estado",
    "Tipo_Regimen_Hidrico", "Tipo_parcela", "Area_total_de_la_parcela(ha)",
    "Proyecto", "Id_Parcela(Unico)", "Id_Productor", "Genero", "Latitud", "Longitud", "Cultivo(s)", "Tipo de sistema", "HUB_Agroecológico"
]

for columna in columnas_requeridas:
    if columna not in datos.columns:
        st.error(f"La columna '{columna}' no existe en el archivo CSV.")
        st.stop()
    datos[columna] = datos[columna].fillna("NA" if datos[columna].dtype == "object" else 0)

columnas_categoricas = ["Categoria_Proyecto", "Ciclo", "Estado", "Tipo_Regimen_Hidrico", "Tipo_parcela", "Proyecto"]
for col in columnas_categoricas:
    datos[col] = datos[col].astype(str)

datos["Anio"] = pd.to_numeric(datos["Anio"], errors="coerce")
datos["Area_total_de_la_parcela(ha)"] = pd.to_numeric(datos["Area_total_de_la_parcela(ha)"], errors="coerce").fillna(0)
datos = datos[(datos["Anio"] >= 2012) & (datos["Anio"] <= 2025)]

color_map_parcela = {
    "Área de Impacto": "#87CEEB",
    "Área de extensión": "#2ca02c",
    "Módulo": "#d62728",
}

# ----------------------------
# --- Filtros con últimos 2 años preseleccionados ---
# ----------------------------

# --- Sidebar de filtros encadenados ---
st.sidebar.header(" 🔽 Filtros")

# --- Función para checkboxes con opción de seleccionar todos ---
def checkbox_list(label, opciones, prefix, preseleccionadas=None):
    """Crea un grupo de checkboxes con opción de seleccionar/deseleccionar todo"""
    st.sidebar.markdown(f"**{label}**")
    seleccionadas = []
    for o in opciones:
        default_value = o in preseleccionadas if preseleccionadas else True
        key_name = f"{prefix}_{str(o)}"
        if st.sidebar.checkbox(str(o), value=default_value, key=key_name):
            seleccionadas.append(o)
    return seleccionadas

# --- Preselección de años (últimos 2 años) ---
ultimos_anos = sorted(datos["Anio"].dropna().unique())[-2:]
opciones_anio = sorted(datos["Anio"].unique())
seleccion_anio = checkbox_list("Año", opciones_anio, "anio", preseleccionadas=ultimos_anos)
datos_filtrados = datos[datos["Anio"].isin(seleccion_anio)].copy()

# --- Filtro por HUB Agroecológico ---
hubs = sorted(datos_filtrados["HUB_Agroecológico"].dropna().unique())
seleccion_hubs = checkbox_list("HUB Agroecológico", hubs, "hub")
if seleccion_hubs:
    datos_filtrados = datos_filtrados[datos_filtrados["HUB_Agroecológico"].isin(seleccion_hubs)]

# --- Filtro por Categoría del Proyecto ---
categorias = sorted(datos_filtrados["Categoria_Proyecto"].unique())
seleccion_categorias = checkbox_list("Categoría del Proyecto", categorias, "categoria")
if seleccion_categorias:
    datos_filtrados = datos_filtrados[datos_filtrados["Categoria_Proyecto"].isin(seleccion_categorias)]

# --- Filtro por Proyecto ---
proyectos = sorted(datos_filtrados["Proyecto"].unique())
seleccion_proyectos = checkbox_list("Proyecto", proyectos, "proyecto")
if seleccion_proyectos:
    datos_filtrados = datos_filtrados[datos_filtrados["Proyecto"].isin(seleccion_proyectos)]

# --- Filtro por Ciclo ---
ciclos = sorted(datos_filtrados["Ciclo"].unique())
seleccion_ciclos = checkbox_list("Ciclo", ciclos, "ciclo")
if seleccion_ciclos:
    datos_filtrados = datos_filtrados[datos_filtrados["Ciclo"].isin(seleccion_ciclos)]

# --- Crear columna con categorías de cultivo ---
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

datos_filtrados["Cultivo_Categorizado"] = datos_filtrados["Cultivo(s)"].apply(clasificar_cultivo_multiple)

# --- Filtro por Tipo de Parcela ---
tipos_parcela = sorted(datos_filtrados["Tipo_parcela"].unique())
seleccion_tipos_parcela = checkbox_list("Tipo de Parcela", tipos_parcela, "parcela")
if seleccion_tipos_parcela:
    datos_filtrados = datos_filtrados[datos_filtrados["Tipo_parcela"].isin(seleccion_tipos_parcela)]

# --- Filtro por Estado ---
estados = sorted(datos_filtrados["Estado"].unique())
seleccion_estados = checkbox_list("Estado", estados, "estado")
if seleccion_estados:
    datos_filtrados = datos_filtrados[datos_filtrados["Estado"].isin(seleccion_estados)]

# --- Filtro por Tipo de sistema ---
opciones_sistema = sorted(datos_filtrados["Tipo de sistema"].unique())
seleccion_sistema = checkbox_list("Tipo de sistema", opciones_sistema, "sistema")
if seleccion_sistema:
    datos_filtrados = datos_filtrados[datos_filtrados["Tipo de sistema"].isin(seleccion_sistema)]

# --- Filtro por Cultivo(s) ---
opciones_cultivo = ["Maíz", "Trigo", "Avena", "Cebada", "Frijol", "Otros"]
seleccion_cultivos = checkbox_list("Cultivo(s)", opciones_cultivo, "cultivo")
if seleccion_cultivos:
    datos_filtrados = datos_filtrados[
        datos_filtrados["Cultivo_Categorizado"].apply(lambda cats: any(c in seleccion_cultivos for c in cats))
    ]

# --- Resumen de filtros aplicados ---
st.markdown("### Filtros Aplicados")
filtros_texto = []
def mostrar_filtro(nombre, seleccion):
    if seleccion:
        filtros_texto.append(f"**{nombre}:** {', '.join(str(s) for s in seleccion)}")
    else:
        filtros_texto.append(f"**{nombre}:** Todos")

mostrar_filtro("Años", seleccion_anio)
mostrar_filtro("HUBs Agroecológicos", seleccion_hubs)
mostrar_filtro("Categoría", seleccion_categorias)
mostrar_filtro("Proyectos", seleccion_proyectos)
mostrar_filtro("Ciclos", seleccion_ciclos)
mostrar_filtro("Tipos de Parcela", seleccion_tipos_parcela)
mostrar_filtro("Estados", seleccion_estados)
mostrar_filtro("Tipo de sistema", seleccion_sistema)
mostrar_filtro("Cultivo(s)", seleccion_cultivos)

st.markdown(",  ".join(filtros_texto) if filtros_texto else "No se aplicaron filtros, se muestran todos los datos.")


# ----------------------------
# --- Métricas principales ---
# ----------------------------
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


# Asegurar que la columna Año siempre sea numérica
datos_filtrados["Anio"] = pd.to_numeric(datos_filtrados["Anio"], errors="coerce").astype("Int64")

# --- Gráficas principales ---
col5, col6 = st.columns(2)

with col5:
    color_arg = "Tipo_parcela" if seleccion_tipos_parcela else None
    bitacoras_por_anio = (
        datos_filtrados.groupby(["Anio", "Tipo_parcela"]).size().reset_index(name="Bitácoras")
        if color_arg else datos_filtrados.groupby("Anio").size().reset_index(name="Bitácoras")
    )
    fig_bitacoras = px.bar(
        bitacoras_por_anio,
        x="Anio",
        y="Bitácoras",
        color=color_arg,
        color_discrete_map=color_map_parcela if color_arg else None,
        title="📋 Número de Bitácoras por Año"
    )
    fig_bitacoras.update_traces(marker=dict(line=dict(color="black", width=1)))
    fig_bitacoras.update_xaxes(tickmode="linear", dtick=1)  # ✅ forzar años enteros
    st.plotly_chart(fig_bitacoras, use_container_width=True)

with col6:
    area_por_anio = (
        datos_filtrados.groupby(["Anio", "Tipo_parcela"])["Area_total_de_la_parcela(ha)"].sum().reset_index()
        if seleccion_tipos_parcela else datos_filtrados.groupby("Anio")["Area_total_de_la_parcela(ha)"].sum().reset_index()
    )
    fig_area = px.bar(
        area_por_anio,
        x="Anio",
        y="Area_total_de_la_parcela(ha)",
        color="Tipo_parcela" if seleccion_tipos_parcela else None,
        color_discrete_map=color_map_parcela if seleccion_tipos_parcela else None,
        title="🌿 Área Total de Parcelas por Año",
        labels={"Area_total_de_la_parcela(ha)": "Área (ha)"}
    )
    fig_area.update_traces(marker=dict(line=dict(color="black", width=1)))
    fig_area.update_xaxes(tickmode="linear", dtick=1)  # ✅
    st.plotly_chart(fig_area, use_container_width=True)

col7, col8 = st.columns(2)

with col7:
    if "Id_Parcela(Unico)" in datos_filtrados.columns:
        parcelas_por_anio = (
            datos_filtrados.groupby(["Anio", "Tipo_parcela"])["Id_Parcela(Unico)"].nunique().reset_index()
            if seleccion_tipos_parcela else datos_filtrados.groupby("Anio")["Id_Parcela(Unico)"].nunique().reset_index()
        )
        fig_parcelas = px.bar(
            parcelas_por_anio,
            x="Anio",
            y="Id_Parcela(Unico)",
            color="Tipo_parcela" if seleccion_tipos_parcela else None,
            color_discrete_map=color_map_parcela if seleccion_tipos_parcela else None,
            title="🌄 Número de Parcelas por Año",
            labels={"Id_Parcela(Unico)": "Parcelas"}
        )
        fig_parcelas.update_traces(marker=dict(line=dict(color="black", width=1)))
        fig_parcelas.update_xaxes(tickmode="linear", dtick=1)  # ✅
        st.plotly_chart(fig_parcelas, use_container_width=True)

with col8:
    if "Id_Productor" in datos_filtrados.columns:
        productores_por_anio = (
            datos_filtrados.groupby(["Anio", "Tipo_parcela"])["Id_Productor"].nunique().reset_index()
            if seleccion_tipos_parcela else datos_filtrados.groupby("Anio")["Id_Productor"].nunique().reset_index()
        )
        fig_productores = px.bar(
            productores_por_anio,
            x="Anio",
            y="Id_Productor",
            color="Tipo_parcela" if seleccion_tipos_parcela else None,
            color_discrete_map=color_map_parcela if seleccion_tipos_parcela else None,
            title="👩‍🌾👨‍🌾 Número de Productores por Año",
            labels={"Id_Productor": "Productores"}
        )
        fig_productores.update_traces(marker=dict(line=dict(color="black", width=1)))
        fig_productores.update_xaxes(tickmode="linear", dtick=1)  # ✅
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
conteo_pivot.insert(0, "🔢 Bitacoras ", total_anual.set_index("Anio")["Total"])

# Insertar "Proyecto Dominante" justo después (posición 1)
conteo_pivot.insert(1, "🏆 Proyecto Dominante", proyecto_max)

# Convertir tabla final y redondear solo columnas numéricas
tabla_final = conteo_pivot.copy()

for col in tabla_final.columns:
    if pd.api.types.is_numeric_dtype(tabla_final[col]):
        # Redondear floats a 2 decimales
        tabla_final[col] = tabla_final[col].apply(lambda x: round(x, 2) if pd.notnull(x) else x)

# Asegurar que "🔢 Bitacoras " sea entero
if "🔢 Bitacoras " in tabla_final.columns:
    tabla_final["🔢 Bitacoras "] = tabla_final["🔢 Bitacoras "].astype(int)

# Mostrar tabla final en Streamlit
st.markdown("### 📋 Número Total de Bitácoras y Distribución(%) por Proyecto y Categoría, por Año")
st.dataframe(tabla_final.reset_index(), use_container_width=False, height=min(120, 60* len(tabla_final)))





# ----------

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

#----------------------------------


import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import geopandas as gpd
import numpy as np

# --- --- --- Preparar datos de parcelas (tu código original) --- --- --- #
datos_filtrados["Latitud"] = pd.to_numeric(datos_filtrados["Latitud"], errors="coerce")
datos_filtrados["Longitud"] = pd.to_numeric(datos_filtrados["Longitud"], errors="coerce")
datos_geo = datos_filtrados.dropna(subset=["Latitud", "Longitud"])

datos_geo["Latitud_r"] = datos_geo["Latitud"].round(4)
datos_geo["Longitud_r"] = datos_geo["Longitud"].round(4)

def muestrear_puntos(df, max_puntos=5000):
    if len(df) > max_puntos:
        return df.sample(n=max_puntos, random_state=1)
    return df

# --- --- --- Función original de parcelas --- --- --- #
def crear_figura(datos_filtrados, zoom=4):
    datos_geo_filtrado = datos_filtrados.dropna(subset=["Latitud", "Longitud"]).copy()
    datos_geo_filtrado["Latitud_r"] = datos_geo_filtrado["Latitud"].round(4)
    datos_geo_filtrado["Longitud_r"] = datos_geo_filtrado["Longitud"].round(4)

    parcelas_geo = (
        datos_geo_filtrado.groupby(["Latitud_r", "Longitud_r", "Tipo_parcela"])
        .agg(
            Parcelas=("Id_Parcela(Unico)", "nunique"),
            Cultivos_unicos=("Cultivo(s)", lambda x: ", ".join([str(i) for i in x.dropna().unique()]))
        )
        .reset_index()
        .rename(columns={"Latitud_r": "Latitud", "Longitud_r": "Longitud", "Cultivos_unicos": "Cultivo(s)"})
    )

    parcelas_geo = muestrear_puntos(parcelas_geo, max_puntos=5000)

    colores_parcela_dict = {
        "Área de Impacto": "#87CEEB",
        "Área de extensión": "#2ca02c",
        "Módulo": "#d62728"
    }

    fig = go.Figure()
    for tipo, color in colores_parcela_dict.items():
        df_tipo = parcelas_geo[parcelas_geo["Tipo_parcela"] == tipo]
        if not df_tipo.empty:
            tamanios_base = np.clip(df_tipo["Parcelas"] * 2, 5, 25)
            tamanios = tamanios_base * (zoom / 4)
            fig.add_trace(go.Scattermapbox(
                lat=df_tipo["Latitud"],
                lon=df_tipo["Longitud"],
                mode="markers",
                marker=dict(size=tamanios, sizemode="area", color=color),
                text=df_tipo["Cultivo(s)"],
                hovertemplate="<b>%{text}</b><extra></extra>",
                name=tipo
            ))

    fig.update_layout(
        mapbox=dict(center={"lat": 23.0, "lon": -102.0}, zoom=zoom, style="carto-positron"),
        margin={"l":0,"r":0,"t":50,"b":0},
        height=700,
        width=900,
        title="📍 Distribución de Parcelas Atendidas",
        legend=dict(
            title="Tipo de Parcela",
            orientation="v",
            x=1.05,
            y=1,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="black",
            borderwidth=1
        )
    )
    return fig

# --- --- --- Streamlit --- --- --- #
zoom = st.slider("Nivel de zoom del mapa", 4, 12, 4)

# Crear figura de parcelas
fig_mapa_geo = crear_figura(datos_filtrados, zoom=zoom)

# --- --- --- Cargar y filtrar HUBs --- --- --- #
hubs = gpd.read_parquet("HUBs.parquet")
if "Nombre" not in hubs.columns:
    hubs["Nombre"] = [f"HUB {i}" for i in range(len(hubs))]

hub_seleccionado = st.selectbox("Selecciona HUB", ["Todos"] + list(hubs["Nombre"].unique()))
hubs_to_plot = hubs if hub_seleccionado == "Todos" else hubs[hubs["Nombre"] == hub_seleccionado]

# Colores HUBs
unique_hubs = hubs["Nombre"].unique()
palette = px.colors.qualitative.Set3 * ((len(unique_hubs) // 12) + 1)
hub_color_dict = {hub: palette[i] for i, hub in enumerate(unique_hubs)}

# --- --- --- Agregar HUBs encima (solo un elemento en la leyenda por HUB) --- --- --- #
for _, row in hubs_to_plot.iterrows():
    geom = row.geometry
    geoms = [geom] if geom.geom_type == "Polygon" else geom.geoms
    for i, poly in enumerate(geoms):
        x, y = poly.exterior.xy
        fig_mapa_geo.add_trace(go.Scattermapbox(
            lat=list(y),
            lon=list(x),
            mode="lines",
            fill="toself",
            fillcolor=hub_color_dict[row["Nombre"]].replace("rgb", "rgba").replace(")", ",0.3)"),
            line=dict(color=hub_color_dict[row["Nombre"]], width=2),
            name=f"HUB - {row['Nombre']}" if i==0 else None,
            showlegend=True if i==0 else False,
            hovertext=f"HUB: {row['Nombre']}",
            hoverinfo="text"
        ))

# Mostrar mapa final
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
    zoom=4.0,
    center={"lat": 23.0, "lon": -102.0},
    mapbox_style="carto-positron",
    title="📍 Intensidad de Parcelas Atendidas por Estado"
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
    width=900,
    coloraxis_colorbar=dict(
        title="Parcelas",
        tickvals=list(range(cmin, cmax + step, step)),
        ticktext=[f"{v//1000}k" for v in range(cmin, cmax + step, step)]
    )
)

# --- Mostrar en Streamlit ---
st.plotly_chart(fig_estado, use_container_width=True)





