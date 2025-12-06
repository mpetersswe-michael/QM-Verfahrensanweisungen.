import streamlit as st
import pandas as pd
import datetime as dt
import io
import os
from fpdf import FPDF
from zoneinfo import ZoneInfo  # ab Python 3.9 verfügbar

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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

    for feld in QM_COLUMNS[1:]:
        add_section(feld, row.get(feld, ""))

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

# -----------------------------------
# Eingabe + Anzeige/Export (nur wenn eingeloggt)
# -----------------------------------
if st.session_state.logged_in:
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
                df_neu.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig",
                              mode="a", header=not os.path.exists(DATA_FILE_QM) or os.path.getsize(DATA_FILE_QM) == 0)
                st.success(f"VA {va_nr} hinzugefügt (Append-only).")
        else:
            df_neu.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"VA {va_nr} gespeichert (neue Datei erstellt, Append-only).")

    # -----------------------------------
    # Verfahrensanweisungen anzeigen und exportieren
    # -----------------------------------
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
            label="VA-Tabelle als CSV herunterladen",  # eindeutiger Label
            data=csv_data,
            file_name=f"qm_va_{dt.date.today()}.csv",
            mime="text/csv",
            type="primary"
        )

        st.markdown("### PDF erzeugen")
        if selected_va:
            if st.button("PDF erzeugen für ausgewählte VA", type="primary"):
                df_sel = df_all[df_all["VA_Nr"].astype(str).str.strip() == selected_va]
                if not df_sel.empty:
                    pdf_bytes = export_va_to_pdf(df_sel.iloc[0].to_dict())
                    st.download_button(
                        label="VA-PDF herunterladen",  # eindeutiger Label
                        data=pdf_bytes,
                        file_name=f"{selected_va}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error("Keine Daten für die ausgewählte VA gefunden.")
        else:
            st.info("Bitte eine VA auswählen, um ein PDF zu erzeugen.")

    # -----------------------------------
    # Sidebar-Hinweis "Aktuelles"
    # -----------------------------------
    st.sidebar.markdown("### Aktuelles")
    try:
        df_all_sidebar = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
        if not df_all_sidebar.empty:
            letzte_va = df_all_sidebar.iloc[-1]
            st.sidebar.info(f"Neue VA verfügbar: **{letzte_va['VA_Nr']} – {letzte_va['Titel']}**")
        else:
            st.sidebar.info("Keine neuen Verfahrensanweisungen vorhanden.")
    except:
        st.sidebar.info("Noch keine VA-Datei vorhanden.")

# -----------------------------------
# Lesebestätigung durch Mitarbeiter
# -----------------------------------
if st.session_state.logged_in:
    st.markdown("## Lesebestätigung")
    st.markdown("Bitte bestätigen Sie, dass Sie die ausgewählte VA gelesen haben.")

    # Eingabefelder mit eindeutigen Keys
    vorname = st.text_input("Vorname", key="lese_vorname")
    name = st.text_input("Name", key="lese_name")

    try:
        df_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
        # Dropdown nur mit Nummern (z. B. "004")
        va_list = sorted(
            df_va["VA_Nr"].dropna().astype(str)
            .str.replace("VA", "", regex=False)
            .str.strip()
        )
        va_auswahl_num = st.selectbox(
            "VA auswählen zur Lesebestätigung",
            options=va_list,
            key="lesebestaetigung_va"
        )
    except Exception:
        va_auswahl_num = None
        st.info("VA-Datei konnte nicht geladen werden oder enthält keine gültigen Einträge.")

    if st.button("Lesebestätigung bestätigen", key="lesebestaetigung_button"):
        if vorname.strip() and name.strip() and va_auswahl_num:
            zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")

            # Einheitlich als "VAxxx" speichern
            va_nr_speichern = f"VA{va_auswahl_num}"

            eintrag = {
                "Vorname": vorname.strip(),
                "Name": name.strip(),
                "VA_Nr": va_nr_speichern,
                "Zeitpunkt": zeitpunkt
            }
            df_kenntnis = pd.DataFrame([eintrag], columns=["Vorname", "Name", "VA_Nr", "Zeitpunkt"])

            # Robuste Schreiblogik: erster Eintrag mit Header, danach Append ohne Header
            write_header = not os.path.exists(DATA_FILE_KENNTNIS) or os.path.getsize(DATA_FILE_KENNTNIS) == 0
            df_kenntnis.to_csv(
                DATA_FILE_KENNTNIS,
                sep=";",
                index=False,
                mode="w" if write_header else "a",
                header=write_header,
                encoding="utf-8-sig"
            )

            st.success(f"Lesebestätigung für {va_nr_speichern} gespeichert.")
        else:
            st.error("Bitte Vorname, Name und VA auswählen.")

# -----------------------------------
# Live-Vorschau: Kenntnisnahmen anzeigen
# -----------------------------------
if st.session_state.logged_in:
    st.markdown("## Live-Vorschau: Kenntnisnahmen")

    try:
        df_anzeige = pd.read_csv(DATA_FILE_KENNTNIS, sep=";", encoding="utf-8-sig", dtype=str)
        if df_anzeige.empty:
            st.info("Noch keine Lesebestätigungen vorhanden.")
        else:
            st.dataframe(df_anzeige[["Vorname", "Name", "VA_Nr", "Zeitpunkt"]], use_container_width=True)
    except Exception as e:
        st.error(f"Fehler beim Laden der Kenntnisnahmen: {e}")






# -----------------------------------
# Debug: Lesebestätigung prüfen
# -----------------------------------
if st.session_state.logged_in and "Vorname" in df_kenntnis.columns:
    st.markdown("### 🔍 Debug: Lesebestätigung intern")

    st.write
