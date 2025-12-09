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
import streamlit_authenticator as stauth   # <--- NEU

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

    for feld in QM_COLUMNS[1:]:
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
if "selected_va" not in st.session_state:
    st.session_state.selected_va = None
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

# --------------------------
# Authenticator Setup
# --------------------------
# Nutzer aus CSV laden
users_df = pd.read_csv(os.path.join("va_app", "users.csv"))
credentials = {"usernames": {}}
for _, row in users_df.iterrows():
    credentials["usernames"][row["username"]] = {
        "password": row["password"],
        "role": row["role"]
    }

authenticator = stauth.Authenticate(
    credentials,
    "va_app_cookie",
    "secret_key",
    cookie_expiry_days=30
)

# --------------------------
# Tabs
# --------------------------
tabs = st.tabs(["System & Login", "Verfahrensanweisungen", "Lesebestätigung", "Mitarbeiter"])

# --------------------------
# Tab 0: Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔒 Login")

    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = credentials["usernames"][username]["role"]
        st.success(f"✅ Eingeloggt als {username} ({st.session_state.role})")
    elif authentication_status is False:
        st.error("❌ Login fehlgeschlagen")
    else:
        st.info("Bitte einloggen")


# --------------------------
# Tab 1: Verfahrensanweisungen
# --------------------------
with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")

    DATA_FILE_QM = "qm_verfahrensanweisungen.csv"

    # Hilfsfunktion: Formular zurücksetzen
    def reset_form():
        for key in [
            "va_nr_input", "titel_input", "kapitel_input", "unterkapitel_input",
            "revisionsstand_input", "geltungsbereich_input", "ziel_input",
            "vorgehensweise_input", "kommentar_input", "mitgeltende_input"
        ]:
            st.session_state[key] = ""

    # Hilfsfunktion: sichere Texte für PDF (latin-1)
    def safe(text):
        return str(text).encode("latin-1", "replace").decode("latin-1")

    # PDF-Klasse mit Kopf- und Fußzeile
    class CustomPDF(FPDF):
        def header(self):
            self.set_font("Arial", size=9)
            self.cell(0, 10, safe("Pflegedienst: xy"), ln=0, align="L")
            self.cell(0, 10, safe(f"Verfahrensanweisung Pflege, Kap. {self.unterkapitel}"), ln=0, align="R")
            self.ln(15)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", size=8)
            self.cell(60, 10, safe(f"{self.va_nr} – {self.va_titel}"), ln=0)
            self.set_x((210 - 90) / 2)
            self.cell(90, 10, safe("Erstellt von: Peters, Michael – Qualitätsbeauftragter"), align="C")
            self.set_x(-30)
            self.cell(0, 10, f"Seite {self.page_no()}", align="R")

    # 📝 VA-Eingabe
    st.markdown("### 📝 Neue VA eingeben & speichern")
    va_nr_input = st.text_input("VA-Nummer", key="va_nr_input")
    titel_input = st.text_input("Titel", key="titel_input")
    kapitel_input = st.text_input("Kapitel", key="kapitel_input")
    unterkapitel_input = st.text_input("Unterkapitel", key="unterkapitel_input")
    revisionsstand_input = st.text_input("Revisionsstand", key="revisionsstand_input")
    geltungsbereich_input = st.text_input("Geltungsbereich", key="geltungsbereich_input")
    ziel_input = st.text_input("Ziel", key="ziel_input")
    vorgehensweise_input = st.text_area("Vorgehensweise", key="vorgehensweise_input")
    kommentar_input = st.text_area("Kommentar", key="kommentar_input")
    mitgeltende_input = st.text_area("Mitgeltende Unterlagen", key="mitgeltende_input")

    if st.button("VA speichern", key="va_speichern_button_tab1"):
        if all([va_nr_input.strip(), titel_input.strip(), kapitel_input.strip(), unterkapitel_input.strip()]):
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
            st.session_state.last_saved_va = va_nr_input.strip()
        else:
            st.error("Pflichtfelder fehlen.")

    # 📄 PDF erzeugen & manuell herunterladen
    st.markdown("### 📄 PDF erzeugen & herunterladen")
    if "last_saved_va" in st.session_state:
        df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
        match = df_va[df_va["VA_Nr"] == st.session_state.last_saved_va]

        if not match.empty:
            row = match.iloc[0]
            pdf = CustomPDF()
            pdf.va_nr = row["VA_Nr"]
            pdf.va_titel = row["Titel"]
            pdf.unterkapitel = row["Unterkapitel"]
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.set_left_margin(10)
            pdf.set_right_margin(10)

            for field in ["VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand", "Geltungsbereich"]:
                pdf.cell(0, 10, txt=f"{field}: {safe(row[field])}", ln=True)

            for block in ["Ziel", "Vorgehensweise", "Kommentar", "Mitgeltende_Unterlagen"]:
                pdf.ln(5)
                pdf.set_font("Arial", style="B", size=12)
                pdf.cell(0, 10, f"{block}:", ln=True)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 8, safe(row[block]))

            buffer = io.BytesIO()
            pdf.output(buffer)
            pdf_bytes = buffer.getvalue()

            st.download_button(
                label=f"📄 PDF herunterladen: {row['VA_Nr']}",
                data=pdf_bytes,
                file_name=f"{row['VA_Nr'].replace(' ', '')}.pdf",
                mime="application/pdf",
                key="pdf_download_tab1"
            )
        else:
            st.error("❌ VA konnte nicht gefunden werden – PDF-Erzeugung abgebrochen.")

    # 🔵 VA-Auswahl & Löschung
    st.markdown("### 🔵 VA auswählen & löschen")
    if os.path.exists(DATA_FILE_QM):
        df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
        df_va["Label"] = df_va["VA_Nr"] + " – " + df_va["Titel"]

        # Auswahlfeld zur Anzeige
        sel = st.selectbox("Dokument auswählen", df_va["Label"].tolist(), index=None, key="va_anzeige_select_tab1")
        if sel:
            va_id = sel.split(" – ")[0]
            df_va_sel = df_va[df_va["VA_Nr"] == va_id]
            if not df_va_sel.empty:
                row = df_va_sel.iloc[0]
                st.markdown("### Aktuelles Dokument")
                st.write(f"{row['VA_Nr']} – {row['Titel']}")
                st.write(f"Kapitel: {row['Kapitel']}, Unterkapitel: {row['Unterkapitel']}")
                st.write(f"Revisionsstand: {row['Revisionsstand']}")
                st.write(f"Geltungsbereich: {row['Geltungsbereich']}")
                st.write(f"Ziel: {row['Ziel']}")
                st.write(f"Vorgehensweise: {row['Vorgehensweise']}")
                st.write(f"Kommentar: {row['Kommentar']}")
                st.write(f"Mitgeltende Unterlagen: {row['Mitgeltende_Unterlagen']}")

        # Auswahlfeld zum Löschen
        sel_del = st.selectbox("VA auswählen zum Löschen", df_va["Label"].tolist(), index=None, key="va_loeschen_select_tab1")
        if sel_del and st.button("VA löschen", key="va_loeschen_button_tab1"):
            va_id_del = sel_del.split(" – ")[0]
            df_va = df_va[df_va["VA_Nr"] != va_id_del]
            df_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"❌ VA {va_id_del} wurde gelöscht.")

    # 🔁 Reset-Button immer sichtbar
    if st.button("Formular zurücksetzen", key="reset_tab1"):
        reset_form()
        st.info("Formular wurde geleert.")
