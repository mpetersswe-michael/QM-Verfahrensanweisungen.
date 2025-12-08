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
    pdf.va_name = f"VA {row.get('VA_Nr', '')}"
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Titel
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text(f"QM-Verfahrensanweisung - {row.get('VA_Nr', '')}"), ln=True, align="C")
    pdf.ln(5)

    # Abschnittshelfer
    def add_section(title, content):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, clean_text(title), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, clean_text(content))
        pdf.ln(3)

    # Inhalte aus QM_COLUMNS (Index 1: ohne VA_Nr)
    for feld in QM_COLUMNS[1:]:
        add_section(feld, row.get(feld, ""))

    # Bytes erzeugen
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    # Datei im Ordner va_pdf speichern
    va_nr = norm_va(row.get("VA_Nr", "VA000"))
    pdf_path = f"va_pdf/{va_nr}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Bytes zurückgeben (für Download-Button etc.)
    return pdf_bytes, pdf_path


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
# Tab 0: Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔒 Login")

    if not st.session_state.get("logged_in", False):
        pw = st.text_input("Passwort", type="password", key="login_pw")
        if st.button("Login", key="login_button"):
            if pw == "qm2025":
                st.session_state.logged_in = True
                st.success("✅ Login erfolgreich.")
            else:
                st.error("❌ Passwort falsch.")
    else:
        st.info("Du bist bereits eingeloggt. Logout über die Sidebar.")

# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")

    DATA_FILE_QM = "qm_verfahrensanweisungen.csv"

    # Eingabe nur hier im Tab
    st.markdown("### Neue VA eingeben")
    va_nr_input = st.text_input("VA-Nummer", key="va_nr_input")
    titel_input = st.text_input("Titel", key="titel_input")
    kapitel_input = st.text_input("Kapitel", key="kapitel_input")
    unterkapitel_input = st.text_input("Unterkapitel", key="unterkapitel_input")
    revisionsstand_input = st.text_input("Revisionsstand", key="revisionsstand_input")
    geltungsbereich_input = st.text_input("Geltungsbereich", key="geltungsbereich_input")  # NEU
    ziel_input = st.text_input("Ziel", key="ziel_input")
    vorgehensweise_input = st.text_area("Vorgehensweise", key="vorgehensweise_input")
    kommentar_input = st.text_area("Kommentar", key="kommentar_input")
    mitgeltende_input = st.text_area("Mitgeltende Unterlagen", key="mitgeltende_input")

    if st.button("VA speichern", key="tab_va_speichern"):
        if all([
            va_nr_input.strip(),
            titel_input.strip(),
            kapitel_input.strip(),
            unterkapitel_input.strip(),
            revisionsstand_input.strip(),
            geltungsbereich_input.strip()
        ]):
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
                "Mitgeltende_Unterlagen": mitgeltende_input.strip()
            }])

            if os.path.exists(DATA_FILE_QM):
                df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
                df_va = pd.concat([df_va, neuer_eintrag], ignore_index=True)
            else:
                df_va = neuer_eintrag

            df_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"✅ VA {va_nr_input} gespeichert.")
        else:
            st.error("Pflichtfelder fehlen.")



    # Auswahl
    st.markdown("---")
    st.markdown("### VA auswählen")
    if os.path.exists(DATA_FILE_QM):
        df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
        df_va["Label"] = df_va["VA_Nr"] + " – " + df_va["Titel"]
        sel = st.selectbox("Dokument auswählen", df_va["Label"].tolist(), index=None)
        if sel:
            st.session_state.selected_va = sel.split(" – ")[0]
            st.success(f"Ausgewählt: {sel}")


# --------------------------
# Tab 2: Lesebestätigung (final)
# --------------------------
with tabs[2]:
    st.markdown("## ✅ Lesebestätigung")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
    else:
        # VA-Liste für Auswahl
        va_liste = []
        if os.path.exists("qm_verfahrensanweisungen.csv"):
            df_va = pd.read_csv("qm_verfahrensanweisungen.csv", sep=";", encoding="utf-8-sig", dtype=str)
            if "VA_Nr" in df_va.columns:
                df_va["VA_clean"] = df_va["VA_Nr"].apply(norm_va)
                va_liste = sorted(df_va["VA_clean"].unique())

        # Eingaben
        name_raw = st.text_input("Name (Nachname, Vorname)")
        va_nummer = st.selectbox("VA auswählen", options=va_liste, index=None)

        # Sidebar-Sync
        if va_nummer:
            st.session_state.selected_va = va_nummer

        # Bestätigen
        if st.button("Bestätigen", key="confirm_tab2"):
            name_kombi = re.sub(r"\s*,\s*", ",", name_raw.strip())
            if name_kombi and va_nummer:
                zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
                eintrag = {"Name": name_kombi, "VA_Nr": va_nummer, "Zeitpunkt": zeitpunkt}
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

                # Optionaler CSV-Download
                if st.checkbox("Eigenen Nachweis als CSV herunterladen"):
                    csv_bytes = df_new.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
                    st.download_button(
                        "Diese Lesebestätigung herunterladen",
                        data=csv_bytes,
                        file_name=f"lesebestaetigung_{va_nummer}_{dt.date.today()}.csv",
                        mime="text/csv",
                        key="download_tab2"
                    )
            else:
                st.error("Bitte Name und VA auswählen.")

        # Tabelle: bereits bestätigte Einträge
        st.markdown("---")
        st.markdown("### 📄 Bereits bestätigte Einträge")
        path_all = "lesebestätigung.csv"
        if os.path.exists(path_all):
            df_alle = pd.read_csv(path_all, sep=";", encoding="utf-8-sig")
            st.dataframe(df_alle.sort_values("Zeitpunkt", ascending=False))
        else:
            st.info("Noch keine Lesebestätigungen vorhanden.")
       
