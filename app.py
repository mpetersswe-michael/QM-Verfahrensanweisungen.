import streamlit as st
import pandas as pd
import datetime as dt
import io
import os
from fpdf import FPDF

# -----------------------------------
# Konfiguration
# -----------------------------------
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
DATA_FILE_KENNTNIS = "kenntnisnahmen.csv"
QM_COLUMNS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
    "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]

# -----------------------------------
# App-Titel (dezent)
# -----------------------------------
st.set_page_config(page_title="Verfahrensanweisungen (Auszug aus dem QMH)")
st.markdown(
    "<h5 style='text-align:center; color:#444;'>Verfahrensanweisungen (Auszug aus dem QMH)</h5>",
    unsafe_allow_html=True
)

# -----------------------------------
# Login
# -----------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("## Login")
    st.markdown(
        "<div style='background-color:#fff9c4; padding:20px; border-radius:8px;'>"
        "<h4 style='text-align:center; margin:0;'>Bitte Passwort eingeben</h4></div>",
        unsafe_allow_html=True
    )
    password = st.text_input("Passwort", type="password")
    if st.button("Login", type="primary"):
        if password == "qm2025":
            st.session_state.logged_in = True
            st.success("Login erfolgreich!")
        else:
            st.error("Falsches Passwort.")
else:
    st.sidebar.success("Eingeloggt")
    if st.sidebar.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.sidebar.info("Logout erfolgreich.")

# -----------------------------------
# PDF-Hilfsfunktionen
# -----------------------------------
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

    for feld in ["Titel", "Kapitel", "Unterkapitel", "Revisionsstand", "Ziel",
                 "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"]:
        add_section(feld, row.get(feld, ""))

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

# -----------------------------------
# Eingabe + Anzeige/Export (nur wenn eingeloggt)
# -----------------------------------
if st.session_state.logged_in:
    # -----------------------------
    # Eingabeformular (Append-only)
    # -----------------------------
    st.markdown("## Neue Verfahrensanweisung eingeben")

    # Numerische Auswahl für Kapitel/Unterkapitel
    kapitel_nr = st.selectbox("Kapitel-Nr", options=list(range(1, 21)), index=0)
    unterkap_nr = st.selectbox("Unterkapitel-Nr", options=list(range(1, 21)), index=0)

    # Ableitung Felder
    va_nr = st.text_input("VA-Nr").strip()
    titel = st.text_input("Titel")
    kapitel = str(kapitel_nr)  # bewusst numerisch als String
    unterkapitel = f"Kap. {kapitel_nr}-{unterkap_nr}"  # garantiertes Format "Kap. X-Y"
    revisionsstand = st.text_input("Revisionsstand")
    ziel = st.text_area("Ziel")
    geltungsbereich = st.text_area("Geltungsbereich")
    vorgehensweise = st.text_area("Vorgehensweise")
    kommentar = st.text_area("Kommentar")
    mitgeltende_unterlagen = st.text_area("Mitgeltende Unterlagen")

    if st.button("Speichern (Append-only)", type="primary"):
        # neuer Eintrag in definierter Spaltenreihenfolge
        neuer_eintrag = {
            "VA_Nr": va_nr,
            "Titel": titel,
            "Kapitel": kapitel,
            "Unterkapitel": unterkapitel,
            "Revisionsstand": revisionsstand,
            "Ziel": ziel,
            "Geltungsbereich": geltungsbereich,
            "Vorgehensweise": vorgehensweise,
            "Kommentar": kommentar,
            "Mitgeltende Unterlagen": mitgeltende_unterlagen
        }
        df_neu = pd.DataFrame([neuer_eintrag]).reindex(columns=QM_COLUMNS)

        # Anhängen nur, wenn VA_Nr noch nicht existiert
        if os.path.exists(DATA_FILE_QM):
            try:
                df_alt = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
            except Exception:
                df_alt = pd.DataFrame(columns=QM_COLUMNS)

            if not df_alt.empty and df_alt["VA_Nr"].astype(str).str.strip().eq(va_nr).any():
                st.error(f"VA {va_nr} existiert bereits. Append-only: kein Überschreiben, bitte neue VA-Nr wählen.")
            else:
                df_neu.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig",
                              mode="a", header=not os.path.exists(DATA_FILE_QM) or os.path.getsize(DATA_FILE_QM) == 0)
                st.success(f"VA {va_nr} hinzugefügt (Append-only).")
        else:
            # Erste Speicherung mit Kopfzeile
            df_neu.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"VA {va_nr} gespeichert (neue Datei erstellt, Append-only).")

    # -----------------------------
    # Verwaltung/Anzeige
    # -----------------------------
    st.markdown("## Verfahrensanweisungen anzeigen und exportieren")
    try:
        df_all = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
    except Exception:
        df_all = pd.DataFrame(columns=QM_COLUMNS)

    if df_all.empty:
        st.info("Noch keine Verfahrensanweisungen gespeichert.")
    else:
        # Anzeigeauswahl „VA-Nr – Titel“
        df_all["VA_Anzeige"] = df_all["VA_Nr"].astype(str).str.strip() + " – " + df_all["Titel"].astype(str).str.strip()
        selected_va_display = st.selectbox(
            "VA auswählen zur Anzeige oder PDF-Erzeugung",
            options=[""] + sorted(df_all["VA_Anzeige"].dropna().unique()),
            index=0
        )
        selected_va = selected_va_display.split(" – ")[0] if selected_va_display else ""

        # Tabelle (gefiltert oder komplett)
        df_filtered = df_all[df_all["VA_Nr"].astype(str).str.strip() == selected_va] if selected_va else df_all
        st.dataframe(df_filtered, use_container_width=True)

        # CSV-Download (immer gesamte Tabelle)
        csv_data = df_all.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="CSV herunterladen",
            data=csv_data,
            file_name=f"qm_va_{dt.date.today()}.csv",
            mime="text/csv",
            type="primary"
        )

        # PDF-Export nur für ausgewählte VA
        st.markdown("### PDF erzeugen")
        if selected_va:
            if st.button("PDF erzeugen für ausgewählte VA", type="primary"):
                df_sel = df_all[df_all["VA_Nr"].astype(str).str.strip() == selected_va]
                if not df_sel.empty:
                    pdf_bytes = export_va_to_pdf(df_sel.iloc[0].to_dict())
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"{selected_va}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error("Keine Daten für die ausgewählte VA gefunden.")
        else:
            st.info("Bitte eine VA auswählen, um ein PDF zu erzeugen.")

