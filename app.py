# --- RESULTADOS FINALES ---
    else:
        st.balloons()
        st.header(f"🏁 ¡Felicidades, {st.session_state.nombre}!")
        
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
                st.success("✅ Intento guardado en el registro institucional.")
                st.session_state.registro_intentado = True
            except Exception as e:
                st.warning(f"⚠️ Error de registro en la nube. Por favor descarga tu PDF.")

        # Tabla diagnóstica
        diag_data = []
        for k, v in st.session_state.analitica.items():
            ef = (v['a']/v['t'])*100
            if ef >= 80: s = "🟢 Óptimo"
            elif ef >= 60: s = "🟡 En desarrollo"
            else: s = "🔴 Requiere refuerzo"
            diag_data.append({"Área": k[0], "Subárea": k[1], "Aciertos": f"{v['a']}/{v['t']}", "Eficacia": ef, "Diagnóstico": s})
        
        df_res = pd.DataFrame(diag_data)
        st.table(df_res[["Área", "Subárea", "Aciertos", "Diagnóstico"]])

        # --- GENERACIÓN DE PDF CORREGIDA (Librería fpdf2) ---
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        # Usamos 'helvetica' que es estándar y soporta mejor los caracteres
        pdf.set_font("helvetica", 'B', 16)
        
        # Título
        pdf.cell(190, 10, "REPORTE DE EVALUACION EGEL", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font("helvetica", '', 12)
        # Limpiamos el texto de caracteres que latin-1 no soporta (reemplazo seguro)
        def clean_txt(t):
            return str(t).encode('latin-1', 'replace').decode('latin-1')

        pdf.cell(190, 8, clean_txt(f"Estudiante: {st.session_state.nombre}"), 0, 1)
        pdf.cell(190, 8, clean_txt(f"Carrera: {st.session_state.carrera}"), 0, 1)
        pdf.cell(190, 8, clean_txt(f"Puntaje: {st.session_state.puntaje}/{len(df)}"), 0, 1)
        pdf.ln(10)

        # Tabla PDF
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(85, 8, "Subarea", 1); pdf.cell(40, 8, "Aciertos", 1); pdf.cell(60, 8, "Diagnostico", 1, 1)
        
        pdf.set_font("helvetica", '', 9)
        for _, r in df_res.iterrows():
            pdf.cell(85, 8, clean_txt(r['Subárea'][:45]), 1)
            pdf.cell(40, 8, clean_txt(r['Aciertos']), 1, 0, 'C')
            pdf.cell(60, 8, clean_txt(r['Diagnóstico']), 1, 1, 'C')

        # Convertir a bytes para descarga
        pdf_output = pdf.output() 
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_output,
            file_name=f"Resultado_{st.session_state.nombre}.pdf",
            mime="application/pdf"
        )

        mostrar_imagen("felino40.png", "¡Orgullo Felino!")
        if st.button("Finalizar y Reiniciar"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
