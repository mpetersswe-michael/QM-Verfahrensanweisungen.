# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
from io import BytesIO
import matplotlib.figure

# ----------------------------
# Grundkonfiguration
# ----------------------------
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide")

# Platzhalter für spätere Datenquellen
DATA_FILE_QM = "qm_anweisungen.csv"
QM_COLUMNS = ["Titel", "Version", "Gültig ab"]

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
# SessionState für Login
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ----------------------------
# Sidebar: Login / Logout
# ----------------------------
with st.sidebar:
    st.markdown("## 🔐 Loginbereich")
    if not st.session_state.logged_in:
        with st.container():
            st.markdown('<div class="login-box">Bitte Passwort eingeben</div>', unsafe_allow_html=True)
            password = st.text_input("Login Passwort", type="password")
            if st.button("Login"):
                if password == "qm2024":
                    st.session_state.logged_in = True
                    st.experimental_rerun()
                else:
                    st.error("Falsches Passwort.")
    else:
        st.success("✅ Eingeloggt")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()

# ----------------------------
# Hauptbereich nach Login
# ----------------------------
if st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>📋 QM-Verfahrensanweisungen</h1>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📘 Anweisungen", "✅ Quittierung", "📤 Export"])

    with tab1:
        st.subheader("📘 Verfahrensanweisungen")
        st.info("Hier findest du alle aktuellen QM-Anweisungen zum Nachlesen.")
        df_qm = pd.DataFrame({
            "Titel": ["Hygieneplan", "Dokumentationsrichtlinie", "Notfallablauf"],
            "Version": ["v1.2", "v3.0", "v2.1"],
            "Gültig ab": ["2023-01-01", "2024-05-15", "2023-11-10"]
        })
        st.dataframe(df_qm, use_container_width=True)

    with tab2:
        st.subheader("✅ Quittierung")
        name = st.text_input("Name")
        datum = st.date_input("Datum")
        quittiert = st.checkbox("Ich bestätige, dass ich alle Anweisungen gelesen habe.")
        if st.button("Quittieren"):
            if name and quittiert:
                st.toast(f"Quittierung gespeichert für {name} am {datum}.")
            else:
                st.warning("Bitte Name eingeben und Checkbox aktivieren.")

    with tab3:
        st.subheader("📤 Export")
        if st.button("CSV herunterladen"):
            df_export = pd.DataFrame({
                "Name": [name],
                "Datum": [datum],
                "Quittiert": [quittiert]
            })
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="quittierung.csv", mime="text/csv")

else:
    st.markdown("<h2 style='text-align: center;'>🔐 Bitte logge dich ein, um fortzufahren.</h2>", unsafe_allow_html=True)


    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["📘 Anweisungen", "✅ Quittierung", "📤 Export"])

    # --- Tab 1: Anweisungen ---
    with tab1:
        st.subheader("📘 Verfahrensanweisungen")
        st.info("Hier findest du alle aktuellen QM-Anweisungen zum Nachlesen.")
        df_anweisungen = pd.DataFrame({
            "Titel": ["Hygieneplan", "Dokumentationsrichtlinie", "Notfallablauf"],
            "Version": ["v1.2", "v3.0", "v2.1"],
            "Gültig ab": ["2023-01-01", "2024-05-15", "2023-11-10"]
        })
        st.dataframe(df_anweisungen, use_container_width=True)

    # --- Tab 2: Quittierung ---
    with tab2:
        st.subheader("✅ Quittierung")
        name = st.text_input("Name")
        datum = st.date_input("Datum")
        quittiert = st.checkbox("Ich bestätige, dass ich alle Anweisungen gelesen habe.")
        if st.button("Quittieren"):
            if name and quittiert:
                st.toast(f"Quittierung gespeichert für {name} am {datum}.")
            else:
                st.warning("Bitte Name eingeben und Checkbox aktivieren.")

    # --- Tab 3: Export ---
    with tab3:
        st.subheader("📤 Export")
        if st.button("CSV herunterladen"):
            df_export = pd.DataFrame({
                "Name": [name],
                "Datum": [datum],
                "Quittiert": [quittiert]
            })
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="quittierung.csv", mime="text/csv")

