from entities import SensorDecibeles


def decidir_accion(sensor_decibeles: SensorDecibeles) -> str:
    if sensor_decibeles.value > 50:
        return "atacar"

    return "ignorar"
