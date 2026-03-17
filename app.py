import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🛠️ Diagnóstico de Conexión EGEL")

# --- PASO 1: VERIFICAR SECRETS ---
st.subheader("1. Verificación de Secrets")
try:
    # Intentamos acceder a un valor cualquiera de tus secrets
    test_secret = st.secrets["connections"]["gsheets"]["project_id"]
    st.success(f"✅ Secrets detectados para el proyecto: {test_secret}")
except Exception as e:
    st.error(f"❌ Error en Secrets: No se encuentra la configuración [connections.gsheets]. Revisa el formato TOML.")
    st.stop()

# --- PASO 2: INTENTAR CONEXIÓN ---
st.subheader("2. Prueba de Enlace con Google")
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.success("✅ Objeto de conexión creado.")
except Exception as e:
    st.error(f"❌ Error al crear la conexión: {e}")
    st.stop()

# --- PASO 3: PRUEBA DE ESCRITURA (Aquí suele dar el Error 400) ---
st.subheader("3. Prueba de Escritura en 'Resultados'")
if st.button("Ejecutar Prueba de Escritura"):
    try:
        # Intentamos leer primero para ver si tenemos acceso
        df_prueba = conn.read(worksheet="Resultados")
        st.write("Lectura exitosa. Columnas detectadas:", df_prueba.columns.tolist())
        
        # Intentamos escribir una fila de prueba
        test_data = pd.DataFrame([{"Fecha": "TEST", "Nombre": "TEST", "Correo": "test@test.com", "Carrera": "TEST", "Resultado": "0/0"}])
        actualizado = pd.concat([df_prueba, test_data], ignore_index=True)
        
        conn.update(worksheet="Resultados", data=actualizado)
        st.success("🎉 ¡CONEXIÓN TOTAL EXITOSA! El Error 400 ha sido superado.")
    except Exception as e:
        st.error(f"❌ Fallo en la escritura (Error 400 probable): {e}")
        st.info("Si el error menciona 'Columns', verifica que los títulos en tu Excel sean EXACTAMENTE: Fecha, Nombre, Correo, Carrera, Resultado")