else:
    st.markdown("<h2 style='text-align: center;'>🔐 Bitte logge dich ein, um fortzufahren.</h2>", unsafe_allow_html=True)

# --- Hauptbereich: Nur anzeigen, wenn eingeloggt ---
if st.session_state.logged_in:

    # --- Titelblock ---
    st.markdown("<h1 style='text-align: center;'>📋 QM-Verfahrensanweisungen</h1>", unsafe_allow_html=True)
    st.divider()

    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["📘 Anweisungen", "✅ Quittierung", "📤 Export"])

    # --- Tab 1: Anweisungen ---
    with tab1:
        st.subheader("📘 Verfahrensanweisungen")
        st.info("Hier findest du alle aktuellen QM-Anweisungen zum Nachlesen.")
        df_anweisungen = pd.DataFrame({
            "Titel": ["Hygieneplan", "Dokumentationsrichtlinie", "Notfallablauf"],
            "Version": ["v1.2", "v3.0", "v2.1"],
            "Gültig ab": ["2023-01-01", "2024-05-15", "2023-11-10"]
        })
        st.dataframe(df_anweisungen, use_container_width=True)

    # --- Tab 2: Quittierung ---
    with tab2:
        st.subheader("✅ Quittierung")
        name = st.text_input("Name")
        datum = st.date_input("Datum")
        quittiert = st.checkbox("Ich bestätige, dass ich alle Anweisungen gelesen habe.")
        if st.button("Quittieren"):
            if name and quittiert:
                st.toast(f"Quittierung gespeichert für {name} am {datum}.")
            else:
                st.warning("Bitte Name eingeben und Checkbox aktivieren.")

    # --- Tab 3: Export ---
    with tab3:
        st.subheader("📤 Export")
        if st.button("CSV herunterladen"):
            df_export = pd.DataFrame({
                "Name": [name],
                "Datum": [datum],
                "Quittiert": [quittiert]
            })
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="quittierung.csv", mime="text/csv")

else:
    st.markdown("<h2 style='text-align: center;'>🔐 Bitte logge dich ein, um fortzufahren.</h2>", unsafe_allow_html=True)


# --- Titelblock ---
st.markdown("<h1 style='text-align: center;'>📋 QM-Verfahrensanweisungen</h1>", unsafe_allow_html=True)
st.divider()

# --- Tabs für Navigation ---
tab1, tab2, tab3 = st.tabs(["📘 Anweisungen", "✅ Quittierung", "📤 Export"])

# --- Tab 1: Anweisungen anzeigen ---
with tab1:
    st.subheader("📘 Verfahrensanweisungen")
    st.info("Hier findest du alle aktuellen QM-Anweisungen zum Nachlesen.")
    
    # Beispielhafte Tabelle
    df_anweisungen = pd.DataFrame({
        "Titel": ["Hygieneplan", "Dokumentationsrichtlinie", "Notfallablauf"],
        "Version": ["v1.2", "v3.0", "v2.1"],
        "Gültig ab": ["2023-01-01", "2024-05-15", "2023-11-10"]
    })
    st.dataframe(df_anweisungen, use_container_width=True)

# --- Tab 2: Quittierung ---
with tab2:
    st.subheader("✅ Quittierung")
    st.success("Bitte bestätige, dass du die Anweisungen gelesen hast.")
    
    name = st.text_input("Name")
    datum = st.date_input("Datum")
    quittiert = st.checkbox("Ich bestätige, dass ich alle Anweisungen gelesen habe.")
    
    if st.button("Quittieren"):
        if name and quittiert:
            st.toast(f"Quittierung gespeichert für {name} am {datum}.")
        else:
            st.warning("Bitte Name eingeben und Checkbox aktivieren.")

# --- Tab 3: Export ---
with tab3:
    st.subheader("📤 Export")
    st.info("Hier kannst du die Quittierungen als CSV exportieren.")
    
    if st.button("CSV herunterladen"):
        df_export = pd.DataFrame({
            "Name": [name],
            "Datum": [datum],
            "Quittiert": [quittiert]
        })
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="quittierung.csv", mime="text/csv")


