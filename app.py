# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import datetime as dt

# ----------------------------
# Konfiguration
# ----------------------------
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide")
DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
QM_COLUMNS = [
    "VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand",
    "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen"
]

# ----------------------------
# Styles
# ----------------------------
st.markdown("""
<style>
.stButton>button {
    background-color: #4CAF50;
    color: white;
    border-radius: 8px;
    padding: 0.5em 1em;
    font-weight: bold;
    border: none;
}
.stButton>button:hover {
    background-color: #45a049;
}
.logout-button > button {
    background-color: #e74c3c;
    color: white;
    border-radius: 8px;
    padding: 0.5em 1em;
    font-weight: bold;
}
.logout-button > button:hover {
    background-color: #c0392b;
}
.login-box {
    background-color: #fff8cc;
    padding: 1.2em;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 2em;
    font-size: 1.4em;
    font-weight: bold;
    color: #333333;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Login-Block
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown('<div class="login-box">Login QM-Verfahrensanweisungen</div>', unsafe_allow_html=True)
    password = st.text_input("Login Passwort", type="password", key="login_pw")
    if st.button("Login", key="login_btn"):
        if password == "QM2024":
            st.session_state["auth"] = True
            st.success("Login erfolgreich. Eingabefelder sind jetzt sichtbar.")
        else:
            st.error("Falsches Passwort.")
            st.stop()
    else:
        st.stop()

# ----------------------------
# Nach Login: Eingabeformular + Verwaltung
# ----------------------------
if st.session_state["auth"]:
    with st.sidebar:
        st.markdown("### Navigation")
        if st.button("Logout", key="logout_btn"):
            st.session_state["auth"] = False
        st.markdown("---")

    # Eingabeformular
    st.markdown("## Neue Verfahrensanweisung erfassen")

    va_nr = st.text_input("VA Nummer", placeholder="z. B. VA003")
    va_title = st.text_input("Titel", placeholder="Kommunikationswege im Pflegedienst")

    kapitel_num = st.selectbox("Kapitel Nr.", list(range(1, 11)), index=6)
    kapitel = f"Kapitel {kapitel_num}"

    unterkapitel = st.text_input("Unterkapitel", placeholder=f"Kap. {kapitel_num}-3")

    revision_date = st.date_input("Revisionsstand", value=dt.date.today())
    revision_str = revision_date.strftime("%d.%m.%Y")

    ziel = st.text_area("Ziel", height=100)
    geltung = st.text_area("Geltungsbereich", height=80)
    vorgehen = st.text_area("Vorgehensweise", height=150)
    kommentar = st.text_area("Kommentar", height=80)
    unterlagen = st.text_area("Mitgeltende Unterlagen", height=80)

    if st.button("Verfahrensanweisung speichern", type="primary"):
        if not va_nr.strip() or not va_title.strip():
            st.warning("Bitte VA Nummer und Titel eingeben.")
        else:
            new_va = pd.DataFrame([{
                "VA_Nr": va_nr.strip(),
                "Titel": va_title.strip(),
                "Kapitel": kapitel,
                "Unterkapitel": unterkapitel.strip(),
                "Revisionsstand": revision_str,
                "Ziel": ziel.strip(),
                "Geltungsbereich": geltung.strip(),
                "Vorgehensweise": vorgehen.strip(),
                "Kommentar": kommentar.strip(),
                "Mitgeltende Unterlagen": unterlagen.strip()
            }])

            try:
                df_existing = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
            except:
                df_existing = pd.DataFrame(columns=QM_COLUMNS)

            df_combined = pd.concat([df_existing, new_va], ignore_index=True)
            df_combined.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")

            st.success(f"Verfahrensanweisung {va_nr} wurde gespeichert.")

# ----------------------------
# Verwaltung: Anzeige, Auswahl, Download, Löschen, PDF
# ----------------------------
st.markdown("## Verfahrensanweisungen anzeigen und verwalten")

try:
    df_all = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
except:
    df_all = pd.DataFrame(columns=QM_COLUMNS)

if df_all.empty:
    st.info("Noch keine Verfahrensanweisungen gespeichert.")
else:
    # Auswahlfeld
    selected_va = st.selectbox(
        "VA auswählen zur Anzeige oder PDF-Erzeugung",
        options=[""] + sorted(df_all["VA_Nr"].dropna().astype(str).unique()),
        index=0
    )

    # Gefilterte Anzeige
    df_filtered = df_all[df_all["VA_Nr"].astype(str) == selected_va] if selected_va else df_all
    st.dataframe(df_filtered, use_container_width=True)

    # CSV-Download
    csv_data = df_filtered.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="CSV herunterladen",
        data=csv_data,
        file_name=f"qm_va_{dt.date.today()}.csv",
        mime="text/csv"
    )

    # Löschfunktion
    st.markdown("### VA löschen")
    if selected_va:
        if st.button("Ausgewählte VA löschen", type="secondary"):
            df_remaining = df_all[df_all["VA_Nr"].astype(str) != selected_va]
            df_remaining.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
            st.success(f"VA {selected_va} wurde gelöscht. Bitte Seite neu laden.")
    else:
        st.warning("Bitte zuerst eine VA auswählen, um sie zu löschen.")

    # ----------------------------
    # PDF-Funktion mit Unicode-Bereinigung und Bytes-Buffer
    # ----------------------------
    import io
    from fpdf import FPDF

    def clean_text(text):
        if not text:
            return "-"
        return (
            str(text)
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
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, clean_text(f"QM-Verfahrensanweisung - {row['VA_Nr']}"), ln=True, align="C")
        pdf.ln(5)

        def add_section(title, content):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, clean_text(title), ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 8, clean_text(content if content else "-"))
            pdf.ln(3)

        add_section("Titel", row.get("Titel", ""))
        add_section("Kapitel", row.get("Kapitel", ""))
        add_section("Unterkapitel", row.get("Unterkapitel", ""))
        add_section("Revisionsstand", row.get("Revisionsstand", ""))
        add_section("Ziel", row.get("Ziel", ""))
        add_section("Geltungsbereich", row.get("Geltungsbereich", ""))
        add_section("Vorgehensweise", row.get("Vorgehensweise", ""))
        add_section("Kommentar", row.get("Kommentar", ""))
        add_section("Mitgeltende Unterlagen", row.get("Mitgeltende Unterlagen", ""))

        # Schreibe PDF in Bytes-Buffer
        buffer = io.BytesIO()
        pdf.output(buffer)
        return buffer.getvalue()

    # ----------------------------
    # PDF-Export-Button
    # ----------------------------
    st.markdown("### PDF erzeugen")
    if selected_va:
        if st.button("PDF erzeugen für ausgewählte VA"):
            df_sel = df_all[df_all["VA_Nr"].astype(str) == selected_va]
            if not df_sel.empty:
                pdf_bytes = export_va_to_pdf(df_sel.iloc[0])
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"{selected_va}.pdf",
                    mime="application/pdf"
                )
    else:
        st.warning("Bitte zuerst eine VA auswählen, um PDF zu erzeugen.")


