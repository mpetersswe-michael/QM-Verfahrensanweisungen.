# --------------------------
# Imports
# --------------------------
import streamlit as st
import pandas as pd
import datetime as dt
import io
import os
import re
from fpdf import FPDF
from zoneinfo import ZoneInfo

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
# Session-Status initialisieren
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "selected_va" not in st.session_state:
    st.session_state.selected_va = ""

# --------------------------
# App-Titel
# --------------------------
st.set_page_config(page_title="Verfahrensanweisungen (Auszug aus dem QMH)")
st.markdown(
    "<h5 style='text-align:center; color:#444;'>Verfahrensanweisungen (Auszug aus dem QMH)</h5>",
    unsafe_allow_html=True
)

# --------------------------
# Tabs
# --------------------------
tab0, tab1, tab2 = st.tabs(["System & Login", "Verfahrensanweisungen", "Lesebestätigung"])

# --------------------------
# Tab 0: System & Login
# --------------------------
with tab0:
    if not st.session_state.logged_in:
        st.markdown("## Login")
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
            st.sidebar.info("Logout erfolgreich.")


# --------------------------
# Upload für Mitarbeiterliste
# --------------------------
st.markdown("## Mitarbeiterliste hochladen")

uploaded_file = st.file_uploader("Bitte die mitarbeiter.csv hochladen", type=["csv"])

if uploaded_file is not None:
    try:
        # Datei speichern im App-Verzeichnis
        with open("mitarbeiter.csv", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("Datei 'mitarbeiter.csv' erfolgreich hochgeladen und gespeichert.")

        # Vorschau anzeigen
        df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")
        st.dataframe(df_mitarbeiter)

    except Exception as e:
        st.error(f"Fehler beim Verarbeiten der Datei: {e}")
else:
    if not os.path.exists("mitarbeiter.csv"):
        st.warning("Noch keine 'mitarbeiter.csv' vorhanden. Bitte hochladen.")
    else:
        st.info("Es existiert bereits eine 'mitarbeiter.csv' im App-Verzeichnis.")
        df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")
        st.dataframe(df_mitarbeiter)



# Sidebar: aktuelles Dokument + Fortschritt
if st.session_state.selected_va:
    st.sidebar.markdown(f"**Aktuelles Dokument:** {st.session_state.selected_va}")

    try:
        # Prüfen, ob mitarbeiter.csv existiert
        if not os.path.exists("mitarbeiter.csv"):
            st.sidebar.warning("Die Datei 'mitarbeiter.csv' fehlt. Bitte im App-Verzeichnis ablegen oder hochladen.")
            raise FileNotFoundError("mitarbeiter.csv fehlt")

        # Lesebestätigungen laden
        df_kenntnis = pd.read_csv("lesebestätigung.csv", sep=";", encoding="utf-8-sig")

        # Mitarbeiterliste laden
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

        # VA-Format harmonisieren
        def norm_va(x):
            s = str(x).upper().replace(" ", "")
            m = s.replace("VA", "")
            if m.isdigit():
                s = f"VA{int(m):03d}"
            return s

        va_current = norm_va(st.session_state.selected_va)

        # Zielgruppe für aktuelle VA
        if "VA_Nr" in df_mitarbeiter.columns:
            df_mitarbeiter["VA_norm"] = df_mitarbeiter["VA_Nr"].apply(norm_va)
            zielgruppe = df_mitarbeiter[df_mitarbeiter["VA_norm"] == va_current]["Name_full"].dropna().unique()
        else:
            zielgruppe = df_mitarbeiter["Name_full"].dropna().unique()

        gesamt = len(zielgruppe)

        # Lesebestätigungen für aktuelle VA
        if "VA_Nr" in df_kenntnis.columns:
            df_kenntnis["VA_Nr_norm"] = df_kenntnis["VA_Nr"].apply(norm_va)
            gelesen = df_kenntnis[df_kenntnis["VA_Nr_norm"] == va_current]["Name"].dropna().unique()
        else:
            st.sidebar.warning("Spalte 'VA_Nr' fehlt in lesebestätigung.csv.")
            raise ValueError("Spalte 'VA_Nr' fehlt")

        # Schnittmenge: nur Zielgruppe zählt
        gelesen_count = len(set(gelesen) & set(zielgruppe))

        fortschritt = (gelesen_count / gesamt) if gesamt > 0 else 0.0
        st.sidebar.progress(fortschritt, text=f"{gelesen_count} von {gesamt} Mitarbeiter (gelesen)")
    except Exception as e:
        st.sidebar.warning(f"Fortschritt konnte nicht berechnet werden: {e}")
else:
    st.sidebar.info("Noch kein Dokument ausgewählt.")

## --------------------------
# Tab 1: VA-Eingabe, Anzeige, Export, PDF
# --------------------------
with tab1:
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
            df_all["VA_Anzeige"] = (
                df_all["VA_Nr"].astype(str).str.strip()
                + " – "
                + df_all["Titel"].astype(str).str.strip()
            )

            selected_va_display = st.selectbox(
                "VA auswählen für Anzeige und PDF-Erzeugung",
                options=[""] + sorted(df_all["VA_Anzeige"].dropna().unique()),
                index=0,
                key="va_select_display"
            )

            selected_va = selected_va_display.split(" – ")[0] if selected_va_display else ""
            st.session_state.selected_va = selected_va

            df_filtered = (
                df_all[df_all["VA_Nr"].astype(str).str.strip() == selected_va]
                if selected_va else df_all
            )
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
        st.markdown("### PDF erzeugen")

        if st.session_state.selected_va:
            if st.button("PDF erzeugen für ausgewählte VA", type="primary"):
                df_sel = df_all[df_all["VA_Nr"].astype(str).str.strip() == st.session_state.selected_va]
                if not df_sel.empty:
                    pdf_bytes = export_va_to_pdf(df_sel.iloc[0].to_dict())
                    st.download_button(
                        label="VA-PDF herunterladen",
                        data=pdf_bytes,
                        file_name=f"{st.session_state.selected_va}_{dt.date.today()}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error("Keine Daten für die ausgewählte VA gefunden.")
        else:
            st.info("Bitte eine VA auswählen, um ein PDF zu erzeugen.")
    else:
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")


# --------------------------
# Tab 2: Lesebestätigung
# --------------------------
with tab2:
    if st.session_state.logged_in:
        st.markdown("## Lesebestätigung")
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

        if st.button("Bestätigen & CSV herunterladen", key="lese_button"):
            name_kombi = re.sub(r"\s*,\s*", ",", name_raw.strip())
            if name_kombi and va_nummer:
                zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
                va_nr_speichern = f"VA{va_nummer}"

                eintrag = {"Name": name_kombi, "VA_Nr": va_nr_speichern, "Zeitpunkt": zeitpunkt}
                df_kenntnis = pd.DataFrame([eintrag])[["Name", "VA_Nr", "Zeitpunkt"]]

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

                csv_bytes = df_kenntnis.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    label="Diese Lesebestätigung als CSV herunterladen",
                    data=csv_bytes,
                    file_name=f"lesebestaetigung_{va_nr_speichern}_{dt.date.today()}.csv",
                    mime="text/csv",
                    type="primary"
                )

                st.success(f"Bestätigung für {va_nr_speichern} gespeichert.")
            else:
                st.error("Bitte Name und VA auswählen.")
    else:
        st.warning("Bitte zuerst im Tab 'System & Login' anmelden.")
