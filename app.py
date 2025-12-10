# --------------------------
# Imports
# --------------------------
import os
import re
import io
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from fpdf import FPDF
import pathlib
import html


st.set_page_config(
    page_title="Verfahrensanweisungen (Auszug aus dem QMH)",
    page_icon="📘",
    layout="wide"
)

# --------------------------
# Datenkonfiguration
# --------------------------
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
DATA_FILE_KENNTNIS = "lesebestätigung.csv"
DATA_FILE_MA = "mitarbeiter.csv"

# --------------------------
# PDF-Hilfsfunktionen
# --------------------------
def norm_va(x):
    s = str(x).upper().replace(" ", "")
    m = s.replace("VA", "")
    if m.isdigit():
        s = f"VA{int(m):03d}"
    return s

def clean_text(text):
    if text is None or str(text).strip() == "":
        return "-"
    return (
        str(text)
        .encode("latin-1", errors="ignore")
        .decode("latin-1")
        .replace("–", "-")
        .replace("•", "*")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("€", "EUR")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )

class CustomPDF(FPDF):
    def header(self):
        self.set_font("Arial", size=9)
        self.cell(0, 10, clean_text("Pflegedienst: xy"), ln=0, align="L")
        self.cell(0, 10, clean_text(f"Verfahrensanweisung Pflege, Kap. {getattr(self, 'unterkapitel', '')}"), ln=0, align="R")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", size=8)
        self.cell(60, 10, clean_text(f"{getattr(self, 'va_nr', '')} – {getattr(self, 'va_titel', '')}"), ln=0)
        self.set_x((210 - 90) / 2)
        self.cell(90, 10, clean_text("Erstellt von: Peters, Michael – Qualitätsbeauftragter"), align="C")
        self.set_x(-30)
        self.cell(0, 10, f"Seite {self.page_no()}", align="R")

def export_va_to_pdf(row):
    os.makedirs("va_pdf", exist_ok=True)
    pdf = CustomPDF()
    pdf.alias_nb_pages()
    pdf.va_nr = f"{row.get('VA_Nr', '')}"
    pdf.va_titel = f"{row.get('Titel', '')}"
    pdf.unterkapitel = f"{row.get('Unterkapitel', '')}"
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text(f"QM-Verfahrensanweisung - {row.get('VA_Nr', '')}"), ln=True, align="C")
    pdf.ln(5)

    def add_section(title, content):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, clean_text(title), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, clean_text(content))
        pdf.ln(3)

    fields = [
        "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
        "Geltungsbereich", "Ziel", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
    ]
    for feld in fields:
        add_section(feld, row.get(feld, ""))

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    va_nr = norm_va(row.get("VA_Nr", "VA000"))
    pdf_path = f"va_pdf/{va_nr}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    return pdf_bytes, pdf_path

# --------------------------
# Session-Init
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "selected_va" not in st.session_state:
    st.session_state.selected_va = None

# --------------------------
# Tabs
# --------------------------
tabs = st.tabs(["System & Login", "Verfahrensanweisungen", "Lesebestätigung", "Mitarbeiter","Berechtigungen & Rollen"])

# Prüfung der Benutzerdatei users.csv
def check_users_csv():
    path = "users.csv"
    if not os.path.exists(path):
        st.error("❌ Datei 'users.csv' wurde nicht gefunden.")
        return False

    try:
        df = pd.read_csv(path, sep=";", dtype=str)
        expected_cols = {"username", "password", "role"}
        actual_cols = set([str(col).strip().lower() for col in users_df.columns])

        missing = expected_cols - actual_cols
        if missing:
            st.error(f"❌ Spalten fehlen in 'users.csv': {', '.join(missing)}")
            st.info(f"Gefundene Spalten: {', '.join(df.columns)}")
            return False
        st.success("✅ Benutzerdatei 'users.csv' erfolgreich geprüft.")
        return True
    except Exception as e:
        st.error(f"❌ Fehler beim Einlesen der Datei 'users.csv': {e}")
        return False

# --------------------------
# Tab 0 System & Login
# --------------------------

