import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Simulador EGEL CENEVAL", page_icon="📝")

# 1. Cargar los datos desde tu enlace de Google Sheets (CSV)
URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

@st.cache_data
def cargar_preguntas():
    return pd.read_csv(URL_DATOS)

df = cargar_preguntas()

# Título de la aplicación
st.title("🚀 Simulador de Examen EGEL CENEVAL")
st.write("Responde a las preguntas para poner a prueba tus conocimientos.")

# Inicializar variables de estado (para guardar el progreso)
if 'indice_pregunta' not in st.session_state:
    st.session_state.indice_pregunta = 0
if 'puntaje' not in st.session_state:
    st.session_state.puntaje = 0

# Verificar si aún hay preguntas disponibles
if st.session_state.indice_pregunta < len(df):
    # Obtener la pregunta actual del DataFrame
    fila = df.iloc[st.session_state.indice_pregunta]
    
    st.subheader(f"Pregunta {st.session_state.indice_pregunta + 1}:")
    st.info(fila['Pregunta']) # Ajusta 'Pregunta' al nombre exacto de tu columna

    # Opciones (Asumiendo que tus columnas se llaman 'A', 'B', 'C', 'D')
    opciones = [fila['A'], fila['B'], fila['C'], fila['D']]
    respuesta_correcta = fila['Correcta'] # Ajusta al nombre de tu columna con la respuesta

    # Mostrar radio buttons para seleccionar respuesta
    seleccion = st.radio("Selecciona una opción:", opciones, key=f"p_{st.session_state.indice_pregunta}")

    # Botón para calificar y pasar a la siguiente
    if st.button("Enviar respuesta"):
        if seleccion == respuesta_correcta:
            st.success("¡Correcto! ✨")
            st.session_state.puntaje += 1
        else:
            st.error(f"Incorrecto. La respuesta era: {respuesta_correcta}")
        
        # Avanzar al siguiente índice
        st.session_state.indice_pregunta += 1
        st.button("Siguiente pregunta")

else:
    # Pantalla final de resultados
    st.balloons()
    st.header("¡Has terminado el simulador!")
    st.metric("Tu puntaje final es:", f"{st.session_state.puntaje} / {len(df)}")
    
    if st.button("Reiniciar Simulador"):
        st.session_state.indice_pregunta = 0
        st.session_state.puntaje = 0

        st.rerun()
