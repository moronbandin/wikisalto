import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
import altair as alt

# --- Configuración ---
st.set_page_config(page_title="Hipervínculos", layout="wide")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "puntuaciones.csv")
JUGADORES = ["Alejandro", "Nicolás"]

# --- Utilidades seguras ---
def ensure_csv(path: str):
    if not os.path.exists(path):
        df_vacio = pd.DataFrame(columns=["usuario", "origen", "destino", "saltos", "puntos", "fecha"])
        df_vacio.to_csv(path, index=False)

def safe_read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        ensure_csv(path)
    try:
        return pd.read_csv(path)
    except Exception:
        # Se algo vai mal lendo, recréao baleiro (evita crash)
        ensure_csv(path)
        return pd.read_csv(path)

def safe_append_csv(path: str, row_df: pd.DataFrame):
    # Lectura → concat → escritura atómica sinxela
    df = safe_read_csv(path)
    df = pd.concat([df, row_df], ignore_index=True)
    df.to_csv(path, index=False)

def get_random_wikipedia_article():
    url = "https://es.wikipedia.org/api/rest_v1/page/random/summary"
    try:
        resp = requests.get(url, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        return data.get("title", "Sen título"), data.get("content_urls", {}).get("desktop", {}).get("page", "#")
    except Exception:
        # Fallback seguro
        return "Wikipedia", "https://es.wikipedia.org/wiki/Wikipedia:Portada"

# --- Init de datos ---
ensure_csv(DATA_FILE)

# --- UI Tabs ---
tab1, tab2 = st.tabs(["🎮 Xogo", "📈 Estatísticas"])

with tab1:
    st.title("🧩 Hipervínculos – O xogo do wikisalto")
    st.write("Conecta dúas páxinas reais da Wikipedia usando só hipervínculos azuis. Conta os teus saltos e acumula puntos!")

    if st.button("🎲 Sortear novo par"):
        origen_title, origen_url = get_random_wikipedia_article()
        destino_title, destino_url = get_random_wikipedia_article()
        st.session_state['origen_title'] = origen_title
        st.session_state['origen_url'] = origen_url
        st.session_state['destino_title'] = destino_title
        st.session_state['destino_url'] = destino_url

    if 'origen_title' in st.session_state and 'destino_title' in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔵 Orixe")
            st.markdown(f"[{st.session_state['origen_title']}]({st.session_state['origen_url']})")
        with col2:
            st.subheader("🔴 Destino")
            st.markdown(f"[{st.session_state['destino_title']}]({st.session_state['destino_url']})")

        st.markdown("---")
        st.subheader("📤 Rexistro de partida")

        usuario = st.selectbox("Quen xogou?", JUGADORES, index=0)
        saltos = st.number_input("Número de saltos", min_value=1, step=1)

        if st.button("💾 Gardar puntuación"):
            saltos_int = int(saltos)
            puntos = max(10 - saltos_int, 1)
            nova_fila = pd.DataFrame([{
                "usuario": usuario,
                "origen": st.session_state.get('origen_title', ''),
                "destino": st.session_state.get('destino_title', ''),
                "saltos": saltos_int,
                "puntos": puntos,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            safe_append_csv(DATA_FILE, nova_fila)
            st.success(f"Puntuación gardada! {usuario} obtivo {puntos} puntos 🏅")
            st.rerun()  # <- en lugar de experimental_rerun

        st.markdown("### 📊 Últimos rexistros")
        df = safe_read_csv(DATA_FILE)
        # Ordenando por texto funciona porque é YYYY-MM-DD HH:MM:SS; se queres 100% seguro, parsea:
        # df['fecha'] = pd.to_datetime(df['fecha'])
        st.dataframe(df.tail(10).sort_values(by="fecha", ascending=False), use_container_width=True)

with tab2:
    st.title("📈 Estatísticas e ranking")

    df = safe_read_csv(DATA_FILE)
    if df.empty:
        st.info("Aínda non hai rexistros.")
    else:
        # Tipado robusto
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df["puntos"] = pd.to_numeric(df["puntos"], errors="coerce")
        df["saltos"] = pd.to_numeric(df["saltos"], errors="coerce")

        resumen = (
            df.dropna(subset=["usuario", "puntos", "saltos"])
              .groupby("usuario", as_index=False)
              .agg(
                  partidas=("usuario", "count"),
                  total_puntos=("puntos", "sum"),
                  media_puntos=("puntos", "mean"),
                  media_saltos=("saltos", "mean")
              )
              .sort_values(by="total_puntos", ascending=False)
        )

        st.subheader("🏆 Ranking por puntos acumulados")
        st.dataframe(resumen, use_container_width=True)

        st.subheader("📈 Evolución temporal")
        chart = (
            alt.Chart(df.dropna(subset=["fecha"]))
               .mark_line(point=True)
               .encode(
                   x='fecha:T',
                   y='puntos:Q',
                   color='usuario:N',
                   tooltip=['usuario', 'origen', 'destino', 'puntos', 'saltos', 'fecha:T']
               )
               .properties(width=700, height=400)
        )
        st.altair_chart(chart, use_container_width=True)

        st.subheader("🥇 Podio das últimas 5 partidas")
        st.dataframe(df.sort_values(by="fecha", ascending=False).head(5), use_container_width=True)