with tabs[0]:
    st.markdown("## 🔒 Login")

    if not st.session_state.get("logged_in", False):
        input_user = st.text_input("Benutzername")
        input_pass = st.text_input("Passwort", type="password")
        if st.button("Login"):
            try:
                users_df = pd.read_csv("users.csv", sep=";", dtype=str)
                users_df["username"] = users_df["username"].str.strip()
                users_df["password"] = users_df["password"].str.strip()
                input_user = input_user.strip()
                input_pass = input_pass.strip()

                match = users_df[
                    (users_df["username"] == input_user) &
                    (users_df["password"] == input_pass)
                ]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = input_user
                    st.session_state.role = match.iloc[0]["role"]
                    st.success(f"✅ Eingeloggt als {input_user} (Rolle: {st.session_state.role})")
                    st.rerun()
                else:
                    st.error("❌ Login fehlgeschlagen.")
            except Exception as e:
                st.error(f"Fehler beim Login-Vorgang: {e}")
    else:
        st.info("Du bist bereits eingeloggt. Logout über die Sidebar.")



# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")

    if not st.session_state.get("logged_in"):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")

    elif st.session_state.role != "admin":
        st.warning("🔒 Kein Zugriff für Benutzerrolle. Sichtbar zur Orientierung.")

    else:
        va_nr_input = st.text_input("VA-Nummer")
        titel_input = st.text_input("Titel")
        kapitel_input = st.text_input("Kapitel")
        unterkapitel_input = st.text_input("Unterkapitel")
        revisionsstand_input = st.text_input("Revisionsstand")
        geltungsbereich_input = st.text_input("Geltungsbereich")
        ziel_input = st.text_input("Ziel")
        vorgehensweise_input = st.text_area("Vorgehensweise")
        kommentar_input = st.text_area("Kommentar")
        mitgeltende_input = st.text_area("Mitgeltende Unterlagen")

        if st.button("VA speichern"):
            neuer_eintrag = pd.DataFrame([{
                "VA_Nr": va_nr_input.strip(),
                "Titel": titel_input.strip(),
                "Kapitel": kapitel_input.strip(),
                "Unterkapitel": unterkapitel_input.strip(),
                "Revisionsstand": revisionsstand_input.strip(),
                "Geltungsbereich": geltungsbereich_input.strip(),
                "Ziel": ziel_input.strip(),
                "Vorgehensweise": vorgehensweise_input.strip(),
                "Kommentar": kommentar_input.strip(),
                "Mitgeltende Unterlagen": mitgeltende_input.strip()
            }])

            if os.path.exists(DATA_FILE_QM):
                df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
                df_va = pd.concat([df_va, neuer_eintrag], ignore_index=True)
            else:
                df_va = neuer_eintrag

            df_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"✅ VA {va_nr_input} gespeichert.")

            # PDF erzeugen
            row = neuer_eintrag.iloc[0].to_dict()
            pdf_bytes, pdf_path = export_va_to_pdf(row)
            st.download_button(
                label=f"📄 PDF herunterladen: {norm_va(va_nr_input)}",
                data=pdf_bytes,
                file_name=f"{norm_va(va_nr_input)}.pdf",
                mime="application/pdf"
            )

        # VA-Tabelle anzeigen
        if os.path.exists(DATA_FILE_QM):
            df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_va)
        else:
            st.info("Noch keine Verfahrensanweisungen gespeichert.")




# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
with tabs[2]:
    st.markdown("## ✅ Lesebestätigung")
    if not st.session_state.get("logged_in"):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
    elif st.session_state.role != "admin":
        st.warning("🔒 Kein Zugriff für Benutzerrolle. Sichtbar zur Orientierung.")
    else:
        if os.path.exists(DATA_FILE_KENNTNIS):
            df_all = pd.read_csv(DATA_FILE_KENNTNIS, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_all)
        else:
            st.info("Noch keine Lesebestätigungen vorhanden.")

