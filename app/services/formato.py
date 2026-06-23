def fmt_money(valor: float) -> str:
    """Formatea un monto con punto como separador de miles y signo $, sin decimales.
    Ej: 207079.0 -> '$ 207.079'. (Convención local UY/AR.)"""
    return f"$ {valor:,.0f}".replace(",", ".")


def fmt_money_delta(valor: float) -> str:
    """Igual que fmt_money, pero para usar en el `delta` de st.metric: el signo "-" va
    primero (st.metric solo pinta la flecha roja si el string empieza con "-"; con fmt_money
    normal el "$" queda antes y la flecha de una baja se mostraba verde como si fuera una suba)."""
    return f"-{fmt_money(abs(valor))}" if valor < 0 else fmt_money(valor)


def tarjeta_metrica(titulo: str, valor: str) -> str:
    """HTML de una tarjeta de métrica chica (con fondo y borde, como la de saldo pero más
    compacta), para que las métricas no queden como texto plano flotando sobre el fondo."""
    return f"""
        <div style="
            padding: 0.9rem 1.1rem; border-radius: 12px; height: 100%;
            background: #181C26; border: 1px solid #262B38;">
            <div style="font-size: 0.72rem; letter-spacing: 0.04em; text-transform: uppercase;
                        color: #8A90A0; margin-bottom: 0.3rem;">{titulo}</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #E6E8EC; line-height: 1.1;">
                {valor}</div>
        </div>
        """
