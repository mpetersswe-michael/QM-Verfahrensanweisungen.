#		
import streamlit as st
import pandas as pd
import datetime as dt
from fpdf import FPDF
#		
#	Konfiguration
#		
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide")
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
QM_COLUMNS = [
"VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
"Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]
#		
#	Styles
#		
st.markdown("""
<style>
.stButton>button {
background-color: #4CAF50;
color: white;
border-radius: 8px;
padding: 0.5em 1em;
font-weight: bold;
border: none;
}
.stButton>button:hover {
background-color: #45a049;
}
.logout-button > button {
background-color: #e74c3c;
color: white;
border-radius: 8px;
padding: 0.5em 1em;
font-weight: bold;
}
.logout-button > button:hover {
background-color: #c0392b;
}
.login-box {
background-color: #fff8cc;
padding: 1.2em;
border-radius: 10px;
text-align: center;
margin-bottom: 2em;
font-size: 1.4em;
font-weight: bold;
color: #333333;
}
</style>
""", unsafe_allow_html=True)
#		
#       
#   Hilfsfunktionen
#       
def load_data(file, columns):
    try:
        df = pd.read_csv(file, sep=";", encoding="utf-8-sig")
    except:
        df = pd.DataFrame(columns=columns)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    return df[columns]

def to_csv_semicolon(df):
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

def export_pdf(df_row):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "QM-Verfahrensanweisung", ln=True, align="C")
        pdf.ln(5)
        for col in df_row.index:
            val = str(df_row[col])
            pdf.multi_cell(0, 8, f"{col}: {val}")
            pdf.ln(1)
        pdf_str = pdf.output(dest="S")
        pdf_bytes = pdf_str.encode("latin-1") if isinstance(pdf_str, str) else pdf_str
        return pdf_bytes
    except Exception as e:
        return None

#		
#	Login-Block
#		
if "auth" not in st.session_state:
st.session_state["auth"] = False
if not st.session_state["auth"]:
st.markdown('<div class="login-box">Login QM-Verfahrensanweisungen</div>', unsafe_allow_html=True)
password = st.text_input("Login Passwort", type="password", key="login_pw")
if st.button("Login", key="login_btn"):
if password == "QM2024":
st.session_state["auth"] = True
st.success("Willkommen - du bist eingeloggt. Bitte oben rechts 'Rerun' starten.")
else:
st.error("Falsches Passwort.")
st.stop()
with st.sidebar:
st.markdown("### Navigation")
if st.button("Logout", key="logout_btn"):
st.session_state["auth"] = False
st.stop()
st.markdown("---")
# ----------------------------
# ----------------------------
# Daten laden und VA-Auswahl
# ----------------------------
df_qm = load_data(DATA_FILE_QM, QM_COLUMNS)
options_va = df_qm["VA_Nr"].dropna().astype(str).unique().tolist()

st.markdown("## 📁 Verfahrensanweisungen anzeigen und exportieren")

if not options_va:
    st.info("Keine VAs vorhanden. Bitte zuerst eine Verfahrensanweisung speichern.")
    st.stop()

selected_va = st.selectbox("VA auswählen", options=options_va, key="va_select")
df_sel = df_qm[df_qm["VA_Nr"].astype(str) == str(selected_va)]

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

# Zusatzfelder (Formular)
ziel = st.text_area("Ziel", value=row.get("Ziel", ""), key="ziel")
geltung = st.text_area("Geltungsbereich", value=row.get("Geltungsbereich", ""), key="geltung")
vorgehen = st.text_area("Vorgehensweise", value=row.get("Vorgehensweise", ""), key="vorgehen")
kommentar = st.text_area("Kommentar", value=row.get("Kommentar", ""), key="kommentar")
unterlagen = st.text_area("Mitgeltende Unterlagen", value=row.get("Mitgeltende Unterlagen", ""), key="unterlagen")

# ----------------------------
# PDF Export
# ----------------------------
st.markdown("### 📤 PDF Export")

if st.button("PDF Export starten", key="btn_pdf_generate"):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Arial", style="", size=16)
        pdf.cell(0, 10, "QM-Verfahrensanweisung", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", size=11)
        for col in ["VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand"]:
            val = str(row[col]) if pd.notna(row[col]) else ""
            pdf.multi_cell(0, 8, f"{col}: {val}")
        pdf.ln(3)

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

        section("Ziel", ziel)
        section("Geltungsbereich", geltung)
        section("Vorgehensweise", vorgehen)
        section("Kommentar", kommentar)
        section("Mitgeltende Unterlagen", unterlagen)

        pdf.set_y(-30)
        pdf.set_font("Arial", style="I", size=10)
        pdf.cell(0, 10, "Erstellt von: Peters, Michael – Qualitätsbeauftragter", ln=True, align="L")

        pdf_raw = pdf.output(dest="S")
        pdf_bytes = pdf_raw.encode("latin-1") if isinstance(pdf_raw, str) else pdf_raw

        st.session_state["pdf_bytes"] = pdf_bytes
        st.session_state["pdf_filename"] = f"{row['VA_Nr']}.pdf"
        st.success("PDF erstellt. Jetzt kannst du es herunterladen.")

        # Zusatzfelder speichern
        df_qm.loc[df_qm["VA_Nr"] == row["VA_Nr"], "Ziel"] = ziel
        df_qm.loc[df_qm["VA_Nr"] == row["VA_Nr"], "Geltungsbereich"] = geltung
        df_qm.loc[df_qm["VA_Nr"] == row["VA_Nr"], "Vorgehensweise"] = vorgehen
        df_qm.loc[df_qm["VA_Nr"] == row["VA_Nr"], "Kommentar"] = kommentar
        df_qm.loc[df_qm["VA_Nr"] == row["VA_Nr"], "Mitgeltende Unterlagen"] = unterlagen

        with open(DATA_FILE_QM, "wb") as f:
            f.write(to_csv_semicolon(df_qm))

    except Exception as e:
        st.session_state["pdf_bytes"] = None
        st.session_state["pdf_filename"] = None
        st.error(f"PDF konnte nicht erzeugt werden: {e}")

# ----------------------------
# Download-Button
# ----------------------------
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
