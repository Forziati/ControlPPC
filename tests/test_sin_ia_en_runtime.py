"""Verifica programáticamente que el sistema no usa IA generativa en runtime.

`docs/ANALISIS_ECONOMICO.md` y `docs/GOBERNANZA.md` afirman que el cálculo de
PPC, inversión, curva S y CNC es 100% determinístico (pandas), sin ninguna
llamada a un modelo de lenguaje. Este test hace esa afirmación reproducible en
vez de sólo declarada: falla si alguien agrega en el futuro un import de un SDK
de IA generativa a `src/` o a `streamlit_app.py`.
"""

import re
import unittest
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent

PATRONES_SDK_IA = [
    r"\bimport\s+anthropic\b",
    r"\bimport\s+openai\b",
    r"\bfrom\s+anthropic\b",
    r"\bfrom\s+openai\b",
    r"\bimport\s+google\.generativeai\b",
    r"\bfrom\s+google\.generativeai\b",
    r"\bimport\s+cohere\b",
    r"\bfrom\s+cohere\b",
    r"\bimport\s+langchain\b",
    r"\bfrom\s+langchain\b",
    r"\bimport\s+mistralai\b",
    r"\bfrom\s+mistralai\b",
    r"\bimport\s+ollama\b",
]

ARCHIVOS_RUNTIME = [
    RAIZ_REPO / "streamlit_app.py",
    *sorted((RAIZ_REPO / "src").glob("*.py")),
]


class TestSinIAEnRuntime(unittest.TestCase):
    def test_ningun_archivo_de_runtime_importa_un_sdk_de_ia(self):
        regex = re.compile("|".join(PATRONES_SDK_IA))
        coincidencias = []

        for ruta in ARCHIVOS_RUNTIME:
            contenido = ruta.read_text(encoding="utf-8")
            if regex.search(contenido):
                coincidencias.append(str(ruta.relative_to(RAIZ_REPO)))

        self.assertEqual(
            coincidencias,
            [],
            f"Se encontró un import de SDK de IA generativa en: {coincidencias}. "
            "Esto contradice DEC-001 y la afirmación de costo $0 en runtime "
            "de docs/ANALISIS_ECONOMICO.md.",
        )

    def test_requirements_no_incluye_sdks_de_ia_generativa(self):
        requirements = (RAIZ_REPO / "requirements.txt").read_text(encoding="utf-8").lower()
        paquetes_ia = ["anthropic", "openai", "google-generativeai", "cohere", "langchain", "mistralai"]
        encontrados = [paquete for paquete in paquetes_ia if paquete in requirements]
        self.assertEqual(encontrados, [])

    def test_hay_al_menos_un_archivo_de_runtime_para_auditar(self):
        # Guarda contra un refactor que borre streamlit_app.py o vacíe src/ sin darse cuenta.
        self.assertGreaterEqual(len(ARCHIVOS_RUNTIME), 5)


if __name__ == "__main__":
    unittest.main()
