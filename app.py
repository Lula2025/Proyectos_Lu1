import pandas as pd
import zipfile
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# Leer archivo ZIP
archivo_zip = "Archivos.zip"
nombre_csv = "Datos_Historicos_cuenta_al26032025.csv"

# Leer el archivo CSV directamente desde el ZIP
try:
    with zipfile.ZipFile(archivo_zip, 'r') as z:
        with z.open(nombre_csv) as f:
            datos = pd.read_csv(f)
    print("Archivo cargado exitosamente desde el ZIP.")
except FileNotFoundError:
    print(f"Error: El archivo '{archivo_zip}' no se encontró.")
    exit()
except KeyError:
    print(f"Error: El archivo '{nombre_csv}' no está dentro del ZIP.")
    exit()

# Preprocesamiento
columnas_requeridas = ["Anio", "Categoria_Proyecto", "Ciclo", "Estado", "Tipo_Regimen_Hidrico", "Tipo_parcela", "Area_total_de_la_parcela(ha)"]
for columna in columnas_requeridas:
    if columna not in datos.columns:
        raise ValueError(f"La columna '{columna}' no existe en el archivo CSV.")

for columna in columnas_requeridas:
    datos[columna] = datos[columna].fillna("NA")

datos["Anio"] = pd.to_numeric(datos["Anio"], errors="coerce")
datos["Area_total_de_la_parcela(ha)"] = pd.to_numeric(datos["Area_total_de_la_parcela(ha)"], errors="coerce").fillna(0)
datos = datos[(datos["Anio"] >= 2012) & (datos["Anio"] <= 2025)]

datos_agrupados = datos.groupby(
    ["Anio", "Categoria_Proyecto", "Ciclo", "Estado", "Tipo_Regimen_Hidrico", "Tipo_parcela"]
).size().reset_index(name="Observaciones")

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Img(src="/assets/cimmyt.png", style={"height": "100px", "marginRight": "20px"}),
        html.H1("Datos Históricos 2012-marzo2025. Bitácoras Agronómicas", style={"textAlign": "center", "flex": "1"}),
        html.Img(src="/assets/ea.png", style={"height": "100px", "marginLeft": "20px"})
    ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "10px 20px"}),

    html.Div([
        html.Div([
            html.Div(id="total-observaciones", style={"textAlign": "center", "marginBottom": "10px", "fontSize": "18px", "fontWeight": "bold"}),
            dcc.Graph(id="grafico-observaciones", style={"height": "800px", "marginBottom": "50px"}),
            html.Hr(),

            html.Div(id="total-area", style={"textAlign": "center", "marginBottom": "10px", "fontSize": "18px", "fontWeight": "bold"}),
            dcc.Graph(id="grafico-area-total", style={"height": "800px", "marginBottom": "50px"}),
            html.Hr(),

            html.Div(id="total-parcelas", style={"textAlign": "center", "marginBottom": "10px", "fontSize": "18px", "fontWeight": "bold"}),
            dcc.Graph(id="grafico-parcelas", style={"height": "800px"}),
            html.Hr(),

            html.Div(id="total-productores", style={"textAlign": "center", "marginBottom": "10px", "fontSize": "18px", "fontWeight": "bold"}),
            dcc.Graph(id="grafico-productores", style={"height": "800px", "marginBottom": "50px"}),
            html.Hr(),

            html.Div(id="total-genero", style={"textAlign": "center", "marginBottom": "10px", "fontSize": "18px", "fontWeight": "bold"}),
            dcc.Graph(id="grafico-genero", style={"height": "800px"})
        ], style={"width": "80%", "padding": "20px"}),

        html.Div([
            html.Label("Categoría del Proyecto:"),
            dcc.Dropdown(id="categoria-dropdown", options=[{"label": "Todos", "value": "Todos"}] + [{"label": cat, "value": cat} for cat in datos_agrupados["Categoria_Proyecto"].unique()], value="Todos"),
            html.Label("Ciclo:"),
            dcc.Dropdown(id="ciclo-dropdown", options=[{"label": "Todos", "value": "Todos"}] + [{"label": ciclo, "value": ciclo} for ciclo in datos_agrupados["Ciclo"].unique()], value="Todos"),
            html.Label("Tipo de Parcela:"),
            dcc.Dropdown(id="tipo-parcela-dropdown", options=[{"label": "Todos", "value": "Todos"}] + [{"label": tipo, "value": tipo} for tipo in datos_agrupados["Tipo_parcela"].unique()], value="Todos"),
            html.Label("Estado:"),
            dcc.Dropdown(id="estado-dropdown", options=[{"label": "Todos", "value": "Todos"}] + [{"label": estado, "value": estado} for estado in datos_agrupados["Estado"].unique()], value="Todos"),
            html.Label("Régimen Hídrico:"),
            dcc.Dropdown(id="regimen-dropdown", options=[{"label": "Todos", "value": "Todos"}] + [{"label": regimen, "value": regimen} for regimen in datos_agrupados["Tipo_Regimen_Hidrico"].unique()], value="Todos")
        ], className="filters-container", style={"width": "15%", "padding": "10px", "borderLeft": "1px solid #ccc", "position": "sticky", "top": "0", "backgroundColor": "white", "zIndex": "1000", "overflowY": "auto", "height": "auto", "textAlign": "center"})
    ], style={"display": "flex", "flexDirection": "row", "height": "100%", "margin": "0 50px"})
])

