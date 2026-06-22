"""Categoriza el histórico de gastos de NeptunoShop (cargados antes de que existiera la
columna categoria, que quedaron todos en 'otros' por default).

Mapeo armado a mano revisando los 95 valores distintos de concepto que había en la base
el 2026-06-22. Si aparece un concepto nuevo que no está en el mapeo, se deja en 'otros'
y se avisa al final para revisarlo a mano.

Uso:
    python scripts/categorizar_gastos.py --dry-run   # solo muestra qué haría
    python scripts/categorizar_gastos.py              # aplica los cambios
"""

import argparse
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

MAPEO = {
    # BPS / Impuestos
    "BPS": "bps_impuestos",
    "DGI": "bps_impuestos",
    "IRAE": "bps_impuestos",
    "UES": "bps_impuestos",
    # Contabilidad / Software
    "contabilium": "contabilidad_software",
    "contador": "contabilidad_software",
    "Contador": "contabilidad_software",
    "ALEGRA": "contabilidad_software",
    "canva": "contabilidad_software",
    "Artlist": "contabilidad_software",
    "artlist ": "contabilidad_software",
    "Photoroom": "contabilidad_software",
    "hosting ": "contabilidad_software",
    "ampliación hosting ": "contabilidad_software",
    "dominio": "contabilidad_software",
    "dominio Marea": "contabilidad_software",
    "dominio Neptuno Shop": "contabilidad_software",
    # Publicidad
    "publicidad": "publicidad",
    "publicidad fb": "publicidad",
    "publicidad fb ": "publicidad",
    "publicidad Ig": "publicidad",
    "publicidad IG": "publicidad",
    "Publicidad ig": "publicidad",
    "Publicidad IG": "publicidad",
    "Publicidad Ig ": "publicidad",
    "publicidad meta": "publicidad",
    "Publicidad meta": "publicidad",
    "Publicidad ML ": "publicidad",
    # Packing / Insumos
    "Bolsas": "packing_insumos",
    "bolsas ": "packing_insumos",
    "Bolsas + cinta": "packing_insumos",
    "Bolsas nylon": "packing_insumos",
    "Bolsas TNT (32)": "packing_insumos",
    "CINTA ADHESIVA": "packing_insumos",
    "cintas": "packing_insumos",
    "Cintas": "packing_insumos",
    "Etiquetas impresora": "packing_insumos",
    "ETIQUETAS TEMU": "packing_insumos",
    "Film": "packing_insumos",
    "hojas a4 (2paq)": "packing_insumos",
    "IMPRESORA TEMU": "packing_insumos",
    "ARREGLO IMPRESORA": "packing_insumos",
    "Packing": "packing_insumos",
    "ESTANTERIAS": "packing_insumos",
    "Estanterias x4": "packing_insumos",
    "LUCAS (Bolsas)": "packing_insumos",
    "Martin - bolsas rocha": "packing_insumos",
    # Envíos / Cadetería
    "CORREO": "envios_cadeteria",
    "Correo (arbol)": "envios_cadeteria",
    "CORREO (PH)": "envios_cadeteria",
    "CORREO LAMPARAS": "envios_cadeteria",
    "CORREO VENTA WEB": "envios_cadeteria",
    "envío a salto": "envios_cadeteria",
    "envío de mercaderia ": "envios_cadeteria",
    "PAGO A LUCAS POR DESPACHOS/FLEX": "envios_cadeteria",
    # Combustible / Viáticos
    "DAC": "combustible_viaticos",
    "DAC ": "combustible_viaticos",
    "DAC (a casa)": "combustible_viaticos",
    "DAC (a Salto)": "combustible_viaticos",
    "DAC (Mandó Claudia cuando estabamos en Buzios)": "combustible_viaticos",
    "DAC buzos ig": "combustible_viaticos",
    "dac canguros": "combustible_viaticos",
    "Dac ida Maldonado": "combustible_viaticos",
    "DAC LAMPARA CULTIVO": "combustible_viaticos",
    "DAC MOTOSIERRA": "combustible_viaticos",
    "DAC venta wbe": "combustible_viaticos",
    "DAC venta web": "combustible_viaticos",
    "Dac vuelta Maldonado": "combustible_viaticos",
    "ida al chuy": "combustible_viaticos",
    "ida Chuy": "combustible_viaticos",
    "Ida Chuy": "combustible_viaticos",
    "ida chuy (martin)": "combustible_viaticos",
    "combustible chuy bolsa": "combustible_viaticos",
    "combustible y peaje pde": "combustible_viaticos",
    "nafta y peajes bolsas": "combustible_viaticos",
    "medias chuy": "combustible_viaticos",
    # Otros (asados, comisiones bancarias, compras de equipo sueltas, nombres propios sin
    # contexto claro - mejor dejarlos en Otros que adivinar mal)
    "Asadito": "otros",
    "Asado Cuchilla": "otros",
    "asado dom": "otros",
    "ASADO DOMINGO": "otros",
    "Comision de los putos de Santander": "otros",
    "Comision Santander": "otros",
    "DRON F10 + GUANTE SPIDER SOTO": "otros",
    "E99 SOTO": "otros",
    "GUANTE SPIDER": "otros",
    "SOTO DRONES": "otros",
    "Lucia": "otros",
    "LUCIA": "otros",
    "NUÑEZ": "otros",
    "PEDIDOS YA (ZENSEI)": "otros",
    "POS MERCADO PAGO": "otros",
    "ROMY": "otros",
    "Saldo pendiente en Romy (ni idea)": "otros",
    "SALDO CELU": "otros",
    "TURIL": "otros",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    engine = create_engine(os.environ["DATABASE_URL"])

    with engine.begin() as conn:
        conceptos_db = {
            row[0] for row in conn.execute(text("select distinct concepto from gastos")).fetchall()
        }
        sin_mapeo = conceptos_db - set(MAPEO.keys())

        for concepto, categoria in MAPEO.items():
            if concepto not in conceptos_db:
                continue
            res = conn.execute(
                text("update gastos set categoria = :categoria where concepto = :concepto"),
                {"categoria": categoria, "concepto": concepto},
            )
            print(f"{concepto!r:55} -> {categoria:25} ({res.rowcount} fila(s))")

        if args.dry_run:
            conn.rollback()

    if sin_mapeo:
        print("\nConceptos sin mapeo (quedaron en 'otros' por default, revisar a mano):")
        for c in sorted(sin_mapeo):
            print(f"  {c!r}")

    if args.dry_run:
        print("\n(dry-run: no se modificó nada)")


if __name__ == "__main__":
    main()
