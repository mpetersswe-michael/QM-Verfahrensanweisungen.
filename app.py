import streamlit as st
import pandas as pd

# ----------------------------
# Login-Block
# ----------------------------
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("## 🔐 Login QM-Verfahrensanweisungen")
    password = st.text_input("Login Passwort", type="password", key="login_pw")
    if st.button("Login", key="login_btn"):
        if password == "QM2024":
            st.session_state["auth"] = True
            st.experimental_rerun()
        else:
            st.error("Falsches Passwort.")
            st.stop()
    else:
        st.stop()

with st.sidebar:
    st.markdown("### Navigation")
    if st.button("Logout", key="logout_btn"):
        st.session_state["auth"] = False
        st.experimental_rerun()

# ----------------------------
# Eingabemaske für neue VA
# ----------------------------
st.markdown("## 📁 Neue Verfahrensanweisung erfassen und speichern")

va_nr = st.text_input("VA Nummer", key="va_nr")
titel = st.text_input("Titel", key="titel")
kapitel = st.text_input("Kapitel", key="kapitel")
unterkapitel = st.text_input("Unterkapitel", key="unterkapitel")
revisionsstand = st.text_input("Revisionsstand", key="revisionsstand")

ziel = st.text_area("Ziel", key="ziel")
geltungsbereich = st.text_area("Geltungsbereich", key="geltung")
vorgehensweise = st.text_area("Vorgehensweise", key="vorgehen")
kommentar = st.text_area("Kommentar", key="kommentar")
unterlagen = st.text_area("Mitgeltende Unterlagen", key="unterlagen")

# ----------------------------
# Speichern in qm_va.csv
# ----------------------------
def to_csv_semicolon(df):
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

if st.button("Speichern", key="btn_save_va"):
    new_entry = pd.DataFrame([{
        "VA_Nr": va_nr,
        "Titel": titel,
        "Kapitel": kapitel,
        "Unterkapitel": unterkapitel,
        "Revisionsstand": revisionsstand,
        "Ziel": ziel,
        "Geltungsbereich": geltungsbereich,
        "Vorgehensweise": vorgehen,
        "Kommentar": kommentar,
        "Mitgeltende Unterlagen": unterlagen
    }])

    try:
        # Bestehende Datei anhängen, falls vorhanden
        try:
            df_existing = pd.read_csv("qm_va.csv", sep=";", encoding="utf-8-sig")
        except:
            df_existing = pd.DataFrame(columns=new_entry.columns)

        df_combined = pd.concat([df_existing, new_entry], ignore_index=True)
        with open("qm_va.csv", "wb") as f:
            f.write(to_csv_semicolon(df_combined))

        st.success("Verfahrensanweisung wurde gespeichert.")
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")

