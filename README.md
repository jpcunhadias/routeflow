# routeflow

Plataforma **end-to-end** de dados e experimentação para logística/entregas:
ETL → features → treino → tracking com MLflow → avaliação e “A/B” simulado,
orquestrado com Airflow.

## Stack
- **Docker + docker-compose**
- **Airflow** (orquestração)
- **MLflow** (tracking de experimentos e artefatos)
- **Python 3.10+** (Pandas, scikit-learn; opcional Spark depois)
- **Streamlit** (dashboard opcional para KPIs)

## Como subir
```bash
cp .env.example .env
make build
make up
