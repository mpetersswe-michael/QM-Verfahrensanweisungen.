# ==========================================
# QM-Verfahrensanweisungen – Komplettversion (Tab-getrennte CSVs)
# ==========================================
import streamlit as st
import pandas as pd
import pathlib

# --------------------------
# Basis & Pfade
# --------------------------
BASE_DIR = pathlib.Path(__file__).parent.resolve()
DATA_FILE_VA = BASE_DIR / "qm_verfahrensanweisungen.csv"
DATA_FILE_MA = BASE_DIR / "mitarbeiter.csv"
DATA_FILE_KENNTNIS = BASE_DIR / "lesebestätigung.csv"
DATA_FILE_USERS = BASE_DIR / "users.csv"

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
def read_csv_robust(path: pathlib.Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.replace("\ufeff", "", regex=False).str.strip().str.lower()
    return df

def write_csv(df: pd.DataFrame, path: pathlib.Path):
    df.to_csv(path, sep="\t", index=False, encoding="utf-8-sig")

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
# Sidebar (VA-Auswahl + Lesebestätigung für User)
# --------------------------
with st.sidebar:
    st.markdown("## 📚 Übersicht")
    if st.session_state.get("logged_in", False):
        st.success(f"Eingeloggt: {st.session_state.get('username')} ({st.session_state.get('role')})")

        # Logout
        if st.button("Logout", key="logout_sidebar"):
            st.session_state.clear()
            st.rerun()

        # VA-Liste laden
        va_list = []
        df_va_sidebar = None
        if DATA_FILE_VA.exists():
            df_va_sidebar = read_csv_robust(DATA_FILE_VA)
            if "va_nr" in df_va_sidebar.columns:
                df_va_sidebar["va_clean"] = df_va_sidebar["va_nr"].apply(norm_va)
                va_list = sorted([v for v in df_va_sidebar["va_clean"].dropna().unique() if v])

        selected_va = st.selectbox("VA auswählen", options=va_list, index=None)
        if selected_va:
            st.session_state.selected_va = selected_va

        # Lesebestätigung nur für User
        if st.session_state.get("role") == "user":
            st.markdown("### ✅ Lesebestätigung")
            if st.session_state.get("selected_va"):
                name_input = st.text_input("Name (Nachname, Vorname)", key="sidebar_name_input")
                if st.button("Bestätigen", key="sidebar_confirm_button"):
                    entry = pd.DataFrame([{
                        "name": normalize_name(name_input.strip()),
                        "va_nr": st.session_state.selected_va,
                        "va_nr_norm": norm_va(st.session_state.selected_va),
                        "zeitpunkt": pd.Timestamp.now(tz="Europe/Berlin").strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    file_exists = DATA_FILE_KENNTNIS.exists()
                    entry.to_csv(
                        DATA_FILE_KENNTNIS,
                        sep="\t",
                        index=False,
                        mode="a" if file_exists else "w",
                        header=not file_exists,
                        encoding="utf-8-sig"
                    )
                    st.success("Bestätigung gespeichert.")
            else:
                st.info("Bitte zuerst eine VA auswählen.")
    else:
        st.info("Bitte zuerst im Tab 'System & Login' anmelden.")

# --------------------------
# Tabs nur einmal definieren
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
            try:
                df_users = read_csv_robust(DATA_FILE_USERS)
                required = {"username", "password", "role"}
                if not required.issubset(set(df_users.columns)):
                    st.error("users.csv muss Spalten username, password, role enthalten.")
                else:
                    match = df_users[
                        (df_users["username"].fillna("").str.strip().str.lower() == u.strip().lower()) &
                        (df_users["password"].fillna("").str.strip() == p.strip())
                    ]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.username = match["username"].values[0].strip()
                        st.session_state.role = match["role"].values[0].strip().lower()
                        st.success(f"Eingeloggt als {st.session_state.username} ({st.session_state.role})")
                        st.rerun()
                    else:
                        st.error("Login fehlgeschlagen.")
            except Exception as e:
                st.error(f"Fehler beim Laden der Benutzerliste: {e}")
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
        st.write("Hier können Admins neue VA anlegen und bestehende anzeigen.")
        # Beispiel: neue VA speichern
        va_nr = st.text_input("VA-Nr")
        titel = st.text_input("Titel")
        kapitel = st.text_input("Kapitel")
        if st.button("Speichern"):
            new_entry = pd.DataFrame([{
                "va_nr": va_nr,
                "titel": titel,
                "kapitel": kapitel
            }])
            file_exists = DATA_FILE_VA.exists()
            new_entry.to_csv(
                DATA_FILE_VA,
                sep="\t",
                index=False,
                mode="a" if file_exists else "w",
                header=not file_exists,
                encoding="utf-8-sig"
            )
            st.success(f"VA {va_nr} gespeichert.")

        if DATA_FILE_VA.exists():
            df_va = read_csv_robust(DATA_FILE_VA)
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
        if DATA_FILE_KENNTNIS.exists():
            df_k = read_csv_robust(DATA_FILE_KENNTNIS)
            st.dataframe(df_k)
        else:
            st.info("Noch keine Lesebestätigungen vorhanden.")

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
        if DATA_FILE_MA.exists():
            df_ma = read_csv_robust(DATA_FILE_MA)
            st.dataframe(df_ma)
        else:
            st.info("Noch keine Mitarbeiter-Datei vorhanden.")

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

        # Bestehende Benutzer anzeigen
        if DATA_FILE_USERS.exists():
            df_users_view = read_csv_robust(DATA_FILE_USERS)
            st.dataframe(df_users_view)
        else:
            st.info("Noch keine Benutzerliste vorhanden.")

        # CSV-Upload
        st.markdown("### ➕ Benutzerliste aktualisieren")
        uploaded_users = st.file_uploader(
            "users.csv hochladen (Tab-getrennt)", type=["csv"], key="upload_users"
        )
        if uploaded_users is not None:
            df_new = pd.read_csv(
                uploaded_users, sep="\t", encoding="utf-8-sig", dtype=str
            )
            df_new.columns = df_new.columns.str.replace("\ufeff", "", regex=False).str.strip().str.lower()
            # nur relevante Spalten behalten
            keep = [c for c in ["username", "password", "role"] if c in df_new.columns]
            df_new = df_new[keep] if keep else df_new
            write_csv(df_new, DATA_FILE_USERS)
            st.success("Benutzerliste aktualisiert.")
            st.rerun()

        # Einzelnen Benutzer hinzufügen
        st.markdown("### ➕ Einzelnen Benutzer hinzufügen")
        new_user = st.text_input("Benutzername", key="new_user")
        new_pass = st.text_input("Passwort", type="password", key="new_pass")
        new_role = st.selectbox("Rolle", options=["user", "admin"], key="new_role")

        if st.button("Benutzer hinzufügen", key="add_user_btn"):
            if new_user.strip() and new_pass.strip():
                new_entry = pd.DataFrame([{
                    "username": new_user.strip(),
                    "password": new_pass.strip(),
                    "role": new_role.strip().lower()
                }])
                file_exists = DATA_FILE_USERS.exists()
                new_entry.to_csv(
                    DATA_FILE_USERS,
                    sep="\t",
                    index=False,
                    mode="a" if file_exists else "w",
                    header=not file_exists,
                    encoding="utf-8-sig"
                )
                st.success(f"Benutzer {new_user} hinzugefügt.")
                st.rerun()
            else:
                st.error("Bitte Benutzername und Passwort eingeben.")
