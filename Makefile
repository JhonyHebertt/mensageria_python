.PHONY: help up down logs test test-smoke test-api test-integration test-database test-errors test-performance test-coverage test-watch clean

help:
	@echo "📨 Sistema de Mensageria - Comandos"
	@echo ""
	@echo "Gerenciamento de Containers:"
	@echo "  make up              - Inicia todos os containers"
	@echo "  make down            - Para todos os containers"
	@echo "  make logs            - Mostra logs de todos os containers"
	@echo "  make logs-producer   - Mostra logs do Producer"
	@echo "  make logs-consumer   - Mostra logs do Consumer"
	@echo "  make logs-rabbitmq   - Mostra logs do RabbitMQ"
	@echo "  make logs-db         - Mostra logs do PostgreSQL"
	@echo ""
	@echo "Testes:"
	@echo "  make test            - Executa todos os testes"
	@echo "  make test-smoke      - Executa testes rápidos (health check)"
	@echo "  make test-api        - Executa testes da API do Producer"
	@echo "  make test-integration- Executa testes de integração completos"
	@echo "  make test-database   - Executa testes do banco de dados"
	@echo "  make test-errors     - Executa testes de tratamento de erros"
	@echo "  make test-performance- Executa testes de performance"
	@echo "  make test-coverage   - Executa testes com cobertura de código"
	@echo "  make test-watch      - Executa testes continuamente"
	@echo ""
	@echo "Utilitários:"
	@echo "  make clean           - Remove arquivos temporários e caches"
	@echo "  make db-shell        - Acessa shell do PostgreSQL"
	@echo "  make rabbitmq-ui     - Abre UI do RabbitMQ no navegador"
	@echo "  make api-docs        - Abre documentação Swagger da API"
	@echo "  make install-test    - Instala dependências de teste"
	@echo ""

# ============================================================================
# CONTAINER MANAGEMENT
# ============================================================================

up:
	@echo "🚀 Iniciando containers..."
	docker-compose up --build

down:
	@echo "🛑 Parando containers..."
	docker-compose down

logs:
	docker-compose logs -f

logs-producer:
	docker-compose logs -f producer

logs-consumer:
	docker-compose logs -f consumer

logs-rabbitmq:
	docker-compose logs -f rabbitmq

logs-db:
	docker-compose logs -f db

# ============================================================================
# TEST MANAGEMENT
# ============================================================================

install-test:
	@echo "📦 Instalando dependências de teste..."
	pip install -r requirements-test.txt

test: install-test
	@echo "🧪 Executando todos os testes..."
	pytest test_integration.py -v

test-smoke: install-test
	@echo "🔍 Executando smoke tests (rápidos)..."
	pytest test_integration.py::TestSmoke -v --tb=short

test-api: install-test
	@echo "🔍 Executando testes da API..."
	pytest test_integration.py::TestProducerAPI -v

test-integration: install-test
	@echo "🔍 Executando testes de integração..."
	pytest test_integration.py::TestMessageQueueIntegration -v

test-database: install-test
	@echo "🔍 Executando testes do banco de dados..."
	pytest test_integration.py::TestDatabaseIntegrity -v

test-errors: install-test
	@echo "🔍 Executando testes de tratamento de erros..."
	pytest test_integration.py::TestErrorHandling -v

test-performance: install-test
	@echo "🔍 Executando testes de performance..."
	pytest test_integration.py::TestPerformance -v

test-coverage: install-test
	@echo "📊 Executando testes com cobertura de código..."
	pytest test_integration.py --cov --cov-report=html --cov-report=term-missing
	@echo "✅ Relatório HTML gerado em: htmlcov/index.html"

test-watch: install-test
	@echo "👀 Executando testes continuamente..."
	pytest-watch test_integration.py -- -v

# ============================================================================
# UTILITIES
# ============================================================================

clean:
	@echo "🧹 Limpando arquivos temporários..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".pytest_cache" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete
	@echo "✅ Limpeza concluída"

db-shell:
	@echo "📊 Acessando PostgreSQL shell..."
	docker exec -it postgres_db psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-mensageria_db}

rabbitmq-ui:
	@echo "🐰 Abrindo UI do RabbitMQ..."
	@which xdg-open > /dev/null && xdg-open http://localhost:15672 || \
	which open > /dev/null && open http://localhost:15672 || \
	echo "Acesse manualmente: http://localhost:15672"

api-docs:
	@echo "📚 Abrindo documentação da API..."
	@which xdg-open > /dev/null && xdg-open http://localhost:8000/docs || \
	which open > /dev/null && open http://localhost:8000/docs || \
	echo "Acesse manualmente: http://localhost:8000/docs"

# ============================================================================
# QUICK START
# ============================================================================

.DEFAULT_GOAL := help

start: up
	@echo ""
	@echo "✅ Sistema iniciado!"
	@echo ""
	@echo "🔗 URLs importantes:"
	@echo "  📚 API Docs: http://localhost:8000/docs"
	@echo "  🐰 RabbitMQ: http://localhost:15672"
	@echo "  📊 PostgreSQL: localhost:5432"
	@echo ""
	@echo "Próximos passos:"
	@echo "  1. make test-smoke       # Verificar saúde do sistema"
	@echo "  2. make test             # Executar todos os testes"
	@echo "  3. make logs-consumer    # Monitorar consumidor"
	@echo ""
