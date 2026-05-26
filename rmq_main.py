import json
import logging
import math
import os
import random
import sys
import threading
import time

import pika

from decibeles_sat import leer_decibeles
from entities import Objetivo, Posicion
from filtro_sat import decidir_accion
from grid import draw_grid, draw_sonar
from objetivo_sat import calcular_paso_exacto
from pos_sat import obtener_objetivo_mas_cercano

logging.getLogger('pika').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL)

RABBIT_URL = os.getenv('RABBIT_URL', 'amqp://guest:guest@localhost:5672/%2F')

SONAR_NODE = 'node1'
ATTACK_NODES = ['node2', 'node3', 'node4', 'node5', 'node6']
ALL_SOUNDS = [f'test{i}.mp3' for i in range(6)]

enemigos = []
_attack_idx = 0


def _pick_attack_node():
    global _attack_idx
    node = ATTACK_NODES[_attack_idx % len(ATTACK_NODES)]
    _attack_idx += 1
    return node


def random_pos():
    while True:
        y = random.randint(0, 34)
        x = random.randint(0, 34)
        if (y, x) != (17, 17):
            return (y, x)


def crear_enemigos(n):
    while len(enemigos) < n:
        p = random_pos()
        if p not in enemigos:
            enemigos.append(p)


def cleanup():
    seen = []
    for e in enemigos:
        if e not in seen:
            seen.append(e)
    enemigos[:] = seen


def publish_play(ch, node, sound, loops=-1):
    ch.basic_publish(
        exchange='sonar',
        routing_key='',
        body=json.dumps({'event': 'play', 'target_node': node, 'sound': sound, 'loops': loops}),
    )


def publish_stop(ch, node='all'):
    ch.basic_publish(
        exchange='sonar',
        routing_key='',
        body=json.dumps({'event': 'stop', 'target_node': node}),
    )


def run_sonar(pub_ch):
    player = (17, 17)

    # Solo node1 suena durante el sonar — los nodos de ataque permanecen en silencio
    publish_play(pub_ch, SONAR_NODE, 'sonar.mp3', loops=-1)

    for radio in range(26):
        draw_sonar(radio, player, enemigos, play_audio=False)
        time.sleep(0.8)

    publish_stop(pub_ch, SONAR_NODE)


def fire_exacto(pub_ch):
    posicion_actual = Posicion(y=17, x=17)
    objetivos_entidad = [Objetivo(y=e[0], x=e[1]) for e in enemigos]
    objetivo_entidad = obtener_objetivo_mas_cercano(posicion_actual, objetivos_entidad)
    objetivo = (int(objetivo_entidad.y), int(objetivo_entidad.x))

    # El nodo empieza a sonar justo cuando comienza el ataque
    attack_node = _pick_attack_node()
    sound = random.choice(ALL_SOUNDS)
    publish_play(pub_ch, attack_node, sound, loops=-1)

    py, px = 17.0, 17.0
    target_y, target_x = objetivo
    vy, vx = calcular_paso_exacto((py, px), objetivo)

    while True:
        draw_grid((round(py), round(px)), (17, 17), enemigos)

        if abs(py - target_y) < 0.5 and abs(px - target_x) < 0.5:
            if objetivo in enemigos:
                enemigos.remove(objetivo)
            cleanup()
            # El nodo muere exactamente en el impacto
            publish_stop(pub_ch, attack_node)
            draw_grid((17, 17), (17, 17), enemigos)
            print(f'¡IMPACTO! [{attack_node}] silenciado. Quedan {len(enemigos)} enemigos.')
            time.sleep(1)
            break

        if not (0 <= py <= 34 and 0 <= px <= 34):
            publish_stop(pub_ch, attack_node)
            print("El proyectil se perdió.")
            time.sleep(1)
            break

        time.sleep(0.15)
        py += vy
        px += vx


def main():
    try:
        params = pika.URLParameters(RABBIT_URL)
        pub_conn = pika.BlockingConnection(params)
        con_conn = pika.BlockingConnection(params)
    except Exception as e:
        print(f"No se pudo conectar a RabbitMQ: {e}")
        sys.exit(1)

    pub_ch = pub_conn.channel()
    pub_ch.exchange_declare(exchange='sonar', exchange_type='fanout', durable=True)
    pub_ch.queue_declare(queue='main_responses', durable=True)

    con_ch = con_conn.channel()
    con_ch.exchange_declare(exchange='sonar', exchange_type='fanout', durable=True)
    con_ch.queue_declare(queue='main_responses', durable=True)

    con_ch.basic_consume(queue='main_responses', on_message_callback=lambda *a: None, auto_ack=True)
    threading.Thread(target=con_ch.start_consuming, daemon=True).start()

    cantidad = 5
    crear_enemigos(cantidad)

    print(f"[MAIN] {cantidad} enemigos creados. Esperando nodos...")
    for i in range(5, 0, -1):
        print(f"[MAIN] Iniciando en {i}...")
        time.sleep(1)

    run_sonar(pub_ch)

    while enemigos:
        sensor = leer_decibeles(60)
        accion = decidir_accion(sensor)

        if accion == 'atacar':
            fire_exacto(pub_ch)
        else:
            time.sleep(2)

    print("[MAIN] Todos los objetivos eliminados.")
    publish_stop(pub_ch, 'all')
    pub_conn.close()
    try:
        con_conn.close()
    except Exception:
        pass


if __name__ == '__main__':
    main()
