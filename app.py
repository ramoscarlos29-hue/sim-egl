import streamlit as st
import pandas as pd
import random
import os
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF

# --- CONFIGURACIÓN INSTITUCIONAL ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; width: 100%; font-weight: bold; height: 3.5em; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    .stRadio > label { font-size: 18px !important; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# Función de imagen corregida para evitar el error de ancho
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
    except: return None

# --- INICIALIZACIÓN DE ESTADO ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'correo': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'analitica': {}, 'opciones_mezcladas': None,
        'registro_intentado': False
    })

# --- PANTALLA DE INICIO ---
if not st.session_state.examen_iniciado:
    col_l, _ = st.columns([1, 2])
    with col_l: mostrar_imagen("Turismo_Color.png")
    st.title("🚀 Simulador de Examen EGEL")
    st.info("Bienvenido. Tus resultados se guardarán automáticamente y podrás descargar un reporte al finalizar.")
    
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
                st.error("❌ Acceso restringido a comunidad La Salle Bajío.")
            else: st.warning("⚠️ Completa tus datos.")
    with col_img:
        mostrar_imagen("felino46.png", "¡Mucho éxito!")

# --- EXAMEN ---
else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        
        # Mezclamos opciones una sola vez por reactivo
        if not st.session_state.respondido and st.session_state.opciones_mezcladas is None:
            opts = [str(fila[c]).strip() for c in ['A', 'B', 'C', 'D'] if str(fila[c]) not in ['nan', '', 'None']]
            random.shuffle(opts)
            st.session_state.opciones_mezcladas = opts

        st.write(f"Participante: **{st.session_state.nombre}** | Reactivo {st.session_state.indice + 1}/{len(df)}")
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
                else: st.session_state.res_actual = "ERR"
                st.rerun()

        if st.session_state.respondido:
            if st.session_state.res_actual == "OK": st.success("✅ ¡Correcto!")
            else: st.error(f"❌ Incorrecto. La respuesta era: {fila['Correcta']}")
            if st.button("Siguiente Pregunta ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.opciones_mezcladas = None
                st.rerun()

    # --- RESULTADOS FINALES ---
    else:
        st.header(f"🏁 Resultados: {st.session_state.nombre}")
        st.subheader(f"Puntaje: {st.session_state.puntaje} / {len(df)}")
        
        # Procesar Semáforo
        diag_data = []
        for k, v in st.session_state.analitica.items():
            ef = (v['a']/v['t'])*100
            if ef >= 80: s, c = "🟢 Óptimo", [0, 128, 0]
            elif ef >= 60: s, c = "🟡 En desarrollo", [255, 165, 0]
            else: s, c = "🔴 Requiere refuerzo", [200, 0, 0]
            diag_data.append({"Área": k[0], "Subárea": k[1], "Aciertos": f"{v['a']}/{v['t']}", "Eficacia": ef, "Diagnóstico": s, "color": c})
        
        df_res = pd.DataFrame(diag_data)
        st.bar_chart(df_res.set_index('Subárea')['Eficacia'])
        st.table(df_res[["Área", "Subárea", "Aciertos", "Diagnóstico"]])

        # REGISTRO FORZADO A GOOGLE SHEETS
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
                st.success("✅ Intento guardado en el registro institucional.")
                st.session_state.registro_intentado = True
            except Exception as e:
                st.warning(f"⚠️ El registro en la nube falló (Error 400). Por favor descarga tu PDF.")

        # GENERACIÓN DE PDF
        pdf = FPDF()
        pdf.add_page()
        if os.path.exists("Turismo_Color.png"): pdf.image("Turismo_Color.png", 10, 8, 40)
        pdf.ln(20)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "REPORTE DE EVALUACIÓN EGEL", 0, 1, 'C')
        pdf.set_font("Arial", '', 11)
        pdf.cell(190, 8, f"Estudiante: {st.session_state.nombre}", 0, 1)
        pdf.cell(190, 8, f"Puntaje: {st.session_state.puntaje}/{len(df)}", 0, 1)
        pdf.ln(5)

        # Tabla PDF
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(85, 8, "Subarea", 1); pdf.cell(40, 8, "Aciertos", 1); pdf.cell(60, 8, "Resultado", 1, 1)
        pdf.set_font("Arial", '', 9)
        for _, r in df_res.iterrows():
            pdf.cell(85, 8, str(r['Subárea'])[:45], 1)
            pdf.cell(40, 8, r['Aciertos'], 1, 0, 'C')
            # Color del semáforo en texto
            pdf.cell(60, 8, r['Diagnóstico'], 1, 1, 'C')

        pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
        st.download_button("📥 Descargar Reporte PDF", pdf_output, f"Resultado_{st.session_state.nombre}.pdf", "application/pdf")

        mostrar_imagen("felino40.png", "¡Orgullo Felino!")
        if st.button("Finalizar Sesión"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
