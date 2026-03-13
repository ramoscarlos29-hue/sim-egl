import streamlit as st
import pandas as pd
import time
import random

# --- CONFIGURACIÓN DE DISEÑO (FOMENTA CONCENTRACIÓN) ---
st.set_page_config(page_title="Simulador EGEL Pro", page_icon="🎓", layout="wide")

# Estilo CSS para una interfaz limpia y minimalista
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stRadio > label { font-size: 18px; font-weight: bold; color: #1e3d59; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1e3d59; color: white; }
    .stProgress > div > div > div > div { background-color: #ffc13b; }
    </style>
    """, unsafe_allow_html=True)

URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_DATOS)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return None

# --- ESTADO DE LA SESIÓN ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'carrera': "", 'preguntas': None, 'feedback': None
    })

# --- PANTALLA DE REGISTRO ---
if not st.session_state.examen_iniciado:
    st.title("🛡️ Centro de Evaluación EGEL")
    st.subheader("Configura tu sesión de estudio")
    
    with st.container():
        nombre = st.text_input("Nombre del Estudiante:", placeholder="Ej. Juan Pérez")
        carrera = st.selectbox("Selecciona tu Carrera:", 
                              ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Iniciar Evaluación (20 Reactivos)"):
            if nombre:
                df_full = cargar_datos()
                if df_full is not None:
                    # Filtro por carrera y selección aleatoria de 20
                    # Asegúrate de tener una columna llamada 'Carrera' en tu Sheets
                    df_carrera = df_full[df_full['Carrera'] == carrera]
                    
                    if len(df_carrera) >= 20:
                        seleccionadas = df_carrera.sample(20)
                    else:
                        seleccionadas = df_carrera.sample(len(df_carrera))
                    
                    st.session_state.update({
                        'nombre': nombre, 'carrera': carrera,
                        'preguntas': seleccionadas, 'examen_iniciado': True
                    })
                    st.rerun()
            else:
                st.warning("Por favor, ingresa tu nombre.")

# --- PANTALLA DE EXAMEN ---
else:
    df = st.session_state.preguntas
    fila = df.iloc[st.session_state.indice]
    
    # Header de concentración
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.caption(f"Estudiante: {st.session_state.nombre} | Carrera: {st.session_state.carrera}")
    with col_b:
        st.write(f"Pregunta {st.session_state.indice + 1} / {len(df)}")
    
    st.progress((st.session_state.indice) / len(df))
    st.divider()

    # Pregunta y Opciones con Incisos
    st.markdown(f"### {fila['Pregunta']}")
    
    # Diccionario de opciones para mostrar incisos A), B)...
    dict_opciones = {
        f"A) {fila['A']}": fila['A'],
        f"B) {fila['B']}": fila['B'],
        f"C) {fila['C']}": fila['C'],
        f"D) {fila['D']}": fila['D']
    }

    with st.form(key=f"form_{st.session_state.indice}"):
        seleccion_display = st.radio("Elija la opción correcta:", list(dict_opciones.keys()))
        btn_validar = st.form_submit_button("Validar Respuesta")

    # Retroalimentación (Feedback)
    if btn_validar:
        valor_seleccionado = dict_opciones[seleccion_display]
        valor_correcto = str(fila['Correcta']).strip()
        
        if str(valor_seleccionado).strip() == valor_correcto:
            st.success(f"✅ **¡Correcto!** El inciso seleccionado es el adecuado.")
            st.session_state.puntaje += 1
        else:
            st.error(f"❌ **Incorrecto.** La respuesta correcta era: {valor_correcto}")
        
        # Mostrar explicación si existe en tu Sheets (columna opcional 'Feedback')
        if 'Feedback' in fila:
            st.info(f"💡 **Nota:** {fila['Feedback']}")
        
        time.sleep(2.5) # Tiempo para leer el feedback
        st.session_state.indice += 1
        st.rerun()

    # --- FINALIZACIÓN ---
    if st.session_state.indice >= len(df):
        st.balloons()
        st.header("Evaluación Finalizada")
        st.metric("Puntaje Final", f"{st.session_state.puntaje} / {len(df)}")
        
        # Aquí puedes agregar el código de conexión a Google Sheets (punto 5 anterior)
        
        if st.button("Finalizar y Salir"):
            st.session_state.examen_iniciado = False
            st.session_state.indice = 0
            st.session_state.puntaje = 0
            st.rerun()
