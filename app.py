# --------------------------
# Imports
# --------------------------
import os
import re
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from fpdf import FPDF


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
QM_COLUMNS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
    "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]

# --------------------------
# PDF-Hilfsfunktionen
# --------------------------
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
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        va_name = getattr(self, "va_name", "")
        self.cell(60, 10, clean_text(va_name), align="L")
        text = f"Erstellt von Peters, Michael - Qualitaetsbeauftragter am {dt.date.today().strftime('%d.%m.%Y')}"
        self.cell(70, 10, clean_text(text), align="C")
        page_text = f"Seite {self.page_no()} von {{nb}}"
        self.cell(0, 10, clean_text(page_text), align="R")

def export_va_to_pdf(row):
    pdf = CustomPDF()
    pdf.alias_nb_pages()
    pdf.va_name = f"VA {row.get('VA_Nr','')}"
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text(f"QM-Verfahrensanweisung - {row.get('VA_Nr','')}"), ln=True, align="C")
    pdf.ln(5)

    def add_section(title, content):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, clean_text(title), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, clean_text(content))
        pdf.ln(3)

    for feld in QM_COLUMNS[1:]:
        add_section(feld, row.get(feld, ""))

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

# --------------------------
# Session-Init
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "selected_va" not in st.session_state:
    st.session_state.selected_va = None

# --------------------------
# Tabs
# --------------------------
tabs = st.tabs(["System & Login", "Verfahrensanweisungen", "Lesebestätigung", "Mitarbeiter"])

# --------------------------
# Tab 0: System & Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔐 Login")
    if not st.session_state.get("logged_in", False):
        password = st.text_input("Passwort", type="password")
        if st.button("Login", key="login_button", type="primary"):
            if password == "qm2025":
                st.session_state.logged_in = True
                st.success("Login erfolgreich!")
            else:
                st.error("Falsches Passwort.")
    else:
        st.sidebar.success("Eingeloggt")
        if st.sidebar.button("Logout", key="sidebar_logout"):
            st.session_state.logged_in = False
            st.session_state.selected_va = None
            st.sidebar.info("Logout erfolgreich.")

# --------------------------
# Tab 1: Verfahrensanweisungen (VA-Auswahl)
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")
    try:
        df_va = pd.read_csv("qm_verfahrensanweisungen.csv", sep=";", encoding="utf-8-sig", dtype=str)
        # Anzeige mit Text, aber Speicherung nur VA-Nr
        options = (
            df_va.dropna(subset=["VA_Nr"])
                 .assign(Label=lambda d: d["VA_Nr"].astype(str) + " – " + d["Titel"].astype(str))
        )
        sel = st.selectbox(
            "Dokument auswählen",
            options=options["Label"].tolist(),
            index=None,
            placeholder="Bitte wählen…"
        )
        if sel:
            va_nr = sel.split(" – ")[0]  # z. B. "VA004"
            st.session_state.selected_va = va_nr  # Sidebar bekommt die reine VA-Nummer
            st.success(f"Ausgewählt: {sel}")
    except Exception as e:
        st.warning(f"VA-Datei konnte nicht geladen werden: {e}")

# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
with tabs[2]:
    if st.session_state.get("logged_in", False):
        st.markdown("## ✅ Lesebestätigung")
        st.markdown("Bitte bestätigen Sie, dass Sie die ausgewählte VA gelesen haben.")

        name_raw = st.text_input("Name (Nachname,Vorname)", key="lese_name")

        # VA-Auswahl ohne Text (nur Nummern)
        try:
            df_va = pd.read_csv("qm_verfahrensanweisungen.csv", sep=";", encoding="utf-8-sig", dtype=str)
            va_list = sorted(
                df_va["VA_Nr"].dropna().astype(str).str.replace("VA", "", regex=False).str.strip()
            )
            va_nummer = st.selectbox("VA auswählen", options=va_list, key="lese_va")
        except Exception:
            va_nummer = None
            st.warning("VA-Datei konnte nicht geladen werden.")

        if st.button("Bestätigen & CSV herunterladen", key="lese_button"):
            name_kombi = re.sub(r"\s*,\s*", ",", name_raw.strip())
            if name_kombi and va_nummer:
                zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
                va_nr_speichern = f"VA{va_nummer}"

                eintrag = {"Name": name_kombi, "VA_Nr": va_nr_speichern, "Zeitpunkt": zeitpunkt}
                df_kenntnis = pd.DataFrame([eintrag])[["Name", "VA_Nr", "Zeitpunkt"]]

                DATA_FILE_KENNTNIS = "lesebestätigung.csv"
                file_exists = os.path.exists(DATA_FILE_KENNTNIS)
                file_empty = (not file_exists) or (os.path.getsize(DATA_FILE_KENNTNIS) == 0)

                df_kenntnis.to_csv(
                    DATA_FILE_KENNTNIS,
                    sep=";",
                    index=False,
                    mode="a" if file_exists and not file_empty else "w",
                    header=True if file_empty else False,
                    encoding="utf-8-sig"
                )

                # Eindeutiger Download-Name
                zeitstempel = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d_%H-%M-%S")
                csv_bytes = df_kenntnis.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    label="Diese Lesebestätigung als CSV herunterladen",
                    data=csv_bytes,
                    file_name=f"lesebestaetigung_{va_nr_speichern}_{zeitstempel}.csv",
                    mime="text/csv",
                    type="primary"
                )

                st.success(f"Bestätigung für {va_nr_speichern} gespeichert.")
            else:
                st.error("Bitte Name und VA auswählen.")
    else:
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")

