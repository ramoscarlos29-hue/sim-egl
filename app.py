import streamlit as st
import pandas as pd
import random
import os
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF # Necesitarás agregar 'fpdf' a tu requirements.txt

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    </style>
    """, unsafe_allow_html=True)

def mostrar_image(ruta, pie=""):
    if os.path.exists(ruta):
        st.image(ruta, caption=pie, width='stretch')
    else:
        st.caption(f"(Imagen {ruta} no disponible)")

URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_csv(URL_DATOS)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- ESTADO DE SESIÓN ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'correo': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'analitica': {}, 'opciones_mezcladas': None
    })

# --- INICIO ---
if not st.session_state.examen_iniciado:
    col_l, _ = st.columns([1, 2])
    with col_l: mostrar_image("Turismo_Color.png")
    st.title("🚀 Simulador de Examen EGEL")
    
    nombre = st.text_input("Nombre completo:")
    correo = st.text_input("Correo Institucional (@lasallebajio.edu.mx):")
    carrera = st.selectbox("Carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
    
    if st.button("Empezar Simulación"):
        if nombre and correo.lower().endswith("@lasallebajio.edu.mx"):
            df_f = cargar_datos()
            if df_f is not None:
                df_c = df_f[df_f['Carrera'] == carrera].reset_index(drop=True)
                st.session_state.preguntas = df_c.sample(min(20, len(df_c))).reset_index(drop=True)
                st.session_state.update({'nombre': nombre, 'correo': correo, 'carrera': carrera, 'examen_iniciado': True})
                st.rerun()
        else: st.warning("Por favor ingresa tus datos institucionales.")

# --- EXAMEN ---
else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        
        # 1) ALEATORIZACIÓN DE OPCIONES
        if not st.session_state.respondido and st.session_state.opciones_mezcladas is None:
            opts = [str(fila[c]).strip() for c in ['A', 'B', 'C', 'D'] if str(fila[c]) != 'nan']
            random.shuffle(opts)
            st.session_state.opciones_mezcladas = opts

        st.write(f"Estudiante: **{st.session_state.nombre}** | {st.session_state.indice + 1}/{len(df)}")
        st.progress(st.session_state.indice / len(df))
        st.markdown(f"#### {fila['Pregunta']}")

        with st.form(key=f"f_{st.session_state.indice}"):
            # Mostramos las opciones ya revueltas
            seleccion = st.radio("Selecciona la respuesta:", st.session_state.opciones_mezcladas, disabled=st.session_state.respondido)
            if st.form_submit_button("Validar"):
                st.session_state.respondido = True
                correcta = str(fila['Correcta']).strip()
                
                area, sub = str(fila.get('Area','Gral')), str(fila.get('Subarea','Gral'))
                key = (area, sub)
                if key not in st.session_state.analitica: st.session_state.analitica[key] = {'a': 0, 't': 0}
                st.session_state.analitica[key]['t'] += 1
                
                if seleccion == correcta:
                    st.session_state.puntaje += 1
                    st.session_state.analitica[key]['a'] += 1
                    st.session_state.feedback = "OK"
                else: st.session_state.feedback = "ERR"
                st.rerun()

        if st.session_state.respondido:
            if st.session_state.feedback == "OK": st.success("✅ ¡Correcto!")
            else: st.error(f"❌ Incorrecto. La respuesta era: {fila['Correcta']}")
            
            if st.button("Siguiente ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.opciones_mezcladas = None
                st.rerun()

    # --- RESULTADOS Y GENERACIÓN DE PDF ---
    else:
        st.header(f"🏁 Resultados: {st.session_state.nombre}")
        st.subheader(f"Puntaje: {st.session_state.puntaje} / {len(df)}")
        
        # Tabla analítica
        diag_df = pd.DataFrame([{"Área": k[0], "Subárea": k[1], "Aciertos": f"{v['a']}/{v['t']}"} for k, v in st.session_state.analitica.items()])
        st.table(diag_df)

        # 2) GENERACIÓN DE PDF (Botón de descarga)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Comprobante Simulador EGEL - La Salle Bajío", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Estudiante: {st.session_state.nombre}", ln=True)
        pdf.cell(200, 10, txt=f"Carrera: {st.session_state.carrera}", ln=True)
        pdf.cell(200, 10, txt=f"Puntaje Total: {st.session_state.puntaje}/{len(df)}", ln=True)
        pdf.cell(200, 10, txt="--------------------------------------------------", ln=True)
        for _, r in diag_df.iterrows():
            pdf.cell(200, 10, txt=f"{r['Área']} - {r['Subárea']}: {r['Aciertos']}", ln=True)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button(label="📥 Descargar Reporte de Resultados (PDF)", 
                           data=pdf_output, 
                           file_name=f"Resultado_EGEL_{st.session_state.nombre}.pdf", 
                           mime="application/pdf")

        mostrar_image("felino40.png", "¡Orgullo Felino!")
        if st.button("Reiniciar"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