from zoneinfo import ZoneInfo  # ab Python 3.9 verfügbar

# -----------------------------------
# Sidebar-Hinweis "Aktuelles"
# -----------------------------------
if st.session_state.logged_in:
    st.sidebar.markdown("### Aktuelles")
    try:
        df_all_sidebar = pd.read_csv("qm_verfahrensanweisungen.csv", sep=";", encoding="utf-8-sig")
        if not df_all_sidebar.empty:
            letzte_va = df_all_sidebar.iloc[-1]
            st.sidebar.info(f"Neue VA verfügbar: **{letzte_va['VA_Nr']} – {letzte_va['Titel']}**")
        else:
            st.sidebar.info("Keine neuen Verfahrensanweisungen vorhanden.")
    except:
        st.sidebar.info("Noch keine VA-Datei vorhanden.")

# -----------------------------------
# Button-Farben anpassen (CSS)
# -----------------------------------
st.markdown(
    """
    <style>
    /* Standard-Buttons: Blau */
    div.stButton > button {
        background-color: #2196F3;
        color: white;
    }
    div.stButton > button:hover {
        background-color: #1976D2;
        color: white;
    }

    /* Speichern & Kenntnisnahme: Grün */
    div.stButton > button:has-text("Speichern"),
    div.stButton > button:has-text("Zur Kenntnis genommen") {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    div.stButton > button:has-text("Speichern"):hover,
    div.stButton > button:has-text("Zur Kenntnis genommen"):hover {
        background-color: #45a049 !important;
        color: white !important;
    }

    /* CSV-Download: Rot */
    div.stDownloadButton > button:has-text("CSV herunterladen"),
    div.stDownloadButton > button:has-text("Kenntnisnahmen als CSV herunterladen") {
        background-color: #f44336 !important;
        color: white !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #d32f2f !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------
# Kenntnisnahme durch Mitarbeiter
# -----------------------------------
if st.session_state.logged_in:
    st.markdown("## Kenntnisnahme bestätigen")
    st.markdown("Bitte bestätigen Sie, dass Sie die ausgewählte VA gelesen haben.")

    name = st.text_input("Name")
    email = st.text_input("E-Mail")

    try:
        df_va = pd.read_csv("qm_verfahrensanweisungen.csv", sep=";", encoding="utf-8-sig")
        if not df_va.empty:
            va_list = sorted(df_va["VA_Nr"].dropna().astype(str).unique())
            va_auswahl = st.selectbox("VA auswählen", options=va_list)
        else:
            va_auswahl = None
            st.info("Noch keine Verfahrensanweisungen vorhanden.")
    except:
        va_auswahl = None
        st.info("VA-Datei konnte nicht geladen werden.")

    if st.button("Zur Kenntnis genommen", type="primary"):
        if name.strip() and email.strip() and va_auswahl:
            # Lokaler Zeitstempel mit Zeitzone Europe/Berlin
            zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")

            eintrag = {
                "Name": name.strip(),
                "E-Mail": email.strip(),
                "VA_Nr": va_auswahl,
                "Zeitpunkt": zeitpunkt
            }
            df_kenntnis = pd.DataFrame([eintrag], columns=["Name", "E-Mail", "VA_Nr", "Zeitpunkt"])

            if os.path.exists("kenntnisnahmen.csv") and os.path.getsize("kenntnisnahmen.csv") > 0:
                df_kenntnis.to_csv("kenntnisnahmen.csv", sep=";", index=False,
                                   mode="a", header=False, encoding="utf-8-sig")
            else:
                df_kenntnis.to_csv("kenntnisnahmen.csv", sep=";", index=False,
                                   header=True, encoding="utf-8-sig")

            st.success(f"Kenntnisnahme für VA {va_auswahl} gespeichert.")
        else:
            st.error("Bitte Name, E-Mail und VA auswählen.")

# -----------------------------------
# Kenntnisnahmen anzeigen und exportieren
# -----------------------------------
if st.session_state.logged_in:
    st.markdown("## Kenntnisnahmen anzeigen")
    try:
        df_k = pd.read_csv("kenntnisnahmen.csv", sep=";", encoding="utf-8-sig", dtype=str)
        st.dataframe(df_k, use_container_width=True)
        st.download_button(
            label="Kenntnisnahmen als CSV herunterladen",
            data=df_k.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig"),
            file_name=f"kenntnisnahmen_{dt.date.today()}.csv",
            mime="text/csv",
            type="secondary"
        )
    except:
        st.info("Noch keine Kenntnisnahmen vorhanden oder Datei nicht lesbar.")


