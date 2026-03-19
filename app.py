import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# El resto del código que te envié anteriormente...

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

# Estilo Visual Institucional
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
        st.image(ruta, caption=pie_foto, width='stretch')
    else:
        st.caption(f"(Imagen '{ruta}' no encontrada)")

# URL de la base de datos (CSV público)
URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

@st.cache_data(ttl=60)
def cargar_preguntas():
    try:
        df = pd.read_csv(URL_DATOS)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return None

# --- INICIALIZACIÓN DE ESTADO ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'correo': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'analitica': {}, 'opciones_mezcladas': None,
        'res_actual': None, 'fecha_hora': ""
    })

# --- PANTALLA DE INICIO (REGISTRO) ---
if not st.session_state.examen_iniciado:
    col_l, _ = st.columns([1, 2])
    with col_l:
        mostrar_imagen("Turismo_Color.png")
    
    st.title("🚀 Simulador de Examen EGEL")
    st.info("Bienvenido. Al finalizar, podrás descargar tu reporte de resultados en PDF como evidencia de tu desempeño.")
    
    col_reg, col_img = st.columns([2, 1])
    with col_reg:
        nombre = st.text_input("Nombre completo del Alumno:")
        correo = st.text_input("Correo Institucional (@lasallebajio.edu.mx):")
        carrera = st.selectbox("Carrera a evaluar:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Comenzar Evaluación"):
            if nombre and correo.lower().endswith("@lasallebajio.edu.mx"):
                df_f = cargar_preguntas()
                if df_f is not None:
                    df_c = df_f[df_f['Carrera'] == carrera].reset_index(drop=True)
                    if len(df_c) > 0:
                        # Selección aleatoria de 20 reactivos
                        st.session_state.preguntas = df_c.sample(min(20, len(df_c))).reset_index(drop=True)
                        st.session_state.update({
                            'nombre': nombre, 'correo': correo, 'carrera': carrera, 
                            'examen_iniciado': True,
                            'fecha_hora': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        })
                        st.rerun()
            elif not correo.lower().endswith("@lasallebajio.edu.mx"):
                st.error("❌ Acceso restringido: Usa tu correo institucional.")
            else:
                st.warning("⚠️ Completa los campos de registro.")
    with col_img:
        mostrar_imagen("felino46.png", "¡Mucho éxito, Felino!")

# --- PANTALLA DE EXAMEN ---
else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        
        # Mezcla aleatoria de incisos para cada pregunta
        if not st.session_state.respondido and st.session_state.opciones_mezcladas is None:
            opts = [str(fila[c]).strip() for c in ['A', 'B', 'C', 'D'] if str(fila[c]) not in ['nan', '', 'None']]
            random.shuffle(opts)
            st.session_state.opciones_mezcladas = opts

        st.write(f"Alumno: **{st.session_state.nombre}** | Reactivo {st.session_state.indice + 1}/{len(df)}")
        st.progress((st.session_state.indice) / len(df))
        st.divider()

        area, sub = str(fila.get('Area', 'General')), str(fila.get('Subarea', 'General'))
        st.caption(f"EJE: {area} | SUBÁREA: {sub}")
        st.markdown(f"#### {fila['Pregunta']}")

        with st.form(key=f"quiz_{st.session_state.indice}"):
            sel = st.radio("Selecciona la respuesta correcta:", st.session_state.opciones_mezcladas, disabled=st.session_state.respondido)
            if st.form_submit_button("Validar Respuesta"):
                st.session_state.respondido = True
                
                key = (area, sub)
                if key not in st.session_state.analitica:
                    st.session_state.analitica[key] = {'a': 0, 't': 0}
                st.session_state.analitica[key]['t'] += 1
                
                if sel == str(fila['Correcta']).strip():
                    st.session_state.puntaje += 1
                    st.session_state.analitica[key]['a'] += 1
                    st.session_state.res_actual = "OK"
                else:
                    st.session_state.res_actual = "ERR"
                st.rerun()

        if st.session_state.respondido:
            if st.session_state.res_actual == "OK":
                st.success("✅ **¡Correcto!**")
            else:
                st.error(f"❌ **Incorrecto.** La respuesta correcta era: {fila['Correcta']}")
            
            if st.button("Continuar ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.opciones_mezcladas = None
                st.rerun()

# --- PANTALLA DE RESULTADOS FINALES ---
    else:
        st.header(f"🏁 Simulación Finalizada")
        st.subheader(f"Puntaje de {st.session_state.nombre}: {st.session_state.puntaje} / {len(df)}")
        
        # Procesamiento de datos para tabla y PDF
        resumen_lista = []
        for k, v in st.session_state.analitica.items():
            eficacia = (v['a']/v['t'])*100
            if eficacia >= 80: sem = "🟢 Óptimo"
            elif eficacia >= 60: sem = "🟡 En desarrollo"
            else: sem = "🔴 Requiere refuerzo"
            
            resumen_lista.append({
                "Área": k[0], "Subárea": k[1], 
                "Aciertos": f"{v['a']}/{v['t']}", 
                "Eficacia": eficacia, "Diagnóstico": sem
            })
        
        df_res = pd.DataFrame(resumen_lista)
        
        # Gráfico visual en App
        st.bar_chart(df_res.set_index('Subárea')['Eficacia'])
        st.table(df_res[["Área", "Subárea", "Aciertos", "Diagnóstico"]])

        # --- GENERACIÓN DE PDF PROFESIONAL ---
        pdf = FPDF()
        pdf.add_page()
        
        # Encabezado e Imagen
        if os.path.exists("Turismo_Color.png"):
            pdf.image("Turismo_Color.png", 10, 8, 45)
        
        pdf.set_font("helvetica", 'B', 16)
        pdf.ln(25)
        pdf.cell(190, 10, "REPORTE DE RESULTADOS: SIMULADOR EGEL", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        pdf.set_font("helvetica", '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 8, f"Fecha y Hora del intento: {st.session_state.fecha_hora}", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(5)
        
        # Datos del Alumno
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", 'B', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, f" DATOS DEL ESTUDIANTE", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        pdf.set_font("helvetica", '', 11)
        pdf.cell(190, 8, f" Nombre: {st.session_state.nombre}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(190, 8, f" Carrera: {st.session_state.carrera}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(190, 8, f" Puntaje Total: {st.session_state.puntaje} de {len(df)} aciertos", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(8)

        # Tabla de Desempeño
        pdf.set_font("helvetica", 'B', 11)
        pdf.set_fill_color(0, 45, 114) # Azul La Salle
        pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 10, " Subárea", 1, 0, 'L', True)
        pdf.cell(40, 10, " Aciertos", 1, 0, 'C', True)
        pdf.cell(60, 10, " Diagnóstico", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", '', 9)
        
        def clean(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

        for _, r in df_res.iterrows():
            pdf.cell(90, 8, clean(r['Subárea'][:50]), 1)
            pdf.cell(40, 8, clean(r['Aciertos']), 1, 0, 'C')
            pdf.cell(60, 8, clean(r['Diagnóstico']), 1, 1, 'C')

        pdf_bytes = pdf.output()
        st.download_button(
            label="📥 Descargar Reporte de Evidencia (PDF)",
            data=bytes(pdf_bytes),
            file_name=f"Resultado_EGEL_{st.session_state.nombre.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

        mostrar_imagen("felino40.png", "¡Orgullo Felino!")
        if st.button("Finalizar y Salir"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
