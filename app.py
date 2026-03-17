import streamlit as st
import pandas as pd
import os
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

# Estilo Institucional
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    </style>
    """, unsafe_allow_html=True)

def mostrar_imagen(ruta, pie_foto=""):
    if os.path.exists(ruta):
        # Actualizado a la nueva normativa de Streamlit
        st.image(ruta, caption=pie_foto, width=None, use_container_width=True)
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

# --- ESTADO DE SESIÓN ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'correo': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'analitica': {}, 'registro_exitoso': False
    })

# --- LÓGICA DE INICIO ---
if not st.session_state.examen_iniciado:
    col_l, _ = st.columns([1, 2]); 
    with col_l: mostrar_imagen("Turismo_Color.png")
    st.title("🚀 Simulador de Examen EGEL")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        nombre = st.text_input("Nombre completo:")
        correo = st.text_input("Correo Institucional:")
        carrera = st.selectbox("Carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
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
                st.error("❌ Usa tu correo @lasallebajio.edu.mx")
            else: st.warning("⚠️ Completa los campos.")
    with col2: mostrar_imagen("felino46.png", "¡Vamos Felino!")

# --- LÓGICA DE EXAMEN ---
else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        area, sub = str(fila.get('Area', 'Gral')), str(fila.get('Subarea', 'Gral'))
        
        st.write(f"Estudiante: **{st.session_state.nombre}**")
        st.progress(st.session_state.indice / len(df))
        st.divider()
        st.caption(f"ÁREA: {area} | SUBÁREA: {sub}")
        st.markdown(f"#### {fila.get('Pregunta', '...')}")
        
        opc = {"A": str(fila.get('A','')), "B": str(fila.get('B','')), "C": str(fila.get('C','')), "D": str(fila.get('D',''))}
        disp = [f"{k}) {v}" for k, v in opc.items() if v not in ["nan", ""]]
        
        with st.form(key=f"q_{st.session_state.indice}"):
            sel = st.radio("Elija respuesta:", disp, disabled=st.session_state.respondido)
            if st.form_submit_button("Validar"):
                if not st.session_state.respondido:
                    key = (area, sub)
                    if key not in st.session_state.analitica: st.session_state.analitica[key] = {'a': 0, 't': 0}
                    st.session_state.analitica[key]['t'] += 1
                    if opc[sel[0]] == str(fila.get('Correcta','')).strip():
                        st.session_state.analitica[key]['a'] += 1
                        st.session_state.puntaje += 1
                        st.session_state.res = "OK"
                    else: st.session_state.res = "ERR"
                    st.session_state.respondido = True; st.rerun()

        if st.session_state.respondido:
            if st.session_state.res == "OK": st.success("✅ ¡Correcto!")
            else: st.error(f"❌ Incorrecto. Era: {fila.get('Correcta')}")
            if st.button("Siguiente ➡️"):
                st.session_state.indice += 1; st.session_state.respondido = False; st.rerun()

    # --- RESULTADOS FINALES ---
    else:
        st.balloons()
        st.header(f"🏁 ¡Felicidades, {st.session_state.nombre}!")
        
        # Intentar registro una sola vez
        if not st.session_state.registro_exitoso:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                log = pd.DataFrame([{"Fecha": pd.Timestamp.now().strftime("%d/%m/%Y"), "Nombre": st.session_state.nombre, "Correo": st.session_state.correo, "Carrera": st.session_state.carrera, "Resultado": f"{st.session_state.puntaje}/{len(df)}"}])
                old = conn.read(worksheet="Resultados", usecols=[0,1,2,3,4])
                conn.update(worksheet="Resultados", data=pd.concat([old, log], ignore_index=True))
                st.session_state.registro_exitoso = True
                st.success("✅ Intento registrado exitosamente.")
            except Exception as e:
                st.warning(f"⚠️ Nota: El registro automático no pudo completarse. ({e})")

        st.subheader("📊 Desempeño por Áreas")
        diag = [{"Área": k[0], "Subárea": k[1], "Aciertos": f"{v['a']}/{v['t']}", "Eficiencia": f"{(v['a']/v['t'])*100:.1f}%"} for k, v in st.session_state.analitica.items()]
        st.table(pd.DataFrame(diag))
        
        mostrar_imagen("felino40.png", "¡Orgullo Felino!")
        if st.button("Reiniciar"):
            for k in st.session_state.keys(): del st.session_state[k]
            st.rerun()
