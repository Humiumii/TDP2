from entities import SensorDistancia, Posicion, Objetivo


def calcular_distancia_x(origen: Posicion, objetivo: Objetivo) -> SensorDistancia:
    distancia_x = objetivo.x - origen.x
    return SensorDistancia(id=1, value=distancia_x)


def calcular_distancia_y(origen: Posicion, objetivo: Objetivo) -> SensorDistancia:
    distancia_y = objetivo.y - origen.y
    return SensorDistancia(id=2, value=distancia_y)
