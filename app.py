import streamlit as st
import pandas as pd
import random
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN Y ESTILO LA SALLE ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    </style>
    """, unsafe_allow_html=True)

# URL de tus datos
URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

@st.cache_data(ttl=60)
def cargar_preguntas():
    try:
        df = pd.read_csv(URL_DATOS)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# Inicialización de estado
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'correo': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'analitica': {}
    })

# --- PANTALLA DE INICIO ---
if not st.session_state.examen_iniciado:
    # Header Institucional
    st.image("Turismo_Color.png", width=400)
    st.title("🚀 Simulador de Examen EGEL")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Registro del Estudiante")
        nombre = st.text_input("Nombre completo:")
        correo = st.text_input("Correo Institucional (@lasallebajio.edu.mx):")
        carrera = st.selectbox("Carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Comenzar Evaluación"):
            # Validación de dominio
            if nombre and correo.endswith("@lasallebajio.edu.mx"):
                df_full = cargar_preguntas()
                if df_full is not None:
                    df_c = df_full[df_full['Carrera'] == carrera].reset_index(drop=True)
                    if len(df_c) > 0:
                        st.session_state.preguntas = df_c.sample(min(20, len(df_c))).reset_index(drop=True)
                        st.session_state.update({'nombre': nombre, 'correo': correo, 'carrera': carrera, 'examen_iniciado': True})
                        st.rerun()
            elif not correo.endswith("@lasallebajio.edu.mx"):
                st.error("❌ Por favor utiliza tu correo institucional de La Salle Bajío.")
            else:
                st.warning("⚠️ Completa todos los campos.")
    
    with col2:
        st.image("felino46.jpg", caption="¡A darle con todo, Felino!")

# --- EXAMEN (LÓGICA SIMILAR) ---
else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        st.image("Turismo_Color.png", width=200)
        st.write(f"Estudiante: **{st.session_state.nombre}**")
        st.progress((st.session_state.indice) / len(df))
        
        st.markdown(f"#### {fila['Pregunta']}")
        # ... (Aquí va el resto del código de preguntas que ya teníamos)
        # Asegúrate de mantener la lógica de validación que ya funcionaba
        
        # Simulación de botón continuar para brevedad de este ejemplo
        if st.button("Siguiente"): # Simplificado para el ejemplo
            st.session_state.indice += 1
            st.rerun()

    # --- RESULTADOS ---
    else:
        st.image("Turismo_Color.png", width=300)
        st.header("🏁 Evaluación Finalizada")
        
        # Intento de registro
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            registro = pd.DataFrame([{
                "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "Nombre": st.session_state.nombre,
                "Correo": st.session_state.correo,
                "Carrera": st.session_state.carrera,
                "Resultado": f"{st.session_state.puntaje}/{len(df)}"
            }])
            existentes = conn.read(worksheet="Resultados")
            nuevo_df = pd.concat([existentes, registro], ignore_index=True)
            conn.update(worksheet="Resultados", data=nuevo_df)
            st.success("✅ Tu resultado ha sido registrado en la base de datos de la Facultad.")
        except:
            st.warning("⚠️ Error de conexión. Avisa a tu coordinador.")

        st.image("felino40.png", width=200, caption="¡Felicidades por completar el reto!")
        
        # Tabla de áreas (como la teníamos)
        # ... 

        if st.button("Finalizar Sesión"):
            st.session_state.examen_iniciado = False
            st.rerun()
