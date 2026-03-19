import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

# Estilos CSS optimizados
st.markdown("""
    <style>
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    </style>
    """, unsafe_allow_html=True)

URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

# --- FUNCIONES DE CARGA OPTIMIZADAS ---
@st.cache_data(ttl=3600, show_spinner="Cargando base de datos...")
def cargar_datos_crudos(url):
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception:
        return None

def generar_pdf(nombre, carrera, puntaje, total, fecha, diag_data):
    """Genera el PDF solo bajo demanda para ahorrar RAM"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "EVIDENCIA DE EVALUACIÓN EGEL", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("helvetica", '', 10)
    pdf.cell(190, 8, f"Fecha: {fecha}", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(5)
    
    pdf.set_font("helvetica", '', 12)
    def clean(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
    
    pdf.cell(190, 8, clean(f"Estudiante: {nombre}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(190, 8, clean(f"Carrera: {carrera}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(190, 8, clean(f"Puntaje Final: {puntaje}/{total}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    for r in diag_data:
        pdf.cell(190, 8, clean(f"{r['Subarea']}: {r['Aciertos']} - {r['Semaforo']}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    return pdf.output()

# --- ESTADO DE LA SESIÓN ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'correo': "", 'carrera': "", 
        'preguntas_lista': [], # Lista de diccionarios (Ligero)
        'respondido': False, 'analitica': {}, 'opciones_mezcladas': None,
        'res_actual': None, 'fecha_hora': ""
    })

# --- PANTALLA DE INICIO ---
if not st.session_state.examen_iniciado:
    st.title("🚀 Simulador de Examen EGEL")
    
    col_reg, col_img = st.columns([2, 1])
    with col_reg:
        nombre = st.text_input("Nombre completo:")
        correo = st.text_input("Correo Institucional:")
        carrera = st.selectbox("Carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Comenzar Evaluación"):
            if nombre and correo.lower().endswith("@lasallebajio.edu.mx"):
                df_all = cargar_datos_crudos(URL_DATOS)
                if df_all is not None:
                    df_c = df_all[df_all['Carrera'] == carrera]
                    if not df_c.empty:
                        # Convertimos a lista de diccionarios inmediatamente para liberar el DataFrame de la memoria
                        muestra = df_c.sample(min(20, len(df_c))).to_dict('records')
                        st.session_state.update({
                            'preguntas_lista': muestra,
                            'nombre': nombre, 'correo': correo, 'carrera': carrera,
                            'examen_iniciado': True,
                            'fecha_hora': datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        st.rerun()
            else:
                st.warning("⚠️ Usa tu correo @lasallebajio.edu.mx")
    with col_img:
        if os.path.exists("felino46.jpg"): st.image("felino46.jpg")

# --- FLUJO DEL EXAMEN ---
else:
    preguntas = st.session_state.preguntas_lista
    idx = st.session_state.indice

    if idx < len(preguntas):
        pregunta_actual = preguntas[idx]
        
        if not st.session_state.respondido and st.session_state.opciones_mezcladas is None:
            opts = [str(pregunta_actual[c]).strip() for c in ['A', 'B', 'C', 'D'] if pregunta_actual.get(c)]
            random.shuffle(opts)
            st.session_state.opciones_mezcladas = opts

        st.write(f"**{st.session_state.nombre}** | Pregunta {idx + 1} de {len(preguntas)}")
        st.progress((idx) / len(preguntas))
        
        st.caption(f"EJE: {pregunta_actual.get('Area', 'N/A')} | SUBÁREA: {pregunta_actual.get('Subarea', 'N/A')}")
        st.markdown(f"#### {pregunta_actual['Pregunta']}")

        with st.form(key=f"form_{idx}"):
            sel = st.radio("Selecciona:", st.session_state.opciones_mezcladas, disabled=st.session_state.respondido)
            if st.form_submit_button("Validar"):
                st.session_state.respondido = True
                correcta = str(pregunta_actual['Correcta']).strip()
                
                # Guardar analítica
                area, sub = pregunta_actual.get('Area', 'Gral'), pregunta_actual.get('Subarea', 'Gral')
                key = (area, sub)
                if key not in st.session_state.analitica: st.session_state.analitica[key] = {'a': 0, 't': 0}
                st.session_state.analitica[key]['t'] += 1
                
                if sel == correcta:
                    st.session_state.puntaje += 1
                    st.session_state.res_actual = "OK"
                    st.session_state.analitica[key]['a'] += 1
                else:
                    st.session_state.res_actual = "ERR"
                st.rerun()

        if st.session_state.respondido:
            if st.session_state.res_actual == "OK": st.success("✅ ¡Correcto!")
            else: st.error(f"❌ Incorrecto. La respuesta era: {pregunta_actual['Correcta']}")
            
            if st.button("Siguiente ➡️"):
                st.session_state.update({'indice': idx + 1, 'respondido': False, 'opciones_mezcladas': None})
                st.rerun()

    # --- RESULTADOS FINALES ---
    else:
        st.header("🏁 Evaluación Finalizada")
        total_p = len(preguntas)
        st.subheader(f"Puntaje: {st.session_state.puntaje} / {total_p}")
        
        diag_data = []
        for (a, s), v in st.session_state.analitica.items():
            ef = (v['a']/v['t'])*100
            semaforo = "🟢 Optimo" if ef >= 80 else "🟡 En desarrollo" if ef >= 60 else "🔴 Refuerzo"
            diag_data.append({"Area": a, "Subarea": s, "Aciertos": f"{v['a']}/{v['t']}", "Eficacia": ef, "Semaforo": semaforo})
        
        df_res = pd.DataFrame(diag_data)
        st.table(df_res[["Area", "Subarea", "Aciertos", "Semaforo"]])

        # Generación de PDF optimizada (Solo ocurre al presionar el botón)
        reporte_pdf = generar_pdf(
            st.session_state.nombre, 
            st.session_state.carrera, 
            st.session_state.puntaje, 
            total_p, 
            st.session_state.fecha_hora,
            diag_data
        )

        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=bytes(reporte_pdf),
            file_name=f"EGEL_{st.session_state.nombre.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

        if st.button("Reiniciar Simulador"):
            st.session_state.clear()
            st.rerun()
