def fmt_money(valor: float) -> str:
    """Formatea un monto con punto como separador de miles y signo $, sin decimales.
    Ej: 207079.0 -> '$ 207.079'. (Convención local UY/AR.)"""
    return f"$ {valor:,.0f}".replace(",", ".")
