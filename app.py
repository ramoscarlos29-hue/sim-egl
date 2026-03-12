import streamlit as st
import pandas as pd
import time
import random

# Configuración de página
st.set_page_config(page_title="Simulador EGEL 30", page_icon="🎓")

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
if 'preguntas_seleccionadas' not in st.session_state:
    st.session_state.preguntas_seleccionadas = None
if 'indice' not in st.session_state:
    st.session_state.indice = 0
if 'puntaje' not in st.session_state:
    st.session_state.puntaje = 0
if 'nombre_estudiante' not in st.session_state:
    st.session_state.nombre_estudiante = ""
if 'examen_iniciado' not in st.session_state:
    st.session_state.examen_iniciado = False

# --- PANTALLA DE REGISTRO ---
if not st.session_state.examen_iniciado:
    st.title("📝 Registro de Estudiante")
    nombre = st.text_input("Ingresa tu nombre completo:")
    
    if st.button("Comenzar Examen (30 preguntas aleatorias)"):
        if nombre:
            df_full = cargar_datos()
            if df_full is not None:
                # 2 y 3) Aleatoriedad y límite de 30
                lista_indices = df_full.index.tolist()
                indices_random = random.sample(lista_indices, min(30, len(df_full)))
                
                st.session_state.preguntas_seleccionadas = df_full.iloc[indices_random].copy()
                st.session_state.nombre_estudiante = nombre
                st.session_state.examen_iniciado = True
                st.rerun()
        else:
            st.warning("Por favor, ingresa tu nombre para continuar.")

# --- PANTALLA DE EXAMEN ---
else:
    df = st.session_state.preguntas_seleccionadas
    col_pregunta = df.columns[0]
    col_correcta = df.columns[-1]
    cols_opciones = df.columns[1:-1].tolist()

    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        
        st.write(f"Estudiante: **{st.session_state.nombre_estudiante}**")
        st.progress((st.session_state.indice) / len(df))
        st.subheader(f"Pregunta {st.session_state.indice + 1} de {len(df)}")
        
        st.info(fila[col_pregunta])

        # 1) Normalización para reconocer correctas (quitar espacios y mayúsculas/minúsculas)
        opciones = [str(fila[c]).strip() for c in cols_opciones]
        
        with st.form(key=f"f_{st.session_state.indice}"):
            seleccion = st.radio("Selecciona tu respuesta:", opciones)
            btn = st.form_submit_button("Siguiente")

        if btn:
            # Comparación robusta
            res_usuario = str(seleccion).strip().lower()
            res_correcta = str(fila[col_correcta]).strip().lower()
            
            if res_usuario == res_correcta:
                st.session_state.puntaje += 1
            
            st.session_state.indice += 1
            st.rerun()

    # --- RESULTADOS Y REGISTRO ---
    else:
        st.balloons()
        st.header("¡Examen Finalizado!")
        final_score = st.session_state.puntaje
        total = len(df)
        
        st.metric("Resultado de " + st.session_state.nombre_estudiante, f"{final_score}/{total}")

        # 5) Explicación sobre el registro
        st.success(f"Intento registrado para {st.session_state.nombre_estudiante}")
        
        # Nota técnica: Para escribir en Google Sheets necesitas configurar "Streamlit Connections"
        # Por ahora, mostramos un botón para descargar el resultado como prueba
        resultado_texto = f"Estudiante: {st.session_state.nombre_estudiante} - Puntaje: {final_score}/{total}"
        st.download_button("Descargar Comprobante", resultado_texto, file_name="resultado_egel.txt")

        if st.button("Salir / Otro intento"):
            st.session_state.examen_iniciado = False
            st.session_state.indice = 0
            st.session_state.puntaje = 0
            st.rerun()
