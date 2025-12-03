# ----------------------------
# Imports
# ----------------------------
import streamlit as st
import pandas as pd
import datetime as dt

# ----------------------------
# Grundkonfiguration
# ----------------------------
st.set_page_config(page_title="QM-Verfahrensanweisungen", layout="wide")

DATA_FILE_QM = "qm_verfahrensanweisungen.csv"
QM_COLUMNS = ["Name", "Datum", "Version", "Titel", "Quittiert"]

# ----------------------------
# Styles für Buttons & Login
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
    color: white;
}
.logout-button > button {
    background-color: #e74c3c;
    color: white;
    border-radius: 8px;
    padding: 0.5em 1em;
    font-weight: bold;
    border: none;
}
.logout-button > button:hover {
    background-color: #c0392b;
    color: white;
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
    df = df[columns]
    df["Name"] = df["Name"].fillna("").astype(str)
    return df

def filter_by_name_exact(df, name):
    base = df.copy()
    base["Name_clean"] = base["Name"].str.strip().str.lower()
    if name and name.strip():
        mask = base["Name_clean"] == name.strip().lower()
        base = base[mask]
    base = base.drop(columns=["Name_clean"])
    return base

def to_csv_semicolon(df):
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

# ----------------------------
# Login-Block
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown('<div class="login-box">Login QM-Verfahrensanweisungen</div>', unsafe_allow_html=True)
    password = st.text_input("Login Passwort", type="password", key="login_pw")
    if st.button("Login", key="login_btn"):
        if password == "QM2024":   # ← dein Passwort
            st.session_state["auth"] = True
            st.success("Willkommen – du bist eingeloggt. Bitte bei den drei Punkten oben rechts 'Rerun' starten.")
        else:
            st.error("Falsches Passwort.")
    st.stop()

with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout", key="logout_btn"):
        st.session_state["auth"] = False
        st.stop()
    st.markdown("---")

# ----------------------------
# QM-Eingabe
# ----------------------------
st.markdown("## 📘 QM-Verfahrensanweisung bestätigen")

qm_name = st.text_input("Name", key="qm_name")
qm_date = st.date_input("Datum", value=dt.date.today(), key="qm_date")
qm_title = st.text_input("Titel der Anweisung", key="qm_title")
qm_version = st.text_input("Version", key="qm_version")
qm_quitt = st.checkbox("Ich bestätige, dass ich die Anweisung gelesen habe.", key="qm_quitt")

if st.button("Anweisung speichern", key="qm_save_btn"):
    if not qm_name.strip():
        st.warning("Bitte einen Namen eingeben.")
    else:
        new_qm = pd.DataFrame([{
            "Name": qm_name.strip(),
            "Datum": qm_date.strftime("%Y-%m-%d"),
            "Version": qm_version.strip(),
            "Titel": qm_title.strip(),
            "Quittiert": qm_quitt
        }])
        try:
            existing_qm = pd.read_csv(DATA_FILE_QM, sep=";", encoding="utf-8-sig")
        except:
            existing_qm = pd.DataFrame(columns=QM_COLUMNS)
        for c in QM_COLUMNS:
            if c not in existing_qm.columns:
                existing_qm[c] = ""
        existing_qm = existing_qm[QM_COLUMNS]
        updated_qm = pd.concat([existing_qm, new_qm], ignore_index=True)
        updated_qm.to_csv(DATA_FILE_QM, sep=";", index=False, encoding="utf-8-sig")
        st.success("Quittierung gespeichert.")

# ----------------------------
# Daten anzeigen und exportieren
# ----------------------------
st.markdown("## Daten anzeigen und exportieren")

df_qm_all = load_data(DATA_FILE_QM, QM_COLUMNS)

filter_name_qm = st.selectbox(
    "Filter nach Name",
    options=[""] + sorted(df_qm_all["Name"].dropna().str.strip().unique()),
    index=0,
    key="filter_qm"
)

st.markdown("### Quittierungen")
df_filtered_qm = filter_by_name_exact(df_qm_all, filter_name_qm)
st.dataframe(df_filtered_qm, use_container_width=True, height=300, key="qm_table")

csv_qm = to_csv_semicolon(df_filtered_qm)
st.download_button(
    "CSV Quittierungen herunterladen",
    data=csv_qm,
    file_name=f"qm_verfahrensanweisungen_{dt.date.today()}.csv",
    mime="text/csv",
    key="qm_csv_dl"
)





