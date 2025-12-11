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
# Hilfsfunktion
# --------------------------
def norm_va(va):
    if pd.isna(va):
        return None
    return str(va).strip().upper()

# --------------------------
# Hilfsfunktionen
# --------------------------
CSV_SEP = ","   # Einheitlich Komma

def read_csv_auto(path):
    return pd.read_csv(path, sep=None, engine="python", encoding="utf-8", dtype=str)

def write_csv(df, path):
    df.to_csv(path, sep=CSV_SEP, index=False, encoding="utf-8")

def append_csv_row(row_dict, path):
    df_new = pd.DataFrame([row_dict])
    file_exists = pathlib.Path(path).exists()
    df_new.to_csv(path, sep=CSV_SEP, index=False, mode="a",
                  header=not file_exists, encoding="utf-8")

def normalize_cols(df):
    df.columns = df.columns.str.strip()
    # hier kannst du Spaltennamen tolerant auf Standard bringen
    return df

def norm_va(va):
    if pd.isna(va): return None
    return str(va).strip().upper()

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    if st.session_state.get("logged_in", False):
        st.success(f"Eingeloggt: {st.session_state.get('username')} ({st.session_state.get('role')})")

        # Logout
        if st.button("Logout", key="logout_sidebar"):
            st.session_state.clear()
            st.rerun()

        # VA-Liste laden
        va_liste = []
        df_va = None
        if DATA_FILE_VA.exists():
            try:
                df_va = pd.read_csv(DATA_FILE_VA, sep=",", encoding="utf-8", dtype=str)
                df_va.columns = df_va.columns.str.strip()

                va_col = None
                for c in ["VA_Nr", "va_nr", "Va_Nr", "VA-nr"]:
                    if c in df_va.columns:
                        va_col = c
                        break

                if va_col:
                    df_va["VA_clean"] = df_va[va_col].apply(norm_va)
                    va_liste = sorted([v for v in df_va["VA_clean"].dropna().unique() if v])
                else:
                    st.error("Spalte 'VA_Nr' fehlt in qm_verfahrensanweisungen.csv.")
            except Exception as e:
                st.error(f"Fehler beim Lesen der VA-Datei: {e}")

        # Auswahlfeld
        selected_va = st.selectbox("VA auswählen", options=va_liste, index=None, key="sidebar_va_select")
        st.session_state.selected_va = selected_va if selected_va else st.session_state.get("selected_va")

        # Vorschau + Gelbes Dokument + Lesebestätigung + Fortschritt
        if st.session_state.get("selected_va") and df_va is not None:
            row = df_va[df_va["VA_clean"] == st.session_state.selected_va]
            if not row.empty:
                def g(col):
                    return row[col].values[0] if col in row.columns else ""

                # Gelbe Info-Box mit VA-Daten
                st.info(f"""
**VA {st.session_state.selected_va} – {g('Titel')}**

Kapitel: {g('Kapitel')} | Unterkapitel: {g('Unterkapitel')}  
Revisionsstand: {g('Revisionsstand')}  
Geltungsbereich: {g('Geltungsbereich')}  
Ziel: {g('Ziel')}  
Vorgehensweise: {g('Vorgehensweise')}  
Kommentar: {g('Kommentar')}  
Mitgeltende Unterlagen: {g('Mitgeltende Unterlagen')}
""")
# Eingabe für Lesebestätigung
st.markdown("### ✅ Lesebestätigung")
name_input = st.text_input("Name (Nachname, Vorname)", key="sidebar_name_input")

if st.button("Bestätigen", key="sidebar_confirm_button"):
    if name_input.strip():
        # Namensformat vereinheitlichen: "Müller, Anna" -> "Anna Müller"
        def normalize_name(name):
            if "," in name:
                nach, vor = [p.strip() for p in name.split(",", 1)]
                return f"{vor} {nach}"
            return name.strip()

        entry = pd.DataFrame([{
            "Name": normalize_name(name_input.strip()),
            "VA_Nr": st.session_state.selected_va,
            "VA_Nr_norm": norm_va(st.session_state.selected_va),
            "Zeitpunkt": pd.Timestamp.now(tz="Europe/Berlin").strftime("%Y-%m-%d %H:%M:%S")
        }])

        file_exists = DATA_FILE_KENNTNIS.exists()
        entry.to_csv(
            DATA_FILE_KENNTNIS,
            sep=",",                # durchgängig Komma
            index=False,
            mode="a" if file_exists else "w",
            header=not file_exists,
            encoding="utf-8"
        )
        st.success("Bestätigung gespeichert.")
        st.write("Zuletzt gespeichert:", entry.to_dict(orient="records")[0])  # Debug-Ausgabe
    else:
        st.error("Bitte Name eingeben.")

