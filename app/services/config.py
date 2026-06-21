import os

import streamlit as st
from dotenv import load_dotenv


def cargar_config() -> None:
    """Carga config desde .env (local) o desde st.secrets (Streamlit Cloud), unificando
    todo en variables de entorno para que el resto de la app no tenga que distinguir."""
    load_dotenv()
    try:
        for clave, valor in st.secrets.items():
            os.environ.setdefault(clave, str(valor))
    except FileNotFoundError:
        pass  # no hay secrets.toml local, normal en desarrollo