# --------------------------
# Tab 3: Mitarbeiter
# --------------------------
with tabs[3]:
    st.markdown("## 👥 Mitarbeiterverwaltung")
    if not st.session_state.get("logged_in"):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
    elif st.session_state.role != "admin":
        st.warning("🔒 Kein Zugriff für Benutzerrolle. Sichtbar zur Orientierung.")
    else:
        uploaded_file = st.file_uploader("Mitarbeiterliste hochladen (CSV)", type=["csv"])
        if uploaded_file is not None:
            df_ma = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", dtype=str)
            df_ma.to_csv(DATA_FILE_MA, sep=";", index=False, encoding="utf-8-sig")
            st.success("Mitarbeiterliste gespeichert.")
        if os.path.exists(DATA_FILE_MA):
            df_ma = pd.read_csv(DATA_FILE_MA, sep=";", encoding="utf-8-sig", dtype=str)
            st.dataframe(df_ma)
        else:
            st.info("Keine Mitarbeiterliste vorhanden.")


# --------------------------
# Tab 4: Berechtigungen & Rollen
# --------------------------

DATA_FILE_USERS = "users.csv"

with tabs[4]:
    if st.session_state.get("logged_in", False) and st.session_state.get("role") == "admin":
        st.markdown("## 🛡️ Berechtigungen & Rollen")
        st.info("Hier kannst du die Benutzerdatei (`users.csv`) hochladen und prüfen.")

        uploaded_users = st.file_uploader("📤 Benutzerdatei hochladen", type=["csv"], key="upload_users_tab4")

        users_df = None
        if uploaded_users is not None:
            try:
                # Datei einlesen und sofort speichern
                users_df = pd.read_csv(uploaded_users, sep=";", encoding="utf-8-sig", dtype=str)
                users_df.to_csv(DATA_FILE_USERS, sep=";", index=False, encoding="utf-8-sig")
                st.success("✅ Benutzerdatei gespeichert.")
            except Exception as e:
                st.error(f"❌ Fehler beim Einlesen der Datei: {e}")

        # Falls bereits gespeichert, erneut laden
        if os.path.exists(DATA_FILE_USERS):
            try:
                users_df = pd.read_csv(DATA_FILE_USERS, sep=";", encoding="utf-8-sig", dtype=str)
                st.dataframe(users_df)
            except Exception as e:
                st.error(f"❌ Fehler beim Einlesen der lokalen Datei: {e}")
        else:
            st.info("Keine Benutzerdatei vorhanden.")

        # Spaltenprüfung
        if users_df is not None:
            users_df.columns = [str(c).strip() for c in users_df.columns]
            expected_cols = {"username", "password", "role"}
            actual_cols = set(c.lower() for c in users_df.columns)

            missing = expected_cols - actual_cols
            if missing:
                st.error(f"❌ Spalten fehlen: {', '.join(sorted(missing))}")
                st.info(f"Gefundene Spalten: {', '.join(users_df.columns)}")
            else:
                st.success("✅ Benutzerdatei ist vollständig und korrekt.")
                st.dataframe(users_df)
    else:
        st.warning("🔒 Nur Admins haben Zugriff auf diesen Bereich.")



# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    if st.session_state.get("logged_in", False):
        st.success("✅ Eingeloggt")

        # Logout immer verfügbar
        if st.button("Logout", key="logout_sidebar"):
            st.session_state.logged_in = False
            st.session_state.selected_va = None
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()

        # VA-Auswahl
        va_liste = []
        if os.path.exists("qm_verfahrensanweisungen.csv"):
            df_va = pd.read_csv("qm_verfahrensanweisungen.csv", sep=";", encoding="utf-8-sig", dtype=str)
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

                va_text = f"""
                <strong>VA-Nr:</strong> {va_nummer}<br>
                <strong>Titel:</strong> {clean(row['Titel'].values[0])}<br>
                <strong>Kapitel:</strong> {clean(row['Kapitel'].values[0])}<br>
                <strong>Unterkapitel:</strong> {clean(row['Unterkapitel'].values[0])}<br>
                <strong>Revisionsstand:</strong> {clean(row['Revisionsstand'].values[0])}<br>
                <strong>Geltungsbereich:</strong> {clean(row['Geltungsbereich'].values[0])}<br>
                <strong>Ziel:</strong> {clean(row['Ziel'].values[0])}<br>
                <strong>Vorgehensweise:</strong><br>{clean(row['Vorgehensweise'].values[0])}<br>
                <strong>Kommentar:</strong><br>{clean(row['Kommentar'].values[0])}<br>
                <strong>Mitgeltende Unterlagen:</strong><br>{clean(row['Mitgeltende Unterlagen'].values[0])}
                """

                st.markdown(
                    f"""
                    <div style="background-color:#fff3cd;
                                padding:12px;
                                border-radius:6px;
                                border:1px solid #ffeeba;
                                margin-top:10px;
                                font-size:14px;
                                line-height:1.4">
                    <strong>📘 VA-Inhalt:</strong><br><br>
                    {va_text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

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
                    name_clean = re.sub(r"\s*,\s*", ",", name_sidebar.strip())
                    if name_clean:
                        zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
                        eintrag = {"Name": name_clean, "VA_Nr": va_nummer, "Zeitpunkt": zeitpunkt}
                        df_new = pd.DataFrame([eintrag])[["Name", "VA_Nr", "Zeitpunkt"]]

                        path = "lesebestätigung.csv"
                        file_exists = os.path.exists(path)
                        file_empty = (not file_exists) or (os.path.getsize(path) == 0)

                        df_new.to_csv(
                            path,
                            sep=";",
                            index=False,
                            mode="a" if file_exists and not file_empty else "w",
                            header=True if file_empty else False,
                            encoding="utf-8-sig"
                        )

                        st.success(f"Bestätigung für {va_nummer} gespeichert.")
                    else:
                        st.error("Bitte Name eingeben.")

               # Fortschrittsbalken
try:
    if not os.path.exists("lesebestätigung.csv") or not os.path.exists("mitarbeiter.csv"):
        st.info("Noch keine Daten vorhanden.")
    else:
        # Dateien laden
        df_kenntnis = pd.read_csv("lesebestätigung.csv", sep=";", encoding="utf-8-sig", dtype=str)
        df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig", dtype=str)

        # Einheitliches Namensformat: "Vorname Name"
        if {"Name", "Vorname"}.issubset(df_mitarbeiter.columns):
            df_mitarbeiter["Name_full"] = df_mitarbeiter["Vorname"].str.strip() + " " + df_mitarbeiter["Name"].str.strip()
        else:
            st.warning("Spalten 'Name' und 'Vorname' fehlen in mitarbeiter.csv.")
            raise ValueError("Spalten fehlen")

        # Zielgruppe nach VA_Nr filtern
        if "VA_Nr" in df_mitarbeiter.columns:
            df_mitarbeiter["VA_norm"] = df_mitarbeiter["VA_Nr"].apply(norm_va)
            zielgruppe = df_mitarbeiter[df_mitarbeiter["VA_norm"] == va_nummer]["Name_full"].dropna().unique()
        else:
            zielgruppe = df_mitarbeiter["Name_full"].dropna().unique()

        gesamt = len(zielgruppe)

        # Lesebestätigungen nach VA_Nr filtern
        if "VA_Nr" in df_kenntnis.columns:
            df_kenntnis["VA_Nr_norm"] = df_kenntnis["VA_Nr"].apply(norm_va)
            gelesen = df_kenntnis[df_kenntnis["VA_Nr_norm"] == va_nummer]["Name"].dropna().unique()
        else:
            st.warning("Spalte 'VA_Nr' fehlt in lesebestätigung.csv.")
            raise ValueError("Spalte 'VA_Nr' fehlt")

        # Vergleich: beide im Format "Vorname Name"
        gelesen_set = set(gelesen)
        zielgruppe_set = set(zielgruppe)
        gelesen_count = len(gelesen_set & zielgruppe_set)
        fortschritt = gelesen_count / gesamt if gesamt > 0 else 0.0

        # Fortschrittsanzeige
        st.progress(fortschritt, text=f"{gelesen_count} von {gesamt} Mitarbeiter (gelesen)")

        # Optional: Liste der noch offenen Namen
        offen = zielgruppe_set - gelesen_set
        if offen:
            st.info("Noch nicht gelesen: " + ", ".join(sorted(offen)))

except Exception as e:
    st.warning(f"Fortschritt konnte nicht berechnet werden: {e}")