# Agregá aquí tus callbacks personalizados como los tenías

# Callback para actualizar el gráfico y el total de observaciones
@app.callback(
    [Output("grafico-observaciones", "figure"), Output("total-observaciones", "children")],
    [Input("categoria-dropdown", "value"), Input("ciclo-dropdown", "value"), Input("tipo-parcela-dropdown", "value"),
     Input("estado-dropdown", "value"), Input("regimen-dropdown", "value")]
)
def actualizar_grafico_y_total(categoria, ciclo, tipo_parcela, estado, regimen):
    datos_filtrados = datos_agrupados.copy()
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

    datos_agrupados_filtrados = datos_filtrados.groupby("Anio")["Observaciones"].sum().reset_index()

    fig = px.bar(datos_agrupados_filtrados, x="Anio", y="Observaciones", title="Número de Bitácoras por Año")
    
    fig.update_layout(
        title={
            "text": "Número de Bitácoras por Año",
            "font": {"size": 24},  # Cambia el tamaño del título aquí
            "x": 0.1  
        }
    )
    
    total_observaciones = datos_filtrados["Observaciones"].sum()
    return fig, f"Total de Bitácoras: {total_observaciones}"

# Callback para actualizar el gráfico y el total del área
@app.callback(
    [Output("grafico-area-total", "figure"), Output("total-area", "children")],
    [Input("categoria-dropdown", "value"), Input("ciclo-dropdown", "value"), Input("tipo-parcela-dropdown", "value"),
     Input("estado-dropdown", "value"), Input("regimen-dropdown", "value")]
)
def actualizar_grafico_area(categoria, ciclo, tipo_parcela, estado, regimen):
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

    datos_agrupados_area = datos_filtrados.groupby("Anio")["Area_total_de_la_parcela(ha)"].sum().reset_index()
    fig = px.bar(
        datos_agrupados_area,
        x="Anio",
        y="Area_total_de_la_parcela(ha)",
        title="Superficie (ha) de las Parcelas por Año",
        labels={"Area_total_de_la_parcela(ha)": "Área (ha)"}  # Cambiar etiqueta del eje y
    )
       # Cambiar el tamaño del título
    fig.update_layout(
        title={
            "text": "Superficie (ha) de las Parcelas por Año",
            "font": {"size": 24},  # Cambia el tamaño del título aquí
            "x": 0.1  # Centra el título horizontalmente
        }
    )
    
    total_area = datos_filtrados["Area_total_de_la_parcela(ha)"].sum()
    return fig, f"Total de Área (ha): {total_area:.2f}"

