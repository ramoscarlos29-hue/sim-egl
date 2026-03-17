# --- PRUEBA DE ESCRITURA PURA (SIN CONCATENAR) ---
if st.button("Ejecutar Prueba de Escritura Forzada"):
    try:
        # Creamos un dato simple
        test_data = pd.DataFrame([{
            "Fecha": "17/03/2026", 
            "Nombre": "Admin Test", 
            "Correo": "docente@lasallebajio.edu.mx", 
            "Carrera": "Gastronomía", 
            "Resultado": "20/20"
        }])
        
        # Intentamos escribir directamente ignorando lo que haya
        conn.update(worksheet="Resultados", data=test_data)
        st.success("🎉 ¡LOGRADO! La comunicación pura funciona.")
    except Exception as e:
        st.error(f"❌ Error crítico: {e}")
