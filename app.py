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
# Tab 1: Verfahrensanweisungen (Eingabe & Auswahl mit allen Feldern)
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")

    DATA_FILE_QM = "qm_verfahrensanweisungen.csv"

    # Eingabefelder (komplette Struktur)
    st.markdown("### Neue/aktualisierte VA eingeben")
    va_nr_input = st.text_input("VA-Nummer (z. B. VA004)", key="va_nr_input")
    titel_input = st.text_input("Titel", key="titel_input")
    kapitel_input = st.text_input("Kapitel", key="kapitel_input")
    unterkapitel_input = st.text_input("Unterkapitel", key="unterkapitel_input")
    revisionsstand_input = st.text_input("Revisionsstand", key="rev_input")
    ziel_input = st.text_input("Ziel", key="ziel_input")

    vorgehensweise_input = st.text_area("Vorgehensweise", key="vorgehensweise_input")
    kommentar_input = st.text_area("Kommentar", key="kommentar_input")
    mitgeltende_input = st.text_area("Mitgeltende Unterlagen", key="mitgeltende_input")

    # Speichern
    if st.button("VA speichern", key="save_va"):
        req_ok = all([
            va_nr_input.strip(),
            titel_input.strip(),
            kapitel_input.strip(),
            unterkapitel_input.strip(),
            revisionsstand_input.strip()
        ])
        if not req_ok:
            st.error("Bitte mindestens VA-Nummer, Titel, Kapitel, Unterkapitel und Revisionsstand ausfüllen.")
        else:
            try:
                neuer_eintrag = pd.DataFrame([{
                    "VA_Nr": va_nr_input.strip(),
                    "Titel": titel_input.strip(),
                    "Kapitel": kapitel_input.strip(),
                    "Unterkapitel": unterkapitel_input.strip(),
                    "Revisionsstand": revisionsstand_input.strip(),
                    "Ziel": ziel_input.strip(),
                    "Vorgehensweise": vorgehensweise_input.strip(),
                    "Kommentar": kommentar_input.strip(),
                    "Mitgeltende_Unterlagen": mitgeltende_input.strip()
                }])

                if os.path.exists(DATA_FILE_QM):
                    df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
                    df_va = pd.concat([df_va, neuer_eintrag], ignore_index=True)
                else:
                    df_va = neuer_eintrag

                df_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
                st.success(f"✅ VA {va_nr_input.strip()} gespeichert.")
            except Exception as e:
                st.error(f"Fehler beim Speichern: {e}")

    st.markdown("---")
    st.markdown("### Bestehende VA auswählen")

    try:
        if os.path.exists(DATA_FILE_QM):
            df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
            # Label: VA_Nr + Titel
            df_va["Label"] = df_va["VA_Nr"].astype(str) + " – " + df_va["Titel"].astype(str)

            sel = st.selectbox(
                "Dokument auswählen",
                options=df_va["Label"].tolist(),
                index=None,
                placeholder="Bitte wählen…"
            )
            if sel:
                va_nr = sel.split(" – ")[0]  # z. B. "VA004"
                st.session_state.selected_va = va_nr
                st.success(f"Ausgewählt: {sel}")

            # Übersichtstabelle aller VA
            st.markdown("#### Übersicht aller Verfahrensanweisungen")
            st.dataframe(
                df_va[
                    ["VA_Nr","Titel","Kapitel","Unterkapitel","Revisionsstand",
                     "Ziel","Vorgehensweise","Kommentar","Mitgeltende_Unterlagen"]
                ],
                use_container_width=True
            )
        else:
            st.info("Noch keine VA-Datei vorhanden. Bitte zuerst eine VA eingeben und speichern.")
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

        try:
            df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
            va_list = sorted(
                df_va["VA_Nr"].dropna().astype(str)
                .str.replace("VA", "", regex=False)
                .str.strip()
            )
            va_nummer = st.selectbox("VA auswählen", options=va_list, key="lese_va")
        except Exception:
            va_nummer = None
            st.warning("VA-Datei konnte nicht geladen werden.")

        if st.button("Bestätigen", key="lese_button"):
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

                st.success(f"Bestätigung für {va_nr_speichern} gespeichert.")

               
                # Optionaler Download-Button
            if st.checkbox("Eigenen Nachweis als CSV herunterladen"):
                csv_bytes = df_kenntnis.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                label="Diese Lesebestätigung herunterladen",
                data=csv_bytes,
                file_name=f"lesebestaetigung_{va_nr_speichern}_{dt.date.today()}.csv",
                mime="text/csv",
                type="primary"
    )

            else:
                st.error("Bitte Name und VA auswählen.")
    else:
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")

