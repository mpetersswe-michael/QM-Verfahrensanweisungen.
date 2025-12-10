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

def safe(text):
    return str(text).encode("latin-1", "replace").decode("latin-1")

# --------------------------
# Session-Init
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "selected_va" not in st.session_state:
    st.session_state.selected_va = None

# --------------------------
# Tabs
# --------------------------
tabs = st.tabs(["System & Login", "Verfahrensanweisungen", "Lesebestätigung", "Mitarbeiter"])

# --------------------------
# Tab 0: Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔒 Login")

    if not st.session_state.get("logged_in", False):
        input_user = st.text_input("Benutzername", key="login_user")
        input_pass = st.text_input("Passwort", type="password", key="login_pw")
        if st.button("Login", key="login_button"):
            try:
                users_df = pd.read_csv("users.csv", sep=";", dtype=str)
                match = users_df[
                    (users_df["username"] == input_user) &
                    (users_df["password"] == input_pass)
                ]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = input_user
                    st.session_state.role = match.iloc[0]["role"]
                    st.success(f"✅ Eingeloggt als {input_user} (Rolle: {st.session_state.role})")
                else:
                    st.error("❌ Login fehlgeschlagen. Bitte prüfen Sie Ihre Eingaben.")
            except Exception as e:
                st.error(f"Fehler beim Einlesen der Benutzerdatei: {e}")
    else:
        st.info("Du bist bereits eingeloggt. Logout über die Sidebar.")

# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")
    if not st.session_state.get("logged_in"):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
    elif st.session_state.role != "admin":
        st.warning("🔒 Kein Zugriff für Benutzerrolle. Sichtbar zur Orientierung.")
    else:
        # VA-Eingabe
        va_nr_input = st.text_input("VA-Nummer")
        titel_input = st.text_input("Titel")
        kapitel_input = st.text_input("Kapitel")
        unterkapitel_input = st.text_input("Unterkapitel")
        revisionsstand_input = st.text_input("Revisionsstand")
        geltungsbereich_input = st.text_input("Geltungsbereich")
        ziel_input = st.text_input("Ziel")
        vorgehensweise_input = st.text_area("Vorgehensweise")
        kommentar_input = st.text_area("Kommentar")
        mitgeltende_input = st.text_area("Mitgeltende Unterlagen")

        if st.button("VA speichern"):
            neuer_eintrag = pd.DataFrame([{
                "VA_Nr": va_nr_input.strip(),
                "Titel": titel_input.strip(),
                "Kapitel": kapitel_input.strip(),
                "Unterkapitel": unterkapitel_input.strip(),
                "Revisionsstand": revisionsstand_input.strip(),
                "Geltungsbereich": geltungsbereich_input.strip(),
                "Ziel": ziel_input.strip(),
                "Vorgehensweise": vorgehensweise_input.strip(),
                "Kommentar": kommentar_input.strip(),
                "Mitgeltende Unterlagen": mitgeltende_input.strip()
            }])
            if os.path.exists(DATA_FILE_QM):
                df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
                df_va = pd.concat([df_va, neuer_eintrag], ignore_index=True)
            else:
                df_va = neuer_eintrag
            df_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"✅ VA {va_nr_input} gespeichert.")

        if os.path.exists(DATA_FILE_QM):
            df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_va)
        else:
            st.info("Noch keine Verfahrensanweisungen gespeichert.")

# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
with tabs[2]:
    st.markdown("## ✅ Lesebestätigung")
    if not st.session_state.get("logged_in"):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
    elif st.session_state.role != "admin":
        st.warning("🔒 Kein Zugriff für Benutzerrolle. Sichtbar zur Orientierung.")
    else:
        if os.path.exists(DATA_FILE_KENNTNIS):
            df_all = pd.read_csv(DATA_FILE_KENNTNIS, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_all)
        else:
            st.info("Noch keine Lesebestätigungen vorhanden.")

# --------------------------
# Tab 3: Mitarbeiter
# --------------------------
with tabs[3]:
    st.markdown("## 👥 Mitarbeiterverwaltung")
    if not st.session_state.get("logged_in"):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
    elif st.session_state.role != "admin":
        st.warning("🔒 Kein Zugriff für Benutzerrolle. Sichtbar zur Orientierung.")
    else:
        uploaded_file = st.file_uploader("Mitarbeiterliste hochladen (CSV)", type=["csv"])
        if uploaded_file is not None:
            df_ma = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", dtype=str)
            df_ma.to_csv(DATA_FILE_MA, sep=";", index=False, encoding="utf-8-sig")
            st.success("Mitarbeiterliste gespeichert.")
        if os.path.exists(DATA_FILE_MA):
            df_ma = pd.read_csv(DATA_FILE_MA, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_ma)
        else:
            st.info("Keine Mitarbeiterliste vorhanden.")

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    if st.session_state.get("logged_in", False):
        st.markdown(
            f"✅ **Eingeloggt als:** `{st.session_state.username}`  \n"
            f"🛡️ **Rolle:** `{st.session_state.role}`"
        )

        # VA-Auswahl
        va_liste = []
        if os.path.exists(DATA_FILE_QM):
            df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
            if "VA_Nr" in df_va.columns:
                df_va["VA_clean"] = df_va["VA_Nr"].apply(norm_va)
                va_liste = sorted(df_va["VA_clean"].unique())

        va_nummer = st.selectbox("VA auswählen", options=va_liste, index=None)
        if va_nummer:
            st.session_state.selected_va = va_nummer
            row = df_va[df_va["VA_clean"] == va_nummer]
            if not row.empty:
                titel = row["Titel"].values[0]
                st.markdown(
                    f"<div style='background-color:#fff3b0;padding:8px;border-radius:5px;'>📄 <b>{va_nummer} – {titel}</b></div>",
                    unsafe_allow_html=True
                )

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.selected_va = None
            st.rerun()
    else:
        st.warning("🔒 Nicht eingeloggt. Bitte zuerst im Tab **Login** anmelden.")


  



