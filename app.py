import streamlit as st
import pandas as pd
import random
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE DISEÑO ---
st.set_page_config(page_title="Simulador EGEL", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    .stAlert { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

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
        'nombre': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'ultimo_resultado': None,
        'analitica': {} # Guardará { (Area, Subarea): {aciertos: 0, total: 0} }
    })

# --- PANTALLA DE INICIO ---
if not st.session_state.examen_iniciado:
    st.title("🚀 Simulador EGEL")
    st.markdown("### Bienvenido al Sistema de Preparación")
    
    with st.container():
        nombre = st.text_input("Nombre completo del estudiante:", placeholder="Ej. Juan Pérez")
        carrera = st.selectbox("Selecciona tu carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
        
        if st.button("Comenzar Evaluación (20 Reactivos)"):
            if nombre:
                df_full = cargar_preguntas()
                if df_full is not None:
                    # Filtro por Carrera
                    df_carrera = df_full[df_full['Carrera'] == carrera].reset_index(drop=True)
                    
                    if len(df_carrera) > 0:
                        n_final = min(20, len(df_carrera))
                        st.session_state.preguntas = df_carrera.sample(n_final).reset_index(drop=True)
                        st.session_state.nombre = nombre
                        st.session_state.carrera = carrera
                        st.session_state.examen_iniciado = True
                        st.rerun()
                    else:
                        st.error("No se encontraron preguntas para esta carrera en el Excel.")
            else:
                st.warning("⚠️ Ingresa tu nombre para continuar.")

# --- PANTALLA DE EVALUACIÓN ---
else:
    df = st.session_state.preguntas
    
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        area = str(fila['Area']).strip()
        subarea = str(fila['Subarea']).strip()
        
        st.write(f"Estudiante: **{st.session_state.nombre}** | Carrera: **{st.session_state.carrera}**")
        st.progress((st.session_state.indice) / len(df))
        st.divider()

        st.caption(f"ÁREA: {area} > SUBÁREA: {subarea}")
        st.markdown(f"#### {fila['Pregunta']}")
        
        # Mapeo de opciones
        opc_dict = {
            "A": str(fila['A']).strip(),
            "B": str(fila['B']).strip(),
            "C": str(fila['C']).strip(),
            "D": str(fila['D']).strip()
        }
        display_list = [f"{k}) {v}" for k, v in opc_dict.items()]
        
        with st.form(key=f"q_{st.session_state.indice}"):
            sel = st.radio("Elija la opción correcta:", display_list, disabled=st.session_state.respondido)
            validar = st.form_submit_button("Validar Respuesta")

        if validar and not st.session_state.respondido:
            # Lógica de calificación
            texto_usuario = opc_dict[sel[0]]
            texto_correcto = str(fila['Correcta']).strip()
            es_correcto = texto_usuario == texto_correcto
            
            # Registrar analítica por Área/Subárea
            llave_analitica = (area, subarea)
            if llave_analitica not in st.session_state.analitica:
                st.session_state.analitica[llave_analitica] = {'aciertos': 0, 'total': 0}
            
            st.session_state.analitica[llave_analitica]['total'] += 1
            if es_correcto:
                st.session_state.analitica[llave_analitica]['aciertos'] += 1
                st.session_state.puntaje += 1
                st.session_state.ultimo_resultado = "OK"
            else:
                st.session_state.ultimo_resultado = "ERROR"
            
            st.session_state.respondido = True
            st.rerun()

        if st.session_state.respondido:
            if st.session_state.ultimo_resultado == "OK":
                st.success("✅ **¡Correcto!**")
            else:
                st.error(f"❌ **Incorrecto.** La respuesta correcta era: {fila['Correcta']}")
            
            if 'Feedback' in fila and pd.notna(fila['Feedback']):
                st.info(f"💡 **Nota:** {fila['Feedback']}")
            
            if st.button("Continuar a la siguiente ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.rerun()

    # --- RESULTADOS FINALES ---
    else:
        st.balloons()
        st.header("🏁 Evaluación Finalizada")
        
        # 1. Registro automático en Sheets
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            # Solo intentamos escribir si hay conexión
            registro = pd.DataFrame([{
                "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "Nombre": st.session_state.nombre,
                "Carrera": st.session_state.carrera,
                "Resultado": f"{st.session_state.puntaje}/{len(df)}"
            }])
            existentes = conn.read(worksheet="Resultados")
            nuevo_df = pd.concat([existentes, registro], ignore_index=True)
            conn.update(worksheet="Resultados", data=nuevo_df)
            st.toast("✅ Resultado registrado con éxito")
        except Exception as e:
            st.warning("⚠️ El resultado no se guardó en el registro central. Contacta al docente.")

        # 2. Tabla Diagnóstica
        st.subheader("📊 Diagnóstico por Áreas de Conocimiento")
        tabla_diag = []
        for (a, s), v in st.session_state.analitica.items():
            efect = (v['aciertos'] / v['total']) * 100
            tabla_diag.append({
                "Área": a, "Subárea": s, 
                "Aciertos": f"{v['aciertos']}/{v['total']}", 
                "Efectividad": f"{efect:.1f}%"
            })
        
        st.table(pd.DataFrame(tabla_diag))
        
        if st.button("Finalizar y Salir"):
            st.session_state.examen_iniciado = False
            st.rerun()
