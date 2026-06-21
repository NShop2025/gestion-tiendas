import os

import streamlit as st


def _usuarios_validos() -> dict[str, str]:
    raw = os.environ.get("APP_USERS", "")
    usuarios = {}
    for par in raw.split(","):
        if ":" not in par:
            continue
        nombre, clave = par.split(":", 1)
        usuarios[nombre.strip()] = clave.strip()
    return usuarios


def requerir_login() -> str:
    """Bloquea la página hasta que el usuario ingrese credenciales válidas. Devuelve el nombre logueado."""
    if "usuario" in st.session_state:
        return st.session_state["usuario"]

    st.title("Gestión Tiendas")
    with st.form("login"):
        nombre = st.text_input("Usuario")
        clave = st.text_input("Clave", type="password")
        enviado = st.form_submit_button("Entrar")

    if enviado:
        usuarios = _usuarios_validos()
        if usuarios.get(nombre) == clave and clave != "":
            st.session_state["usuario"] = nombre
            st.rerun()
        else:
            st.error("Usuario o clave incorrectos")

    st.stop()
