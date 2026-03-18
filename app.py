import streamlit as st
import pandas as pd
import random
import os
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN INSTITUCIONAL ---
st.set_page_config(page_title="Simulador EGEL | La Salle Bajío", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #002d72; color: white; border-radius: 8px; width: 100%; font-weight: bold; height: 3em; }
    .stProgress > div > div > div > div { background-color: #d4002a; }
    .stRadio > label { font-size: 18px !important; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# Función para manejo de imágenes con el nuevo estándar de Streamlit
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
    except Exception as e:
        st.error(f"Error al cargar base de datos: {e}")
        return None

# --- ESTADO DE LA SESIÓN ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'correo': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'analitica': {}, 'ultimo_resultado': None,
        'registro_intentado': False
    })

# --- PANTALLA DE REGISTRO ---
if not st.session_state.examen_iniciado:
    col_logo, _ = st.columns([1, 2])
    with col_logo:
        mostrar_imagen("Turismo_Color.png")
    
    st.title("🚀 Simulador de Examen EGEL")
    st.subheader("Facultad de Turismo y Gastronomía")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        nombre = st.text_input("Nombre completo del alumno:", placeholder="Ej. Juan Pérez")
        correo = st.text_input("Correo Institucional:", placeholder="usuario@lasallebajio.edu.mx")
        carrera = st.selectbox("Carrera a evaluar:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Iniciar Simulación"):
            if nombre and correo.lower().endswith("@lasallebajio.edu.mx"):
                df_full = cargar_preguntas()
                if df_full is not None:
                    # Filtro por carrera y selección aleatoria
                    df_c = df_full[df_full['Carrera'] == carrera].reset_index(drop=True)
                    if len(df_c) > 0:
                        n_final = min(20, len(df_c))
                        st.session_state.preguntas = df_c.sample(n_final).reset_index(drop=True)
                        st.session_state.update({
                            'nombre': nombre, 'correo': correo, 
                            'carrera': carrera, 'examen_iniciado': True
                        })
                        st.rerun()
                    else:
                        st.error("No se encontraron reactivos para esta carrera en el repositorio.")
            elif not correo.lower().endswith("@lasallebajio.edu.mx"):
                st.error("❌ Acceso restringido: Solo correos institucionales de La Salle Bajío.")
            else:
                st.warning("⚠️ Por favor completa todos los campos de registro.")
    
    with col2:
        mostrar_imagen("felino46.jpg", "¡Mucho éxito, Felino!")

# --- PANTALLA DE EXAMEN ---
else:
    df = st.session_state.preguntas
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        area = str(fila.get('Area', 'General')).strip()
        subarea = str(fila.get('Subarea', 'General')).strip()
        
        st.write(f"Alumno: **{st.session_state.nombre}** | Progreso: **{st.session_state.indice + 1}/{len(df)}**")
        st.progress((st.session_state.indice) / len(df))
        st.divider()

        st.caption(f"EJE: {area} > SUB-ÁREA: {subarea}")
        st.markdown(f"#### {fila.get('Pregunta', 'Cargando reactivo...')}")
        
        # Mapeo limpio de opciones
        opciones_map = {
            "A": str(fila.get('A', '')).strip(),
            "B": str(fila.get('B', '')).strip(),
            "C": str(fila.get('C', '')).strip(),
            "D": str(fila.get('D', '')).strip()
        }
        display_opciones = [f"{k}) {v}" for k, v in opciones_map.items() if v not in ["nan", "", "None"]]
        
        with st.form(key=f"form_egel_{st.session_state.indice}"):
            seleccion = st.radio("Selecciona la respuesta correcta:", display_opciones, disabled=st.session_state.respondido)
            btn_validar = st.form_submit_button("Validar")

        if btn_validar and not st.session_state.respondido:
            # Procesamiento de respuesta
            texto_usuario = opciones_map[seleccion[0]]
            texto_correcto = str(fila.get('Correcta', '')).strip()
            
            # Registro en analítica interna
            llave_analitica = (area, subarea)
            if llave_analitica not in st.session_state.analitica:
                st.session_state.analitica[llave_analitica] = {'a': 0, 't': 0}
            
            st.session_state.analitica[llave_analitica]['t'] += 1
            if texto_usuario == texto_correcto:
                st.session_state.analitica[llave_analitica]['a'] += 1
                st.session_state.puntaje += 1
                st.session_state.ultimo_resultado = "OK"
            else:
                st.session_state.ultimo_resultado = "ERR"
            
            st.session_state.respondido = True
            st.rerun()

        if st.session_state.respondido:
            if st.session_state.ultimo_resultado == "OK":
                st.success("✅ **¡Correcto!**")
            else:
                st.error(f"❌ **Incorrecto.** La respuesta correcta era: {fila.get('Correcta')}")
            
            if 'Feedback' in fila and pd.notna(fila['Feedback']):
                st.info(f"💡 **Referencia:** {fila['Feedback']}")
            
            if st.button("Siguiente Pregunta ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.rerun()

    # --- PANTALLA DE RESULTADOS Y REGISTRO FORZADO ---
    else:
        st.balloons()
        st.header(f"🏁 Simulación Concluida, {st.session_state.nombre}")
        
        # BLOQUE DE REGISTRO FORZADO
        if not st.session_state.registro_intentado:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                nuevo_log = pd.DataFrame([{
                    "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                    "Nombre": str(st.session_state.nombre),
                    "Correo": str(st.session_state.correo),
                    "Carrera": str(st.session_state.carrera),
                    "Resultado": f"{st.session_state.puntaje}/{len(df)}"
                }])
                
                # Leemos asegurando que existan las 5 columnas básicas
                df_actual = conn.read(worksheet="Resultados", usecols=[0,1,2,3,4])
                df_final = pd.concat([df_actual, nuevo_log], ignore_index=True)
                
                conn.update(worksheet="Resultados", data=df_final)
                st.success("✅ Tu resultado ha sido guardado en el registro institucional.")
                st.session_state.registro_intentado = True
            except Exception as e:
                st.error(f"⚠️ Error 400 de comunicación: No se pudo registrar automáticamente.")
                st.info("Por favor captura pantalla de tus resultados para tu evidencia.")

        # TABLA DIAGNÓSTICA
        st.subheader("📊 Diagnóstico de Competencias CENEVAL")
        if st.session_state.analitica:
            resumen = []
            for (ar, sub), v in st.session_state.analitica.items():
                efectividad = (v['a']/v['t'])*100
                resumen.append({
                    "Área": ar, "Subárea": sub, 
                    "Aciertos": f"{v['a']}/{v['t']}", 
                    "Efectividad": f"{efectividad:.1f}%"
                })
            st.table(pd.DataFrame(resumen))
        
        mostrar_imagen("felino40.jpg", "¡Orgullo Felino!")
        
        if st.button("Finalizar y Reiniciar"):
            # Limpiar todo el estado para un nuevo examen
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
