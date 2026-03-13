import streamlit as st
import pandas as pd
import random

# --- DISEÑO ---
st.set_page_config(page_title="Simulador EGEL", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 8px; height: 3em; font-weight: bold; width: 100%; }
    .stRadio > label { font-size: 20px !important; font-weight: 500; }
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

# --- INICIALIZACIÓN SEGURA DEL ESTADO ---
# Esto previene el error "AttributeError" al asegurar que todas las variables existan desde el segundo 1.
if 'examen_iniciado' not in st.session_state:
    st.session_state.examen_iniciado = False
    st.session_state.indice = 0
    st.session_state.puntaje = 0
    st.session_state.respondido = False
    st.session_state.ultimo_resultado = None
    st.session_state.preguntas = None
    st.session_state.nombre = ""
    st.session_state.carrera = ""

# --- PANTALLA DE REGISTRO ---
if not st.session_state.examen_iniciado:
    st.title("🚀 Simulador EGEL")
    st.subheader("Bienvenido al sistema de preparación profesional")
    
    with st.container():
        nombre = st.text_input("Nombre completo del estudiante:", placeholder="Ej. Carlos García")
        carrera = st.selectbox("Selecciona tu carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Iniciar Evaluación (20 Reactivos)"):
            if nombre:
                df_full = cargar_datos()
                if df_full is not None:
                    # Filtramos por carrera
                    df_carrera = df_full[df_full['Carrera'] == carrera]
                    
                    if len(df_carrera) == 0:
                        st.error(f"No se encontraron preguntas para {carrera}. Revisa tu Excel.")
                    else:
                        # Seleccionamos 20 aleatorias (o todas si hay menos de 20)
                        n_preguntas = min(20, len(df_carrera))
                        seleccion = df_carrera.sample(n_preguntas).reset_index(drop=True)
                        
                        st.session_state.preguntas = seleccion
                        st.session_state.nombre = nombre
                        st.session_state.carrera = carrera
                        st.session_state.examen_iniciado = True
                        st.session_state.indice = 0 # Reiniciar índice al empezar
                        st.session_state.puntaje = 0
                        st.rerun()
            else:
                st.warning("⚠️ Debes ingresar tu nombre para comenzar.")

# --- PANTALLA DE EXAMEN ---
else:
    df = st.session_state.preguntas
    
    # Previene el "IndexError": Solo ejecutamos si el índice es menor al total
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        
        st.write(f"Participante: **{st.session_state.nombre}** | **{st.session_state.carrera}**")
        st.progress((st.session_state.indice) / len(df))
        st.divider()

        st.markdown(f"#### {fila['Pregunta']}")
        
        # Mapeo de opciones para incisos
        opciones_dict = {
            "A": str(fila['A']).strip(),
            "B": str(fila['B']).strip(),
            "C": str(fila['C']).strip(),
            "D": str(fila['D']).strip()
        }
        lista_display = [f"{k}) {v}" for k, v in opciones_dict.items()]
        
        # El radio button se deshabilita después de responder para evitar cambios
        seleccion_display = st.radio(
            "Elija la opción correcta:", 
            lista_display, 
            key=f"radio_{st.session_state.indice}",
            disabled=st.session_state.respondido
        )

        # Botón de validación
        if not st.session_state.respondido:
            if st.button("Validar Respuesta"):
                # Obtenemos solo el texto de la opción elegida (sin el "A) ")
                letra_elegida = seleccion_display[0]
                texto_elegido = opciones_dict[letra_elegida]
                texto_correcto = str(fila['Correcta']).strip()
                
                if texto_elegido == texto_correcto:
                    st.session_state.ultimo_resultado = "correcto"
                    st.session_state.puntaje += 1
                else:
                    st.session_state.ultimo_resultado = "incorrecto"
                
                st.session_state.respondido = True
                st.rerun()

        # Feedback y Botón de Continuar
        if st.session_state.respondido:
            if st.session_state.ultimo_resultado == "correcto":
                st.success("✅ **¡Correcto!**")
            else:
                st.error(f"❌ **Incorrecto.** La respuesta correcta era: {fila['Correcta']}")
            
            if 'Feedback' in fila and pd.notna(fila['Feedback']):
                st.info(f"💡 **Explicación:** {fila['Feedback']}")
            
            if st.button("Siguiente Pregunta ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.ultimo_resultado = None
                st.rerun()

    # --- PANTALLA FINAL ---
    else:
        st.balloons()
        st.header("🏁 Evaluación Finalizada")
        st.subheader(f"¡Buen trabajo, {st.session_state.nombre}!")
        
        col1, col2 = st.columns(2)
        col1.metric("Puntaje", f"{st.session_state.puntaje} / {len(df)}")
        
        porcentaje = (st.session_state.puntaje / len(df)) * 100
        col2.metric("Efectividad", f"{porcentaje}%")

        if st.button("Regresar al Inicio"):
            st.session_state.examen_iniciado = False
            st.rerun()
