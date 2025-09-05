# -------- Config --------
SHELL := /bin/bash
PY ?= python3

AIRFLOW_WEB_PORT ?= 8080
MLFLOW_HOST_PORT ?= 5500   # host: mlflow:5000
COMPOSE ?= docker compose

# Env vars usadas pela DAG (também configuradas no docker-compose.yml)
NYC_TLC_YEARS ?= 2023
NYC_TLC_MONTHS ?= 01,02
NYC_TLC_COLOR ?= yellow

# -------- Ajuda --------
.PHONY: help
help:
	@echo "Comandos disponíveis:"
	@echo "  make build            - (opcional) puxa imagens e prepara ambiente"
	@echo "  make up               - sobe mlflow + airflow (webserver/scheduler)"
	@echo "  make down             - derruba os serviços"
	@echo "  make restart          - reinicia os serviços"
	@echo "  make ps               - lista containers"
	@echo "  make logs             - segue logs do scheduler"
	@echo "  make airflow-init     - inicializa DB do Airflow e cria usuário admin"
	@echo "  make trigger-vrp      - dispara a DAG vrp_pipeline (download + standardize)"
	@echo "  make env-check        - mostra envs no scheduler (NYC_TLC_*, executor)"
	@echo "  make open-airflow     - abre http://localhost:$(AIRFLOW_WEB_PORT)"
	@echo "  make open-mlflow      - abre http://localhost:$(MLFLOW_HOST_PORT)"
	@echo "  make data-one-month   - baixa 1 mês direto (teste) dentro do scheduler"
	@echo ""
	@echo "Portas: Airflow=$(AIRFLOW_WEB_PORT), MLflow=$(MLFLOW_HOST_PORT)"
	@echo "NYC TLC: YEARS=$(NYC_TLC_YEARS) MONTHS=$(NYC_TLC_MONTHS) COLOR=$(NYC_TLC_COLOR)"

# -------- Ciclo de vida dos serviços --------
.PHONY: build up down restart ps logs
build:
	$(COMPOSE) pull || true

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart: down up

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=200 airflow-scheduler

# -------- Airflow: init e utilitários --------
.PHONY: airflow-init trigger-vrp env-check
airflow-init:
	# Inicializa metadados do Airflow
	$(COMPOSE) run --rm airflow-scheduler airflow db init
	# Cria usuário admin (idempotente; ignora erro se já existir)
	$(COMPOSE) run --rm airflow-webserver \
		airflow users create \
			--username airflow \
			--firstname Air \
			--lastname Flow \
			--role Admin \
			--email admin@example.com \
			--password airflow || true

trigger-vrp:
	# Dispara a DAG vrp_pipeline manualmente
	$(COMPOSE) exec -e NYC_TLC_YEARS=$(NYC_TLC_YEARS) \
		-e NYC_TLC_MONTHS=$(NYC_TLC_MONTHS) \
		-e NYC_TLC_COLOR=$(NYC_TLC_COLOR) \
		airflow-scheduler airflow dags trigger vrp_pipeline

env-check:
	$(COMPOSE) exec airflow-scheduler env | grep -E 'NYC_TLC_|AIRFLOW__CORE__EXECUTOR' || true

# -------- Acesso rápido às UIs --------
.PHONY: open-airflow open-mlflow
open-airflow:
	( command -v open >/dev/null && open http://localhost:$(AIRFLOW_WEB_PORT) ) || \
	( command -v xdg-open >/dev/null && xdg-open http://localhost:$(AIRFLOW_WEB_PORT) ) || \
	echo "Abra: http://localhost:$(AIRFLOW_WEB_PORT)"

open-mlflow:
	( command -v open >/dev/null && open http://localhost:$(MLFLOW_HOST_PORT) ) || \
	( command -v xdg-open >/dev/null && xdg-open http://localhost:$(MLFLOW_HOST_PORT) ) || \
	echo "Abra: http://localhost:$(MLFLOW_HOST_PORT)"
