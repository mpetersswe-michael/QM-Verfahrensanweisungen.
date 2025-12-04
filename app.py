import streamlit as st
import pandas as pd
import datetime as dt
from fpdf import FPDF

# ----------------------------
# Basis-Konfiguration
# ----------------------------
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide")
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
QM_COLUMNS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
    "Erstellt von", "Zeitstempel"
]

# ----------------------------
# Hilfsfunktionen
# ----------------------------
def load_data(file: str, columns: list) -> pd.DataFrame:
    try:
        df = pd.read_csv(file, sep=";", encoding="utf-8-sig")
    except Exception:
        df = pd.DataFrame(columns=columns)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    return df[columns]

def save_data(file: str, df: pd.DataFrame) -> None:
    df.to_csv(file, sep=";", index=False, encoding="utf-8-sig")

def to_csv_semicolon(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

def export_pdf_row_to_bytes(df_row: pd.Series) -> bytes:
    if isinstance(df_row, pd.DataFrame):
        df_row = df_row.iloc[0]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, "QM-Verfahrensanweisung", ln=True, align="C")
    pdf.set_font("Arial", size=11)
    pdf.ln(5)

    labels = {
        "VA_Nr": "VA Nummer",
        "Titel": "Titel",
        "Kapitel": "Kapitel",
        "Unterkapitel": "Unterkapitel",
        "Revisionsstand": "Revisionsstand",
        "Erstellt von": "Erstellt von",
        "Zeitstempel": "Zeitstempel",
    }
    for col in QM_COLUMNS:
        val = df_row[col] if col in df_row.index else ""
        text = str(val) if pd.notna(val) else ""
        pdf.multi_cell(0, 8, f"{labels.get(col, col)}: {text}")
        pdf.ln(1)

    try:
        pdf_str = pdf.output(dest="S")
        if isinstance(pdf_str, str):
            return pdf_str.encode("latin-1")
        elif isinstance(pdf_str, bytes):
            return pdf_str
        else:
            return b""
    except Exception:
        return b""

# ----------------------------
# Login
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("## 🔐 Login QM-Verfahrensanweisungen")
    pw = st.text_input("Passwort", type="password", key="pw")
    if st.button("Login"):
        if st.session_state.get("pw", "") == "QM2024":
            st.session_state["auth"] = True
            st.success("Login erfolgreich – du kannst jetzt mit der App arbeiten.")
        else:
            st.error("Falsches Passwort.")
    st.stop()

with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout"):
        st.session_state["auth"] = False
        st.success("Logout erfolgreich – bitte neu einloggen.")
        st.stop()