# Fortschrittsanzeige
if DATA_FILE_KENNTNIS.exists() and DATA_FILE_MA.exists():
    try:
        df_kenntnis = pd.read_csv(DATA_FILE_KENNTNIS, sep=",", encoding="utf-8", dtype=str)
        df_mitarbeiter = pd.read_csv(DATA_FILE_MA, sep=",", encoding="utf-8", dtype=str)

        # Mitarbeiter-Namen vereinheitlichen
        df_mitarbeiter["Name_full"] = df_mitarbeiter["Vorname"].str.strip() + " " + df_mitarbeiter["Name"].str.strip()
        df_mitarbeiter["VA_norm"] = df_mitarbeiter["VA_Nr"].apply(norm_va)

        # Zielgruppe für die ausgewählte VA
        zielgruppe = df_mitarbeiter[
            df_mitarbeiter["VA_norm"] == norm_va(st.session_state.selected_va)
        ]["Name_full"].dropna().unique()
        gesamt = len(zielgruppe)

        # Lesebestätigungen für diese VA
        df_kenntnis["VA_Nr_norm"] = df_kenntnis["VA_Nr"].apply(norm_va)
        gelesen_raw = df_kenntnis[
            df_kenntnis["VA_Nr_norm"] == norm_va(st.session_state.selected_va)
        ]["Name"].dropna().unique()

        # Namensnormalisierung: "Nachname, Vorname" -> "Vorname Nachname"
        def normalize_name(name):
            if not isinstance(name, str):
                return ""
            if "," in name:
                nach, vor = [p.strip() for p in name.split(",", 1)]
                return f"{vor} {nach}"
            return name.strip()

        gelesen_norm = [normalize_name(n) for n in gelesen_raw]

        # Schnittmenge berechnen
        gelesen_count = len(set(gelesen_norm) & set(zielgruppe))
        fortschritt = gelesen_count / gesamt if gesamt > 0 else 0.0

        st.markdown("### 📊 Lesefortschritt")
        st.progress(fortschritt)
        st.caption(f"{gelesen_count} von {gesamt} Mitarbeiter haben bestätigt.")
    except Exception as e:
        st.warning(f"Fortschritt konnte nicht berechnet werden: {e}")
else:
    st.info("Für die Fortschrittsanzeige werden Mitarbeiter- und Lesebestätigungsdateien benötigt.")

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
                df_users = pd.read_csv(DATA_FILE_USERS, sep=",", encoding="utf-8", dtype=str)
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
    # Einmal-Knopf: CSVs konvertieren
    # --------------------------
    st.markdown("### 🛠 CSV-Konvertierung")
    if st.button("Alle CSVs auf Komma konvertieren"):
        try:
            for path in [DATA_FILE_VA, DATA_FILE_MA, DATA_FILE_KENNTNIS, DATA_FILE_USERS]:
                if path.exists():
                    df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8", dtype=str)
                    df.to_csv(path, sep=",", index=False, encoding="utf-8")
            st.success("Alle CSVs erfolgreich auf Komma konvertiert. Bitte App neu laden.")
        except Exception as e:
            st.error(f"Fehler bei der Konvertierung: {e}")

# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        # Eingabefelder für neue VA
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
                "VA_Nr": va_nr,
                "Titel": titel,
                "Kapitel": kapitel,
                "Unterkapitel": unterkapitel,
                "Revisionsstand": revisionsstand,
                "Geltungsbereich": geltungsbereich,
                "Ziel": ziel,
                "Vorgehensweise": vorgehensweise,
                "Kommentar": kommentar,
                "Mitgeltende Unterlagen": unterlagen
            }])

            file_exists = DATA_FILE_VA.exists()
            new_entry.to_csv(
                DATA_FILE_VA,
                sep=",",                # <-- Komma statt Semikolon
                index=False,
                mode="a" if file_exists else "w",
                header=not file_exists,
                encoding="utf-8"
            )

            # PDF erzeugen (einfacher Textinhalt)
            pdf_path = pathlib.Path("va_pdf") / f"{va_nr}.pdf"
            pdf_path.parent.mkdir(exist_ok=True)
            with open(pdf_path, "w", encoding="utf-8") as f:
                f.write(new_entry.to_string())

            st.success(f"VA {va_nr} gespeichert und PDF erzeugt.")

            # Gelbe Info-Box mit VA-Daten
            st.info(f"""
**VA {va_nr} – {titel}**

Kapitel: {kapitel} | Unterkapitel: {unterkapitel}  
Revisionsstand: {revisionsstand}  
Geltungsbereich: {geltungsbereich}  
Ziel: {ziel}  
Vorgehensweise: {vorgehensweise}  
Kommentar: {kommentar}  
Mitgeltende Unterlagen: {unterlagen}
""")

        # Bestehende VAs anzeigen
        if DATA_FILE_VA.exists():
            df_va = pd.read_csv(DATA_FILE_VA, sep=",", encoding="utf-8", dtype=str)
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
        # Eingabe für Lesebestätigung
        name_input = st.text_input("Name (Nachname, Vorname)", key="tab2_name_input")
        if st.button("Bestätigen", key="tab2_confirm_button"):
            if st.session_state.get("selected_va"):
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
            else:
                st.error("Bitte zuerst eine VA in der Sidebar auswählen.")

        # Tabelle mit allen Lesebestätigungen
        if DATA_FILE_KENNTNIS.exists():
            df_k = pd.read_csv(DATA_FILE_KENNTNIS, sep=";", encoding="utf-8-sig", dtype=str)
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
        if DATA_FILE_MA.exists():
            df_ma = pd.read_csv(DATA_FILE_MA, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_ma)

        if st.session_state.role == "admin":
            st.markdown("### ➕ Mitarbeiterliste aktualisieren")
            uploaded_file = st.file_uploader("CSV-Datei hochladen", type=["csv"])
            if uploaded_file is not None:
                df_new = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", dtype=str)
                df_new.to_csv(DATA_FILE_MA, sep=";", index=False, encoding="utf-8-sig")
                st.success("Mitarbeiterliste aktualisiert.")


# --------------------------
# Tab 4: Berechtigungen & Rollen
# --------------------------
with tabs[4]:
    st.markdown("## 🔑 Berechtigungen & Rollen")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
    else:
        if DATA_FILE_USERS.exists():
            df_users = pd.read_csv(DATA_FILE_USERS, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_users)

        if st.session_state.role == "admin":
            st.markdown("### ➕ Benutzerliste aktualisieren")
            uploaded_file = st.file_uploader("users.csv hochladen", type=["csv"])
            if uploaded_file is not None:
                df_new = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", dtype=str)
                df_new.to_csv(DATA_FILE_USERS, sep=";", index=False, encoding="utf-8-sig")
                st.success("Benutzerliste aktualisiert.")

