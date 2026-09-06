"""Estima el costo de desarrollo asistido por IA a partir del tamaño real de los diffs.

Uso:
    python corridas/calcular_costo_desarrollo.py

Para cada commit del repositorio, mide el tamaño real (en bytes) de su diff con
`git show` y estima tokens de salida con una heurística documentada
(~4 bytes ~ 1 token). Multiplica por la tarifa real de salida de Sonnet 5
($10.00 / 1M tokens) para obtener un costo mínimo estimado por commit.

Esto es una COTA INFERIOR, no el costo total de la sesión: sólo mide lo que
terminó commiteado (no cuenta tokens de entrada -contexto, historial de la
conversación, herramientas- ni el texto conversacional que no se plasmó en el
repo). El número autoritativo sale del dashboard de uso de la cuenta de
Anthropic o del comando `/cost` de Claude Code para esta sesión.
"""

import json
import subprocess
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent

BYTES_POR_TOKEN = 4.0  # heurística estándar para texto en inglés/español mixto con código
TARIFA_SALIDA_SONNET5_POR_MTOK = 10.00  # USD por 1,000,000 tokens de salida (Claude Sonnet 5)


def _commits() -> list:
    salida = subprocess.check_output(
        ["git", "log", "--reverse", "--format=%H|%ad|%s", "--date=short"],
        cwd=RAIZ_REPO,
        text=True,
    )
    commits = []
    for linea in salida.strip().splitlines():
        sha, fecha, asunto = linea.split("|", 2)
        commits.append({"sha": sha, "fecha": fecha, "asunto": asunto})
    return commits


def _tamano_diff_bytes(sha: str) -> int:
    diff = subprocess.check_output(["git", "show", sha], cwd=RAIZ_REPO)
    return len(diff)


def calcular_costo_desarrollo() -> dict:
    filas = []
    for commit in _commits():
        bytes_diff = _tamano_diff_bytes(commit["sha"])
        tokens_estimados = round(bytes_diff / BYTES_POR_TOKEN)
        costo_estimado = round(tokens_estimados / 1_000_000 * TARIFA_SALIDA_SONNET5_POR_MTOK, 4)
        filas.append(
            {
                "commit": commit["sha"][:7],
                "fecha": commit["fecha"],
                "asunto": commit["asunto"],
                "bytes_diff": bytes_diff,
                "tokens_salida_estimados": tokens_estimados,
                "costo_estimado_usd": costo_estimado,
            }
        )

    total_tokens = sum(fila["tokens_salida_estimados"] for fila in filas)
    total_costo = round(sum(fila["costo_estimado_usd"] for fila in filas), 4)

    return {
        "metodologia": (
            f"tokens_salida_estimados = bytes_del_diff / {BYTES_POR_TOKEN} (heurística); "
            f"costo = tokens_salida_estimados / 1e6 * ${TARIFA_SALIDA_SONNET5_POR_MTOK} "
            f"(tarifa de salida de Claude Sonnet 5). Cota inferior: no incluye tokens de "
            f"entrada/contexto ni texto conversacional descartado."
        ),
        "commits": filas,
        "total_tokens_salida_estimados": total_tokens,
        "total_costo_estimado_usd": total_costo,
    }


if __name__ == "__main__":
    resultado = calcular_costo_desarrollo()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
