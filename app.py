# --------------------------
# Imports & Setup
# --------------------------
import streamlit as st
import pandas as pd
import pathlib
import os
import re
import html
import datetime as dt
from zoneinfo import ZoneInfo

# zentrale Dateien
DATA_FILE_VA = "qm_verfahrensanweisungen.csv"
DATA_FILE_MA = "mitarbeiter.csv"
DATA_FILE_KENNTNIS = "lesebestätigung.csv"

# Hilfsfunktion zur Normalisierung von VA-Nummern
def norm_va(va):
    if pd.isna(va):
        return None
    return str(va).strip().upper()

# --------------------------
# Tabs anlegen
# --------------------------
tabs = st.tabs([
    "System & Login",
    "Verfahrensanweisungen",
    "Lesebestätigung",
    "Mitarbeiter",
    "Berechtigungen & Rollen"
])

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    if st.session_state.get("logged_in", False):
        st.success("✅ Eingeloggt")

        # Logout
        if st.button("Logout", key="logout_sidebar"):
            st.session_state.logged_in = False
            st.session_state.selected_va = None
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()

        # VA-Auswahl
        va_liste = []
        if os.path.exists(DATA_FILE_VA):
            df_va = pd.read_csv(DATA_FILE_VA, sep=";", encoding="utf-8-sig", dtype=str)
            if "VA_Nr" in df_va.columns:
                df_va["VA_clean"] = df_va["VA_Nr"].apply(norm_va)
                va_liste = sorted(df_va["VA_clean"].unique())

        va_nummer = st.selectbox("VA auswählen", options=va_liste, index=None, key="sidebar_va_select")

        if va_nummer:
            st.session_state.selected_va = va_nummer
            row = df_va[df_va["VA_clean"] == va_nummer]

            if not row.empty:
                def clean(text):
                    return html.escape(str(text)).replace("\n", "<br>")

                va_text = f"""<strong>VA-Nr:</strong> {va_nummer}<br>
                <strong>Titel:</strong> {clean(row['Titel'].values[0])}<br>
                <strong>Kapitel:</strong> {clean(row['Kapitel'].values[0])}<br>
                <strong>Unterkapitel:</strong> {clean(row['Unterkapitel'].values[0])}<br>
                <strong>Revisionsstand:</strong> {clean(row['Revisionsstand'].values[0])}<br>
                <strong>Geltungsbereich:</strong> {clean(row['Geltungsbereich'].values[0])}<br>
                <strong>Ziel:</strong> {clean(row['Ziel'].values[0])}<br>
                <strong>Vorgehensweise:</strong><br>{clean(row['Vorgehensweise'].values[0])}<br>
                <strong>Kommentar:</strong><br>{clean(row['Kommentar'].values[0])}<br>
                <strong>Mitgeltende Unterlagen:</strong><br>{clean(row['Mitgeltende Unterlagen'].values[0])}"""

                st.markdown(f"""<div style="background-color:#fff3cd;
                                padding:12px;
                                border-radius:6px;
                                border:1px solid #ffeeba;
                                margin-top:10px;
                                font-size:14px;
                                line-height:1.4">
                    <strong>📘 VA-Inhalt:</strong><br><br>{va_text}</div>""", unsafe_allow_html=True)

                # PDF-Download
                pdf_name = f"{norm_va(va_nummer)}.pdf"
                pdf_path = pathlib.Path("va_pdf") / pdf_name
                if pdf_path.exists():
                    st.markdown("### 📄 PDF herunterladen")
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label=f"📘 PDF öffnen: {pdf_name}",
                            data=f.read(),
                            file_name=pdf_name,
                            mime="application/pdf",
                            key=f"download_{pdf_name}"
                        )

                # Lesebestätigung
                st.markdown("### ✅ Lesebestätigung")
                name_sidebar = st.text_input("Name (Nachname, Vorname)", key="sidebar_name_input")
                if st.button("Bestätigen", key="sidebar_confirm_button"):
                    if not va_nummer:
                        st.error("Bitte zuerst eine VA auswählen.")
                    else:
                        name_clean = re.sub(r"\s*[,;]\s*", ", ", name_sidebar.strip())
                        name_clean = re.sub(r"\s+", " ", name_clean)

                        if name_clean:
                            zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
                            eintrag = {
                                "Name": name_clean,
                                "VA_Nr": va_nummer,
                                "VA_Nr_norm": norm_va(va_nummer),
                                "Zeitpunkt": zeitpunkt
                            }
                            df_new = pd.DataFrame([eintrag])[["Name", "VA_Nr", "VA_Nr_norm", "Zeitpunkt"]]

                            path = DATA_FILE_KENNTNIS
                            file_exists = os.path.exists(path)
                            file_empty = (not file_exists) or (os.path.getsize(path) == 0)

                            df_new.to_csv(
                                path,
                                sep=";",
                                index=False,
                                mode="a" if file_exists and not file_empty else "w",
                                header=not file_exists or file_empty,
                                encoding="utf-8-sig"
                            )
                            st.success(f"Bestätigung für {va_nummer} gespeichert.")
                        else:
                            st.error("Bitte Name eingeben.")

                # Fortschrittsanzeige
                try:
                    if os.path.exists(DATA_FILE_KENNTNIS) and os.path.exists(DATA_FILE_MA) and va_nummer:
                        df_kenntnis = pd.read_csv(DATA_FILE_KENNTNIS, sep=";", encoding="utf-8-sig", dtype=str)
                        df_mitarbeiter = pd.read_csv(DATA_FILE_MA, sep=";", encoding="utf-8-sig", dtype=str)

                        df_mitarbeiter["Name_full"] = df_mitarbeiter["Vorname"].str.strip() + " " + df_mitarbeiter["Name"].str.strip()
                        df_mitarbeiter["VA_norm"] = df_mitarbeiter["VA_Nr"].apply(norm_va)

                        zielgruppe = df_mitarbeiter[df_mitarbeiter["VA_norm"] == norm_va(va_nummer)]["Name_full"].dropna().unique()
                        gesamt = len(zielgruppe)

                        df_kenntnis["VA_Nr_norm"] = df_kenntnis["VA_Nr"].apply(norm_va)
                        gelesen_raw = df_kenntnis[df_kenntnis["VA_Nr_norm"] == norm_va(va_nummer)]["Name"].dropna().unique()

                        def normalize_name(name):
                            if "," in name:
                                nach, vor = [p.strip() for p in name.split(",", 1)]
                                return f"{vor} {nach}"
                            return name.strip()

                        gelesen_norm = [normalize_name(n) for n in gelesen_raw]
                        gelesen_set = set(gelesen_norm)
                        zielgruppe_set = set(zielgruppe)

                        gelesen_count = len(gelesen_set & zielgruppe_set)
                        fortschritt = gelesen_count / gesamt if gesamt > 0 else 0.0

                        st.markdown("---")
                        st.markdown("### 📊 Lesefortschritt")
                        st.progress(fortschritt)
                        st.caption(f"{gelesen_count} von {gesamt} Mitarbeiter haben bestätigt.")
                except Exception as e:
                    st.warning(f"Fortschritt konnte nicht berechnet werden: {e}")
    else:
        st.info("Bitte zuerst im Tab 'System & Login' anmelden.")

