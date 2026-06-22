from datetime import date

import streamlit as st
from sqlalchemy import text

from app.services.db import get_engine


def panel_eliminar(
    tienda_id: str,
    tabla: str,
    buscar_fn,
    columnas: dict,
    key: str,
    limpiar_cache=(),
    fecha_desde_default: date | None = None,
):
    """Expander con filtro de fecha/texto + tabla editable para tildar y borrar registros
    viejos que no aparecen en el panel de "últimas cargadas".

    columnas: dict columna_db -> etiqueta a mostrar (sin incluir "id", se maneja aparte).
    limpiar_cache: funciones de cache (st.cache_data) a invalidar después de borrar.
    """
    with st.expander("🗑️ Buscar y eliminar un registro viejo"):
        c1, c2, c3 = st.columns([1, 1, 2])
        desde = c1.date_input(
            "Desde", value=fecha_desde_default or date(date.today().year, 1, 1), key=f"desde_{key}"
        )
        hasta = c2.date_input("Hasta", value=date.today(), key=f"hasta_{key}")
        texto = c3.text_input("Buscar texto (producto, concepto, comentario...)", key=f"texto_{key}")

        df = buscar_fn(tienda_id, desde, hasta, texto)

        if df.empty:
            st.caption("No hay registros para ese filtro.")
            return

        df_editor = df.drop(columns=["id"]).rename(columns=columnas)
        df_editor.insert(0, "Eliminar", False)

        editado = st.data_editor(
            df_editor,
            hide_index=True,
            use_container_width=True,
            disabled=[c for c in df_editor.columns if c != "Eliminar"],
            key=f"editor_{key}",
        )

        seleccionados = df.loc[editado["Eliminar"].to_numpy()]
        if not seleccionados.empty:
            if st.button(
                f"Eliminar {len(seleccionados)} registro(s) seleccionado(s)",
                key=f"borrar_{key}",
                type="primary",
            ):
                ids = seleccionados["id"].tolist()
                engine = get_engine()
                with engine.begin() as conn:
                    conn.execute(text(f"delete from {tabla} where id = any(:ids)"), {"ids": ids})
                for fn in limpiar_cache:
                    fn.clear()
                st.success(f"{len(ids)} registro(s) eliminado(s).")
                st.rerun()
