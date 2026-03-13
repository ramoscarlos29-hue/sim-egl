import streamlit as st
import pandas as pd
import random
from streamlit_gsheets import GSheetsConnection

# --- DISEÑO ---
st.set_page_config(page_title="Simulador EGEL", page_icon="🎓", layout="wide")

URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqEPlutGK3ornINr7D09b3KqdQX__1-AZC6hzMle6tOOEPQeIher3Wgcg9jUxgs_RXXNSAsD1omH-/pub?output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_csv(URL_DATOS)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return None

# --- INICIALIZACIÓN ---
if 'examen_iniciado' not in st.session_state:
    st.session_state.update({
        'examen_iniciado': False, 'indice': 0, 'puntaje': 0,
        'nombre': "", 'carrera': "", 'preguntas': None, 
        'respondido': False, 'resultados_por_area': {}
    })

# --- PANTALLA DE REGISTRO ---
if not st.session_state.examen_iniciado:
    st.title("🚀 Simulador EGEL")
    nombre = st.text_input("Nombre completo:")
    carrera = st.selectbox("Carrera:", ["Gastronomía y Negocios", "Negocios Turísticos"])
    
    if st.button("Empezar Evaluación"):
        if nombre:
            df_full = cargar_datos()
            if df_full is not None:
                df_carrera = df_full[df_full['Carrera'] == carrera]
                n_total = min(20, len(df_carrera))
                seleccion = df_carrera.sample(n_total).reset_index(drop=True)
                
                st.session_state.update({
                    'nombre': nombre, 'carrera': carrera,
                    'preguntas': seleccion, 'examen_iniciado': True,
                    'indice': 0, 'puntaje': 0, 'resultados_por_area': {}
                })
                st.rerun()

# --- EXAMEN ---
else:
    df = st.session_state.preguntas
    
    if st.session_state.indice < len(df):
        fila = df.iloc[st.session_state.indice]
        area_actual = fila['Area'] if 'Area' in fila else "General"
        
        st.write(f"Participante: **{st.session_state.nombre}**")
        st.progress((st.session_state.indice) / len(df))
        
        st.markdown(f"**Área de conocimiento:** {area_actual}")
        st.markdown(f"#### {fila['Pregunta']}")
        
        opciones_dict = {"A": str(fila['A']).strip(), "B": str(fila['B']).strip(), "C": str(fila['C']).strip(), "D": str(fila['D']).strip()}
        lista_display = [f"{k}) {v}" for k, v in opciones_dict.items()]
        
        with st.form(key=f"p_{st.session_state.indice}"):
            sel = st.radio("Respuesta:", lista_display, disabled=st.session_state.respondido)
            validar = st.form_submit_button("Validar")

        if validar and not st.session_state.respondido:
            texto_elegido = opciones_dict[sel[0]]
            es_correcto = texto_elegido == str(fila['Correcta']).strip()
            
            # Guardar analítica por área
            if area_actual not in st.session_state.resultados_por_area:
                st.session_state.resultados_por_area[area_actual] = {"aciertos": 0, "total": 0}
            
            st.session_state.resultados_por_area[area_actual]["total"] += 1
            if es_correcto:
                st.session_state.resultados_por_area[area_actual]["aciertos"] += 1
                st.session_state.puntaje += 1
                st.success("✅ ¡Correcto!")
            else:
                st.error(f"❌ Incorrecto. Era la {fila['Correcta']}")
            
            st.session_state.respondido = True
            st.rerun()

        if st.session_state.respondido:
            if st.button("Siguiente Pregunta ➡️"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.rerun()

    # --- PANTALLA FINAL Y REGISTRO ---
    else:
        st.balloons()
        st.header("🏁 Resultados Finales")
        
        # 1) Registro en Google Sheets
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_registro = pd.DataFrame([{
                "Fecha": pd.Timestamp.now(),
                "Nombre": st.session_state.nombre,
                "Carrera": st.session_state.carrera,
                "Puntaje": f"{st.session_state.puntaje}/{len(df)}"
            }])
            # Intentar añadir a pestaña 'Resultados'
            existentes = conn.read(worksheet="Resultados")
            actualizado = pd.concat([existentes, df_registro], ignore_index=True)
            conn.update(worksheet="Resultados", data=actualizado)
            st.toast("✅ Intento guardado en base de datos")
        except:
            st.warning("⚠️ No se pudo conectar con la base de datos de registro.")

        # 2) Tabla de Correspondencia por Áreas
        st.subheader("📊 Desempeño por Áreas de CENEVAL")
        data_areas = []
        for area, datos in st.session_state.resultados_por_area.items():
            perc = (datos['aciertos'] / datos['total']) * 100
            data_areas.append({
                "Área de Conocimiento": area,
                "Aciertos": f"{datos['aciertos']}/{datos['total']}",
                "Efectividad": f"{perc:.1f}%"
            })
        
        st.table(pd.DataFrame(data_areas))

        if st.button("Reiniciar Simulador"):
            st.session_state.examen_iniciado = False
            st.rerun()
