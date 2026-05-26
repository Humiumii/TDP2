import math
from entities import SensorDistancia


def decidir_movimiento_x(sensor_distancia_x: SensorDistancia) -> str:
    if sensor_distancia_x.value > 0:
        return "avanzar"
    elif sensor_distancia_x.value < 0:
        return "retroceder"

    return "quieto_x"


def decidir_movimiento_y(sensor_distancia_y: SensorDistancia) -> str:
    if sensor_distancia_y.value > 0:
        return "bajar"
    elif sensor_distancia_y.value < 0:
        return "subir"

    return "quieto_y"


def calcular_paso_exacto(origen, destino):
    y1, x1 = origen
    y2, x2 = destino

    dy = y2 - y1
    dx = x2 - x1

    distancia = math.sqrt(dy**2 + dx**2)

    if distancia == 0:
        return 0, 0

    paso_y = dy / distancia
    paso_x = dx / distancia

    return paso_y, paso_x
