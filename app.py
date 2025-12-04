import streamlit as st
import pandas as pd
from fpdf import FPDF

# ----------------------------
# Einstellungen
# ----------------------------
CSV_FILE = "qm_va.csv"  # Pfad zur CSV mit Pflichtfeldern
REQUIRED_COLS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel",
    "Revisionsstand", "Erstellt von", "Zeitstempel"
]

# ----------------------------
# Login mit Passworteingabe (einfach, stabil)
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("## 🔒 Login")
    password = st.text_input("Passwort", type="password")
    if st.button("Login"):
        if password == "qm2024":  # Festes Passwort
            st.session_state["logged_in"] = True
        else:
            st.error("Falsches Passwort.")
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
# CSV Import (Pflichtfelder)
# ----------------------------
try:
    df_qm_all = pd.read_csv(CSV_FILE, sep=";", encoding="utf-8")
except FileNotFoundError:
    df_qm_all = pd.DataFrame(columns=REQUIRED_COLS)

# Fehlende Spalten ergänzen, damit die Ansicht stabil bleibt
for c in REQUIRED_COLS:
    if c not in df_qm_all.columns:
        df_qm_all[c] = ""

# VA-Optionen ermitteln
options_va = (
    df_qm_all["VA_Nr"].dropna().astype(str).unique().tolist()
    if not df_qm_all.empty else []
)

# ----------------------------
# UI: Formularansicht + PDF Export
# ----------------------------
st.markdown("## 📄 Verfahrensanweisung anzeigen")

# Session-State für PDF
if "pdf_bytes" not in st.session_state:
    st.session_state["pdf_bytes"] = None
if "pdf_filename" not in st.session_state:
    st.session_state["pdf_filename"] = None

if not options_va:
    st.info("Keine VAs vorhanden. Bitte zuerst eine Verfahrensanweisung speichern.")
else:
    selected_va = st.selectbox("VA auswählen", options=options_va, key="va_select")

    df_sel = df_qm_all[df_qm_all["VA_Nr"].astype(str) == str(selected_va)]
    if df_sel.empty:
        st.error("Für die ausgewählte VA wurden keine Daten gefunden.")
        st.stop()

    row = df_sel.iloc[0]

    # Pflichtfelder sichtbar machen
    st.markdown(f"**VA Nummer:** {row['VA_Nr']}")
    st.markdown(f"**Titel:** {row['Titel']}")
    st.markdown(f"**Kapitel:** {row['Kapitel']}")
    st.markdown(f"**Unterkapitel:** {row['Unterkapitel']}")
    st.markdown(f"**Revisionsstand:** {row['Revisionsstand']}")
    st.markdown(f"**Erstellt von:** {row['Erstellt von']}")
    st.markdown(f"**Zeitstempel:** {row['Zeitstempel']}")

    # Zusatzfelder (nur Formular/Session, nicht CSV gespeichert)
    beschreibung = st.text_area("Beschreibung / Zweck", key="beschreibung")
    geltungsbereich = st.text_area("Geltungsbereich", key="geltungsbereich")
    verantwortlichkeiten = st.text_area("Verantwortlichkeiten", key="verantwortlichkeiten")
    durchfuehrung = st.text_area("Durchführung", key="durchfuehrung")
    nachweise = st.text_area("Dokumentation / Nachweise", key="nachweise")

    # ----------------------------
    # PDF Export
    # ----------------------------
    st.markdown("### 📤 PDF Export")

    if st.button("PDF Export starten", key="btn_pdf_generate"):
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Kopf
            pdf.set_font("Arial", style="", size=16)
            pdf.cell(0, 10, "QM-Verfahrensanweisung", ln=True, align="C")
            pdf.ln(5)

            # Pflichtfelder
            pdf.set_font("Arial", size=11)
            labels = {
                "VA_Nr": "VA Nummer",
                "Titel": "Titel",
                "Kapitel": "Kapitel",
                "Unterkapitel": "Unterkapitel",
                "Revisionsstand": "Revisionsstand",
                "Erstellt von": "Erstellt von",
                "Zeitstempel": "Zeitstempel",
            }
            for col, label in labels.items():
                val = row[col] if col in row else ""
                text = str(val) if pd.notna(val) else ""
                pdf.multi_cell(0, 8, f"{label}: {text}")

            pdf.ln(3)

            # Abschnittsfunktion mit latin-1 Fallback
            def section(title, content):
                pdf.set_font("Arial", style="B", size=12)
                pdf.multi_cell(0, 8, title)
                pdf.set_font("Arial", size=11)
                safe = content if content else ""
                try:
                    pdf.multi_cell(0, 8, safe)
                except Exception:
                    pdf.multi_cell(0, 8, safe.encode("latin-1", "replace").decode("latin-1"))
                pdf.ln(2)

            section("Beschreibung / Zweck", beschreibung)
            section("Geltungsbereich", geltungsbereich)
            section("Verantwortlichkeiten", verantwortlichkeiten)
            section("Durchführung", durchfuehrung)
            section("Dokumentation / Nachweise", nachweise)

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

    # Download-Button
    if st.session_state["pdf_bytes"]:
        st.download_button(
            label="Download PDF",
            data=st.session_state["pdf_bytes"],
            file_name=st.session_state["pdf_filename"],
            mime="application/pdf",
            key="btn_pdf_download"
        )
    else:
        st.button("Download PDF (noch nicht verfügbar)", disabled=True)



