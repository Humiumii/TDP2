from dataclasses import dataclass


@dataclass
class SensorDistancia:
    id: int
    value: float


@dataclass
class SensorDecibeles:
    value: float


@dataclass
class Posicion:
    y: float
    x: float


@dataclass
class Objetivo:
    y: float
    x: float
