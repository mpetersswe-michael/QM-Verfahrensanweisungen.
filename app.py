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
# SessionState für Login
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ----------------------------
# Sidebar: Login / Logout
# ----------------------------
with st.sidebar:
    st.markdown("## 🔒 Loginbereich")
    if not st.session_state.logged_in:
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

    # --- Beispielhafte QM-Daten ---
    df_qm = pd.DataFrame({
        "Titel": ["Hygieneplan", "Dokumentationsrichtlinie", "Notfallablauf"],
        "Version": ["v1.2", "v3.0", "v2.1"],
        "Gültig ab": ["2023-01-01", "2024-05-15", "2023-11-10"]
    })

    st.subheader("📘 Aktuelle QM-Anweisungen")
    st.dataframe(df_qm, use_container_width=True)

    # --- Eingabeformular für neue Quittierung ---
    st.subheader("✅ Quittierung erfassen")
    name = st.text_input("Name")
    datum = st.date_input("Datum", value=dt.date.today())
    quittiert = st.checkbox("Ich bestätige, dass ich alle Anweisungen gelesen habe.")

    # --- Speichern-Button ---
    if st.button("Speichern", type="primary"):
        if name and quittiert:
            st.success(f"Quittierung gespeichert für {name} am {datum}.")
        else:
            st.warning("Bitte Name eingeben und Checkbox aktivieren.")

    # --- Daten löschen ---
    st.markdown('<div class="delete-button">', unsafe_allow_html=True)
    if st.button("Daten löschen"):
        name = ""
        quittiert = False
        st.info("Eingaben wurden zurückgesetzt.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Export als CSV ---
    st.markdown('<div class="export-button">', unsafe_allow_html=True)
    if st.button("CSV Export"):
        df_export = pd.DataFrame({
            "Name": [name],
            "Datum": [datum],
            "Quittiert": [quittiert]
        })
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="quittierung.csv", mime="text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("<h2 style='text-align: center;'>🔐 Bitte logge dich ein, um fortzufahren.</h2>", unsafe_allow_html=True)