# --------------------------
# Übersicht der bisherigen Bestätigungen
# --------------------------
st.markdown("---")
st.markdown("### 📄 Bereits bestätigte Einträge")

if os.path.exists("lesebestätigung.csv"):
    try:
        df_kenntnis = pd.read_csv("lesebestätigung.csv", sep=";", encoding="utf-8-sig")
        df_kenntnis = df_kenntnis.sort_values("Zeitpunkt", ascending=False)
        st.dataframe(df_kenntnis)
    except Exception as e:
        st.error(f"Fehler beim Laden der Lesebestätigungen: {e}")
else:
    st.info("Noch keine Lesebestätigungen vorhanden.")

# --------------------------
# Tab 3: Mitarbeiterliste + Lesebestätigungen
# --------------------------
with tabs[3]:
    st.markdown("## 👥 Mitarbeiterliste verwalten")

    # Upload der Mitarbeiterliste
    uploaded_file = st.file_uploader("📄 mitarbeiter.csv hochladen", type=["csv"])

    if uploaded_file is not None:
        try:
            with open("mitarbeiter.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("✅ Datei 'mitarbeiter.csv' erfolgreich gespeichert.")

            df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")
            st.markdown("### Mitarbeiterliste:")
            st.dataframe(df_mitarbeiter)
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten der Datei: {e}")
    else:
        if os.path.exists("mitarbeiter.csv"):
            st.info("ℹ️ Es existiert bereits eine 'mitarbeiter.csv'.")
            try:
                df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")
                st.markdown("### Mitarbeiterliste:")
                st.dataframe(df_mitarbeiter)
            except Exception as e:
                st.error(f"Fehler beim Laden der vorhandenen Datei: {e}")
        else:
            st.warning("⚠️ Noch keine 'mitarbeiter.csv' vorhanden. Bitte hochladen.")

    # --------------------------
# Übersicht der Lesebestätigungen
# --------------------------
st.markdown("---")
st.markdown("## 📄 Aktuelle Lesebestätigungen")

if os.path.exists("lesebestätigung.csv"):
    try:
        df_kenntnis = pd.read_csv("lesebestätigung.csv", sep=";", encoding="utf-8-sig")
        # Sortiert nach Zeitpunkt, neueste oben
        st.dataframe(df_kenntnis.sort_values("Zeitpunkt", ascending=False))
    except Exception as e:
        st.error(f"Fehler beim Laden der Lesebestätigungen: {e}")
else:
    st.info("Noch keine Lesebestätigungen vorhanden.")

st.markdown("---")
st.markdown("### 🔄 Lesebestätigungen zurücksetzen")

if os.path.exists("lesebestätigung.csv"):
    if st.checkbox("Ich möchte alle Lesebestätigungen löschen"):
        if st.button("Jetzt zurücksetzen", type="primary"):
            try:
                # Datei leeren (nicht löschen, damit Struktur bleibt)
                with open("lesebestätigung.csv", "w", encoding="utf-8-sig") as f:
                    f.write("Name;VA_Nr;Zeitpunkt\n")
                st.success("✅ Alle Lesebestätigungen wurden zurückgesetzt.")
            except Exception as e:
                st.error(f"Fehler beim Zurücksetzen: {e}")


# --------------------------
# Sidebar: aktuelles Dokument + Fortschritt
# --------------------------
def norm_va(x):
    s = str(x).upper().replace(" ", "")
    m = s.replace("VA", "")
    if m.isdigit():
        s = f"VA{int(m):03d}"
    return s

with st.sidebar:
    # Login-Status
    if st.session_state.get("logged_in", False):
        st.success("✅ Eingeloggt")
        st.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    else:
        st.warning("Nicht eingeloggt")

    # Aktuelles Dokument + Fortschritt
    if st.session_state.get("selected_va"):
        va_current = norm_va(st.session_state.selected_va)

        # Titel der VA aus qm_verfahrensanweisungen.csv laden
        try:
            if os.path.exists("qm_verfahrensanweisungen.csv"):
                df_va = pd.read_csv("qm_verfahrensanweisungen.csv", sep=";", encoding="utf-8-sig", dtype=str)
                row = df_va[df_va["VA_Nr"].apply(norm_va) == va_current]
                if not row.empty:
                    titel = row["Titel"].values[0]
                    st.markdown(f"**Aktuelles Dokument:** {va_current} – {titel}")
                else:
                    st.markdown(f"**Aktuelles Dokument:** {va_current}")
            else:
                st.markdown(f"**Aktuelles Dokument:** {va_current}")
        except Exception as e:
            st.sidebar.warning(f"Titel konnte nicht geladen werden: {e}")
            st.markdown(f"**Aktuelles Dokument:** {va_current}")

        # Fortschritt berechnen
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
