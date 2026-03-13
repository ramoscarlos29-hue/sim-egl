import streamlit as st
import pandas as pd
import random

# --- DISEÑO ---
st.set_page_config(page_title="Simulador EGEL", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 10px; }
    .stButton>button { border-radius: 8px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_csv(URL_DATOS)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return None

# --- ESTADO DE SESIÓN ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'ultimo_resultado': None
    })

# --- REGISTRO ---
if not st.session_state.examen_iniciado:
    st.title("🚀 Simulador EGEL")
    nombre = st.text_input("Nombre completo:")
    carrera = st.selectbox("Carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
    
    if st.button("Empezar Evaluación"):
        if nombre:
            df_full = cargar_datos()
            if df_full is not None:
                df_carrera = df_full[df_full['Carrera'] == carrera]
                # Tomamos 20 aleatorias
                n_total = min(20, len(df_carrera))
                seleccion = df_carrera.sample(n_total).reset_index(drop=True)
                
                st.session_state.update({
                    'nombre': nombre, 'carrera': carrera,
                    'preguntas': seleccion, 'examen_iniciado': True,
                    'indice': 0, 'puntaje': 0
                })
                st.rerun()
        else:
            st.warning("Escribe tu nombre.")

# --- EXAMEN ---
else:
    df = st.session_state.preguntas
    
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        
        st.write(f"Participante: **{st.session_state.nombre}** | **{st.session_state.carrera}**")
        st.progress((st.session_state.indice) / len(df))
        st.divider()

        st.markdown(f"#### {fila['Pregunta']}")
        
        # Mapeo de incisos
        opciones_raw = {
            "A": str(fila['A']).strip(),
            "B": str(fila['B']).strip(),
            "C": str(fila['C']).strip(),
            "D": str(fila['D']).strip()
        }
        
        # Mostramos incisos al usuario
        lista_display = [f"{k}) {v}" for k, v in opciones_raw.items()]
        
        # Formulario de pregunta
        with st.form(key=f"p_{st.session_state.indice}"):
            seleccion_web = st.radio("Elija la opción correcta:", lista_display, disabled=st.session_state.respondido)
            validar = st.form_submit_button("Validar Respuesta")

        # LÓGICA DE VALIDACIÓN (Punto 1 corregido)
        if validar and not st.session_state.respondido:
            letra_seleccionada = seleccion_web[0] # Toma solo la "A", "B", "C" o "D"
            texto_seleccionado = opciones_raw[letra_seleccionada]
            texto_correcto = str(fila['Correcta']).strip()
            
            st.session_state.respondido = True
            
            if texto_seleccionado == texto_correcto:
                st.session_state.ultimo_resultado = "correcto"
                st.session_state.puntaje += 1
            else:
                st.session_state.ultimo_resultado = "incorrecto"

        # MOSTRAR FEEDBACK Y BOTÓN CONTINUAR (Punto 2 corregido)
        if st.session_state.respondido:
            if st.session_state.ultimo_resultado == "correcto":
                st.success(f"✅ **¡Correcto!**")
            else:
                st.error(f"❌ **Incorrecto.** La respuesta correcta era la **{fila['Correcta']}**")
            
            if 'Feedback' in fila and pd.notna(fila['Feedback']):
                st.info(f"💡 **Explicación:** {fila['Feedback']}")
            
            if st.button("Continuar a la siguiente pregunta ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.rerun()

    else:
        st.balloons()
        st.header("🏁 Resultado Final")
        st.metric("Puntaje", f"{st.session_state.puntaje} / {len(df)}")
        if st.button("Finalizar"):
            st.session_state.examen_iniciado = False
            st.rerun()
