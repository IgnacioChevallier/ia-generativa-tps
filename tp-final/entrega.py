"""Entrega del grupo: lo único que llama la cátedra (contrato en task/README.md)."""

from pathlib import Path

from buscador import BuscadorNormas


def construir_buscador(ruta_normas: Path) -> BuscadorNormas:
    return BuscadorNormas(ruta_normas)


def construir_agente():
    raise NotImplementedError("el agente se arma en las Partes 3 y 4")
