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
    "Erstellt von", "Zeitstempel"
]

# ----------------------------
# Hilfsfunktionen
# ----------------------------
def load_data(file, columns):
    try:
        df = pd.read_csv(file, sep=";", encoding="utf-8-sig")
    except:
        df = pd.DataFrame(columns=columns)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    return df[columns]

def to_csv_semicolon(df):
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

# ----------------------------
# Login
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("## 🔐 Login QM-Verfahrensanweisungen")
    pw = st.text_input("Passwort", type="password")
    if st.button("Login"):
        if pw == "QM2024":
            st.session_state["auth"] = True
            st.success("Login erfolgreich – du kannst jetzt mit der App arbeiten.")
        else:
            st.error("Falsches Passwort.")
    st.stop()

with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout"):
        st.session_state["auth"] = False
        st.success("Logout erfolgreich – bitte neu einloggen.")
        st.stop()

# ----------------------------
# Eingabeformular (ohne F:J)
# ----------------------------
st.markdown("## 📝 Neue Verfahrensanweisung erfassen")

va_nr = st.text_input("VA Nummer", placeholder="z. B. VA003")
va_title = st.text_input("Titel", placeholder="Kommunikation im Pflegedienst")
kapitel_num = st.selectbox("Kapitel Nr.", list(range(1, 11)), index=5)
kapitel = f"Kapitel {kapitel_num}"
unterkapitel = st.selectbox("Unterkapitel Nr.", [f"{kapitel_num}.{i}" for i in range(1, 6)], index=0)
revision_date = st.date_input("Revisionsstand", value=dt.date.today())
erstellt_von = st.text_input("Erstellt von (Name + Funktion)", placeholder="z. B. Peters-Michael, Qualitätsbeauftragter")

if st.button("Verfahrensanweisung speichern"):
    if not va_nr.strip() or not va_title.strip():
        st.warning("VA Nummer und Titel sind Pflicht.")
    else:
        new_va = pd.DataFrame([{
            "VA_Nr": va_nr.strip(),
            "Titel": va_title.strip(),
            "Kapitel": kapitel,
            "Unterkapitel": unterkapitel,
            "Revisionsstand": revision_date.strftime("%Y-%m-%d"),
            "Erstellt von": erstellt_von.strip(),
            "Zeitstempel": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        try:
            df_old = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
        except:
            df_old = pd.DataFrame(columns=QM_COLUMNS)
        df_new = pd.concat([df_old, new_va], ignore_index=True)
        df_new.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
        st.success(f"VA {va_nr} gespeichert.")

# ----------------------------
# Anzeige & CSV Export
# ----------------------------
st.markdown("## 📂 Verfahrensanweisungen anzeigen und exportieren")

df_qm_all = load_data(DATA_FILE_QM, QM_COLUMNS)
filter_va = st.selectbox("VA auswählen", options=[""] + sorted(df_qm_all["VA_Nr"].dropna().unique()), index=0)
df_filtered = df_qm_all[df_qm_all["VA_Nr"] == filter_va] if filter_va else df_qm_all
st.dataframe(df_filtered, use_container_width=True)

csv_qm = to_csv_semicolon(df_filtered)
st.download_button("CSV herunterladen", data=csv_qm, file_name=f"qm_va_{dt.date.today()}.csv", mime="text/csv")

# ----------------------------
# Daten löschen
# ----------------------------
st.markdown("## 🗑️ Verfahrensanweisung löschen")

delete_va = st.selectbox("VA zum Löschen auswählen", options=sorted(df_qm_all["VA_Nr"].dropna().unique()))
if st.button("Verfahrensanweisung löschen"):
    df_qm_all = df_qm_all[df_qm_all["VA_Nr"] != delete_va]
    df_qm_all.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
    st.success(f"VA {delete_va} wurde gelöscht.")

# ----------------------------
# PDF Export (vorerst deaktiviert)
# ----------------------------
# st.markdown("## 📤 Einzel-PDF Export")
# export_va = st.selectbox("VA für PDF auswählen", options=df_qm_all["VA_Nr"].dropna().unique())
# if st.button("PDF Export starten"):
#     st.warning("PDF-Export vorübergehend deaktiviert – wird später wieder aktiviert.")
