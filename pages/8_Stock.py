import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.reportes import stock_actual
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Stock", page_icon="📦", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Stock — {tienda_nombre}")

df = stock_actual(tienda_id)
if df.empty:
    st.info("Todavía no hay productos cargados.")
    st.stop()

negativos = df[df["stock_actual"] < 0]
if not negativos.empty:
    st.warning(
        f"{len(negativos)} producto(s) con stock negativo: compras y ventas no cierran. "
        "Revisar con un conteo físico."
    )

buscar = st.text_input("Buscar producto")
df_filtrado = df[df["producto"].str.contains(buscar, case=False, na=False)] if buscar else df

st.dataframe(
    df_filtrado.rename(
        columns={
            "producto": "Producto",
            "total_comprado": "Comprado",
            "total_vendido": "Vendido",
            "stock_actual": "Stock actual",
        }
    ),
    use_container_width=True,
    hide_index=True,
)
