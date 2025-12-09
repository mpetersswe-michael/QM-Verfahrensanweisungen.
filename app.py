import streamlit as st
import pandas as pd
import os

# CSV laden
try:
    with open("users.csv", "r", encoding="utf-8") as f:
        first_line = f.readline()
        sep = ";" if ";" in first_line else ","
    users_df = pd.read_csv("users.csv", sep=sep, dtype=str)
    users_df.columns = users_df.columns.str.strip()
except FileNotFoundError:
    st.error("❌ Datei 'users.csv' nicht gefunden.")
    st.stop()
except Exception as e:
    st.error(f"❌ Fehler beim Laden der Datei 'users.csv': {e}")
    st.stop()

# Login-Formular
st.markdown("## 🔒 Login")
input_user = st.text_input("Username")
input_pass = st.text_input("Password", type="password")
login_button = st.button("Login")

if login_button:
    match = users_df[
        (users_df["username"] == input_user) &
        (users_df["password"] == input_pass)
    ]
    if not match.empty:
        st.success(f"✅ Eingeloggt als {input_user}")
        st.session_state.logged_in = True
        st.session_state.username = input_user
        st.session_state.role = match.iloc[0]["role"]
    else:
        st.error("❌ Login fehlgeschlagen. Bitte prüfen Sie Ihre Eingaben.")

# Hinweis für andere Tabs
if not st.session_state.get("logged_in"):
    st.warning("🔒 Nicht eingeloggt. Bitte zuerst im Tab Login anmelden.")
    st.stop()

# --------------------------
# Tabs
# --------------------------
tabs = st.tabs(["Login", "Verfahrensanweisungen", "Lesebestätigung", "Mitarbeiter"])

# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
if st.session_state.get("logged_in", False) and st.session_state.role == "admin":
    with tabs[1]:
        st.markdown("## 📘 Verfahrensanweisungen")

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

        if os.path.exists(DATA_FILE_QM):
            df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_va)

# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
DATA_FILE_KENNTNIS = "lesebestaetigung.csv"
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
DATA_FILE_MA = "mitarbeiter.csv"
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






