# --------------------------
# Imports
# --------------------------
import os
import re
import io
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from fpdf import FPDF
import streamlit_authenticator as stauth
import pathlib

st.set_page_config(
    page_title="Verfahrensanweisungen (Auszug aus dem QMH)",
    page_icon="📘",
    layout="wide"
)

# --------------------------
# Datenkonfiguration
# --------------------------
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
DATA_FILE_KENNTNIS = "lesebestätigung.csv"
DATA_FILE_MA = "mitarbeiter.csv"
QM_COLUMNS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
    "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]

# --------------------------
# Hilfsfunktionen
# --------------------------
def norm_va(x):
    s = str(x).upper().replace(" ", "")
    m = s.replace("VA", "")
    if m.isdigit():
        s = f"VA{int(m):03d}"
    return s

def clean_text(text):
    if text is None or str(text).strip() == "":
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

# --------------------------
# Session-Init
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "selected_va" not in st.session_state:
    st.session_state.selected_va = None
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

# --------------------------
# Authenticator Setup
# --------------------------
users_df = pd.read_csv(os.path.join("va_app", "users.csv"))
credentials = {"usernames": {}}
for _, row in users_df.iterrows():
    credentials["usernames"][row["username"]] = {
        "password": row["password"],
        "role": row["role"]
    }

authenticator = stauth.Authenticate(
    credentials,
    "va_app_cookie",
    "secret_key",
    cookie_expiry_days=30
)

# --------------------------
# Tabs rollenbasiert anzeigen
# --------------------------
if not st.session_state.get("logged_in", False):
    tabs = st.tabs(["System & Login"])
elif st.session_state.role == "admin":
    tabs = st.tabs([
        "System & Login",
        "Verfahrensanweisungen",
        "Lesebestätigung",
        "Mitarbeiter"
    ])
else:
    tabs = st.tabs([
        "System & Login",
        "Lesebestätigung"
    ])

# --------------------------
# Tab 0: Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔒 Login")

    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = credentials["usernames"][username]["role"]
        st.success(f"✅ Eingeloggt als {username} ({st.session_state.role})")
    elif authentication_status is False:
        st.error("❌ Login fehlgeschlagen")
    else:
        st.info("Bitte einloggen")

# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
if st.session_state.get("logged_in", False) and st.session_state.role == "admin":
    with tabs[1]:
        st.markdown("## 📘 Verfahrensanweisungen")

        # Eingabeformular
        va_nr = st.text_input("VA-Nummer")
        titel = st.text_input("Titel")
        kapitel = st.text_input("Kapitel")
        unterkapitel = st.text_input("Unterkapitel")
        revision = st.text_input("Revisionsstand")
        geltung = st.text_input("Geltungsbereich")
        ziel = st.text_input("Ziel")
        vorgang = st.text_area("Vorgehensweise")
        kommentar = st.text_area("Kommentar")
        unterlagen = st.text_area("Mitgeltende Unterlagen")

        if st.button("VA speichern"):
            neuer_eintrag = pd.DataFrame([{
                "VA_Nr": va_nr, "Titel": titel, "Kapitel": kapitel,
                "Unterkapitel": unterkapitel, "Revisionsstand": revision,
                "Geltungsbereich": geltung, "Ziel": ziel,
                "Vorgehensweise": vorgang, "Kommentar": kommentar,
                "Mitgeltende Unterlagen": unterlagen
            }])
            if os.path.exists(DATA_FILE_QM):
                df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
                df_va = pd.concat([df_va, neuer_eintrag], ignore_index=True)
            else:
                df_va = neuer_eintrag
            df_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"VA {va_nr} gespeichert.")

        # Übersicht
        if os.path.exists(DATA_FILE_QM):
            df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_va)

# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
with tabs[2]:
    st.markdown("## ✅ Lesebestätigung")
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
    else:
        if os.path.exists(DATA_FILE_KENNTNIS):
            df_all = pd.read_csv(DATA_FILE_KENNTNIS, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_all)
        else:
            st.info("Noch keine Lesebestätigungen vorhanden.")

# --------------------------
# Tab 3: Mitarbeiter
# --------------------------
if st.session_state.get("logged_in", False) and st.session_state.role == "admin":
    with tabs[3]:
        st.markdown("## 👥 Mitarbeiterverwaltung")
        uploaded_file = st.file_uploader("Mitarbeiterliste hochladen (CSV)", type=["csv"])
        if uploaded_file is not None:
            df_ma = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", dtype=str)
            df_ma.to_csv(DATA_FILE_MA, sep=";", index=False, encoding="utf-8-sig")
            st.success("Mitarbeiterliste gespeichert.")
        if os.path.exists(DATA_FILE_MA):
            df_ma = pd.read_csv(DATA_FILE_MA, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_ma)

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    if st.session_state.get("logged_in", False):
        st.markdown(
            f"✅ **Eingeloggt als:** `{st.session_state.username}`  \n"
            f"🛡️ **Rolle:** `{st.session_state.role}`"
        )
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.selected_va = None
            st.rerun()
    else:
        st.warning("🔒 Nicht eingeloggt. Bitte zuerst im Tab **Login** anmelden.")






