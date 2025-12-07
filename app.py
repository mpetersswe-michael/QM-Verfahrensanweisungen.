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
# --------------------------
# Tab 0: Login
# --------------------------
with tabs[0]:
    st.markdown("## 🔒 Login")

    if st.session_state.get("logged_in", False):
        st.success("✅ Bereits eingeloggt")
        st.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    else:
        pw = st.text_input("Passwort", type="password", key="login_pw")
        if st.button("Login", key="login_button"):
            if pw == "qm2025":
                st.session_state.logged_in = True
                st.success("✅ Login erfolgreich.")
            else:
                st.error("❌ Passwort falsch.")

with tabs[1]:
    st.markdown("## 📘 Verfahrensanweisungen")

    DATA_FILE_QM = "qm_verfahrensanweisungen.csv"

    # Eingabe
    st.markdown("### Neue VA eingeben")
    va_nr_input = st.text_input("VA-Nummer")
    titel_input = st.text_input("Titel")
    kapitel_input = st.text_input("Kapitel")
    unterkapitel_input = st.text_input("Unterkapitel")
    revisionsstand_input = st.text_input("Revisionsstand")
    ziel_input = st.text_input("Ziel")
    vorgehensweise_input = st.text_area("Vorgehensweise")
    kommentar_input = st.text_area("Kommentar")
    mitgeltende_input = st.text_area("Mitgeltende Unterlagen")

    if st.button("VA speichern"):
        if all([va_nr_input.strip(), titel_input.strip(), kapitel_input.strip(), unterkapitel_input.strip(), revisionsstand_input.strip()]):
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
with tabs[2]:
    if st.session_state.get("logged_in", False):
        st.markdown("## ✅ Lesebestätigung")
        name_raw = st.text_input("Name (Nachname, Vorname)")
        va_nummer = st.selectbox("VA auswählen", options=[], key="lese_va")  # dynamisch befüllen

        if st.button("Bestätigen"):
            name_kombi = re.sub(r"\s*,\s*", ",", name_raw.strip())
            if name_kombi and va_nummer:
                zeitpunkt = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
                va_nr_speichern = f"VA{va_nummer}"
                eintrag = {"Name": name_kombi, "VA_Nr": va_nr_speichern, "Zeitpunkt": zeitpunkt}
                df_kenntnis = pd.DataFrame([eintrag])[["Name", "VA_Nr", "Zeitpunkt"]]
                DATA_FILE_KENNTNIS = "lesebestätigung.csv"
                file_exists = os.path.exists(DATA_FILE_KENNTNIS)
                file_empty = (not file_exists) or (os.path.getsize(DATA_FILE_KENNTNIS) == 0)
                df_kenntnis.to_csv(DATA_FILE_KENNTNIS, sep=";", index=False, mode="a" if file_exists and not file_empty else "w", header=True if file_empty else False, encoding="utf-8-sig")
                st.success(f"Bestätigung für {va_nr_speichern} gespeichert.")

                if st.checkbox("Eigenen Nachweis als CSV herunterladen"):
                    csv_bytes = df_kenntnis.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
                    st.download_button("Diese Lesebestätigung herunterladen", data=csv_bytes, file_name=f"lesebestaetigung_{va_nr_speichern}_{dt.date.today()}.csv", mime="text/csv")
            else:
                st.error("Bitte Name und VA auswählen.")

        # Tabelle anzeigen
        st.markdown("---")
        st.markdown("### 📄 Bereits bestätigte Einträge")
        if os.path.exists("lesebestätigung.csv"):
            df_kenntnis = pd.read_csv("lesebestätigung.csv", sep=";", encoding="utf-8-sig")
            st.dataframe(df_kenntnis.sort_values("Zeitpunkt", ascending=False))
        else:
            st.info("Noch keine Lesebestätigungen vorhanden.")
    else:
        st.warning("Bitte zuerst im Tab 'Login' anmelden.")
with tabs[3]:
    st.markdown("## 👥 Mitarbeiterliste")

    if os.path.exists("mitarbeiter.csv"):
        df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")
        st.dataframe(df_mitarbeiter)
    else:
        st.info("Noch keine Mitarbeiterliste vorhanden.")

    st.markdown("---")
    st.markdown("### 🔄 Lesebestätigungen zurücksetzen")
    if os.path.exists("lesebestätigung.csv"):
        if st.checkbox("Ich möchte alle Lesebestätigungen löschen"):
            if st.button("Jetzt zurücksetzen"):
                with open("lesebestätigung.csv", "w", encoding="utf-8-sig") as f:
                    f.write("Name;VA_Nr;Zeitpunkt\n")
                st.success("✅ Alle Lesebestätigungen wurden zurückgesetzt.")
with st.sidebar:
    if st.session_state.get("logged_in", False):
        st.success("✅ Eingeloggt")
        st.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
    else:
        st.warning("Nicht eingeloggt")

    # --------------------------
# Sidebar: VA-Status und Fortschritt
# --------------------------
if st.session_state.get("selected_va"):
    va_current = norm_va(st.session_state.selected_va)

    # Titel anzeigen
    try:
        df_va = pd.read_csv("qm_verfahrensanweisungen.csv", sep=";", encoding="utf-8-sig", dtype=str)
        row = df_va[df_va["VA_Nr"].apply(norm_va) == va_current]
        titel = row["Titel"].values[0] if not row.empty else ""
        st.markdown(f"**Aktuelles Dokument:** {va_current} – {titel}")
    except Exception:
        st.markdown(f"**Aktuelles Dokument:** {va_current}")

    # Fortschritt anzeigen
    try:
        df_kenntnis = pd.read_csv("lesebestätigung.csv", sep=";", encoding="utf-8-sig")
        df_mitarbeiter = pd.read_csv("mitarbeiter.csv", sep=";", encoding="utf-8-sig")

        # Name zusammenbauen
        df_mitarbeiter["Name_full"] = df_mitarbeiter["Name"].str.strip() + "," + df_mitarbeiter["Vorname"].str.strip()
        df_mitarbeiter["VA_norm"] = df_mitarbeiter["VA_Nr"].apply(norm_va)
        zielgruppe = df_mitarbeiter[df_mitarbeiter["VA_norm"] == va_current]["Name_full"].dropna().unique()

        df_kenntnis["VA_Nr_norm"] = df_kenntnis["VA_Nr"].apply(norm_va)
        gelesen = df_kenntnis[df_kenntnis["VA_Nr_norm"] == va_current]["Name"].dropna().unique()

        gelesen_count = len(set(gelesen) & set(zielgruppe))
        gesamt = len(zielgruppe)
        fortschritt = gelesen_count / gesamt if gesamt > 0 else 0.0

        st.progress(fortschritt, text=f"{gelesen_count} von {gesamt} Mitarbeiter (gelesen)")
    except Exception as e:
        st.warning(f"Fortschritt konnte nicht berechnet werden: {e}")
else:
    st.info("Noch kein Dokument ausgewählt.")

