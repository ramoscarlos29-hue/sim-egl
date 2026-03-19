import streamlit as st
import pandas as pd
import random
import os
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; font-weight: bold; height: 3.5em; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    .stRadio > label { font-size: 18px !important; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

def mostrar_imagen(ruta, pie_foto=""):
    if os.path.exists(ruta):
        st.image(ruta, caption=pie_foto, width='stretch')
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
        'registro_intentado': False, 'res_actual': None
    })

# --- PANTALLA DE INICIO ---
if not st.session_state.examen_iniciado:
    col_l, _ = st.columns([1, 2])
    with col_l:
        mostrar_imagen("Turismo_Color.png")
    
    st.title("🚀 Simulador de Examen EGEL")
    st.info("Bienvenido, Felino. Tus resultados se guardarán y podrás descargar tu reporte al finalizar.")
    
    col_reg, col_img = st.columns([2, 1])
    with col_reg:
        nombre = st.text_input("Nombre completo:")
        correo = st.text_input("Correo Institucional (@lasallebajio.edu.mx):")
        carrera = st.selectbox("Carrera a evaluar:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Comenzar Evaluación"):
            if nombre and correo.lower().endswith("@lasallebajio.edu.mx"):
                df_f = cargar_preguntas()
                if df_f is not None:
                    df_c = df_f[df_f['Carrera'] == carrera].reset_index(drop=True)
                    if len(df_c) > 0:
                        st.session_state.preguntas = df_c.sample(min(20, len(df_c))).reset_index(drop=True)
                        st.session_state.update({'nombre': nombre, 'correo': correo, 'carrera': carrera, 'examen_iniciado': True})
                        st.rerun()
            elif not correo.lower().endswith("@lasallebajio.edu.mx"):
                st.error("❌ Acceso restringido a la comunidad de La Salle Bajío.")
            else:
                st.warning("⚠️ Completa tus datos.")
    with col_img:
        mostrar_imagen("felino46.png", "¡Mucho éxito!")

# --- EXAMEN ---
else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        
        if not st.session_state.respondido and st.session_state.opciones_mezcladas is None:
            opts = [str(fila[c]).strip() for c in ['A', 'B', 'C', 'D'] if str(fila[c]) not in ['nan', '', 'None']]
            random.shuffle(opts)
            st.session_state.opciones_mezcladas = opts

        st.write(f"Alumno: **{st.session_state.nombre}** | Reactivo {st.session_state.indice + 1}/{len(df)}")
        st.progress(st.session_state.indice / len(df))
        
        area, sub = str(fila.get('Area', 'Gral')), str(fila.get('Subarea', 'Gral'))
        st.caption(f"EJE: {area} | SUBÁREA: {sub}")
        st.markdown(f"#### {fila['Pregunta']}")

        with st.form(key=f"quiz_{st.session_state.indice}"):
            sel = st.radio("Selecciona la respuesta:", st.session_state.opciones_mezcladas, disabled=st.session_state.respondido)
            if st.form_submit_button("Validar"):
                st.session_state.respondido = True
                correcta = str(fila['Correcta']).strip()
                
                key = (area, sub)
                if key not in st.session_state.analitica: st.session_state.analitica[key] = {'a': 0, 't': 0}
                st.session_state.analitica[key]['t'] += 1
                
                if sel == correcta:
                    st.session_state.puntaje += 1
                    st.session_state.analitica[key]['a'] += 1
                    st.session_state.res_actual = "OK"
                else:
                    st.session_state.res_actual = "ERR"
                st.rerun()

        if st.session_state.respondido:
            if st.session_state.res_actual == "OK":
                st.success("✅ ¡Correcto!")
            else:
                st.error(f"❌ Incorrecto. La respuesta era: {fila['Correcta']}")
            
            if st.button("Siguiente Pregunta ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.opciones_mezcladas = None
                st.rerun()

    # --- RESULTADOS FINALES ---
    else:
        st.header(f"🏁 Resultados: {st.session_state.nombre}")
        st.subheader(f"Puntaje: {st.session_state.puntaje} / {len(df)}")
        
        diag_data = []
        for k, v in st.session_state.analitica.items():
            ef = (v['a']/v['t'])*100
            if ef >= 80: s = "🟢 Optimo"
            elif ef >= 60: s = "🟡 En desarrollo"
            else: s = "🔴 Requiere refuerzo"
            diag_data.append({"Area": k[0], "Subarea": k[1], "Aciertos": f"{v['a']}/{v['t']}", "Eficacia": ef, "Semaforo": s})
        
        df_res = pd.DataFrame(diag_data)
        st.bar_chart(df_res.set_index('Subarea')['Eficacia'])
        st.table(df_res[["Area", "Subarea", "Aciertos", "Semaforo"]])

        # Registro en Google Sheets
        if not st.session_state.registro_intentado:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                log = pd.DataFrame([{
                    "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                    "Nombre": str(st.session_state.nombre),
                    "Correo": str(st.session_state.correo),
                    "Carrera": str(st.session_state.carrera),
                    "Resultado": f"{st.session_state.puntaje}/{len(df)}"
                }])
                existentes = conn.read(worksheet="Resultados", usecols=[0,1,2,3,4])
                conn.update(worksheet="Resultados", data=pd.concat([existentes, log], ignore_index=True))
                st.success("✅ Intento guardado con éxito.")
                st.session_state.registro_intentado = True
            except:
                st.warning("⚠️ El registro en la nube falló. Por favor descarga tu reporte PDF.")

        # PDF moderno (fpdf2) sin warnings
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(190, 10, "REPORTE DE EVALUACION EGEL", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.set_font("helvetica", '', 12)
        
        def clean(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(190, 8, clean(f"Estudiante: {st.session_state.nombre}"), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(190, 8, clean(f"Puntaje: {st.session_state.puntaje}/{len(df)}"), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        for _, r in df_res.iterrows():
            pdf.cell(190, 8, clean(f"{r['Subarea']}: {r['Aciertos']} - {r['Semaforo']}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf_bytes = pdf.output()
        st.download_button("📥 Descargar Reporte PDF", data=bytes(pdf_bytes), file_name=f"Resultado_{st.session_state.nombre}.pdf", mime="application/pdf")

        mostrar_imagen("felino40.png", "¡Orgullo Felino!")
        if st.button("Finalizar Sesión"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
