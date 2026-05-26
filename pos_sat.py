from entities import Posicion, Objetivo
from distancia_sat import calcular_distancia_x, calcular_distancia_y


def obtener_objetivo_mas_cercano(posicion_actual: Posicion, objetivos: list[Objetivo]) -> Objetivo:
    return min(
        objetivos,
        key=lambda objetivo: abs(objetivo.y - posicion_actual.y) + abs(objetivo.x - posicion_actual.x)
    )


def obtener_distancias(posicion_actual: Posicion, objetivo: Objetivo):
    distancia_x = calcular_distancia_x(posicion_actual, objetivo)
    distancia_y = calcular_distancia_y(posicion_actual, objetivo)

    return distancia_x, distancia_y
