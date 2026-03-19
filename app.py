import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    .stRadio > label { font-size: 18px !important; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

def mostrar_imagen(ruta, pie_foto=""):
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
        'respondido': False, 'analitica': {}, 'opciones_mezcladas': None,
        'res_actual': None, 'fecha_hora': ""
    })

# --- PANTALLA DE INICIO ---
if not st.session_state.examen_iniciado:
    col_l, _ = st.columns([1, 2])
    with col_l: mostrar_imagen("Turismo_Color.png")
    
    st.title("🚀 Simulador de Examen EGEL")
    st.info("Bienvenido. Al finalizar, podrás descargar tu reporte PDF como evidencia.")
    
    col_reg, col_img = st.columns([2, 1])
    with col_reg:
        nombre = st.text_input("Nombre completo del Alumno:")
        correo = st.text_input("Correo Institucional:")
        carrera = st.selectbox("Carrera a evaluar:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Comenzar Evaluación"):
            if nombre and correo.lower().endswith("@lasallebajio.edu.mx"):
                df_f = cargar_preguntas()
                if df_f is not None:
                    df_c = df_f[df_f['Carrera'] == carrera].reset_index(drop=True)
                    if len(df_c) > 0:
                        st.session_state.preguntas = df_c.sample(min(20, len(df_c))).reset_index(drop=True)
                        st.session_state.update({
                            'nombre': nombre, 'correo': correo, 'carrera': carrera, 
                            'examen_iniciado': True,
                            'fecha_hora': datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        st.rerun()
            else: st.warning("⚠️ Ingresa tus datos institucionales de La Salle Bajío.")
    with col_img: mostrar_imagen("felino46.png", "¡Mucho éxito!")

else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        if not st.session_state.respondido and st.session_state.opciones_mezcladas is None:
            opts = [str(fila[c]).strip() for c in ['A', 'B', 'C', 'D'] if str(fila[c]) not in ['nan', '', 'None']]
            random.shuffle(opts)
            st.session_state.opciones_mezcladas = opts

        st.write(f"Alumno: **{st.session_state.nombre}** | {st.session_state.indice + 1}/{len(df)}")
        st.progress(st.session_state.indice / len(df))
        
        area, sub = str(fila.get('Area', 'Gral')), str(fila.get('Subarea', 'Gral'))
        st.caption(f"EJE: {area} | SUBÁREA: {sub}")
        st.markdown(f"#### {fila['Pregunta']}")

        with st.form(key=f"q_{st.session_state.indice}"):
            sel = st.radio("Selecciona la respuesta:", st.session_state.opciones_mezcladas, disabled=st.session_state.respondido)
            if st.form_submit_button("Validar"):
                st.session_state.respondido = True
                if sel == str(fila['Correcta']).strip():
                    st.session_state.puntaje += 1
                    res = "OK"
                else: res = "ERR"
                
                key = (area, sub)
                if key not in st.session_state.analitica: st.session_state.analitica[key] = {'a': 0, 't': 0}
                st.session_state.analitica[key]['t'] += 1
                if res == "OK": st.session_state.analitica[key]['a'] += 1
                st.session_state.res_actual = res
                st.rerun()

        if st.session_state.respondido:
            if st.session_state.res_actual == "OK": st.success("✅ ¡Correcto!")
            else: st.error(f"❌ Incorrecto. Era: {fila['Correcta']}")
            if st.button("Siguiente ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.opciones_mezcladas = None
                st.rerun()
    else:
        st.header(f"🏁 Resultados: {st.session_state.nombre}")
        st.subheader(f"Puntaje: {st.session_state.puntaje} / {len(df)}")
        
        diag_data = []
        for k, v in st.session_state.analitica.items():
            ef = (v['a']/v['t'])*100
            s = "🟢 Optimo" if ef >= 80 else "🟡 En desarrollo" if ef >= 60 else "🔴 Refuerzo urgente"
            diag_data.append({"Area": k[0], "Subarea": k[1], "Aciertos": f"{v['a']}/{v['t']}", "Eficacia": ef, "Semaforo": s})
        
        df_res = pd.DataFrame(diag_data)
        st.bar_chart(df_res.set_index('Subarea')['Eficacia'])
        st.table(df_res[["Area", "Subarea", "Aciertos", "Semaforo"]])

        # PDF Reporte
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(190, 10, "EVIDENCIA DE EVALUACION EGEL", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.set_font("helvetica", '', 10)
        pdf.cell(190, 8, f"Fecha: {st.session_state.fecha_hora}", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(5)
        pdf.set_font("helvetica", '', 12)
        def clean(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(190, 8, clean(f"Estudiante: {st.session_state.nombre}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(190, 8, clean(f"Carrera: {st.session_state.carrera}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(190, 8, clean(f"Puntaje: {st.session_state.puntaje}/{len(df)}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        for _, r in df_res.iterrows():
            pdf.cell(190, 8, clean(f"{r['Subarea']}: {r['Aciertos']} - {r['Semaforo']}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf_bytes = pdf.output()
        st.download_button("📥 Descargar Reporte PDF", data=bytes(pdf_bytes), file_name=f"EGEL_{st.session_state.nombre}.pdf", mime="application/pdf")

        mostrar_imagen("felino40.png", "¡Orgullo Felino!")
        if st.button("Finalizar"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
