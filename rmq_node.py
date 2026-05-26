import argparse
import json
import os
import sys

import pika

from audio import start_instance, stop_all_instances

RABBIT_URL = os.getenv('RABBIT_URL', 'amqp://guest:guest@localhost:5672/%2F')


def run_node(node_id, sound_name=None):
    try:
        params = pika.URLParameters(RABBIT_URL)
        conn = pika.BlockingConnection(params)
    except Exception as e:
        print(f"[NODE {node_id}] No se pudo conectar a RabbitMQ: {e}")
        sys.exit(1)

    ch = conn.channel()
    ch.exchange_declare(exchange='sonar', exchange_type='fanout', durable=True)
    ch.queue_declare(queue='main_responses', durable=True)

    result = ch.queue_declare(queue='', exclusive=True)
    sonar_queue = result.method.queue
    ch.queue_bind(exchange='sonar', queue=sonar_queue)

    def on_message(ch, method, properties, body):
        try:
            msg = json.loads(body)
        except Exception:
            return

        event = msg.get('event', 'legacy')
        target = msg.get('target_node', 'all')

        # Only act if this node is targeted or it's a broadcast stop
        if target != 'all' and target != node_id:
            return

        if event == 'stop':
            stop_all_instances()
            print(f"[NODE {node_id}] Audio detenido.")
            ch.basic_publish(
                exchange='',
                routing_key='main_responses',
                body=json.dumps({'node': node_id, 'status': 'stopped', 'sound': None}),
            )
            return

        if event == 'play':
            sound = msg.get('sound', sound_name)
            loops = msg.get('loops', -1)
            if sound:
                print(f"[NODE {node_id}] Reproduciendo {sound} (loops={loops})")
                start_instance(sound, loops=loops)
                ch.basic_publish(
                    exchange='',
                    routing_key='main_responses',
                    body=json.dumps({'node': node_id, 'status': 'playing', 'sound': sound}),
                )
            return

        # Legacy: mensajes con campo 'detected' (compatibilidad hacia atrás)
        if msg.get('detected') and sound_name:
            print(f"[NODE {node_id}] [legacy] Reproduciendo {sound_name}")
            start_instance(sound_name, loops=-1)
            ch.basic_publish(
                exchange='',
                routing_key='main_responses',
                body=json.dumps({'node': node_id, 'status': 'playing', 'sound': sound_name}),
            )

    ch.basic_consume(queue=sonar_queue, on_message_callback=on_message, auto_ack=True)

    print(f"[NODE {node_id}] Esperando mensajes...")
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        print(f"[NODE {node_id}] Saliendo...")
        conn.close()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--id', required=True, help='ID del nodo (ej: node1)')
    p.add_argument('--sound', default=None, help='Sonido por defecto (ej: ping.mp3)')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_node(args.id, args.sound)
