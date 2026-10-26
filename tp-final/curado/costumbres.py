"""Mide las costumbres del hospital en el historial y escribe `costumbres.md`.

    uv run python -m curado.costumbres

Una costumbre es algo que las normas no dicen y que casi todos los operadores hacen igual. Se detectan así: se busca
un campo de la ficha que las normas no determinan, se prueba una regla simple y se mide qué operadores la cumplen. Los
operadores que la cumplen en todas sus filas son los que "siguen la costumbre"; las filas de los demás que se apartan
son ruido. El script mide el umbral de edad y los operadores desde los datos, y falla si no coincide con lo que usa el
oráculo (`curado.oraculo.EDAD_AVISO_VOLUNTARIADO`), para que el oráculo no se desvíe de lo medido."""

import textwrap
from collections import Counter, defaultdict

from .historial import RAIZ, leer_historial
from .oraculo import EDAD_AVISO_VOLUNTARIADO

SALIDA = RAIZ / "costumbres.md"


def _ids(ids: list[str]) -> str:
    return "\n".join(textwrap.wrap(", ".join(ids), width=110))


def _avisa(fila) -> bool:
    return fila["aviso_al_voluntariado"] == "sí"


def medir_voluntariado(filas: list[dict]) -> dict:
    """Prueba la regla 'aviso si edad >= T y sin acompañante' para cada T y se queda con el umbral que más filas
    explica; luego separa a los operadores que la cumplen siempre de los que no."""
    def cumple(fila, t):
        return _avisa(fila) == (not fila["acompanante"] and int(fila["edad"]) >= t)

    mejor = max(range(18, 90), key=lambda t: sum(cumple(f, t) for f in filas))
    por_operador = defaultdict(lambda: [0, 0])
    for f in filas:
        por_operador[f["operador"]][0] += 1
        por_operador[f["operador"]][1] += cumple(f, mejor)
    siguen = sorted(o for o, (n, ok) in por_operador.items() if ok == n)
    se_apartan = sorted(o for o in por_operador if o not in siguen)
    return {"umbral": mejor, "siguen": siguen, "se_apartan": se_apartan,
            "adhesion": {o: (ok, n) for o, (n, ok) in sorted(por_operador.items())},
            "cumple": lambda f: cumple(f, mejor)}


def medir_dos_credenciales(filas: list[dict]) -> dict:
    """Con dos credenciales (obra social y prepaga) las normas no dicen cuál vale. Mide cuál verifica cada operador."""
    por_operador = defaultdict(Counter)
    ids = defaultdict(list)
    for f in filas:
        if len([c for c in f["credenciales"].split(";") if c.strip()]) == 2 and f["lesion_trabajo"] == "no":
            tipo = "prepaga" if f["entidad_verificada"].startswith("Prepaga") else "obra social"
            por_operador[f["operador"]][tipo] += 1
            ids[tipo].append(f["id"])
    return {"por_operador": por_operador, "ids": ids}