# --------------------------
# Tab 3: Mitarbeiterliste (Upload)
# --------------------------
with tabs[3]:
    st.markdown("## 👥 Mitarbeiterliste verwalten")
    uploaded_file = st.file_uploader("📄 mitarbeiter.csv hochladen", type=["csv"])

    if uploaded_file is not None:
        try:
            with open("mitarbeiter.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("✅ Datei 'mitarbeiter.csv' erfolgreich gespeichert.")

            df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")
            st.markdown("### Vorschau der geladenen Mitarbeiter:")
            st.dataframe(df_mitarbeiter)
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten der Datei: {e}")
    else:
        if os.path.exists("mitarbeiter.csv"):
            st.info("ℹ️ Es existiert bereits eine 'mitarbeiter.csv'.")
            try:
                df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")
                st.markdown("### Vorschau der aktuellen Mitarbeiterliste:")
                st.dataframe(df_mitarbeiter)
            except Exception as e:
                st.error(f"Fehler beim Laden der vorhandenen Datei: {e}")
        else:
            st.warning("⚠️ Noch keine 'mitarbeiter.csv' vorhanden. Bitte hochladen.")

# --------------------------
# Sidebar: aktuelles Dokument + Fortschritt
# --------------------------
def norm_va(x):
    s = str(x).upper().replace(" ", "")
    m = s.replace("VA", "")
    if m.isdigit():
        s = f"VA{int(m):03d}"
    return s

if st.session_state.selected_va:
    st.sidebar.markdown(f"**Aktuelles Dokument:** {st.session_state.selected_va}")
    try:
        if not os.path.exists("mitarbeiter.csv"):
            st.sidebar.warning("Die Datei 'mitarbeiter.csv' fehlt. Bitte im Tab 'Mitarbeiter' hochladen.")
            raise FileNotFoundError("mitarbeiter.csv fehlt")

        df_kenntnis = pd.read_csv("lesebestätigung.csv", sep=";", encoding="utf-8-sig")
        df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")

        # Namen vereinheitlichen: Nachname,Vorname
        if {"Vorname", "Name"}.issubset(df_mitarbeiter.columns):
            df_mitarbeiter["Name_full"] = (
                df_mitarbeiter["Name"].astype(str).str.strip() + "," +
                df_mitarbeiter["Vorname"].astype(str).str.strip()
            )
        else:
            st.sidebar.warning("Spalten 'Vorname' und 'Name' fehlen in mitarbeiter.csv.")
            raise ValueError("Spalten fehlen")

        va_current = norm_va(st.session_state.selected_va)
        if "VA_Nr" in df_mitarbeiter.columns:
            df_mitarbeiter["VA_norm"] = df_mitarbeiter["VA_Nr"].apply(norm_va)
            zielgruppe = df_mitarbeiter[df_mitarbeiter["VA_norm"] == va_current]["Name_full"].dropna().unique()
        else:
            zielgruppe = df_mitarbeiter["Name_full"].dropna().unique()

        gesamt = len(zielgruppe)

        if "VA_Nr" in df_kenntnis.columns:
            df_kenntnis["VA_Nr_norm"] = df_kenntnis["VA_Nr"].apply(norm_va)
            gelesen = df_kenntnis[df_kenntnis["VA_Nr_norm"] == va_current]["Name"].dropna().unique()
        else:
            st.sidebar.warning("Spalte 'VA_Nr' fehlt in lesebestätigung.csv.")
            raise ValueError("Spalte 'VA_Nr' fehlt")

        gelesen_count = len(set(gelesen) & set(zielgruppe))
        fortschritt = (gelesen_count / gesamt) if gesamt > 0 else 0.0
        st.sidebar.progress(fortschritt, text=f"{gelesen_count} von {gesamt} Mitarbeiter (gelesen)")
    except Exception as e:
        st.sidebar.warning(f"Fortschritt konnte nicht berechnet werden: {e}")
else:
    st.sidebar.info("Noch kein Dokument ausgewählt.")
