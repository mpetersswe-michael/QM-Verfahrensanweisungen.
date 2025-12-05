# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import datetime as dt

# ----------------------------
# Konfiguration
# ----------------------------
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide")
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
QM_COLUMNS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
    "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]

# ----------------------------
# Styles
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

# ----------------------------
# Login-Block
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown('<div class="login-box">Login QM-Verfahrensanweisungen</div>', unsafe_allow_html=True)
    password = st.text_input("Login Passwort", type="password", key="login_pw")
    if st.button("Login", key="login_btn"):
       if password == "QM2024":
          st.session_state["auth"] = True
          st.experimental_rerun()

        else:
            st.error("Falsches Passwort.")
            st.stop()
    else:
        st.stop()

with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout", key="logout_btn"):
        st.session_state["auth"] = False
        st.stop()
    st.markdown("---")

# ----------------------------
# Eingabeformular
# ----------------------------
st.markdown("## Neue Verfahrensanweisung erfassen")

va_nr = st.text_input("VA Nummer", placeholder="z. B. VA003")
va_title = st.text_input("Titel", placeholder="Kommunikationswege im Pflegedienst")

kapitel_num = st.selectbox("Kapitel Nr.", list(range(1, 11)), index=6)  # Standard: Kapitel 7
kapitel = f"Kapitel {kapitel_num}"

unterkapitel = st.text_input("Unterkapitel", placeholder=f"Kap. {kapitel_num}-3")

revision_date = st.date_input("Revisionsstand", value=dt.date.today())

ziel = st.text_area("Ziel", height=100)
geltung = st.text_area("Geltungsbereich", height=80)
vorgehen = st.text_area("Vorgehensweise", height=150)
kommentar = st.text_area("Kommentar", height=80)
unterlagen = st.text_area("Mitgeltende Unterlagen", height=80)

# ----------------------------
# Speichern in CSV
# ----------------------------
if st.button("Verfahrensanweisung speichern"):
    if not va_nr.strip() or not va_title.strip():
        st.warning("Bitte VA Nummer und Titel eingeben.")
    else:
        new_va = pd.DataFrame([{
            "VA_Nr": va_nr.strip(),
            "Titel": va_title.strip(),
            "Kapitel": kapitel,
            "Unterkapitel": unterkapitel.strip(),
            "Revisionsstand": revision_date.strftime("%d.%m.%Y"),  # Format wie in deiner Tabelle
            "Ziel": ziel.strip(),
            "Geltungsbereich": geltung.strip(),
            "Vorgehensweise": vorgehen.strip(),
            "Kommentar": kommentar.strip(),
            "Mitgeltende Unterlagen": unterlagen.strip()
        }])

        try:
            existing_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
        except:
            existing_va = pd.DataFrame(columns=QM_COLUMNS)

        updated_va = pd.concat([existing_va, new_va], ignore_index=True)
        updated_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")

        st.success(f"Verfahrensanweisung {va_nr} gespeichert.")



