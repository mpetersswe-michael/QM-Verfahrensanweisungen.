import streamlit as st
import pandas as pd
from fpdf import FPDF
from pathlib import Path

# ----------------------------
# Einstellungen
# ----------------------------
CSV_FILE = "qm_va.csv"
REQUIRED_COLS = ["VA_Nr", "Titel", "Kapitel", "Unterkapitel",
                 "Revisionsstand", "Erstellt von", "Zeitstempel"]

# ----------------------------
# CSV laden (inkl. Zusatzfelder F:J)
# ----------------------------
REQUIRED_COLS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel",
    "Revisionsstand", "Erstellt von", "Zeitstempel",
    "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]

if Path(CSV_FILE).exists():
    df_qm_all = pd.read_csv(CSV_FILE, sep=";", encoding="utf-8")
else:
    df_qm_all = pd.DataFrame(columns=REQUIRED_COLS)

# Fehlende Spalten ergänzen
for col in REQUIRED_COLS:
    if col not in df_qm_all.columns:
        df_qm_all[col] = ""


# ----------------------------
# VA-Auswahl und Anzeige
# ----------------------------
st.markdown("## 📁 Verfahrensanweisungen anzeigen und exportieren")

if not options_va:
    st.info("Keine VAs vorhanden. Bitte zuerst eine Verfahrensanweisung speichern.")
    st.stop()

selected_va = st.selectbox("VA auswählen", options=options_va, key="va_select")
df_sel = df_qm_all[df_qm_all["VA_Nr"].astype(str) == str(selected_va)]

if df_sel.empty:
    st.error("Für die ausgewählte VA wurden keine Daten gefunden.")
    st.stop()

row = df_sel.iloc[0]

# Pflichtfelder anzeigen
st.markdown(f"**VA Nummer:** {row['VA_Nr']}")
st.markdown(f"**Titel:** {row['Titel']}")
st.markdown(f"**Kapitel:** {row['Kapitel']}")
st.markdown(f"**Unterkapitel:** {row['Unterkapitel']}")
st.markdown(f"**Revisionsstand:** {row['Revisionsstand']}")
st.markdown(f"**Erstellt von:** {row['Erstellt von']}")
st.markdown(f"**Zeitstempel:** {row['Zeitstempel']}")

# Zusatzfelder (Formular)
beschreibung = st.text_area("Ziel", key="beschreibung")
geltungsbereich = st.text_area("Geltungsbereich", key="geltungsbereich")
durchfuehrung = st.text_area("Vorgehensweise", key="durchfuehrung")
verantwortlichkeiten = st.text_area("Kommentar", key="verantwortlichkeiten")
nachweise = st.text_area("Mitgeltende Unterlagen", key="nachweise")

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

        # Zusatzfelder mit fettgedruckten Überschriften
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

        section("Ziel", beschreibung)
        section("Geltungsbereich", geltungsbereich)
        section("Vorgehensweise", durchfuehrung)
        section("Kommentar", verantwortlichkeiten)
        section("Mitgeltende Unterlagen", nachweise)

        # Fußzeile
        pdf.set_y(-30)
        pdf.set_font("Arial", style="I", size=10)
        pdf.cell(0, 10, "Erstellt von: Peters, Michael – Qualitätsbeauftragter", ln=True, align="L")

        # PDF erzeugen
        pdf_raw = pdf.output(dest="S")
        pdf_bytes = pdf_raw.encode("latin-1") if isinstance(pdf_raw, str) else pdf_raw

        st.session_state["pdf_bytes"] = pdf_bytes
        st.session_state["pdf_filename"] = f"{row['VA_Nr']}.pdf"
        st.success("PDF erstellt. Jetzt kannst du es herunterladen.")

        # Zusatzfelder in CSV speichern
        df_qm_all.loc[df_qm_all["VA_Nr"] == row["VA_Nr"], "Ziel"] = beschreibung
        df_qm_all.loc[df_qm_all["VA_Nr"] == row["VA_Nr"], "Geltungsbereich"] = geltungsbereich
        df_qm_all.loc[df_qm_all["VA_Nr"] == row["VA_Nr"], "Vorgehensweise"] = durchfuehrung
        df_qm_all.loc[df_qm_all["VA_Nr"] == row["VA_Nr"], "Kommentar"] = verantwortlichkeiten
        df_qm_all.loc[df_qm_all["VA_Nr"] == row["VA_Nr"], "Mitgeltende Unterlagen"] = nachweise

        try:
            df_qm_all.to_csv(CSV_FILE, sep=";", index=False, encoding="utf-8")
        except Exception:
            df_qm_all.to_csv(CSV_FILE, sep=";", index=False, encoding="latin-1")

    except Exception as e:
        st.session_state["pdf_bytes"] = None
        st.session_state["pdf_filename"] = None
        st.error(f"PDF konnte nicht erzeugt werden: {e}")

# Download-Button
if "pdf_bytes" in st.session_state and st.session_state["pdf_bytes"]:
    st.download_button(
        label="Download PDF",
        data=st.session_state["pdf_bytes"],
        file_name=st.session_state["pdf_filename"],
        mime="application/pdf",
        key="btn_pdf_download"
    )
else:
    st.info("Noch kein PDF exportiert.")

# ----------------------------
# VA löschen
# ----------------------------
st.markdown("### ❌ Daten bzw. VA löschen")

if st.button("VA löschen", key="btn_va_delete"):
    try:
        df_qm_all = df_qm_all[df_qm_all["VA_Nr"].astype(str) != str(selected_va)]
        df_qm_all.to_csv(CSV_FILE, sep=";", index=False, encoding="utf-8")
        st.success(f"VA {selected_va} wurde gelöscht.")
        st.session_state["va_select"] = None
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Löschen fehlgeschlagen: {e}")


