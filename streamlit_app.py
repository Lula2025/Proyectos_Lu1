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


 

# --- Inicializar filtros ---
filtros_dict = {}

# --- Filtro Año (checkboxes con selección de los últimos 2 años por defecto) ---
ultimos_anios = sorted(datos_filtrados["Anio"].dropna().unique())[-2:]

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

opciones_anio = sorted(datos_filtrados["Anio"].dropna().unique())
seleccion_anio = checkbox_list("Año", opciones_anio, seleccion_previa=ultimos_anios)
datos_filtrados = datos_filtrados[datos_filtrados["Anio"].isin(seleccion_anio)]

# --- Filtros encadenados (solo columnas que existen) ---
columnas_filtro = ["HUB_Agroecológico", "Categoria_Proyecto", "Proyecto", "Ciclo",
                   "Tipo_parcela", "Estado", "Tipo de sistema"]

# Función multiselect segura
def filtro_multiselect(columna, label):
    if columna not in datos_filtrados.columns:
        st.warning(f"El filtro '{label}' no está disponible (columna no existe).")
        return []
    opciones = sorted(datos_filtrados[columna].dropna().unique())
    seleccion = st.sidebar.multiselect(label, opciones, default=opciones)
    return seleccion

for col in columnas_filtro:
    seleccion = filtro_multiselect(col, col.replace("_"," "))
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
for nombre, seleccion in filtros_dict.items():
    if seleccion:
        filtros_texto.append(f"**{nombre}:** {', '.join(str(s) for s in seleccion)}")
    else:
        filtros_texto.append(f"**{nombre}:** Todos")
st.markdown(",  ".join(filtros_texto))



# -------------------- Resumen de cifras -------------------- #
col_area_name = next((c for c in datos_filtrados.columns if "Area_total" in c), None)
total_area = datos_filtrados[col_area_name].sum() if col_area_name else 0
total_bitacoras = len(datos_filtrados)
total_parcelas = datos_filtrados["Id_Parcela_Unico"].nunique() if "Id_Parcela_Unico" in datos_filtrados.columns else 0
total_productores = datos_filtrados["Id_Productor"].nunique() if "Id_Productor" in datos_filtrados.columns else 0

col_r1, col_r2, col_r3, col_r4 = st.columns(4)
col_r1.metric("📋 Total de Bitácoras", f"{total_bitacoras:,}")
col_r2.metric("🌿 Área Total (ha)", f"{total_area:,.2f}")
col_r3.metric("🌄 Número de Parcelas Totales", f"{total_parcelas:,}")
col_r4.metric("👩‍🌾 Productores(as) Totales", f"{total_productores:,}")

# -------------------- Gráficos principales -------------------- #
if not datos_filtrados.empty:
    color_arg = "Tipo_parcela" if filtros_dict["Tipo_parcela"] else None

    # Bitácoras por año
    bitacoras_por_anio = (
        datos_filtrados.groupby(["Anio","Tipo_parcela"]).size().reset_index(name="Bitácoras")
        if color_arg else datos_filtrados.groupby("Anio").size().reset_index(name="Bitácoras")
    )
    fig_bitacoras = px.bar(bitacoras_por_anio, x="Anio", y="Bitácoras", color=color_arg,
                           title="📋 Número de Bitácoras por Año")
    st.plotly_chart(fig_bitacoras, use_container_width=True)

    # Área por año
    if col_area_name:
        area_por_anio = (
            datos_filtrados.groupby(["Anio","Tipo_parcela"])[col_area_name].sum().reset_index()
            if color_arg else datos_filtrados.groupby("Anio")[col_area_name].sum().reset_index()
        )
        fig_area = px.bar(area_por_anio, x="Anio", y=col_area_name, color=color_arg,
                          title="🌿 Área Total de Parcelas por Año",
                          labels={col_area_name:"Área (ha)"})
        st.plotly_chart(fig_area, use_container_width=True)

    # Parcelas por año
    if "Id_Parcela_Unico" in datos_filtrados.columns:
        parcelas_por_anio = (
            datos_filtrados.groupby(["Anio","Tipo_parcela"])["Id_Parcela_Unico"].nunique().reset_index()
            if color_arg else datos_filtrados.groupby("Anio")["Id_Parcela_Unico"].nunique().reset_index()
        )
        fig_parcelas = px.bar(parcelas_por_anio, x="Anio", y="Id_Parcela_Unico", color=color_arg,
                              title="🌄 Número de Parcelas por Año",
                              labels={"Id_Parcela_Unico":"Parcelas"})
        st.plotly_chart(fig_parcelas, use_container_width=True)

    # Productores por año
    if "Id_Productor" in datos_filtrados.columns:
        productores_por_anio = (
            datos_filtrados.groupby(["Anio","Tipo_parcela"])["Id_Productor"].nunique().reset_index()
            if color_arg else datos_filtrados.groupby("Anio")["Id_Productor"].nunique().reset_index()
        )
        fig_productores = px.bar(productores_por_anio, x="Anio", y="Id_Productor", color=color_arg,
                                 title="👩‍🌾👨‍🌾 Número de Productores por Año",
                                 labels={"Id_Productor":"Productores"})
        st.plotly_chart(fig_productores, use_container_width=True)
