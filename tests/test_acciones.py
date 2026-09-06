import unittest
from datetime import date

from src.gestor_acciones import (
    actualizar_estado,
    crear_accion,
    listar_acciones_vencidas,
    obtener_accion_vigente_por_cnc,
    validar_accion,
)


class TestGestorAcciones(unittest.TestCase):
    def test_crear_accion_valida(self):
        accion = crear_accion("SM", "Comprar materiales", "Juan Pérez", "juan@example.com", date(2026, 1, 15))
        self.assertEqual(accion["estado"], "pendiente")
        self.assertEqual(accion["cnc"], "SM")
        self.assertIn("id", accion)

    def test_crear_accion_campos_faltantes(self):
        with self.assertRaises(ValueError):
            crear_accion("SM", "", "Juan Pérez", "juan@example.com", date(2026, 1, 15))

    def test_crear_accion_email_invalido(self):
        with self.assertRaises(ValueError):
            crear_accion("SM", "Comprar materiales", "Juan Pérez", "no-es-un-email", date(2026, 1, 15))

    def test_validar_accion_devuelve_lista_vacia_si_es_valida(self):
        accion = {
            "cnc": "SM",
            "descripcion": "Comprar materiales",
            "responsable": "Juan",
            "email": "juan@example.com",
            "fecha_plazo": "2026-01-15",
        }
        self.assertEqual(validar_accion(accion), [])

    def test_actualizar_estado_accion(self):
        accion = crear_accion("SM", "Comprar materiales", "Juan Pérez", "juan@example.com", date(2026, 1, 15))
        acciones = [accion]
        actualizar_estado(acciones, accion["id"], "completada", resultado="positivo", observaciones="Listo")
        self.assertEqual(acciones[0]["estado"], "completada")
        self.assertEqual(acciones[0]["resultado"], "positivo")
        self.assertEqual(acciones[0]["observaciones"], "Listo")

    def test_actualizar_estado_id_inexistente(self):
        with self.assertRaises(ValueError):
            actualizar_estado([], "id-inexistente", "completada")

    def test_actualizar_estado_invalido(self):
        accion = crear_accion("SM", "Comprar materiales", "Juan Pérez", "juan@example.com", date(2026, 1, 15))
        with self.assertRaises(ValueError):
            actualizar_estado([accion], accion["id"], "estado_invalido")

    def test_obtener_accion_vigente_por_cnc_devuelve_la_mas_reciente(self):
        vieja = crear_accion("SM", "Primera acción", "Juan", "juan@example.com", date(2026, 1, 10))
        vieja["fecha_creacion"] = "2026-01-01T00:00:00"
        nueva = crear_accion("SM", "Segunda acción", "Ana", "ana@example.com", date(2026, 1, 20))
        nueva["fecha_creacion"] = "2026-01-15T00:00:00"
        acciones = [vieja, nueva]

        vigente = obtener_accion_vigente_por_cnc("SM", acciones)

        self.assertEqual(vigente["descripcion"], "Segunda acción")

    def test_obtener_accion_vigente_por_cnc_sin_coincidencias(self):
        accion = crear_accion("SM", "Comprar materiales", "Juan", "juan@example.com", date(2026, 1, 15))
        self.assertIsNone(obtener_accion_vigente_por_cnc("FT", [accion]))

    def test_listar_acciones_vencidas_detecta_plazo_pasado(self):
        vencida = crear_accion("SM", "Comprar materiales", "Juan", "juan@example.com", date(2026, 1, 1))
        vigente = crear_accion("FT", "Sumar cuadrilla", "Ana", "ana@example.com", date(2026, 6, 1))
        acciones = [vencida, vigente]

        resultado = listar_acciones_vencidas(acciones, fecha_referencia=date(2026, 3, 1))

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["cnc"], "SM")

    def test_listar_acciones_vencidas_ignora_completadas(self):
        accion = crear_accion("SM", "Comprar materiales", "Juan", "juan@example.com", date(2026, 1, 1))
        actualizar_estado([accion], accion["id"], "completada")

        resultado = listar_acciones_vencidas([accion], fecha_referencia=date(2026, 3, 1))

        self.assertEqual(resultado, [])

    def test_listar_acciones_vencidas_sin_vencidas(self):
        accion = crear_accion("SM", "Comprar materiales", "Juan", "juan@example.com", date(2026, 12, 1))
        self.assertEqual(listar_acciones_vencidas([accion], fecha_referencia=date(2026, 3, 1)), [])


if __name__ == "__main__":
    unittest.main()
