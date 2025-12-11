# --------------------------
# Pfade robust setzen (relativ zu app.py)
# --------------------------
import streamlit as st
import pandas as pd
import os
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.resolve()

DATA_FILE_VA = BASE_DIR / "qm_verfahrensanweisungen.csv"
DATA_FILE_MA = BASE_DIR / "mitarbeiter.csv"
DATA_FILE_KENNTNIS = BASE_DIR / "lesebestätigung.csv"
DATA_FILE_USERS = BASE_DIR / "users.csv"

# Sichtprüfung (einmalig hilfreich)
st.write("BASE_DIR:", BASE_DIR)
st.write("VA-Datei vorhanden:", DATA_FILE_VA.exists())
st.write("MA-Datei vorhanden:", DATA_FILE_MA.exists())
st.write("Kenntnis-Datei vorhanden:", DATA_FILE_KENNTNIS.exists())
st.write("Users-Datei vorhanden:", DATA_FILE_USERS.exists())
# --------------------------
# Sidebar: VA-Auswahl + Vorschau
# --------------------------
def norm_va(va):
    if pd.isna(va): return None
    return str(va).strip().upper()

with st.sidebar:
    if st.session_state.get("logged_in", False):
        st.success(f"Eingeloggt: {st.session_state.get('username')} ({st.session_state.get('role')})")

        # VA-Liste laden
        va_liste = []
        df_va = None
        if DATA_FILE_VA.exists():
            try:
                df_va = pd.read_csv(DATA_FILE_VA, sep=";", encoding="utf-8-sig", dtype=str)
                # Spalten robust behandeln
                cols = df_va.columns.str.strip()
                df_va.columns = cols

                # VA_Nr finden (robust: VA_Nr oder va_nr)
                va_col = None
                for c in ["VA_Nr", "va_nr", "Va_Nr", "VA-nr"]:
                    if c in df_va.columns:
                        va_col = c
                        break

                if va_col is None:
                    st.error("Spalte 'VA_Nr' fehlt in qm_verfahrensanweisungen.csv.")
                else:
                    df_va["VA_clean"] = df_va[va_col].apply(norm_va)
                    va_liste = sorted([v for v in df_va["VA_clean"].dropna().unique() if v])

            except Exception as e:
                st.error(f"Fehler beim Lesen der VA-Datei: {e}")

        # Auswahlfeld sichtbar machen, auch wenn Liste leer ist
        selected_va = st.selectbox("VA auswählen", options=va_liste, index=None, key="sidebar_va_select")
        st.session_state.selected_va = selected_va if selected_va else st.session_state.get("selected_va")

        # Vorschau, wenn VA gewählt und df_va vorhanden
        if st.session_state.get("selected_va") and df_va is not None:
            row = df_va[df_va["VA_clean"] == st.session_state.selected_va]
            if not row.empty:
                # Versuch, gängige Felder anzuzeigen (ohne Absturz, wenn ein Feld fehlt)
                def g(col):
                    return row[col].values[0] if col in row.columns else ""
                st.markdown("### 📘 VA-Vorschau")
                st.write({
                    "VA_Nr": st.session_state.selected_va,
                    "Titel": g("Titel"),
                    "Kapitel": g("Kapitel"),
                    "Unterkapitel": g("Unterkapitel"),
                    "Revisionsstand": g("Revisionsstand"),
                })
    else:
        st.info("Bitte zuerst im Tab 'System & Login' anmelden.")
# --------------------------
# Tab 0: System & Login
# --------------------------
tabs = st.tabs(["System & Login", "Verfahrensanweisungen", "Lesebestätigung", "Mitarbeiter", "Berechtigungen & Rollen"])

with tabs[0]:
    st.markdown("## 🔒 System & Login")
    if not st.session_state.get("logged_in", False):
        u = st.text_input("Benutzername", key="login_user")
        p = st.text_input("Passwort", type="password", key="login_pass")
        if st.button("Login", key="login_btn"):
            try:
                df_users = pd.read_csv(DATA_FILE_USERS, sep=";", encoding="utf-8-sig", dtype=str)
                df_users = df_users.dropna(subset=["username", "password", "role"])
                match = df_users[
                    (df_users["username"].str.strip().str.lower() == u.strip().lower()) &
                    (df_users["password"].str.strip() == p.strip())
                ]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = match["username"].values[0]
                    st.session_state.role = match["role"].values[0]
                    st.success(f"Eingeloggt als {st.session_state.username} ({st.session_state.role})")
                    st.rerun()
                else:
                    st.error("Login fehlgeschlagen: Benutzername oder Passwort falsch.")
            except Exception as e:
                st.error(f"Fehler beim Laden der Benutzerliste: {e}")
    else:
        st.success(f"Eingeloggt als: {st.session_state.username} ({st.session_state.role})")
# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if DATA_FILE_VA.exists():
            df_va = pd.read_csv(DATA_FILE_VA, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_va)
        else:
            st.info("qm_verfahrensanweisungen.csv nicht gefunden im Ordner der app.py.")

# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
with tabs[2]:
    st.markdown("## ✅ Lesebestätigung")
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        name_input = st.text_input("Name (Nachname, Vorname)", key="tab2_name")
        if st.button("Bestätigen", key="tab2_confirm"):
            if st.session_state.get("selected_va"):
                try:
                    entry = pd.DataFrame([{
                        "Name": name_input.strip(),
                        "VA_Nr": st.session_state.selected_va,
                        "VA_Nr_norm": str(st.session_state.selected_va).strip().upper(),
                        "Zeitpunkt": pd.Timestamp.now(tz="Europe/Berlin").strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    entry.to_csv(
                        DATA_FILE_KENNTNIS,
                        sep=";",
                        index=False,
                        mode="a",
                        header=not DATA_FILE_KENNTNIS.exists(),
                        encoding="utf-8-sig"
                    )
                    st.success("Bestätigung gespeichert.")
                except Exception as e:
                    st.error(f"Fehler beim Speichern: {e}")
            else:
                st.error("Bitte zuerst eine VA in der Sidebar auswählen.")

        if DATA_FILE_KENNTNIS.exists():
            df_k = pd.read_csv(DATA_FILE_KENNTNIS, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_k)
        else:
            st.info("lesebestätigung.csv nicht gefunden neben der app.py.")

# --------------------------
# Tab 3: Mitarbeiter
# --------------------------
with tabs[3]:
    st.markdown("## 👥 Mitarbeiter")
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if DATA_FILE_MA.exists():
            df_ma = pd.read_csv(DATA_FILE_MA, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_ma)
        else:
            st.info("mitarbeiter.csv nicht gefunden neben der app.py.")

# --------------------------
# Tab 4: Berechtigungen & Rollen
# --------------------------
with tabs[4]:
    st.markdown("## 🔑 Berechtigungen & Rollen")
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if st.session_state.get("role") == "admin":
            st.write("Admin: Vollzugriff auf alle Tabs und Funktionen.")
        else:
            st.info("Nur Admins haben Zugriff auf Rollenverwaltung.")

