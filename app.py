# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import datetime as dt
import io
from fpdf import FPDF

# ----------------------------
# Konfiguration
# ----------------------------
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
QM_COLUMNS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
    "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]

# ----------------------------
# Hilfsfunktionen
# ----------------------------
def clean_text(text):
    if not text:
        return "-"
    return (
        str(text)
        .encode("latin-1", errors="ignore")
        .decode("latin-1")
        .replace("–", "-")
        .replace("•", "*")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("€", "EUR")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )

class CustomPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)

        # Linke Seite: VA-Name
        va_name = getattr(self, "va_name", "")
        self.cell(0, 10, clean_text(va_name), align="L")

        # Rechte Seite: Seitenzahl
        self.set_x(-50)
        page_text = f"Seite {self.page_no()} von {{nb}}"
        self.cell(0, 10, clean_text(page_text), align="R")

def export_va_to_pdf(row):
    pdf = CustomPDF()
    pdf.alias_nb_pages()  # Gesamtseitenzahl aktivieren
    pdf.va_name = f"VA {row['VA_Nr']}"  # VA-Name für Fußzeile
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text(f"QM-Verfahrensanweisung - {row['VA_Nr']}"), ln=True, align="C")
    pdf.ln(5)

    def add_section(title, content):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, clean_text(title), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, clean_text(content if content else "-"))
        pdf.ln(3)

    add_section("Titel", row.get("Titel", ""))
    add_section("Kapitel", row.get("Kapitel", ""))
    add_section("Unterkapitel", row.get("Unterkapitel", ""))
    add_section("Revisionsstand", row.get("Revisionsstand", ""))
    add_section("Ziel", row.get("Ziel", ""))
    add_section("Geltungsbereich", row.get("Geltungsbereich", ""))
    add_section("Vorgehensweise", row.get("Vorgehensweise", ""))
    add_section("Kommentar", row.get("Kommentar", ""))
    add_section("Mitgeltende Unterlagen", row.get("Mitgeltende Unterlagen", ""))

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

# ----------------------------
# Verwaltung: Anzeige, Auswahl, Download, Löschen, PDF
# ----------------------------
st.markdown("## Verfahrensanweisungen anzeigen und verwalten")

try:
    df_all = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
except:
    df_all = pd.DataFrame(columns=QM_COLUMNS)

if df_all.empty:
    st.info("Noch keine Verfahrensanweisungen gespeichert.")
else:
    selected_va = st.selectbox(
        "VA auswählen zur Anzeige oder PDF-Erzeugung",
        options=[""] + sorted(df_all["VA_Nr"].dropna().astype(str).unique()),
        index=0
    )

    df_filtered = df_all[df_all["VA_Nr"].astype(str) == selected_va] if selected_va else df_all
    st.dataframe(df_filtered, use_container_width=True)

    # CSV-Download
    csv_data = df_filtered.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="CSV herunterladen",
        data=csv_data,
        file_name=f"qm_va_{dt.date.today()}.csv",
        mime="text/csv"
    )

    # Löschfunktion
    st.markdown("### VA löschen")
    if selected_va:
        if st.button("Ausgewählte VA löschen", type="secondary"):
            df_remaining = df_all[df_all["VA_Nr"].astype(str) != selected_va]
            df_remaining.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"VA {selected_va} wurde gelöscht. Bitte Seite neu laden.")
    else:
        st.warning("Bitte zuerst eine VA auswählen, um sie zu löschen.")

    # PDF-Export
    st.markdown("### PDF erzeugen")
    if selected_va:
        if st.button("PDF erzeugen für ausgewählte VA"):
            df_sel = df_all[df_all["VA_Nr"].astype(str) == selected_va]
            if not df_sel.empty:
                pdf_bytes = export_va_to_pdf(df_sel.iloc[0])
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"{selected_va}.pdf",
                    mime="application/pdf"
                )
    else:
        st.warning("Bitte zuerst eine VA auswählen, um PDF zu erzeugen.")





