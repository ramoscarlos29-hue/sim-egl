import streamlit as st
import pandas as pd
import random
import os
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN Y ESTILO LA SALLE ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    </style>
    """, unsafe_allow_html=True)

# CORRECCIÓN DE FUNCIÓN DE IMAGEN: Eliminamos el problema del ancho inválido
def mostrar_imagen(ruta, pie_foto=""):
    """Muestra una imagen si existe, adaptándose al ancho del contenedor."""
    if os.path.exists(ruta):
        st.image(ruta, caption=pie_foto, use_container_width=True)
    else:
        st.caption(f"(Imagen '{ruta}' no encontrada)")

URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

@st.cache_data(ttl=60)
def cargar_preguntas():
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
        'nombre': "", 'correo': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'analitica': {}, 'ultimo_resultado': None
    })

# --- PANTALLA DE INICIO ---
if not st.session_state.examen_iniciado:
    col_logo, _ = st.columns([1, 2])
    with col_logo:
        mostrar_imagen("Turismo_Color.png")
    
    st.title("🚀 Simulador de Examen EGEL")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        nombre = st.text_input("Nombre completo:")
        correo = st.text_input("Correo Institucional:")
        carrera = st.selectbox("Carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Comenzar Evaluación"):
            if nombre and correo.lower().endswith("@lasallebajio.edu.mx"):
                df_full = cargar_preguntas()
                if df_full is not None:
                    df_c = df_full[df_full['Carrera'] == carrera].reset_index(drop=True)
                    if len(df_c) > 0:
                        n_final = min(20, len(df_c))
                        st.session_state.preguntas = df_c.sample(n_final).reset_index(drop=True)
                        st.session_state.nombre = nombre
                        st.session_state.correo = correo
                        st.session_state.carrera = carrera
                        st.session_state.examen_iniciado = True
                        st.rerun()
            elif not correo.lower().endswith("@lasallebajio.edu.mx"):
                st.error("❌ Por favor usa tu correo de La Salle Bajío.")
            else: st.warning("⚠️ Completa los campos.")
    with col2:
        mostrar_imagen("felino46.png", "¡A darle con todo, Felino!")

# --- EXAMEN ---
else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        
        area = str(fila.get('Area', 'General')).strip()
        subarea = str(fila.get('Subarea', 'General')).strip()
        pregunta_texto = fila.get('Pregunta', 'Cargando...')
        correcta_texto = str(fila.get('Correcta', '')).strip()

        st.write(f"Estudiante: **{st.session_state.nombre}**")
        st.progress((st.session_state.indice) / len(df))
        st.divider()

        st.caption(f"ÁREA: {area} | SUBÁREA: {subarea}")
        st.markdown(f"#### {pregunta_texto}")
        
        # Mapeo de opciones
        opc = {
            "A": str(fila.get('A', '')).strip(),
            "B": str(fila.get('B', '')).strip(),
            "C": str(fila.get('C', '')).strip(),
            "D": str(fila.get('D', '')).strip()
        }
        display_opciones = [f"{k}) {v}" for k, v in opc.items() if v not in ["nan", "", "None"]]
        
        with st.form(key=f"q_form_{st.session_state.indice}"):
            sel = st.radio("Respuesta:", display_opciones, disabled=st.session_state.respondido)
            validar_btn = st.form_submit_button("Validar Respuesta")

        if validar_btn and not st.session_state.respondido:
            ans_texto = opc[sel[0]] 
            key = (area, subarea)
            if key not in st.session_state.analitica: st.session_state.analitica[key] = {'a': 0, 't': 0}
            st.session_state.analitica[key]['t'] += 1
            
            if ans_texto == correcta_texto:
                st.session_state.analitica[key]['a'] += 1
                st.session_state.puntaje += 1
                st.session_state.ultimo_resultado = "OK"
            else:
                st.session_state.ultimo_resultado = "ERR"
            
            st.session_state.respondido = True
            st.rerun()

        if st.session_state.respondido:
            if st.session_state.ultimo_resultado == "OK": st.success("✅ ¡Correcto!")
            else: st.error(f"❌ Incorrecto. La respuesta era: {correcta_texto}")
            
            if st.button("Siguiente Pregunta ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.rerun()

    # --- RESULTADOS Y REGISTRO ---
    else:
        st.balloons()
        st.header(f"🏁 ¡Felicidades, {st.session_state.nombre}!")
        
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            registro = pd.DataFrame([{
                "Fecha": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                "Nombre": st.session_state.nombre,
                "Correo": st.session_state.correo,
                "Carrera": st.session_state.carrera,
                "Puntaje": f"{st.session_state.puntaje}/{len(df)}"
            }])
            existentes = conn.read(worksheet="Resultados")
            actualizado = pd.concat([existentes, registro], ignore_index=True)
            conn.update(worksheet="Resultados", data=actualizado)
            st.success("✅ Intento registrado en la base de datos.")
        except:
            st.warning("⚠️ Error de conexión al registrar. Por favor reporta tu puntaje al coordinador.")

        st.subheader("📊 Resultados por Área/Subárea")
        diag = [{"Área": k[0], "Subárea": k[1], "Resultado": f"{v['a']}/{v['t']}", "Efectividad": f"{(v['a']/v['t'])*100:.1f}%"} for k, v in st.session_state.analitica.items()]
        st.table(pd.DataFrame(diag))
        
        mostrar_imagen("felino40.png", "¡Orgullo Felino!")
        if st.button("Finalizar"):
            st.session_state.examen_iniciado = False
            st.rerun()