# ----------------------------
# Session-State nur initialisieren (nie überschreiben)
# ----------------------------
defaults = {
    "va_nr": "",
    "va_title": "",
    "ziel": "",
    "geltung": "",
    "vorgehen": "",
    "kommentar": "",
    "unterlagen": "",
    "erstellt_von": "",
    "kapitel_num": 7,
    "unterkapitel_num": 3,
    "revision_date": dt.date.today(),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------
# Eingabeformular (Form sichert konsistente Werte)
# ----------------------------
st.markdown("## 📝 Neue Verfahrensanweisung erfassen")

with st.form("va_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("VA Nummer", key="va_nr", placeholder="z. B. VA003")
        st.selectbox("Kapitel Nr.", list(range(1, 11)),
                     index=st.session_state["kapitel_num"] - 1, key="kapitel_num")
        st.date_input("Revisionsstand", value=st.session_state["revision_date"], key="revision_date")
        st.text_input("Erstellt von (Name + Funktion)", key="erstellt_von",
                      placeholder="z. B. Peters, Michael – Qualitätsbeauftragter")
    with col2:
        st.text_input("Titel", key="va_title", placeholder="Kommunikationswege im Pflegedienst")
        st.selectbox("Unterkapitel Nr.", list(range(1, 11)),
                     index=st.session_state["unterkapitel_num"] - 1, key="unterkapitel_num")

    # Sichtbare, nicht persistierte Felder (werden nicht gespeichert)
    st.text_area("Ziel", key="ziel", height=100)
    st.text_area("Geltungsbereich", key="geltung", height=80)
    st.text_area("Vorgehensweise", key="vorgehen", height=150)
    st.text_area("Kommentar", key="kommentar", height=80)
    st.text_area("Mitgeltende Unterlagen", key="unterlagen", height=80)

    # Unterkapitel immer im sicheren 7-3 Format als String
    kapitel_label = f"Kapitel {st.session_state['kapitel_num']}"
    unterkapitel_label = f"{st.session_state['kapitel_num']}-{st.session_state['unterkapitel_num']}"
    st.caption(f"Unterkapitel wird gespeichert als: {unterkapitel_label}")

    submit = st.form_submit_button("Verfahrensanweisung speichern")
    reset_clicked = st.form_submit_button("🧹 Eingabe zurücksetzen")

# Reset: nur vorhandene Keys leeren (in der Form)
if reset_clicked:
    for key in ["va_nr", "va_title", "ziel", "geltung", "vorgehen", "kommentar", "unterlagen", "erstellt_von"]:
        if key in st.session_state:
            st.session_state[key] = ""
    st.success("Eingaben zurückgesetzt.")

# Speichern nach Formular-Submit
if submit:
    va_nr_val = st.session_state["va_nr"].strip()
    va_title_val = st.session_state["va_title"].strip()
    erstellt_von_val = st.session_state["erstellt_von"].strip()
    if not va_nr_val or not va_title_val:
        st.warning("VA Nummer und Titel sind Pflicht.")
    else:
        new_va = pd.DataFrame([{
            "VA_Nr": va_nr_val,
            "Titel": va_title_val,
            "Kapitel": kapitel_label,
            "Unterkapitel": str(unterkapitel_label),  # sicher: String & 7-3
            "Revisionsstand": st.session_state["revision_date"].strftime("%Y-%m-%d"),
            "Erstellt von": erstellt_von_val,
            "Zeitstempel": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }])
        try:
            df_old = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
        except Exception:
            df_old = pd.DataFrame(columns=QM_COLUMNS)
        df_old = df_old.reindex(columns=QM_COLUMNS, fill_value="")
        df_new = pd.concat([df_old, new_va.reindex(columns=QM_COLUMNS)], ignore_index=True)
        save_data(DATA_FILE_QM, df_new)
        st.success(f"VA {va_nr_val} gespeichert.")

# ----------------------------
# Anzeige & CSV Export
# ----------------------------
st.markdown("## 📂 Verfahrensanweisungen anzeigen und exportieren")

df_qm_all = load_data(DATA_FILE_QM, QM_COLUMNS)
options_va = sorted([str(x).strip() for x in df_qm_all["VA_Nr"].dropna().unique() if str(x).strip() != ""])
filter_va = st.selectbox("VA auswählen", options=[""] + options_va, index=0)

df_filtered = df_qm_all[df_qm_all["VA_Nr"] == filter_va] if filter_va else df_qm_all
st.dataframe(df_filtered, use_container_width=True)

csv_qm = to_csv_semicolon(df_filtered)
st.download_button("CSV herunterladen", data=csv_qm,
                   file_name=f"qm_va_{dt.date.today()}.csv", mime="text/csv")

# ----------------------------
# Daten löschen
# ----------------------------
st.markdown("## 🗑️ Verfahrensanweisung löschen")

delete_options = options_va if options_va else ["Keine Einträge vorhanden"]
delete_va = st.selectbox("VA zum Löschen auswählen", options=delete_options, index=0)
if st.button("Verfahrensanweisung löschen"):
    if delete_options == ["Keine Einträge vorhanden"]:
        st.warning("Es gibt keine Einträge zum Löschen.")
    else:
        df_qm_all = df_qm_all[df_qm_all["VA_Nr"] != delete_va]
        save_data(DATA_FILE_QM, df_qm_all)
        st.success(f"VA {delete_va} wurde gelöscht.")

# ----------------------------
# PDF Export (robust, eine Zeile)
# ----------------------------
st.markdown("## 📤 Einzel-PDF Export")

if options_va:
    export_va = st.selectbox("VA für PDF auswählen", options=options_va, index=0)
    if st.button("PDF Export starten"):
        df_sel = df_qm_all[df_qm_all["VA_Nr"] == export_va]
        if df_sel.empty:
            st.error("Keine Daten für die ausgewählte VA gefunden.")
        else:
            row = df_sel.iloc[0]
            pdf_bytes = export_pdf_row_to_bytes(row)
            if isinstance(pdf_bytes, (bytes, bytearray)) and len(pdf_bytes) > 0:
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"{export_va}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("PDF konnte nicht erzeugt werden – interne Fehler.")
else:
    st.info("Keine VAs vorhanden. Bitte zuerst eine Verfahrensanweisung speichern.")




