import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime
import os
import requests
import altair as alt

DATA_FILE = "puntuaciones.csv"
JUGADORES = ["Alejandro", "Nicolás"]

def get_random_wikipedia_article():
    url = "https://es.wikipedia.org/api/rest_v1/page/random/summary"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['title'], data['content_urls']['desktop']['page']
    else:
        return "Error", "#"

if not os.path.exists(DATA_FILE):
    df_vacio = pd.DataFrame(columns=["usuario", "origen", "destino", "saltos", "puntos", "fecha"])
    df_vacio.to_csv(DATA_FILE, index=False)

st.set_page_config(page_title="Hipervínculos", layout="wide")

tab1, tab2 = st.tabs(["🎮 Xogo", "📈 Estatísticas"])

with tab1:
    st.title("🧩 Hipervínculos – O xogo do wikisalto ")
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
            st.markdown(f"[{st.session_state['origen_title']}]({st.session_state['origen_url']})", unsafe_allow_html=True)
        with col2:
            st.subheader("🔴 Destino")
            st.markdown(f"[{st.session_state['destino_title']}]({st.session_state['destino_url']})", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📤 Rexistro de partida")

        usuario = st.selectbox("Quen xogou?", JUGADORES)
        saltos = st.number_input("Número de saltos", min_value=1, step=1)

        if st.button("💾 Gardar puntuación"):
            puntos = max(10 - saltos, 1)
            nova_fila = pd.DataFrame([{
                "usuario": usuario,
                "origen": st.session_state['origen_title'],
                "destino": st.session_state['destino_title'],
                "saltos": saltos,
                "puntos": puntos,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, nova_fila], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"Puntuación gardada! {usuario} obtivo {puntos} puntos 🏅")
            st.experimental_rerun()

        st.markdown("### 📊 Últimos rexistros")
        df = pd.read_csv(DATA_FILE)
        st.dataframe(df.tail(10).sort_values(by="fecha", ascending=False))

with tab2:
    st.title("📈 Estatísticas e ranking")

    df = pd.read_csv(DATA_FILE)
    if df.empty:
        st.info("Aínda non hai rexistros.")
    else:
        df["fecha"] = pd.to_datetime(df["fecha"])
        resumen = df.groupby("usuario").agg(
            partidas=("usuario", "count"),
            total_puntos=("puntos", "sum"),
            media_puntos=("puntos", "mean"),
            media_saltos=("saltos", "mean")
        ).sort_values(by="total_puntos", ascending=False).reset_index()

        st.subheader("🏆 Ranking por puntos acumulados")
        st.dataframe(resumen)

        st.subheader("📈 Evolución temporal")
        chart = alt.Chart(df).mark_line(point=True).encode(
            x='fecha:T',
            y='puntos:Q',
            color='usuario:N',
            tooltip=['usuario', 'origen', 'destino', 'puntos', 'saltos', 'fecha']
        ).properties(width=700, height=400)
        st.altair_chart(chart, use_container_width=True)

        st.subheader("🥇 Podio das últimas 5 partidas")
        st.dataframe(df.sort_values(by="fecha", ascending=False).head(5))
