import streamlit as st
import pandas as pd
import os

# --- Seitentitel und Icon ---
st.set_page_config(
    page_title="QM-Verfahrensanweisungen",
    page_icon="📋",
    layout="centered"
)

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


