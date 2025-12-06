import streamlit as st
import pandas as pd
import datetime as dt
import io
import os
from fpdf import FPDF
from zoneinfo import ZoneInfo
import re

# --------------------------
# Session-Status für Login
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --------------------------
# Konfiguration
# --------------------------
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
DATA_FILE_KENNTNIS = "kenntnisnahmen.csv"
QM_COLUMNS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
    "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]

# --------------------------
# App-Titel
# --------------------------
st.set_page_config(page_title="Verfahrensanweisungen (Auszug aus dem QMH)")
st.markdown(
    "<h5 style='text-align:center; color:#444;'>Verfahrensanweisungen (Auszug aus dem QMH)</h5>",
    unsafe_allow_html=True
)

# --------------------------
# Login
# --------------------------
if not st.session_state.logged_in:
    st.markdown("## Login")
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
# Hauptbereich mit Tabs
# --------------------------
if st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Verfahrensanweisungen", "Lesebestätigung"])

    # --------------------------
    # Tab 1: VA-Eingabe, Anzeige, Export
    # --------------------------
    with tab1:
        st.markdown("## Neue Verfahrensanweisung eingeben")

        kapitel_nr = st.selectbox("Kapitel-Nr", options=list(range(1, 21)), index=0)
        unterkap_nr = st.selectbox("Unterkapitel-Nr", options=list(range(1, 21)), index=0)

        va_nr = st.text_input("VA-Nr").strip()
        titel = st.text_input("Titel")
        kapitel = str(kapitel_nr)
        unterkapitel = f"Kap. {kapitel_nr}-{unterkap_nr}"
        revisionsstand = st.text_input("Revisionsstand")
        ziel = st.text_area("Ziel")
        geltungsbereich = st.text_area("Geltungsbereich")
        vorgehensweise = st.text_area("Vorgehensweise")
        kommentar = st.text_area("Kommentar")
        mitgeltende_unterlagen = st.text_area("Mitgeltende Unterlagen")

        if st.button("Speichern (Append-only)", type="primary"):
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

            if os.path.exists(DATA_FILE_QM):
                try:
                    df_alt = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
                except Exception:
                    df_alt = pd.DataFrame(columns=QM_COLUMNS)

                if not df_alt.empty and df_alt["VA_Nr"].astype(str).str.strip().eq(va_nr).any():
                    st.error(f"VA {va_nr} existiert bereits. Append-only: kein Überschreiben, bitte neue VA-Nr wählen.")
                else:
                    df_neu.to_csv(
                        DATA_FILE_QM,
                        sep=";",
                        index=False,
                        encoding="utf-8-sig",
                        mode="a",
                        header=not os.path.exists(DATA_FILE_QM) or os.path.getsize(DATA_FILE_QM) == 0
                    )
                    st.success(f"VA {va_nr} hinzugefügt (Append-only).")
            else:
                df_neu.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
                st.success(f"VA {va_nr} gespeichert (neue Datei erstellt, Append-only).")

        # --------------------------
        # Anzeige und Export
        # --------------------------
        st.markdown("## Verfahrensanweisungen anzeigen und exportieren")
        try:
            df_all = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
        except Exception:
            df_all = pd.DataFrame(columns=QM_COLUMNS)

        if df_all.empty:
            st.info("Noch keine Verfahrensanweisungen gespeichert.")
        else:
            df_all["VA_Anzeige"] = df_all["VA_Nr"].astype(str).str.strip() + " – " + df_all["Titel"].astype(str).str.strip()
            selected_va_display = st.selectbox(
                "VA auswählen für Anzeige und PDF-Erzeugung",
                options=[""] + sorted(df_all["VA_Anzeige"].dropna().unique()),
                index=0
            )
            selected_va = selected_va_display.split(" – ")[0] if selected_va_display else ""

            df_filtered = df_all[df_all["VA_Nr"].astype(str).str.strip() == selected_va] if selected_va else df_all
            st.dataframe(df_filtered, use_container_width=True)

            csv_data = df_all.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="VA-Tabelle als CSV herunterladen",
                data=csv_data,
                file_name=f"qm_va_{dt.date.today()}.csv",
                mime="text/csv",
                type="primary"
            )

            # --------------------------
            # PDF erzeugen
            # --------------------------
            # --------------------------
# PDF erzeugen
# --------------------------
st.markdown("### PDF erzeugen")

if "selected_va" in locals() and selected_va:
    if st.button("PDF erzeugen für ausgewählte VA", type="primary"):
        df_sel = df_all[df_all["VA_Nr"].astype(str).str.strip() == selected_va]
        if not df_sel.empty:
            pdf_bytes = export_va_to_pdf(df_sel.iloc[0].to_dict())
            st.download_button(
                label="VA-PDF herunterladen",
                data=pdf_bytes,
                file_name=f"{selected_va}.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.error("Keine Daten für die ausgewählte VA gefunden.")
else:
    st.info("Bitte eine VA auswählen, um ein PDF zu erzeugen.")
# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
with tab2:
    st.markdown("## Lesebestätigung")
    st.markdown("Bitte bestätigen Sie, dass Sie die ausgewählte VA gelesen haben.")

    # Eingabe Name
    name_raw = st.text_input("Name (Nachname,Vorname)", key="lese_name")

    # VA-Auswahl
    try:
        df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig", dtype=str)
        va_list = sorted(
            df_va["VA_Nr"].dropna().astype(str)
            .str.replace("VA", "", regex=False)
            .str.strip()
        )
        va_nummer = st.selectbox(
            "VA auswählen zur Lesebestätigung",
            options=va_list,
            key="lesebestaetigung_va"
        )
    except Exception:
        va_nummer = None
        st.info("VA-Datei konnte nicht geladen werden oder enthält keine gültigen Einträge.")

    # Button: Speichern + Download
    if st.button("Lesebestätigung speichern & herunterladen", key="lesebestaetigung_button"):
        name_kombi = re.sub(r"\s*,\s*", ",", name_raw.strip())

        if name_kombi and va_nummer:
            zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
            va_nr_speichern = f"VA{va_nummer}"

            # Eintrag exakt mit drei Spalten
            eintrag = {"Name": name_kombi, "VA_Nr": va_nr_speichern, "Zeitpunkt": zeitpunkt}
            df_kenntnis = pd.DataFrame([eintrag])[["Name", "VA_Nr", "Zeitpunkt"]]

            # Append-only Speicherung
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

            # Sofortiger Download der aktuellen Bestätigung
            csv_bytes = df_kenntnis.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="Diese Lesebestätigung als CSV herunterladen",
                data=csv_bytes,
                file_name=f"lesebestaetigung_{va_nr_speichern}_{dt.date.today()}.csv",
                mime="text/csv",
                type="primary"
            )

            st.success(f"Lesebestätigung für {va_nr_speichern} gespeichert und bereit zum Download.")
        else:
            st.error("Bitte Name (Nachname,Vorname) und VA auswählen.")
