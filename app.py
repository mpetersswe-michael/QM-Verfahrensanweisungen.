# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import datetime as dt

# ----------------------------
# Grundkonfiguration
# ----------------------------
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide")

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
.delete-button > button {
    background-color: #e74c3c;
    color: white;
    border-radius: 8px;
    padding: 0.5em 1em;
    font-weight: bold;
    border: none;
}
.delete-button > button:hover {
    background-color: #c0392b;
    color: white;
}
.export-button > button {
    background-color: #3498db;
    color: white;
    border-radius: 8px;
    padding: 0.5em 1em;
    font-weight: bold;
    border: none;
}
.export-button > button:hover {
    background-color: #2980b9;
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
# SessionState initialisieren
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Fallback für rerun (neuere Versionen nutzen st.rerun)
RERUN = getattr(st, "rerun", getattr(st, "experimental_rerun", None))

# ----------------------------
# Sidebar: Login / Logout
# ----------------------------
with st.sidebar:
    st.markdown("## 🔒 Loginbereich")

    if not st.session_state.logged_in:
        st.markdown('<div class="login-box">Bitte Passwort eingeben</div>', unsafe_allow_html=True)
        password = st.text_input("Login Passwort", type="password")
        login_button = st.button("Login")
        if login_button:
            if password == "qm2024":  # Passwort hier definieren
                st.session_state.logged_in = True
                if RERUN:
                    RERUN()
            else:
                st.error("Falsches Passwort.")
    else:
        st.success("✅ Eingeloggt")
        st.markdown('<div class="logout-button">', unsafe_allow_html=True)
        logout_button = st.button("Logout")
        st.markdown('</div>', unsafe_allow_html=True)
        if logout_button:
            st.session_state.logged_in = False
            if RERUN:
                RERUN()

# ----------------------------
# Hauptbereich: Nur nach Login
# ----------------------------
if st.session_state.logged_in:

    st.markdown("<h1 style='text-align: center;'>📋 QM-Verfahrensanweisungen</h1>", unsafe_allow_html=True)
    st.divider()

    # Beispielhafte QM-Daten
    df_qm = pd.DataFrame({
        "Titel": ["Hygieneplan", "Dokumentationsrichtlinie", "Notfallablauf"],
        "Version": ["v1.2", "v3.0", "v2.1"],
        "Gültig ab": ["2023-01-01", "2024-05-15", "2023-11-10"]
    })

    st.subheader("📘 Aktuelle QM-Anweisungen")
    st.dataframe(df_qm, use_container_width=True)

    # Eingabeformular für Quittierung
    st.subheader("✅ Quittierung erfassen")
    name = st.text_input("Name")
    datum = st.date_input("Datum", value=dt.date.today())
    quittiert = st.checkbox("Ich bestätige, dass ich alle Anweisungen gelesen habe.")

    # Speichern-Button
    if st.button("Speichern"):
        if name and quittiert:





