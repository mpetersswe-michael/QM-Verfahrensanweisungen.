#------------------------- 
#Import

import streamlit as 
st import pandas as
pd import datetime as
dt from fpdf import FPDF 

# ---------------------------- 
# Konfiguration # ---------------------------- 
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide") DATA_FILE_QM = "qm_verfahrensanweisungen.csv" 
QM_COLUMNS = [ 
"VA_Nr", "Titel", "Kapitel", "Unterkapitel", "Revisionsstand", "Ziel", "Geltungsbereich", "Vorgehensweise", "Kommentar", "Mitgeltende Unterlagen" 
] 
# ---------------------------- 
# Styles # ---------------------------- 
st.markdown(""" <style> .stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; padding: 0.5em 1em; font-weight: bold; border: none; } 
.stButton>button:hover { 
background-color: #45a049; 
} 
.logout-button > button { background-color: #e74c3c; color: white; border-radius: 8px; padding: 0.5em 1em; font-weight: bold; 
} 
.logout-button > button:hover { background-color: #c0392b; 
} 
.login-box { background-color: #fff8cc; padding: 1.2em; border-radius: 10px; text-align: center; margin-bottom: 2em; font-size: 1.4em; font-weight: bold; color: #333333; 
} 
</style> """, unsafe_allow_html=True) 
# ---------------------------- 
# Hilfsfunktionen # ---------------------------- 
def load_data(file, columns): try: df = pd.read_csv(file, sep=";", encoding="utf-8-sig") except: 
df = pd.DataFrame(columns=columns) for c in columns: if c not in df.columns: df[c] = "" return df[columns] 
def to_csv_semicolon(df): return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig") 
def export_pdf(df_row): pdf = FPDF() pdf.add_page() pdf.set_font("Arial", size=12) pdf.cell(0, 10, "QM-Verfahrensanweisung", ln=True, align="C") pdf.ln(5) for col in df_row.index: val = str(df_row[col]) pdf.multi_cell(0, 8, f"{col}: {val}") pdf.ln(1) pdf_str = pdf.output(dest="S") pdf_bytes = pdf_str.encode("latin-1") if isinstance(pdf_str, str) else pdf_str return pdf_bytes 
# ---------------------------- 
# Login-Block # ---------------------------- 
if "auth" not in st.session_state: st.session_state["auth"] = False 
if not st.session_state["auth"]: st.markdown('<div class="login-box">Login QM-Verfahrensanweisungen</div>', unsafe_allow_html=True) password = st.text_input("Login Passwort", type="password", key="login_pw") 
if st.button("Login", key="login_btn"): if password == "QM2024": st.session_state["auth"] = True st.success("Willkommen – du bist eingeloggt. Bitte oben rechts 'Rerun' starten.") else: st.error("Falsches Passwort.") st.stop() 
with st.sidebar: st.markdown("### Navigation") if st.button("Logout", key="logout_btn"): st.session_state["auth"] = False st.stop() st.markdown("---") 
# ---------------------------- 
# Eingabeformular # ---------------------------- 
st.markdown("##      Neue Verfahrensanweisung erfassen") 
va_nr = st.text_input("VA Nummer", placeholder="z. B. VA003") va_title = st.text_input("Titel", placeholder="Kommunikation im Pflegedienst") kapitel_num = st.selectbox("Kapitel Nr.", list(range(1, 11)), index=5) kapitel = f"Kapitel {kapitel_num}" unterkapitel = st.selectbox("Unterkapitel Nr.", [f"{kapitel_num}.{i}" for i in range(1, 6)], index=0) revision_date = st.date_input("Revisionsstand", value=dt.date.today()) 
ziel = st.text_area("Ziel", height=100) geltung = st.text_area("Geltungsbereich", height=80) vorgehen = st.text_area("Vorgehensweise", height=150) kommentar = st.text_area("Kommentar", height=80) unterlagen = st.text_area("Mitgeltende Unterlagen", height=80) 
if st.button("Verfahrensanweisung speichern"): if not va_nr.strip() or not va_title.strip(): st.warning("Bitte VA Nummer und Titel eingeben.") else: new_va = pd.DataFrame([{ "VA_Nr": va_nr.strip(), "Titel": va_title.strip(), "Kapitel": kapitel, "Unterkapitel": unterkapitel, "Revisionsstand": revision_date.strftime("%Y-%m-%d"), "Ziel": ziel.strip(), "Geltungsbereich": geltung.strip(), "Vorgehensweise": vorgehen.strip(), "Kommentar": kommentar.strip(), "Mitgeltende Unterlagen": unterlagen.strip() }]) 
try: existing_va = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig") except: existing_va = pd.DataFrame(columns=QM_COLUMNS) updated_va = pd.concat([existing_va, new_va], ignore_index=True) updated_va.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig") st.success(f"Verfahrensanweisung {va_nr} gespeichert.") 
# ---------------------------- 
# Anzeige & Export # ---------------------------- 
st.markdown("##    Verfahrensanweisungen anzeigen und exportieren") 
df_qm_all = load_data(DATA_FILE_QM, QM_COLUMNS) 
filter_va = st.selectbox("VA auswählen", options=[""] + sorted(df_qm_all["VA_Nr"].dropna().unique()), index=0) 
df_filtered = df_qm_all[df_qm_all["VA_Nr"] == filter_va] if filter_va else df_qm_all st.dataframe(df_filtered, use_container_width=True) 
csv_qm = to_csv_semicolon(df_filtered) st.download_button("CSV herunterladen", data=csv_qm, file_name=f"qm_va_{dt.date.today()}.csv", mime="text/csv") 
# ---------------------------- 
# PDF Export # ---------------------------- 
import tempfile, os from fpdf import FPDF 
def export_pdf_row_to_bytes(df_row): pdf = FPDF() pdf.add_page() pdf.set_font("Arial", size=12) 
pdf.cell(0, 10, "QM-Verfahrensanweisung", ln=True, align="C") pdf.ln(5) 
for col in df_row.index: val = str(df_row[col]) pdf.multi_cell(0, 8, f"{col}: {val}") pdf.ln(1) 
# Primärer Weg: Ausgabe als String oder Bytes out = pdf.output(dest="S") if isinstance(out, bytes): return out 
elif isinstance(out, str): return out.encode("latin-1") else: # Fallback: Datei schreiben und wieder einlesen with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp: tmp_path = tmp.name try: pdf.output(tmp_path, dest="F") with open(tmp_path, "rb") as f: data = f.read() return data finally: try: os.remove(tmp_path) except: pass 
# ---------------------------- 
# Streamlit-Block für Export # ---------------------------- 
st.markdown("##      Einzel-PDF Export") 
export_va = st.selectbox( "VA für PDF auswählen", options=df_qm_all["VA_Nr"].unique() if not df_qm_all.empty else [] 
) 
if st.button("PDF Export starten"): df_sel = df_qm_all[df_qm_all["VA_Nr"] == export_va] if df_sel.empty: st.warning("Keine Daten für die ausgewählte VA gefunden.") else: 
pdf_bytes = export_pdf_row_to_bytes(df_sel.iloc[0]) if not isinstance(pdf_bytes, (bytes, bytearray)): st.error(f"Interner Fehler: PDF-Daten sind kein Bytes-Objekt (Typ: {type(pdf_bytes)})") else: st.download_button( label="Download PDF", data=pdf_bytes, file_name=f"{export_va}.pdf", mime="application/pdf" ) 