# --------------------------
# Tab 0: System & Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔒 System & Login")

    if not st.session_state.get("logged_in", False):
        user = st.text_input("Benutzername", key="login_user")
        pw = st.text_input("Passwort", type="password", key="login_pass")

        if st.button("Login", key="login_button"):
            if user == "admin" and pw == "geheim":
                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = "admin"
                st.success("✅ Admin eingeloggt")
            elif user == "mitarbeiter" and pw == "1234":
                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = "user"
                st.success("✅ Mitarbeiter eingeloggt")
            else:
                st.error("Login fehlgeschlagen")
    else:
        st.success(f"Eingeloggt als: {st.session_state.username} ({st.session_state.role})")
        if st.session_state.role == "admin":
            st.markdown("### 🛠️ Admin-Bereich")
            st.markdown

# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if os.path.exists(DATA_FILE_VA):
            df_va = pd.read_csv(DATA_FILE_VA, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_va)

            if st.session_state.role == "admin":
                st.markdown("### ➕ Neue VA hochladen")
                uploaded_file = st.file_uploader("CSV-Datei hochladen", type=["csv"], key="upload_va")
                if uploaded_file is not None:
                    df_new = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", dtype=str)
                    df_new.to_csv(DATA_FILE_VA, sep=";", index=False, encoding="utf-8-sig")
                    st.success("Neue Verfahrensanweisungen gespeichert.")
        else:
            st.info("Noch keine Verfahrensanweisungen vorhanden.")
# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
with tabs[2]:
    st.markdown("## ✅ Lesebestätigung")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if os.path.exists(DATA_FILE_KENNTNIS):
            df_all = pd.read_csv(DATA_FILE_KENNTNIS, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_all)

            # Admin-Löschfunktion
            if st.session_state.role == "admin":
                st.markdown("### 🗑️ Einträge verwalten")
                index_to_delete = st.number_input(
                    "Zeilenindex zum Löschen auswählen",
                    min_value=0,
                    max_value=len(df_all)-1,
                    step=1,
                    key="delete_index_tab"
                )
                if st.button("Eintrag löschen", key="delete_button_tab"):
                    df_all = df_all.drop(index_to_delete).reset_index(drop=True)
                    df_all.to_csv(DATA_FILE_KENNTNIS, sep=";", index=False, encoding="utf-8-sig")
                    st.success(f"Zeile {index_to_delete} gelöscht.")
        else:
            st.info("Noch keine Lesebestätigungen vorhanden.")
# --------------------------
# Tab 3: Mitarbeiter
# --------------------------
with tabs[3]:
    st.markdown("## 👥 Mitarbeiter")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if os.path.exists(DATA_FILE_MA):
            df_ma = pd.read_csv(DATA_FILE_MA, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_ma)

            if st.session_state.role == "admin":
                st.markdown("### ➕ Mitarbeiterliste aktualisieren")
                uploaded_file = st.file_uploader("CSV-Datei hochladen", type=["csv"], key="upload_ma")
                if uploaded_file is not None:
                    df_new = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", dtype=str)
                    df_new.to_csv(DATA_FILE_MA, sep=";", index=False, encoding="utf-8-sig")
                    st.success("Mitarbeiterliste aktualisiert.")
        else:
            st.info("Noch keine Mitarbeiterliste vorhanden.")
# --------------------------
# Tab 4: Berechtigungen & Rollen
# --------------------------
with tabs[4]:
    st.markdown("## 🔑 Berechtigungen & Rollen")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if st.session_state.role == "admin":
            st.markdown("### Rollenübersicht")
            st.write("Admin: Vollzugriff auf alle Tabs und Funktionen")
            st.write("User: Zugriff auf VA-Auswahl und Lesebestätigung")

            st.markdown("### Benutzerverwaltung")
            st.info("Hier könnte eine Benutzerverwaltung ergänzt werden (z. B. aus einer CSV).")
        else:
            st.info("🔐 Nur Admins haben Zugriff auf Rollenverwaltung.")

