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
tabs = st.tabs(["System & Login", "Verfahrensanweisungen", "Lesebestätigung", "Mitarbeiter"])

# Prüfung der Benutzerdatei users.csv
def check_users_csv():
    path = "users.csv"
    if not os.path.exists(path):
        st.error("❌ Datei 'users.csv' wurde nicht gefunden.")
        return False

    try:
        df = pd.read_csv(path, sep=";", dtype=str)
        expected_cols = {"username", "password", "role"}
        actual_cols = set(df.columns.str.strip().str.lower())
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
# Tab 0: Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔒 Login")

    if not st.session_state.get("logged_in", False):
        input_user = st.text_input("Benutzername")
        input_pass = st.text_input("Passwort", type="password")
        if st.button("Login"):
            try:
                users_df = pd.read_csv("users.csv", sep=";", dtype=str)

                match = users_df[
                    (users_df["username"] == input_user) &
                    (users_df["password"] == input_pass)
                ]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = input_user
                    st.session_state.role = match.iloc[0]["role"]
                    st.success(f"✅ Eingeloggt als {input_user} (Rolle: {st.session_state.role})")
                    st.experimental_rerun()   # <- sorgt dafür, dass die Seite sofort neu gerendert wird
                else:
                    st.error("❌ Login fehlgeschlagen.")
            except Exception as e:
                st.error(f"Fehler beim Einlesen der Benutzerdatei: {e}")

    else:
        st.info("Du bist bereits eingeloggt. Logout über die Sidebar.")

        # Vorschau nur für Admins sichtbar
        if st.session_state.get("role") == "admin":
            st.markdown("### 👥 Benutzerdatei-Vorschau (`users.csv`)")
            try:
                users_df = pd.read_csv("users.csv", sep=";", dtype=str)
                st.dataframe(users_df)
            except Exception as e:
                st.error(f"Fehler beim Laden der Benutzerdatei: {e}")





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
# Sidebar
# --------------------------


with st.sidebar:
    if st.session_state.get("logged_in", False):
        st.success("✅ Eingeloggt")

        # Logout
        if st.button("Logout", key="logout_sidebar"):
            st.session_state.logged_in = False
            st.session_state.selected_va = None
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
                # Alle Inhalte der VA zusammenstellen
                va_text = f"""
                <strong>VA-Nr:</strong> {va_nummer}<br>
                <strong>Titel:</strong> {row['Titel'].values[0]}<br>
                <strong>Kapitel:</strong> {row['Kapitel'].values[0]}<br>
                <strong>Unterkapitel:</strong> {row['Unterkapitel'].values[0]}<br>
                <strong>Revisionsstand:</strong> {row['Revisionsstand'].values[0]}<br>
                <strong>Geltungsbereich:</strong> {row['Geltungsbereich'].values[0]}<br>
                <strong>Ziel:</strong> {row['Ziel'].values[0]}<br>
                <strong>Vorgehensweise:</strong> {row['Vorgehensweise'].values[0]}<br>
                <strong>Kommentar:</strong> {row['Kommentar'].values[0]}<br>
                <strong>Mitgeltende Unterlagen:</strong> {row['Mitgeltende Unterlagen'].values[0]}
                """

                # Gelber Hintergrund für den gesamten Block
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

                # PDF-Button nur anzeigen, wenn Datei existiert
                pdf_name = f"{norm_va(va_nummer)}.pdf"
                pdf_path = pathlib.Path("va_pdf") / pdf_name
                if pdf_path.exists():
                    st.markdown("### 📘 Verfahrensanweisung als PDF")
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label=f"📄 PDF öffnen: {pdf_name}",
                            data=f.read(),
                            file_name=pdf_name,
                            mime="application/pdf",
                            key=f"download_{pdf_name}"
                        )
    else:
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