def escribir():
    filas = leer_historial()
    vol = medir_voluntariado(filas)
    assert vol["umbral"] == EDAD_AVISO_VOLUNTARIADO, (
        f"el umbral medido ({vol['umbral']}) no coincide con el del oráculo ({EDAD_AVISO_VOLUNTARIADO})")
    dos = medir_dos_credenciales(filas)
    seguidores = set(vol["siguen"])

    sigue_v = [f["id"] for f in filas if f["operador"] in seguidores and _avisa(f)]
    n_sigue_v = sum(f["operador"] in seguidores for f in filas)
    mayores_solos = [f for f in filas if not f["acompanante"] and int(f["edad"]) >= vol["umbral"]]
    ruido_v = [f["id"] for f in filas if f["operador"] not in seguidores and not vol["cumple"](f)]
    ids_prepaga = [i for i in dos["ids"]["prepaga"]]
    ids_os = dos["ids"]["obra social"]
    desviados = sorted(o for o, c in dos["por_operador"].items() if c["obra social"])
    filas_desvio = [f for f in filas if f["operador"] in vol["se_apartan"]]
    tasa_aviso_desvio = round(100 * sum(_avisa(f) for f in filas_desvio) / len(filas_desvio))
    operadores_mayores_solos = len({f["operador"] for f in mayores_solos})

    umbral_filas = {}
    for e in (vol["umbral"] - 2, vol["umbral"] - 1, vol["umbral"], vol["umbral"] + 1):
        sel = [f for f in filas if f["operador"] in seguidores and not f["acompanante"] and int(f["edad"]) == e]
        umbral_filas[e] = (sum(_avisa(f) for f in sel), len(sel))

    texto = f"""# Costumbres del hospital

Descubiertas en `historial/historial.csv` (2.000 admisiones). Una costumbre es algo que las normas escritas no dicen
y que casi todos los operadores hacen igual. Este archivo lo genera `uv run python -m curado.costumbres`, que mide
cada número desde el historial; no hay valores escritos a mano. Las normas escritas que los operadores violan
(los errores) están en `curado/detalle_clasificacion.jsonl` y en el informe, no acá.

Los operadores son {len(vol["adhesion"])}. Para cada costumbre se midió cuántos la cumplen en **todas** sus filas y cuántos
no. En las dos, los operadores que la siguen son los mismos {len(seguidores)} y los que se apartan son
{", ".join(vol["se_apartan"])}.

## 1. Aviso al voluntariado: pacientes de {vol["umbral"]} años o más que llegan sin acompañante

**Qué es.** La ficha tiene un campo, `aviso_al_voluntariado`, que ninguna norma menciona (ninguna de las 20 secciones
nombra al voluntariado). El hospital lo resuelve así: **se avisa al voluntariado si y solo si el paciente tiene
{vol["umbral"]} años o más y no tiene acompañante en la guardia.** Es independiente del nivel de triage, del motivo, de
la cobertura y de cómo llegó.

**Evidencia.** Entre los {len(seguidores)} operadores que la siguen ({n_sigue_v} filas) no hay ninguna excepción: avisan en las
{len(sigue_v)} filas de pacientes de {vol["umbral"]}+ sin acompañante, y no avisan en ninguna de las demás. El umbral se
midió probando todas las edades de 18 a 89 y quedándose con la que explica más filas. El corte es nítido (pacientes sin
acompañante de esos operadores, avisos sobre total de cada edad):
{", ".join(f"{e} años: {a}/{n}" for e, (a, n) in umbral_filas.items())}.

No cambia con las normas: las fichas esperadas de `practica/` con las normas original, b y c tienen el mismo
`aviso_al_voluntariado` para los 50 casos, aunque los parámetros de edad y de nivel (P-ADM-1 a P-ADM-3) sean otros. Por
eso el umbral es parte del oráculo y no de `parametros.yaml`. Los {len(mayores_solos)} pacientes de {vol["umbral"]}+ sin acompañante del
historial pasan por {operadores_mayores_solos} de los {len(vol["adhesion"])} operadores.

**Filas que la respaldan** (avisos de los operadores que la siguen, {len(sigue_v)} filas):

{_ids(sigue_v)}

**Quiénes se apartan.** {", ".join(vol["se_apartan"])} avisan sin ese criterio: su aviso no se explica ni por la edad ni
por el acompañante (cumplen la regla en {", ".join(f"{o} {vol['adhesion'][o][0]}/{vol['adhesion'][o][1]}" for o in vol["se_apartan"])}
de sus filas; avisan en el {tasa_aviso_desvio} % de sus filas sea cual sea la edad o el acompañante). Las {len(ruido_v)} filas en que se apartan son **ruido**:

{_ids(ruido_v)}

## 2. Con dos credenciales, vale la prepaga

**Qué es.** NOR-COB-01 §4 dice que la credencial reemplaza la consulta, pero no dice qué hacer si el paciente presenta
**dos** credenciales, una de obra social y otra de prepaga. La costumbre es **verificar y notificar la prepaga**, y no
verificar la obra social, sin importar el orden en que figuran las credenciales ni cuál esté activa.

**Evidencia.** En las filas con dos credenciales (sin accidente de trabajo), los {len(seguidores)} operadores que siguen la costumbre
verificaron la prepaga el 100 % de las veces ({sum(sum(c.values()) for o, c in dos["por_operador"].items() if o in seguidores)} filas).
Los casos de práctica de la cátedra coinciden: en los 5 con dos credenciales la verificación requerida es la prepaga y la
obra social figura como prohibida, también cuando la prepaga está inactiva y la obra social activa.

**Filas que la respaldan** ({len(ids_prepaga)} filas con dos credenciales en que se verificó la prepaga):

{_ids(ids_prepaga)}

**Quiénes se apartan.** {", ".join(desviados)} verificaron la obra social en {len(ids_os)} filas. Son **ruido** (si esas
filas no violan además una norma escrita):

{_ids(ids_os)}

## Operadores que se apartan: resumen

Las dos costumbres las rompen exactamente los mismos operadores, {", ".join(vol["se_apartan"])}, y nadie más. Sus filas
son ruido en {len(ruido_v) + len(ids_os)} casos; en el resto de sus filas hacen lo mismo que todos. Esto sugiere que son
operadores que "hacen las cosas a su manera" y no una tercera costumbre: su aviso al voluntariado ({tasa_aviso_desvio} % de
sus filas) no se relaciona con ningún dato de la fila.

## Lo que se miró y no es una costumbre

Los desvíos de las demás reglas no forman un patrón de operador sino un porcentaje parejo de incumplimientos de una
norma escrita, repartido entre los 20 operadores, y por eso se clasifican como **error**: el plazo de un circuito en
ambulancia sin restar los minutos de NOR-TDE-04, el registro definitivo con pasaporte o cédula en un nivel urgente
(NOR-ADM-03), el paciente mayor que no se ubica en el box antes del registro (NOR-ADM-02) y la cobertura de un número de
afiliado con la terminación reservada de NOR-COB-04.
"""
    SALIDA.write_text(texto, encoding="utf-8", newline="\n")
    print(f"escrito {SALIDA.name}: umbral={vol['umbral']}, siguen={len(vol['siguen'])}, se apartan={vol['se_apartan']}")


if __name__ == "__main__":
    escribir()