else:
    st.info("No hay datos para mostrar con los filtros seleccionados.")

# -------------------- Distribución por género -------------------- #
if "Genero" in datos_filtrados.columns:
    datos_filtrados["Genero"] = datos_filtrados["Genero"].fillna("NA..").replace({"Hombre":"Masculino","Mujer":"Femenino","NA":"NA.."})
    categorias_genero = ["Masculino","Femenino","NA.."]
    datos_genero = datos_filtrados.groupby("Genero").size().reset_index(name="Registros")
    datos_genero = datos_genero.set_index("Genero").reindex(categorias_genero, fill_value=0).reset_index()
    total_registros = datos_genero["Registros"].sum()
    datos_genero["Porcentaje"] = (datos_genero["Registros"] / total_registros * 100) if total_registros>0 else 0

    color_map_genero = {"Masculino":"#2ca02c","Femenino":"#ff7f0e","NA..":"#F0F0F0"}
    fig_genero = px.pie(datos_genero, names="Genero", values="Registros",
                        title="👩👨 Distribución Total de Productores(as) por Género",
                        color="Genero", color_discrete_map=color_map_genero)
    st.plotly_chart(fig_genero, use_container_width=True)

# -------------------- Evolución productores por género -------------------- #
if {"Genero","Anio","Id_Productor"}.issubset(datos_filtrados.columns):
    prod_gen_anio = datos_filtrados.groupby(["Anio","Genero"])["Id_Productor"].nunique().reset_index(name="Cantidad")
    totales_anio = prod_gen_anio.groupby("Anio")["Cantidad"].sum().reset_index(name="Total")
    prod_gen_anio = prod_gen_anio.merge(totales_anio,on="Anio")
    prod_gen_anio["Porcentaje"] = (prod_gen_anio["Cantidad"]/prod_gen_anio["Total"]*100).round(1)
    emoji_genero = {"Femenino":"👩 Mujeres","Masculino":"👨 Hombres","NA..":"❔ Sin dato"}
    prod_gen_anio["Genero_Emoji"] = prod_gen_anio["Genero"].map(emoji_genero)
    fig_gen_pct = px.bar(prod_gen_anio, x="Anio", y="Porcentaje", color="Genero_Emoji",
                         title="📊 Porcentaje de Productores(as) por Género y Año",
                         labels={"Porcentaje":"% del total por año"},
                         color_discrete_map={"👨 Hombres":"#2ca02c","👩 Mujeres":"#ff7f0e","❔ Sin dato":"#F0F0F0"},
                         text=prod_gen_anio["Porcentaje"].astype(str)+"%")
    fig_gen_pct.update_layout(barmode="stack")
    fig_gen_pct.update_traces(textposition="inside")
    st.plotly_chart(fig_gen_pct,use_container_width=True)

# -------------------- Mapas y tablas -------------------- #
def crear_figura(datos_filtrados):
    datos_geo = datos_filtrados.dropna(subset=["Latitud","Longitud"]).copy()
    if datos_geo.empty:
        return go.Figure()
    datos_geo["Latitud_r"] = datos_geo["Latitud"].round(4)
    datos_geo["Longitud_r"] = datos_geo["Longitud"].round(4)
    parcelas_geo = (
        datos_geo.groupby(["Latitud_r","Longitud_r","Tipo_parcela"])
        .agg(Parcelas=("Id_Parcela_Unico","nunique"),
             Cultivos_unicos=("Cultivo(s)", lambda x: ", ".join([str(i) for i in x.dropna().unique()])))
        .reset_index()
        .rename(columns={"Latitud_r":"Latitud","Longitud_r":"Longitud","Cultivos_unicos":"Cultivo(s)"})
    )
    colores_parcela_dict = {"Área de Impacto":"#87CEEB","Área de extensión":"#2ca02c","Módulo":"#d62728"}
    fig = go.Figure()
    for tipo,color in colores_parcela_dict.items():
        df_tipo = parcelas_geo[parcelas_geo["Tipo_parcela"]==tipo]
        if not df_tipo.empty:
            tamanios = np.clip(df_tipo["Parcelas"]*2,5,25)
            fig.add_trace(go.Scattermapbox(lat=df_tipo["Latitud"],lon=df_tipo["Longitud"],mode="markers",
                                           marker=dict(size=tamanios,sizemode="area",color=color),
                                           text=df_tipo["Cultivo(s)"], hovertemplate="<b>%{text}</b><extra></extra>",
                                           name=tipo))
    fig.update_layout(mapbox=dict(center={"lat":23.0,"lon":-102.0}, zoom=4, style="carto-positron"),
                      margin={"l":0,"r":0,"t":50,"b":0}, height=700, width=900,
                      title="📍 Distribución de Parcelas Atendidas")
    return fig

st.plotly_chart(crear_figura(datos_filtrados), use_container_width=True)


