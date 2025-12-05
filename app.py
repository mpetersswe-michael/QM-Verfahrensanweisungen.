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
# Eingabe + Verwaltung (nur wenn eingeloggt)
# -----------------------------------
if st.session_state.logged_in:
    # Eingabeformular
    st.markdown("## Neue Verfahrensanweisung eingeben")
    va_nr = st.text_input("VA-Nr").strip()
    titel = st.text_input("Titel")
    kapitel = st.text_input("Kapitel")
    unterkapitel = st.text_input("Unterkapitel")
    revisionsstand = st.text_input("Revisionsstand")
    ziel = st.text_area("Ziel")
    geltungsbereich = st.text_area("Geltungsbereich")
    vorgehensweise = st.text_area("Vorgehensweise")
    kommentar = st.text_area("Kommentar")
    mitgeltende_unterlagen = st.text_area("Mitgeltende Unterlagen")

    # Speichern-Block (robust: anlegen/anhängen/aktualisieren)
    if st.button("Speichern", type="primary"):
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

            maske = df_alt["VA_Nr"].astype(str).str.strip() == va_nr
            if maske.any():
                df_alt.loc[maske, QM_COLUMNS] = df_neu.iloc[0][QM_COLUMNS].values
                df_alt.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
                st.success(f"VA {va_nr} aktualisiert.")
            else:
                # Anhängen ohne Überschreiben
                df_neu.to_csv(
                    DATA_FILE_QM,
                    sep=";",
                    index=False,
                    encoding="utf-8-sig",
                    mode="a",
                    header=False
                )
                st.success(f"VA {va_nr} hinzugefügt.")
        else:
            # Erste Speicherung mit Kopfzeile
            df_neu.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"VA {va_nr} gespeichert (neue Datei erstellt).")

    # Verwaltung
    st.markdown("## Verfahrensanweisungen anzeigen und verwalten")
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

        # Tabelle
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

        # Löschfunktion
        st.markdown("### VA löschen")
        if selected_va:
            if st.button("Ausgewählte VA löschen", type="secondary"):
                df_remaining = df_all[df_all["VA_Nr"].astype(str).str.strip() != selected_va]
                df_remaining.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
                st.success(f"VA {selected_va} wurde gelöscht. Bitte Seite neu laden.")
        else:
            st.warning("Bitte zuerst eine VA auswählen, um sie zu löschen.")

        # PDF-Export
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
