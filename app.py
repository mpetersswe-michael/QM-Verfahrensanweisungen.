import streamlit as st
import pandas as pd

# --- App-Konfiguration ---
st.set_page_config(page_title="QM-Verfahrensanweisungen", page_icon="📋", layout="centered")

# --- SessionState initialisieren ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Sidebar: Login & Logout ---
with st.sidebar:
    st.markdown("## 🔐 Loginbereich")

    if not st.session_state.logged_in:
        password = st.text_input("Passwort eingeben", type="password")
        if st.button("Login"):
            if password == "qm2024":  # ← Passwort hier definieren
                st.session_state.logged_in = True
                st.experimental_rerun()
            else:
                st.error("Falsches Passwort.")
    else:
        st.success("✅ Eingeloggt")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()

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