# --------------------------
# Tab 3: Mitarbeiter
# --------------------------
with tabs[3]:
    st.markdown("## 👥 Mitarbeiterverwaltung")

    DATA_FILE_MA = "mitarbeiter.csv"

    # Drag & Drop Upload
    uploaded_file = st.file_uploader("Mitarbeiterliste hochladen (CSV)", type=["csv"], key="upload_mitarbeiter")

    if uploaded_file is not None:
        try:
            df_ma = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", dtype=str)
            df_ma.to_csv(DATA_FILE_MA, sep=";", index=False, encoding="utf-8-sig")
            st.success("✅ Mitarbeiterliste erfolgreich hochgeladen und gespeichert.")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")

    # Reset-Funktion
    if st.button("Mitarbeiterliste zurücksetzen", key="reset_mitarbeiter"):
        if os.path.exists(DATA_FILE_MA):
            os.remove(DATA_FILE_MA)
            st.warning("⚠️ Mitarbeiterliste wurde zurückgesetzt (Datei gelöscht).")
        else:
            st.info("Keine Mitarbeiterliste vorhanden, nichts zu löschen.")

    # Anzeige der aktuellen Mitarbeiterliste
    if os.path.exists(DATA_FILE_MA):
        st.markdown("### Aktuelle Mitarbeiterliste")
        df_ma = pd.read_csv(DATA_FILE_MA, sep=";", encoding="utf-8-sig", dtype=str)
        st.dataframe(df_ma)
    else:
        st.info("Noch keine Mitarbeiterliste vorhanden.")



# --------------------------
# Sidebar: Fortschritt + Lesebestätigung
# --------------------------
with st.sidebar:
    # Login-Status
    if st.session_state.get("logged_in", False):
        st.success("✅ Eingeloggt")
        if st.button("Logout", key="logout_sidebar"):
            st.session_state.logged_in = False
            st.session_state.selected_va = None  # optional: VA-Auswahl zurücksetzen

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
            va_current = norm_va(va_nummer)
            row = df_va[df_va["VA_clean"] == va_current]
            titel = row["Titel"].values[0] if not row.empty else ""

            # 🔔 Gelber Hinweis
            st.markdown(
                f"""
                <div style="background-color:#fff3cd;
                            padding:10px;
                            border-radius:5px;
                            border:1px solid #ffeeba;
                            margin-bottom:10px">
                <strong>Aktuelles Dokument:</strong><br>{va_current} – {titel}
                </div>
                """,
                unsafe_allow_html=True
            )

            # 📄 PDF aus Ordner va_pdf laden und anzeigen
            pdf_path = f"va_pdf/{va_current}.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label=f"📄 PDF öffnen: {va_current}",
                    data=pdf_bytes,
                    file_name=f"{va_current}.pdf",
                    mime="application/pdf",
                    key=f"download_{va_current}"
                )
            else:
                st.info("PDF noch nicht vorhanden – bitte zuerst erzeugen.")

            # Lesebestätigung
            st.markdown("### Lesebestätigung")
            name_sidebar = st.text_input("Name (Nachname, Vorname)", key="sidebar_name_input")
            if st.button("Bestätigen", key="sidebar_confirm_button"):
                name_clean = re.sub(r"\s*,\s*", ",", name_sidebar.strip())
                if name_clean:
                    zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
                    eintrag = {"Name": name_clean, "VA_Nr": va_current, "Zeitpunkt": zeitpunkt}
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

                    st.success(f"Bestätigung für {va_current} gespeichert.")
                else:
                    st.error("Bitte Name eingeben.")

            # Fortschritt anzeigen
            try:
                if not os.path.exists("lesebestätigung.csv") or not os.path.exists("mitarbeiter.csv"):
                    st.info("Noch keine Daten vorhanden.")
                else:
                    df_kenntnis = pd.read_csv("lesebestätigung.csv", sep=";", encoding="utf-8-sig", dtype=str)
                    df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig", dtype=str)

                    if {"Name", "Vorname"}.issubset(df_mitarbeiter.columns):
                        df_mitarbeiter["Name_full"] = df_mitarbeiter["Name"].str.strip() + "," + df_mitarbeiter["Vorname"].str.strip()
                    else:
                        st.warning("Spalten 'Name' und 'Vorname' fehlen in mitarbeiter.csv.")
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
                        st.warning("Spalte 'VA_Nr' fehlt in lesebestätigung.csv.")
                        raise ValueError("Spalte 'VA_Nr' fehlt")

                    gelesen_count = len(set(gelesen) & set(zielgruppe))
                    fortschritt = gelesen_count / gesamt if gesamt > 0 else 0.0

                    st.progress(fortschritt, text=f"{gelesen_count} von {gesamt} Mitarbeiter (gelesen)")
            except Exception as e:
                st.warning(f"Fortschritt konnte nicht berechnet werden: {e}")
    else:
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