# Callback para actualizar el gráfico y el total de valores únicos de Id_Parcela(Unico)
@app.callback(
    [Output("grafico-parcelas", "figure"), Output("total-parcelas", "children")],
    [Input("categoria-dropdown", "value"), Input("ciclo-dropdown", "value"), Input("tipo-parcela-dropdown", "value"),
     Input("estado-dropdown", "value"), Input("regimen-dropdown", "value")]
)
def actualizar_grafico_parcelas(categoria, ciclo, tipo_parcela, estado, regimen):
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

    # Calcular valores únicos de Id_Parcela(Unico) por año
    datos_agrupados_parcelas = datos_filtrados.groupby("Anio")["Id_Parcela(Unico)"].nunique().reset_index()
    fig = px.bar(
        datos_agrupados_parcelas,
        x="Anio",
        y="Id_Parcela(Unico)",
        title="Número de Parcelas por Año",
        labels={"Id_Parcela(Unico)": "Parcelas"}
    )

    # Cambiar el tamaño del título
    fig.update_layout(
        title={
            "text": "Número de Parcelas por Año",
            "font": {"size": 24},  # Cambia el tamaño del título aquí
            "x": 0.1  # Centra el título horizontalmente
        }
    )
    total_parcelas = datos_filtrados["Id_Parcela(Unico)"].nunique()
    return fig, f"Total de Parcelas: {total_parcelas}"

# Callback para actualizar el gráfico y el total de valores únicos de Id_Productor
@app.callback(
    [Output("grafico-productores", "figure"), Output("total-productores", "children")],
    [Input("categoria-dropdown", "value"), Input("ciclo-dropdown", "value"), Input("tipo-parcela-dropdown", "value"),
     Input("estado-dropdown", "value"), Input("regimen-dropdown", "value")]
)
def actualizar_grafico_productores(categoria, ciclo, tipo_parcela, estado, regimen):
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

    # Calcular valores únicos de Id_Productor por año
    datos_agrupados_productores = datos_filtrados.groupby("Anio")["Id_Productor"].nunique().reset_index()
    fig = px.bar(
        datos_agrupados_productores,
        x="Anio",
        y="Id_Productor",
        title="Número de Productores por Año",
        labels={"Id_Productor": "Productores"}
    )
    # Cambiar el tamaño del título
    fig.update_layout(
        title={
            "text": "Número de Productores por Año",
            "font": {"size": 24},  # Cambia el tamaño del título aquí
            "x": 0.1  # Centra el título horizontalmente
        }
    )

    total_productores = datos_filtrados["Id_Productor"].nunique()
    return fig, f"Total de Productores: {total_productores}"



# Callback para actualizar la gráfica de género
@app.callback(
    Output("grafico-genero", "figure"),
    [Input("categoria-dropdown", "value"), Input("ciclo-dropdown", "value"), Input("tipo-parcela-dropdown", "value"),
     Input("estado-dropdown", "value"), Input("regimen-dropdown", "value")]
)
def actualizar_grafico_genero(categoria, ciclo, tipo_parcela, estado, regimen):
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

    # Calcular el porcentaje por género
    if "Genero" not in datos_filtrados.columns:
        return {}

    datos_genero = datos_filtrados.groupby("Genero").size().reset_index(name="Registros")
    datos_genero["Porcentaje"] = (datos_genero["Registros"] / datos_genero["Registros"].sum()) * 100

    # Definir colores fijos para cada género
    colores_fijos = {
        "Masculino": "#2ca02c",
        "Femenino": "#ff7f0e",
        "NA..": "#D3D3D3"
    }

    # Crear la gráfica
    fig = px.pie(
        datos_genero,
        names="Genero",
        values="Porcentaje",
        title="Distribución (%) por Género de Productores(as)",
        labels={"Genero": "Género", "Porcentaje": "Porcentaje"}
    )
    # Cambiar el tamaño del título
    fig.update_layout(
        title={
            "text": "Distribución (%) por Género de Productores(as)",
            "font": {"size": 24},  # Cambia el tamaño del título aquí
            "x": 0.1  # Centra el título horizontalmente
        }
    )
    # Aplicar los colores fijos
    fig.update_traces(marker=dict(colors=[colores_fijos.get(genero, "#7f7f7f") for genero in datos_genero["Genero"]]))

    return fig

if __name__ == "__main__":
    app.run (debug=True, port=8051)