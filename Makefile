SHELL  = cmd.exe
PYTHON = $(CURDIR)/.venv/Scripts/python.exe

# Parametros para agregar nodos extra: make node ID=node3 SOUND=test1.mp3
ID    ?= node3
SOUND ?= test1.mp3

.PHONY: all up down run main node1 node2 node3 node4 node5 node6 node logs

all: run

# Levanta RabbitMQ en background y espera que este listo
up:
	docker compose up -d
	@echo Esperando que RabbitMQ arranque...
	@timeout /t 8 /nobreak > nul
	@echo RabbitMQ listo.

# Apaga el broker
down:
	docker compose down

# Ver logs del broker
logs:
	docker compose logs -f

# Nodo central (sonar/orquestador) — abre su propia terminal
main:
	start "sonar-main" cmd /k $(PYTHON) rmq_main.py

# Nodos de sonido predefinidos — cada uno abre su propia terminal
node1:
	start "node1-sonar" cmd /k $(PYTHON) rmq_node.py --id node1 --sound sonar.mp3

node2:
	start "node2-test0" cmd /k $(PYTHON) rmq_node.py --id node2 --sound test0.mp3

node3:
	start "node3-test1" cmd /k $(PYTHON) rmq_node.py --id node3 --sound test1.mp3

node4:
	start "node4-test2" cmd /k $(PYTHON) rmq_node.py --id node4 --sound test2.mp3

node5:
	start "node5-test3" cmd /k $(PYTHON) rmq_node.py --id node5 --sound test3.mp3

node6:
	start "node6-test4" cmd /k $(PYTHON) rmq_node.py --id node6 --sound test4.mp3

# Nodo extra generico: make node ID=node7 SOUND=ping.mp3
node:
	start "$(ID)" cmd /k $(PYTHON) rmq_node.py --id $(ID) --sound $(SOUND)

# Lanza todo de una vez: broker + main + 6 nodos
run: up main node1 node2 node3 node4 node5 node6
