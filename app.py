import streamlit as st
import pandas as pd
from fpdf import FPDF

# ----------------------------
# Login-Logik ohne rerun
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("## 🔐 Login")
    if st.button("Login"):
        st.session_state["logged_in"] = True
    else:
        st.stop()

# ----------------------------
# Sidebar mit Logout
# ----------------------------
with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.stop()

# ----------------------------
# Datenimport
# ----------------------------
CSV_FILE = "qm_va.csv"

try:
    df_qm_all = pd.read_csv(CSV_FILE, sep=";", encoding="utf-8")
except FileNotFoundError:
    df_qm_all = pd.DataFrame(columns=[
        "VA_Nr", "Titel", "Kapitel", "Unterkapitel",
        "Revisionsstand", "Erstellt von", "Zeitstempel"
    ])

options_va = df_qm_all["VA_Nr"].unique().tolist() if not df_qm_all.empty else []

# ----------------------------
# Formularansicht einer VA
# ----------------------------
st.markdown("## 📄 Verfahrensanweisung anzeigen")

if options_va:
    selected_va = st.selectbox("VA auswählen", options=options_va, key="va_select")
    df_sel = df_qm_all[df_qm_all["VA_Nr"] == selected_va]

    if not df_sel.empty:
        row = df_sel.iloc[0]

        # Pflichtfelder sichtbar machen
        st.markdown(f"**VA Nummer:** {row['VA_Nr']}")
        st.markdown(f"**Titel:** {row['Titel']}")
        st.markdown(f"**Kapitel:** {row['Kapitel']}")
        st.markdown(f"**Unterkapitel:** {row['Unterkapitel']}")
        st.markdown(f"**Revisionsstand:** {row['Revisionsstand']}")
        st.markdown(f"**Erstellt von:** {row['Erstellt von']}")
        st.markdown(f"**Zeitstempel:** {row['Zeitstempel']}")

        # Zusatzfelder (nicht in CSV gespeichert, nur Session)
        beschreibung = st.text_area("Beschreibung / Zweck", key="beschreibung")
        geltungsbereich = st.text_area("Geltungsbereich", key="geltungsbereich")
        verantwortlichkeiten = st.text_area("Verantwortlichkeiten", key="verantwortlichkeiten")
        durchfuehrung = st.text_area("Durchführung", key="durchfuehrung")
        nachweise = st.text_area("Dokumentation / Nachweise", key="nachweise")

        # ----------------------------
        # PDF Export mit zwei Buttons
        # ----------------------------
        if "pdf_bytes" not in st.session_state:
            st.session_state["pdf_bytes"] = None
        if "pdf_filename" not in st.session_state:
            st.session_state["pdf_filename"] = None

        # Button 1: PDF erzeugen
        if st.button("PDF Export starten", key="btn_pdf_generate"):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=14)
                pdf.cell(0, 10, "QM-Verfahrensanweisung", ln=True, align="C")
                pdf.set_font("Arial", size=11)
                pdf.ln(5)

                # Pflichtfelder
                labels = {
                    "VA_Nr": "VA Nummer",
                    "Titel": "Titel",
                    "Kapitel": "Kapitel",
                    "Unterkapitel": "Unterkapitel",
                    "Revisionsstand": "Revisionsstand",
                    "Erstellt von": "Erstellt von",
                    "Zeitstempel": "Zeitstempel",
                }
                for col in labels:
                    val = row.get(col, "")
                    text = str(val) if pd.notna(val) else ""
                    pdf.multi_cell(0, 8, f"{labels[col]}: {text}")
                    pdf.ln(1)

                # Zusatzfelder
                pdf.ln(5)
                pdf.multi_cell(0, 8, f"Beschreibung / Zweck:\n{beschreibung}")
                pdf.multi_cell(0, 8, f"Geltungsbereich:\n{geltungsbereich}")
                pdf.multi_cell(0, 8, f"Verantwortlichkeiten:\n{verantwortlichkeiten}")
                pdf.multi_cell(0, 8, f"Durchführung:\n{durchfuehrung}")
                pdf.multi_cell(0, 8, f"Dokumentation / Nachweise:\n{nachweise}")

                # PDF-Bytes robust erzeugen
                pdf_raw = pdf.output(dest="S")
                pdf_bytes = pdf_raw.encode("latin-1") if isinstance(pdf_raw, str) else pdf_raw

                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["pdf_filename"] = f"{row['VA_Nr']}.pdf"
                st.success("PDF erstellt. Jetzt kannst du es herunterladen.")
            except Exception as e:
                st.session_state["pdf_bytes"] = None
                st.session_state["pdf_filename"] = None
                st.error(f"PDF konnte nicht erzeugt werden: {e}")

        # Button 2: Download nur wenn PDF vorhanden
        if st.session_state["pdf_bytes"]:
            st.download_button(
                label="Download PDF",
                data=st.session_state["pdf_bytes"],
                file_name=st.session_state["pdf_filename"],
                mime="application/pdf",
                key="btn_pdf_download"
            )
else:
    st.info("Keine VAs vorhanden. Bitte zuerst eine Verfahrensanweisung speichern.")

