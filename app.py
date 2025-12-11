# ==========================================
# QM-Verfahrensanweisungen – Komplettversion (Google Sheets)
# ==========================================
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --------------------------
# Verbindung zu Google Sheets
# --------------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds_dict = json.loads(st.secrets["gspread_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict)

client = gspread.authorize(creds)

# Tabellen öffnen (Name muss mit deinem Google Sheet übereinstimmen)
sheet_va = client.open("qm_verfahrensanweisungen").sheet1
sheet_ma = client.open("mitarbeiter").sheet1
sheet_users = client.open("users").sheet1
sheet_kenntnis = client.open("lesebestätigung").sheet1

# --------------------------
# Session-State Initialisierung
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "selected_va" not in st.session_state:
    st.session_state.selected_va = None

# --------------------------
# Hilfsfunktionen
# --------------------------
def df_from_sheet(sheet):
    return pd.DataFrame(sheet.get_all_records())

def norm_va(va):
    if pd.isna(va):
        return None
    return str(va).strip().upper()

def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.strip()
    if "," in name:
        nach, vor = [p.strip() for p in name.split(",", 1)]
        return f"{vor} {nach}"
    return name

# --------------------------
# Sidebar (VA-Auswahl + Lesebestätigung + Dokumentanzeige)
# --------------------------
with st.sidebar:
    st.markdown("## 📚 Übersicht")
    if st.session_state.get("logged_in", False):
        st.success(f"Eingeloggt: {st.session_state.get('username')} ({st.session_state.get('role')})")

        if st.button("Logout", key="logout_sidebar"):
            st.session_state.clear()
            st.rerun()

        # VA-Liste laden
        df_va_sidebar = df_from_sheet(sheet_va)
        va_list = sorted([norm_va(v) for v in df_va_sidebar["va_nr"].dropna().unique()])

        selected_va = st.selectbox("VA auswählen", options=va_list, index=None)
        if selected_va:
            st.session_state.selected_va = selected_va

        # Dokumentanzeige
        if st.session_state.get("selected_va"):
            doc = df_va_sidebar[df_va_sidebar["va_nr"].apply(norm_va) == st.session_state.selected_va]
            if not doc.empty:
                st.markdown("### 📄 Aktuelles Dokument")
                st.table(doc)

        # Lesebestätigung nur für User
        if st.session_state.get("role") == "user":
            st.markdown("### ✅ Lesebestätigung")
            if st.session_state.get("selected_va"):
                name_input = st.text_input("Name (Nachname, Vorname)", key="sidebar_name_input")
                if st.button("Bestätigen", key="sidebar_confirm_button"):
                    sheet_kenntnis.append_row([
                        normalize_name(name_input.strip()),
                        st.session_state.selected_va,
                        norm_va(st.session_state.selected_va),
                        pd.Timestamp.now(tz="Europe/Berlin").strftime("%Y-%m-%d %H:%M:%S")
                    ])
                    st.success("Bestätigung gespeichert.")
            else:
                st.info("Bitte zuerst eine VA auswählen.")
    else:
        st.info("Bitte zuerst im Tab 'System & Login' anmelden.")

# --------------------------
# Tabs
# --------------------------
tabs = st.tabs([
    "System & Login",
    "Verfahrensanweisungen",
    "Lesebestätigung",
    "Mitarbeiter",
    "Berechtigungen & Rollen"
])

# --------------------------
# Tab 0: System & Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔒 System & Login")

    if not st.session_state.get("logged_in", False):
        u = st.text_input("Benutzername")
        p = st.text_input("Passwort", type="password")

        if st.button("Login"):
            df_users = df_from_sheet(sheet_users)
            match = df_users[
                (df_users["username"].str.strip().str.lower() == u.strip().lower()) &
                (df_users["password"].str.strip() == p.strip())
            ]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.username = match["username"].values[0].strip()
                st.session_state.role = match["role"].values[0].strip().lower()
                st.success(f"Eingeloggt als {st.session_state.username} ({st.session_state.role})")
                st.rerun()
            else:
                st.error("Login fehlgeschlagen.")
    else:
        st.success(f"Eingeloggt als: {st.session_state.username} ({st.session_state.role})")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

# --------------------------
# Tab 1: Verfahrensanweisungen (Admin-only)
# --------------------------
with tabs[1]:
    st.markdown("## 📑 Verfahrensanweisungen")
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    elif st.session_state.get("role") != "admin":
        st.info("Nur Administratoren haben Zugriff auf diesen Bereich.")
    else:
        va_nr = st.text_input("VA-Nr")
        titel = st.text_input("Titel")
        kapitel = st.text_input("Kapitel")
        if st.button("Speichern"):
            sheet_va.append_row([va_nr, titel, kapitel])
            st.success(f"VA {va_nr} gespeichert.")

        df_va = df_from_sheet(sheet_va)
        st.dataframe(df_va)

# --------------------------
# Tab 2: Lesebestätigung (Admin-only Übersicht)
# --------------------------
with tabs[2]:
    st.markdown("## ✅ Lesebestätigung")
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    elif st.session_state.get("role") != "admin":
        st.info("Nur Administratoren sehen die Übersicht.")
    else:
        df_k = df_from_sheet(sheet_kenntnis)
        st.dataframe(df_k)

# --------------------------
# Tab 3: Mitarbeiter (Admin-only)
# --------------------------
with tabs[3]:
    st.markdown("## 👥 Mitarbeiter")
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    elif st.session_state.get("role") != "admin":
        st.info("Nur Administratoren haben Zugriff auf diesen Bereich.")
    else:
        uploaded_ma = st.file_uploader("Mitarbeiterliste hochladen (Tab-getrennt)", type=["csv"], key="upload_ma")
        if uploaded_ma is not None:
            df_new = pd.read_csv(uploaded_ma, sep="\t", encoding="utf-8-sig", dtype=str)
            for row in df_new.values.tolist():
                sheet_ma.append_row(row)
            st.success("Mitarbeiterliste aktualisiert.")
            st.rerun()

        df_ma = df_from_sheet(sheet_ma)
        st.dataframe(df_ma)

# --------------------------
# Tab 4: Benutzerverwaltung (Admin-only)
# --------------------------
with tabs[4]:
    st.markdown("## ⚙️ Berechtigungen & Rollen")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    elif st.session_state.get("role") != "admin":
        st.info("Nur Administratoren können die Benutzerverwaltung nutzen.")
    else:
        st.success("Admin-Bereich: volle Berechtigungen")

        df_users_view = df_from_sheet(sheet_users)
        st.dataframe(df_users_view)

        st.markdown("### ➕ Einzelnen Benutzer hinzufügen")
        new_user = st.text_input("Benutzername", key="new_user")
        new_pass = st.text_input("Passwort", type="password", key="new_pass")
        new_role = st.selectbox("Rolle", options=["user", "admin"], key="new_role")

        if st.button("Benutzer hinzufügen", key="add_user_btn"):
            if new_user.strip() and new_pass.strip():
                sheet_users.append_row([new_user.strip(), new_pass.strip(), new_role.strip().lower()])
                st.success(f"Benutzer {new_user} hinzugefügt.")
                st.rerun()
            else:
                st.error("Bitte Benutzername und Passwort eingeben.")


