# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import datetime as dt
from fpdf import FPDF

# ----------------------------
# Grundkonfiguration
# ----------------------------
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide")

DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
QM_COLUMNS = ["VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand"]

# ----------------------------
# Styles für Buttons & Login
# ----------------------------
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
    color: white;
}
.logout-button > button {
    background-color: #e74c3c;
    color: white;
    border-radius: 8px;
    padding: 0.5em 1em;
    font-weight: bold;
    border: none;
}
.logout-button > button:hover {
    background-color: #c0392b;
    color: white;
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

# ----------------------------
# Hilfsfunktionen
# ----------------------------
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
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="QM-Verfahrensanweisung", ln=True, align="C")
    pdf.ln(10)
    for col in df_row.index:
        pdf.cell(200, 10, txt=f"{col}: {df_row[col]}", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# ----------------------------
# Login-Block
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown('<div class="login-box">Login QM-Verfahrensanweisungen</div>', unsafe_allow_html=True)
    password = st.text_input("Login Passwort", type="password", key="login_pw")
    if st.button("Login", key="login_btn"):
        if password == "QM2024":   # ← dein Passwort
            st.session_state["auth"] = True
            st.success("Willkommen – du bist eingeloggt. Bitte bei den drei Punkten oben rechts 'Rerun' starten.")
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
# Eingabe einer Verfahrensanweisung
# ----------------------------
st.markdown("## 📘 Neue Verfahrensanweisung erfassen")

va_name = st.text_input("Verfahrensanweisung Nr.", placeholder="VA 001")
va_title = st.text_input("Titel der Verfahrensanweisung", placeholder="Hygieneplan")
kapitel = st.selectbox("Kapitel Nr.", ["Kapitel 1", "Kapitel 2", "Kapitel 3", "Kapitel 4", "Kapitel 5", "Kapitel 6"], index=5)
unterkapitel = st.selectbox("Unterkapitel Nr.", ["6.1", "6.2", "6.3", "6.4"], index=0)
revision_date = st.date_input("Revisionsstand", value=dt.date.today())

if st.button("Verfahrensanweisung speichern"):
    if not va_name.strip() or not va_title.strip():
        st.warning("Bitte Name und Titel eingeben.")
    else:
        new_va = pd.DataFrame([{
            "VA_Nr": va_name.strip(),
            "Titel": va_title.strip(),
            "Kapitel": kapitel,
            "Unterkapitel": unterkapitel,
            "Revisionsstand": revision_date.strftime("%Y-%m-%d")
        }])
        try:
            existing_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
        except:
            existing_va = pd.DataFrame(columns=QM_COLUMNS)
        updated_va = pd.concat([existing_va, new_va], ignore_index=True)
        updated_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
        st.success(f"Verfahrensanweisung {va_name} gespeichert.")

# ----------------------------
# Daten anzeigen und exportieren
# ----------------------------
st.markdown("## Daten anzeigen und exportieren")

df_qm_all = load_data(DATA_FILE_QM, QM_COLUMNS)

filter_va = st.selectbox(
    "Filter nach Verfahrensanweisung",
    options=[""] + sorted(df_qm_all["VA_Nr"].dropna().str.strip().unique()),
    index=0,
    key="filter_va"
)

df_filtered = df_qm_all[df_qm_all["VA_Nr"] == filter_va] if filter_va else df_qm_all
st.dataframe(df_filtered, use_container_width=True, height=300)

csv_qm = to_csv_semicolon(df_filtered)
st.download_button(
    "CSV herunterladen",
    data=csv_qm,
    file_name=f"qm_verfahrensanweisungen_{dt.date.today()}.csv",
    mime="text/csv"
)

# ----------------------------
# PDF Export einer ausgewählten VA
# ----------------------------
st.markdown("## 📤 Export als PDF")

export_va = st.selectbox("Verfahrensanweisung auswählen", options=df_qm_all["VA_Nr"].unique() if not df_qm_all.empty else [])

if st.button("PDF Export starten"):
    if export_va:
        df_selected = df_qm_all[df_qm_all["VA_Nr"] == export_va].iloc[0]
        pdf_output = export_pdf(df_selected)
        st.download_button("Download PDF", data=pdf_output, file_name=f"{export_va}.pdf", mime="application/pdf")
    else:
        st.warning("Bitte eine Verfahrensanweisung auswählen.")







