# --- GENERACIÓN DE PDF SIN WARNINGS ---
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos # Importamos los nuevos controles de posición

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 16)
        
        # Título - Usando los nuevos parámetros recomendados
        pdf.cell(190, 10, "REPORTE DE EVALUACION EGEL", border=0, 
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        pdf.set_font("helvetica", '', 12)
        def clean(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
        
        # Datos del alumno
        pdf.cell(190, 8, clean(f"Estudiante: {st.session_state.nombre}"), border=0, 
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(190, 8, clean(f"Puntaje: {st.session_state.puntaje}/{len(df)}"), border=0, 
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        # Tabla de resultados
        pdf.set_font("helvetica", 'B', 10)
        for _, r in df_res.iterrows():
            texto_linea = f"{r['Subarea']}: {r['Aciertos']} - {r['Semaforo']}"
            pdf.cell(190, 8, clean(texto_linea), border=1, 
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Convertir a bytes para descarga
        pdf_bytes = pdf.output()
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=bytes(pdf_bytes),
            file_name=f"Resultado_{st.session_state.nombre}.pdf",
            mime="application/pdf"
        )
