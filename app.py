# ==========================================
# QM-Verfahrensanweisungen – Komplettversion
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

CSV_SEP = ","   # Einheitlich Komma in allen Dateien

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
    """
    Liest CSV robust mit UTF-8-SIG, erkennt Trennzeichen automatisch,
    normalisiert Spaltennamen (strip + lower).
    """
    df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.replace("\ufeff", "", regex=False).str.strip().str.lower()
    return df

def write_csv(df: pd.DataFrame, path: pathlib.Path, sep: str = CSV_SEP):
    df.to_csv(path, sep=sep, index=False, encoding="utf-8-sig")

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

def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c.lower() in df.columns:
            return c.lower()
    return None

# --------------------------
# Sidebar (VA-Auswahl + Vorschau + Fortschritt)
# --------------------------
with st.sidebar:
    st.markdown("## 📚 Übersicht")
    if st.session_state.get("logged_in", False):
        st.success(f"Eingeloggt: {st.session_state.get('username')} ({st.session_state.get('role')})")

        # Logout
        if st.button("Logout", key="logout_sidebar"):
            st.session_state.clear()
            st.rerun()

        # VA-Liste laden für Auswahl
        va_list = []
        df_va_sidebar = None
        if DATA_FILE_VA.exists():
            try:
                df_va_sidebar = read_csv_robust(DATA_FILE_VA)
                va_col = find_col(df_va_sidebar, ["va_nr", "va-nr", "va", "va nummer", "va nr"])
                if va_col:
                    df_va_sidebar["va_clean"] = df_va_sidebar[va_col].apply(norm_va)
                    va_list = sorted([v for v in df_va_sidebar["va_clean"].dropna().unique() if v])
                else:
                    st.error("Spalte VA_Nr/va_nr in qm_verfahrensanweisungen.csv nicht gefunden.")
            except Exception as e:
                st.error(f"Fehler beim Lesen der VA-Datei: {e}")

        # Auswahl
        selected_va = st.selectbox("VA auswählen", options=va_list, index=None)
        if selected_va:
            st.session_state.selected_va = selected_va

        # Vorschau + Fortschritt
        if st.session_state.get("selected_va") and df_va_sidebar is not None:
            row = df_va_sidebar[df_va_sidebar["va_clean"] == st.session_state.selected_va]
            if not row.empty:
                def g(col):
                    c = col.lower()
                    return row[c].values[0] if c in row.columns else ""

                st.info(
                    f"**VA {st.session_state.selected_va} – {g('titel')}**\n\n"
                    f"Kapitel: {g('kapitel')} | Unterkapitel: {g('unterkapitel')}\n"
                    f"Revisionsstand: {g('revisionsstand')}\n"
                    f"Geltungsbereich: {g('geltungsbereich')}\n"
                    f"Ziel: {g('ziel')}\n"
                    f"Vorgehensweise: {g('vorgehensweise')}\n"
                    f"Kommentar: {g('kommentar')}\n"
                    f"Mitgeltende Unterlagen: {g('mitgeltende unterlagen')}"
                )

                # Fortschritt berechnen
                if DATA_FILE_KENNTNIS.exists() and DATA_FILE_MA.exists():
                    try:
                        selected_va_norm = norm_va(st.session_state.selected_va)
                        df_k = read_csv_robust(DATA_FILE_KENNTNIS)
                        df_m = read_csv_robust(DATA_FILE_MA)

                        # Name zusammenbauen (Vorname + Nachname) oder aus "name"/"fullname"
                        col_vor = find_col(df_m, ["vorname"])
                        col_nach = find_col(df_m, ["nachname", "name"])
                        col_name_single = find_col(df_m, ["name", "fullname", "full name"])

                        if col_vor and col_nach:
                            df_m["name_full"] = df_m[col_vor].str.strip() + " " + df_m[col_nach].str.strip()
                        elif col_name_single:
                            df_m["name_full"] = df_m[col_name_single].apply(normalize_name)
                        else:
                            df_m["name_full"] = df_m.iloc[:, 0].astype(str).apply(normalize_name)

                        # VA-Zuordnung in Mitarbeiter
                        col_va_m = find_col(df_m, ["va_nr", "va-nr", "va"])
                        if col_va_m is None:
                            col_va_m = df_m.columns[-1]
                        df_m["va_norm"] = df_m[col_va_m].apply(norm_va)

                        zielgruppe = df_m[df_m["va_norm"] == selected_va_norm]["name_full"].dropna().unique()
                        gesamt = len(zielgruppe)

                        # Lesebestätigungen
                        col_va_k = find_col(df_k, ["va_nr", "va-nr", "va"])
                        col_name_k = find_col(df_k, ["name", "fullname", "full name"])
                        if col_va_k is None:
                            df_k["va_nr_norm"] = selected_va_norm
                        else:
                            df_k["va_nr_norm"] = df_k[col_va_k].apply(norm_va)

                        gelesen_raw = df_k[df_k["va_nr_norm"] == selected_va_norm][col_name_k].dropna().unique() if col_name_k else []
                        gelesen_norm = [normalize_name(n) for n in gelesen_raw]

                        gelesen_count = len(set(gelesen_norm) & set(zielgruppe))
                        fortschritt = gelesen_count / gesamt if gesamt > 0 else 0.0

                        st.markdown("### 📊 Lesefortschritt")
                        st.progress(fortschritt)
                        st.caption(f"{gelesen_count} von {gesamt} Mitarbeiter haben bestätigt.")
                    except Exception as e:
                        st.warning(f"Fortschritt konnte nicht berechnet werden: {e}")
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

                # Sicherstellen, dass Spalten vorhanden sind
                required = {"username", "password", "role"}
                missing = required - set(df_users.columns)
                if missing:
                    st.error(f"Fehlende Spalten in users.csv: {missing}")
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
                        st.error("Login fehlgeschlagen: Benutzername oder Passwort falsch.")
            except Exception as e:
                st.error(f"Fehler beim Laden der Benutzerliste: {e}")
    else:
        st.success(f"Eingeloggt als: {st.session_state.username} ({st.session_state.role})")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # Einmal-Knopf: CSVs vereinheitlichen (Komma + UTF-8-SIG)
    st.markdown("### 🛠 CSV-Konvertierung")
    if st.button("Alle CSVs auf Komma & UTF-8-SIG konvertieren"):
        try:
            for path in [DATA_FILE_VA, DATA_FILE_MA, DATA_FILE_KENNTNIS, DATA_FILE_USERS]:
                if path.exists():
                    df = read_csv_robust(path)
                    write_csv(df, path, sep=CSV_SEP)
            st.success("Alle CSVs erfolgreich vereinheitlicht. Bitte App neu laden.")
        except Exception as e:
            st.error(f"Fehler bei der Konvertierung: {e}")

# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
with tabs[1]:
    st.markdown("## 📑 Verfahrensanweisungen")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        # Eingabe neue VA
        st.markdown("### Neue VA anlegen")
        va_nr = st.text_input("VA-Nr")
        titel = st.text_input("Titel")
        kapitel = st.text_input("Kapitel")
        unterkapitel = st.text_input("Unterkapitel")
        revisionsstand = st.text_input("Revisionsstand")
        geltungsbereich = st.text_area("Geltungsbereich")
        ziel = st.text_area("Ziel")
        vorgehensweise = st.text_area("Vorgehensweise")
        kommentar = st.text_area("Kommentar")
        unterlagen = st.text_area("Mitgeltende Unterlagen")

        if st.button("Speichern & PDF erzeugen"):
            new_entry = pd.DataFrame([{
                "va_nr": va_nr,
                "titel": titel,
                "kapitel": kapitel,
                "unterkapitel": unterkapitel,
                "revisionsstand": revisionsstand,
                "geltungsbereich": geltungsbereich,
                "ziel": ziel,
                "vorgehensweise": vorgehensweise,
                "kommentar": kommentar,
                "mitgeltende unterlagen": unterlagen
            }])
            file_exists = DATA_FILE_VA.exists()
            mode = "a" if file_exists else "w"
            header = not file_exists
            write_csv(new_entry, DATA_FILE_VA)
            # Falls Append gewünscht:
            if file_exists:
                new_entry.to_csv(DATA_FILE_VA, sep=CSV_SEP, index=False, mode="a", header=False, encoding="utf-8-sig")

            # PDF (einfacher Text)
            pdf_path = BASE_DIR / "va_pdf" / f"{va_nr}.txt"
            pdf_path.parent.mkdir(exist_ok=True)
            with open(pdf_path, "w", encoding="utf-8") as f:
                f.write(new_entry.to_string())

            st.success(f"VA {va_nr} gespeichert und Textdatei erzeugt.")
            st.info(
                f"**VA {va_nr} – {titel}**\n\n"
                f"Kapitel: {kapitel} | Unterkapitel: {unterkapitel}\n"
                f"Revisionsstand: {revisionsstand}\n"
                f"Geltungsbereich: {geltungsbereich}\n"
                f"Ziel: {ziel}\n"
                f"Vorgehensweise: {vorgehensweise}\n"
                f"Kommentar: {kommentar}\n"
                f"Mitgeltende Unterlagen: {unterlagen}"
            )

        # Bestehende VAs
        if DATA_FILE_VA.exists():
            df_va = read_csv_robust(DATA_FILE_VA)
            st.dataframe(df_va)
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
        name_input = st.text_input("Name (Nachname, Vorname)")
        if st.button("Bestätigen"):
            if st.session_state.get("selected_va"):
                entry = pd.DataFrame([{
                    "name": normalize_name(name_input.strip()),
                    "va_nr": st.session_state.selected_va,
                    "va_nr_norm": norm_va(st.session_state.selected_va),
                    "zeitpunkt": pd.Timestamp.now(tz="Europe/Berlin").strftime("%Y-%m-%d %H:%M:%S")
                }])
                file_exists = DATA_FILE_KENNTNIS.exists()
                entry.to_csv(
                    DATA_FILE_KENNTNIS,
                    sep=CSV_SEP,
                    index=False,
                    mode="a" if file_exists else "w",
                    header=not file_exists,
                    encoding="utf-8-sig"
                )
                st.success("Bestätigung gespeichert.")
            else:
                st.error("Bitte zuerst eine VA in der Sidebar auswählen.")

        if DATA_FILE_KENNTNIS.exists():
            df_k = read_csv_robust(DATA_FILE_KENNTNIS)
            st.dataframe(df_k)
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
        # Anzeige
        if DATA_FILE_MA.exists():
            df_ma = read_csv_robust(DATA_FILE_MA)
            st.dataframe(df_ma)
        else:
            st.info("Noch keine Mitarbeiter-Datei vorhanden.")

        # Admin darf aktualisieren
        if st.session_state.get("role") == "admin":
            st.markdown("### ➕ Mitarbeiterliste aktualisieren")
            uploaded_file = st.file_uploader("CSV-Datei hochladen (Komma-separiert)", type=["csv"])
            if uploaded_file is not None:
                df_new = pd.read_csv(uploaded_file, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
                df_new.columns = df_new.columns.str.replace("\ufeff", "", regex=False).str.strip().str.lower()
                write_csv(df_new, DATA_FILE_MA)
                st.success("Mitarbeiterliste aktualisiert.")
                st.rerun()
        else:
            st.caption("Upload nur für Administratoren.")

# --------------------------
# Tab 4: Benutzerverwaltung (Admin)
# --------------------------
with tabs[4]:
    st.markdown("## ⚙️ Berechtigungen & Rollen")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if st.session_state.get("role") == "admin":
            st.success("Admin-Bereich: volle Berechtigungen")

            # Anzeige
            if DATA_FILE_USERS.exists():
                df_users_view = read_csv_robust(DATA_FILE_USERS)
                st.dataframe(df_users_view)
            else:
                st.info("Noch keine Benutzerliste vorhanden.")

            # CSV-Upload
            st.markdown("### ➕ Benutzerliste aktualisieren")
            uploaded_users = st.file_uploader("users.csv hochladen (Komma-separiert)", type=["csv"], key="upload_users")
            if uploaded_users is not None:
                df_new = pd.read_csv(uploaded_users, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
                df_new.columns = df_new.columns.str.replace("\ufeff", "", regex=False).str.strip().str.lower()
                # nur relevante Spalten behalten, wenn vorhanden
                keep = [c for c in ["username", "password", "role"] if c in df_new.columns]
                df_new = df_new[keep] if keep else df_new
                write_csv(df_new, DATA_FILE_USERS)
                st.success("Benutzerliste aktualisiert.")
                st.rerun()

            # Einzelner Benutzer
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
                        sep=CSV_SEP,
                        index=False,
                        mode="a" if file_exists else "w",
                        header=not file_exists,
                        encoding="utf-8-sig"
                    )
                    st.success(f"Benutzer {new_user} hinzugefügt.")
                    st.rerun()
                else:
                    st.error("Bitte Benutzername und Passwort eingeben.")
        else:
            st.info("Nur Administratoren können die Benutzerverwaltung nutzen.")


