import zipfile
import pandas as pd
import streamlit as st
from io import BytesIO

st.title('Cargar CSV desde un ZIP automáticamente')

# Cargar el archivo ZIP
uploaded_file = st.file_uploader("Sube un archivo ZIP", type="zip")

if uploaded_file is not None:
    try:
        # Abrir el archivo ZIP
        with zipfile.ZipFile(uploaded_file, 'r') as z:
            # Buscar archivos que terminen en .csv
            csv_files = [name for name in z.namelist() if name.endswith('.csv')]

            if csv_files:
                # Seleccionar el primer CSV encontrado
                csv_filename = csv_files[0]
                st.write(f"📄 CSV detectado automáticamente: {csv_filename}")

                # Leer el CSV dentro del ZIP
                with z.open(csv_filename) as f:
                    df = pd.read_csv(f)

                # Mostrar los primeros datos
                st.dataframe(df)

            else:
                st.error("❌ No se encontró ningún archivo CSV dentro del ZIP.")
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
