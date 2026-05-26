import random
import time
import os

from entities import Posicion, Objetivo
from pos_sat import obtener_objetivo_mas_cercano, obtener_distancias
from objetivo_sat import decidir_movimiento_x, decidir_movimiento_y, calcular_paso_exacto
from decibeles_sat import leer_decibeles
from filtro_sat import decidir_accion
from grid import draw_grid, draw_sonar
from audio import start_instance, stop_one_instance, stop_all_instances

# Optional RabbitMQ integration
try:
    import json
    import threading
    import pika

    RABBIT_URL = os.getenv('RABBIT_URL', 'amqp://guest:guest@localhost:5672/%2F')
    try:
        _params = pika.URLParameters(RABBIT_URL)
        _conn = pika.BlockingConnection(_params)
        _ch = _conn.channel()
        _ch.exchange_declare(exchange='sonar', exchange_type='fanout', durable=True)
        _ch.queue_declare(queue='main_responses', durable=True)

        def _on_response(ch, method, properties, body):
            try:
                msg = json.loads(body)
            except Exception:
                print('[MAIN-RMQ] Mensaje no JSON recibido')
                return

            node = msg.get('node')
            status = msg.get('status')
            sound = msg.get('sound')
            print(f"[MAIN-RMQ] Mensaje de {node}: {status} (sound={sound})")

            if status == 'playing':
                control_queue = f'node.{node}.control'
                payload = json.dumps({'cmd': 'stop'})
                ch.basic_publish(exchange='', routing_key=control_queue, body=payload)
                print(f"[MAIN-RMQ] Enviado stop a {node}")

            if status == 'stopped':
                print(f"[MAIN-RMQ] {node} confirmó que apagó el audio.")

        def _consume_loop():
            _ch.basic_consume(queue='main_responses', on_message_callback=_on_response, auto_ack=True)
            try:
                _ch.start_consuming()
            except Exception:
                pass

        _consumer_thread = threading.Thread(target=_consume_loop, daemon=True)
        _consumer_thread.start()
        RMQ_AVAILABLE = True
        print('[MAIN-RMQ] Conectado a RabbitMQ, integración activada.')
    except Exception:
        RMQ_AVAILABLE = False
        _conn = None
        _ch = None
        print('[MAIN-RMQ] RabbitMQ no disponible en localhost, usando modo local.')
except Exception:
    RMQ_AVAILABLE = False
    _conn = None
    _ch = None


PLAYER_POS = Posicion(y=17, x=17)
enemigos = []


def random_pos():
    pos = (17, 17)

    while pos == (17, 17):
        y = random.randint(0, 35)
        x = random.randint(0, 35)
        pos = (y, x)

    return pos


def crear_enemigo():
    pos = random_pos()

    while pos in enemigos:
        pos = random_pos()

    enemigos.append(pos)


def cleanup_entities():
    # Remove duplicates and any invalid entries from enemigos
    global enemigos
    cleaned = []
    for e in enemigos:
        if not isinstance(e, tuple) or len(e) != 2:
            continue
        if e not in cleaned:
            cleaned.append(e)
    enemigos = cleaned


def crear_enemigos(cantidad):
    for _ in range(cantidad):
        crear_enemigo()
    cleanup_entities()


def run_sonar(obstacles):
    player = (17, 17)
    max_radius = 25

    start_instance("sonar.mp3", loops=-1)

    for radio in range(max_radius + 1):
        draw_sonar(radio, player, obstacles)

        # If RabbitMQ available, publish a sonar message containing obstacles on this radius
        if RMQ_AVAILABLE and _ch is not None:
            # build list of obstacles detected at this radius
            detected = []
            py, px = player
            for (y, x) in obstacles:
                dist = ((y - py) ** 2 + (x - px) ** 2) ** 0.5
                if abs(dist - radio) < 0.5:
                    detected.append({'y': y, 'x': x})

            payload = {'detected': len(detected) > 0, 'radius': radio, 'player': {'y': py, 'x': px}, 'obstacles': detected}
            try:
                _ch.basic_publish(exchange='sonar', routing_key='', body=json.dumps(payload))
                if detected:
                    print(f"[MAIN-RMQ] Pulsado radio {radio}: {len(detected)} objetivo(s) detectado(s)")
            except Exception as e:
                print(f"[MAIN-RMQ] Error publicando sonar: {e}")

        time.sleep(0.3)

    stop_all_instances()


def fire_exacto(objetivos):
    posicion_actual = Posicion(y=17, x=17)

    objetivos_entidad = [
        Objetivo(y=objetivo[0], x=objetivo[1])
        for objetivo in objetivos
    ]

    objetivo_entidad = obtener_objetivo_mas_cercano(posicion_actual, objetivos_entidad)
    objetivo = (int(objetivo_entidad.y), int(objetivo_entidad.x))

    distancia_x, distancia_y = obtener_distancias(posicion_actual, objetivo_entidad)

    movimiento_x = decidir_movimiento_x(distancia_x)
    movimiento_y = decidir_movimiento_y(distancia_y)

    print(f"Movimiento X: {movimiento_x}")
    print(f"Movimiento Y: {movimiento_y}")

    py, px = 17.0, 17.0
    target_y, target_x = objetivo

    vy, vx = calcular_paso_exacto((py, px), objetivo)

    while True:
        draw_grid((round(py), round(px)), (17, 17), objetivos)

        if abs(py - target_y) < 0.5 and abs(px - target_x) < 0.5:
            print("¡IMPACTO DIRECTO!")
            objetivos.remove(objetivo)
            cleanup_entities()
            break

        if not (0 <= py <= 35 and 0 <= px <= 35):
            print("El proyectil se perdió.")
            break

        time.sleep(0.1)

        py += vy
        px += vx


def play(cantidad):
    return random.choices(range(0, 6), k=cantidad)


def menu():
    cantidad_enemigos = 15

    crear_enemigos(cantidad_enemigos)

    print(enemigos)

    run_sonar(enemigos)

    orden_sonidos = play(cantidad_enemigos)
    i = 0

    while len(enemigos) > 0:
        sensor_decibeles = leer_decibeles(60)
        accion = decidir_accion(sensor_decibeles)

        if accion == "atacar":
            start_instance(f"test{orden_sonidos[i]}.mp3", loops=-1)
            fire_exacto(enemigos)
            stop_one_instance()
        else:
            print("Ruido bajo, se ignora el objetivo.")

        time.sleep(2)
        i += 1


if __name__ == "__main__":
    menu()
