# 🧪 Guia de Testes - Sistema de Mensageria

## 📋 Visão Geral

Este projeto inclui testes de integração completos que validam:

✅ API do Producer  
✅ Fila RabbitMQ  
✅ Consumidor de Mensagens  
✅ Persistência no PostgreSQL  
✅ Tratamento de Erros  
✅ Performance e Throughput  

---

## 🚀 Como Executar os Testes

### Pré-requisitos

1. **Containers rodando**:
   ```bash
   docker-compose up --build
   ```

2. **Instalar dependências de teste**:
   ```bash
   pip install -r requirements-test.txt
   ```

### Executar Todos os Testes

```bash
# Com output detalhado
pytest test_integration.py -v

# Com cobertura de código
pytest test_integration.py --cov --cov-report=html

# Com output muito detalhado
pytest test_integration.py -vv -s
```

### Executar Testes Específicos

```bash
# Apenas testes de Health Check
pytest test_integration.py::TestSmoke -v

# Apenas testes de integração da fila
pytest test_integration.py::TestMessageQueueIntegration -v

# Apenas testes de integridade do banco
pytest test_integration.py::TestDatabaseIntegrity -v

# Apenas testes de performance
pytest test_integration.py::TestPerformance -v

# Um teste específico
pytest test_integration.py::TestProducerAPI::test_send_single_message -v
```

### Executar com Marcadores

```bash
# Testes rápidos (smoke tests)
pytest test_integration.py -m "not slow" -v

# Testes com cobertura
pytest test_integration.py --cov=. --cov-report=term-missing
```

---

## 📊 Estrutura dos Testes

### 1. **TestSmoke** - Testes de Saúde
- Verificações rápidas se o sistema está funcionando
- Use para CI/CD pipelines
- Tempo: ~2-3 segundos

```bash
pytest test_integration.py::TestSmoke -v
```

### 2. **TestProducerAPI** - Testes da API
- Validação de endpoints
- Tratamento de requisições bem-formadas
- Validação de schemas
- Tempo: ~5 segundos

```bash
pytest test_integration.py::TestProducerAPI -v
```

### 3. **TestMessageQueueIntegration** - Testes de Fluxo
- Envio até persistência
- Processamento de múltiplas mensagens
- Ordem FIFO
- Suporte a Unicode
- Tempo: ~30-45 segundos

```bash
pytest test_integration.py::TestMessageQueueIntegration -v
```

### 4. **TestDatabaseIntegrity** - Testes de Dados
- Estrutura da tabela
- Auto-incremento de IDs
- Timestamps automáticos
- Tempo: ~10 segundos

```bash
pytest test_integration.py::TestDatabaseIntegrity -v
```

### 5. **TestErrorHandling** - Testes de Erros
- JSON malformado
- Requisições inválidas
- Envio concorrente
- Tempo: ~15 segundos

```bash
pytest test_integration.py::TestErrorHandling -v
```

### 6. **TestPerformance** - Testes de Performance
- Throughput de mensagens
- Tempo de resposta da API
- Capacidade de processamento
- Tempo: ~30-40 segundos

```bash
pytest test_integration.py::TestPerformance -v
```

---

## 🔧 Variáveis de Ambiente

Os testes usam estas variáveis (com defaults):

```env
# API do Producer
PRODUCER_URL=http://localhost:8000

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=mensageria_db
```

Para usar valores diferentes, crie um arquivo `.env` na raiz do projeto:

```bash
cat > .env << EOF
PRODUCER_URL=http://producer:8000
POSTGRES_HOST=db
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=sua_db
EOF
```

---

## 📈 Analisando Resultados

### Output Típico Bem-Sucedido

```
test_integration.py::TestSmoke::test_producer_responds PASSED           [  5%]
test_integration.py::TestSmoke::test_can_send_message PASSED            [ 10%]
test_integration.py::TestProducerAPI::test_send_single_message PASSED   [ 15%]
test_integration.py::TestMessageQueueIntegration::test_message_persists PASSED [ 25%]

📊 Throughput: 12.45 mensagens/segundo
⏱️  Tempo de Resposta:
   Média: 45.32ms
   Máximo: 125.67ms

======================== 25 passed in 42.53s ========================
```

### Interpretando Falhas

#### ❌ "Producer não iniciou a tempo"
- Producer não está rodando ou levou muito tempo para iniciar
- **Solução**: Verifique se `docker-compose up` está rodando

#### ❌ "Mensagem não foi processada"
- Consumer não está consumindo mensagens
- RabbitMQ não está accessível
- **Solução**: Verifique os logs: `docker-compose logs consumer`

#### ❌ "Conexão com PostgreSQL recusada"
- Banco de dados não está rodando
- Credenciais incorretas
- **Solução**: Verifique `docker-compose logs db`

---

## 🐛 Debugging de Testes

### Modo Verbose com Prints

```bash
pytest test_integration.py -vv -s
```

### Parar no Primeiro Erro

```bash
pytest test_integration.py -x
```

### Mostrar Output do Print

```bash
pytest test_integration.py -s
```

### Executar com Debugging

```bash
pytest test_integration.py --pdb
```

### Ver Logs do Docker Durante Testes

Terminal 1:
```bash
docker-compose logs -f
```

Terminal 2:
```bash
pytest test_integration.py -v
```

---

## 📊 Cobertura de Testes

Gerar relatório de cobertura HTML:

```bash
pytest test_integration.py --cov=. --cov-report=html
open htmlcov/index.html
```

Cobertura esperada:
- Producer API: 95%+
- Consumer Worker: 90%+
- Helpers: 100%

---

## ⚡ Testes Rápidos vs Completos

### Modo Rápido (Smoke Tests) - ~5 segundos
```bash
pytest test_integration.py::TestSmoke -v
```

### Modo Completo - ~60 segundos
```bash
pytest test_integration.py -v
```

### Modo Development (com logging)
```bash
pytest test_integration.py -v -s --tb=short
```

---

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      rabbitmq:
        image: rabbitmq:3.11-management
        options: >-
          --health-cmd "rabbitmq-diagnostics ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements-test.txt
      - run: pytest test_integration.py -v --cov
```

---

## 🎯 Checklist Pré-Deploy

- [ ] Todos os testes passam localmente
- [ ] `pytest test_integration.py::TestSmoke -v` passa
- [ ] Performance está aceitável (> 1 msg/seg)
- [ ] Sem erro de conexão
- [ ] Banco de dados intacto após testes
- [ ] Logs não têm warnings ou erros críticos

---

## 📞 Troubleshooting

| Problema | Solução |
|----------|---------|
| Testes pendem indefinidamente | Aumentar `timeout` em `wait_for_processing()` |
| "PostgreSQL connection refused" | Verificar variáveis de ambiente no `.env` |
| "RabbitMQ not accessible" | Verificar se RabbitMQ container está rodando |
| Testes falham aleatoriamente | Aumentar waits em `wait_for_processing()` |
| Performance muito lenta | Verificar logs do Docker, pode estar full |

---

## 📚 Recursos Adicionais

- [Pytest Documentation](https://docs.pytest.org/)
- [RabbitMQ Testing Guide](https://www.rabbitmq.com/testing.html)
- [PostgreSQL Testing](https://www.postgresql.org/docs/current/testing.html)
- [Docker Compose Best Practices](https://docs.docker.com/compose/compose-file/)

---

**Última atualização**: 2024  
**Versão**: 1.0.0