# --------------------------
# Tab 2: Lesebestätigung (nur CSV-Download)
# --------------------------
with tabs[2]:
    st.markdown("## ✅ Lesebestätigung")

    if not st.session_state.get("logged_in", False):
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
    else:
        path_all = "lesebestätigung.csv"
        if not os.path.exists(path_all) or os.path.getsize(path_all) == 0:
            st.info("Noch keine Lesebestätigungen vorhanden.")
        else:
            df_all = pd.read_csv(path_all, sep=";", encoding="utf-8-sig", dtype=str)

            st.markdown("### 📄 Bereits bestätigte Einträge")
            st.dataframe(df_all.sort_values("Zeitpunkt", ascending=False))

            # Sammel-CSV Download
            st.markdown("---")
            st.markdown("### 📥 Sammel-CSV herunterladen")
            csv_str = df_all[["Name", "VA_Nr", "Zeitpunkt"]].to_csv(index=False, sep=";", encoding="utf-8-sig")
            csv_bytes = csv_str.encode("utf-8-sig")

            st.download_button(
                label="📥 Sammel-CSV herunterladen",
                data=csv_bytes,
                file_name="sammeldatei.csv",
                mime="text/csv",
                key="tab2_csv_download"
            )


          
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
# Sidebar: VA-Inhalte + PDF + Lesebestätigung + Fortschritt
# --------------------------
import pathlib

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
                titel = row["Titel"].values[0] if "Titel" in row.columns else ""
                kapitel = row["Kapitel"].values[0] if "Kapitel" in row.columns else ""
                unterkapitel = row["Unterkapitel"].values[0] if "Unterkapitel" in row.columns else ""
                revision = row["Revisionsstand"].values[0] if "Revisionsstand" in row.columns else ""
                geltung = row["Geltungsbereich"].values[0] if "Geltungsbereich" in row.columns else ""
                ziel = row["Ziel"].values[0] if "Ziel" in row.columns else ""
                vorgang = row["Vorgehensweise"].values[0] if "Vorgehensweise" in row.columns else ""
                kommentar = row["Kommentar"].values[0] if "Kommentar" in row.columns else ""
                unterlagen = row["Mitgeltende Unterlagen"].values[0] if "Mitgeltende Unterlagen" in row.columns else ""

                st.markdown(
                    f"""
                    <div style="background-color:#fff3cd;
                                padding:10px;
                                border-radius:5px;
                                border:1px solid #ffeeba;
                                margin-top:10px;
                                font-size:14px">
                    <strong>VA-Inhalt:</strong><br><br>
                    <strong>VA-Nr:</strong> {va_nummer}<br>
                    <strong>Titel:</strong> {titel}<br>
                    <strong>Kapitel:</strong> {kapitel}<br>
                    <strong>Unterkapitel:</strong> {unterkapitel}<br>
                    <strong>Revisionsstand:</strong> {revision}<br>
                    <strong>Geltungsbereich:</strong> {geltung}<br>
                    <strong>Ziel:</strong> {ziel}<br>
                    <strong>Vorgehensweise:</strong> {vorgang}<br>
                    <strong>Kommentar:</strong> {kommentar}<br>
                    <strong>Mitgeltende Unterlagen:</strong> {unterlagen}
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

            # Lesebestätigung
            st.markdown("### Lesebestätigung")
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

            # Fortschritt
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
                        zielgruppe = df_mitarbeiter[df_mitarbeiter["VA_norm"] == va_nummer]["Name_full"].dropna().unique()
                    else:
                        zielgruppe = df_mitarbeiter["Name_full"].dropna().unique()

                    gesamt = len(zielgruppe)

                    if "VA_Nr" in df_kenntnis.columns:
                        df_kenntnis["VA_Nr_norm"] = df_kenntnis["VA_Nr"].apply(norm_va)
                        gelesen = df_kenntnis[df_kenntnis["VA_Nr_norm"] == va_nummer]["Name"].dropna().unique()
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






