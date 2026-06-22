def fmt_money(valor: float) -> str:
    """Formatea un monto con punto como separador de miles y signo $, sin decimales.
    Ej: 207079.0 -> '$ 207.079'. (Convención local UY/AR.)"""
    return f"$ {valor:,.0f}".replace(",", ".")


def fmt_money_delta(valor: float) -> str:
    """Igual que fmt_money, pero para usar en el `delta` de st.metric: el signo "-" va
    primero (st.metric solo pinta la flecha roja si el string empieza con "-"; con fmt_money
    normal el "$" queda antes y la flecha de una baja se mostraba verde como si fuera una suba)."""
    return f"-{fmt_money(abs(valor))}" if valor < 0 else fmt_money(valor)
