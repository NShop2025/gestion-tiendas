from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.services.db import get_engine

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
LOGOS_POR_SLUG = {
    "neptunoshop": ASSETS_DIR / "logo_neptuno.jpeg",
    "marea": ASSETS_DIR / "logo_marea.jpeg",
}


@st.cache_data(ttl=300)
def listar_tiendas() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text("select id, nombre, slug from tiendas where activa order by nombre"),
            conn,
        )


def _sincronizar_tienda():
    # El key del widget no sobrevive el cambio de página en Streamlit (cada página es un
    # script distinto); por eso copiamos el valor a una entrada de session_state aparte,
    # que sí persiste entre páginas igual que el login.
    st.session_state["tienda_nombre"] = st.session_state["tienda_widget"]


def selector_tienda() -> tuple[str, str]:
    """Muestra un selector de tienda en la sidebar, persistente entre páginas.
    Devuelve (tienda_id, nombre)."""
    tiendas = listar_tiendas()
    if tiendas.empty:
        st.sidebar.error("No hay tiendas cargadas todavía.")
        st.stop()

    opciones = tiendas["nombre"].tolist()
    if "tienda_nombre" not in st.session_state or st.session_state["tienda_nombre"] not in opciones:
        st.session_state["tienda_nombre"] = opciones[0]

    index = opciones.index(st.session_state["tienda_nombre"])
    st.sidebar.selectbox("Tienda", opciones, index=index, key="tienda_widget", on_change=_sincronizar_tienda)

    nombre = st.session_state["tienda_nombre"]
    fila = tiendas[tiendas["nombre"] == nombre].iloc[0]

    logo = LOGOS_POR_SLUG.get(fila["slug"])
    if logo and logo.exists():
        st.logo(str(logo), size="large")

    return fila["id"], fila["nombre"]
