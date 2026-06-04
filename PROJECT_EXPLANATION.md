# 📨 Mensageria Python - Explicação Detalhada

## 🎯 O que é este projeto?

Este é um **sistema de mensageria assíncrona** baseado em filas, que demonstra como construir uma arquitetura escalável e desacoplada usando:
- **FastAPI** - API produtor de mensagens
- **RabbitMQ** - Message Broker (gerenciador de filas)
- **PostgreSQL** - Persistência de dados
- **Docker & Docker Compose** - Orquestração de containers

---

## 🔄 Fluxo de Funcionamento

```
┌──────────────────┐         ┌──────────────┐         ┌──────────────┐
│   Cliente HTTP   │         │  RabbitMQ    │         │  PostgreSQL  │
│   (ou cURL)      │         │  (Fila)      │         │  (Storage)   │
└────────┬─────────┘         └────┬─────────┘         └──────┬───────┘
         │                        │                         │
         │ POST /send-message     │                         │
         │────────────────────────>│                         │
         │                        │                         │
         │   202 Accepted         │                         │
         │<────────────────────────│                         │
         │                        │                         │
         │                        │  Consumer consome       │
         │                        │  e persiste no DB       │
         │                        │────────────────────────>│
         │                        │                         │
         │                        │   Confirmação de        │
         │                        │   processamento         │
         │                        │<────────────────────────│
```

### 📍 Componentes

#### 1. **Producer (API FastAPI)**
- **Arquivo**: `producer/app/main.py`
- **Porta**: `8000`
- **Responsabilidade**: Recebe mensagens via HTTP POST e as publica na fila do RabbitMQ
- **Endpoint Principal**: `POST /send-message`
  - Aceita um JSON com o campo `text`
  - Retorna `202 Accepted` se bem-sucedido
  - Não aguarda processamento (padrão assíncrono)

#### 2. **RabbitMQ (Message Broker)**
- **Porta**: `5672` (AMQP) e `15672` (Management UI)
- **Fila**: `message_queue` (durável)
- **Responsabilidade**: Armazena mensagens na fila de forma persistente
- **Garantias**:
  - Mensagens permanecem na fila até serem processadas
  - Suporta múltiplos consumidores

#### 3. **Consumer (Worker)**
- **Arquivo**: `consumer/app/worker.py`
- **Responsabilidade**: Consome mensagens da fila e armazena no PostgreSQL
- **Características**:
  - Aguarda disponibilidade do PostgreSQL antes de iniciar
  - Processa 1 mensagem por vez (`prefetch_count=1`)
  - Confirma sucesso (ACK) ou rejeita (NACK) cada mensagem
  - Trata erros graciosamente

#### 4. **PostgreSQL (Banco de Dados)**
- **Porta**: `5432`
- **Tabela**: `messages`
  - `id` (Serial Primary Key)
  - `content` (Text - conteúdo da mensagem)
  - `created_at` (Timestamp - data de criação automática)

---

## 🚀 Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados
- Arquivo `.env.development` configurado

### Passos

1. **Inicie os containers**:
   ```bash
   docker-compose up --build
   ```

2. **Acesse a API do Produtor**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Envie uma mensagem**:
   ```bash
   curl -X POST http://localhost:8000/send-message \
     -H "Content-Type: application/json" \
     -d '{"text": "Olá, mundo!"}'
   ```

4. **Acompanhe o consumidor**:
   ```bash
   docker-compose logs -f consumer
   ```

5. **Verifique os dados no PostgreSQL**:
   ```bash
   docker exec -it postgres_db psql -U seu_usuario -d sua_db
   SELECT * FROM messages;
   ```

6. **Acesse a UI do RabbitMQ** (opcional):
   - URL: http://localhost:15672
   - Usuário: guest (padrão)
   - Senha: guest (padrão)

---

## 🏗️ Estrutura do Projeto

```
.
├── producer/
│   ├── Dockerfile          # Imagem do produtor
│   ├── requirements.txt     # Dependências Python
│   └── app/
│       └── main.py         # API FastAPI
│
├── consumer/
│   ├── Dockerfile          # Imagem do consumidor
│   ├── requirements.txt     # Dependências Python
│   └── app/
│       └── worker.py       # Worker que consome mensagens
│
├── db/
│   └── init.sql            # Script de inicialização do PostgreSQL
│
├── docker-compose.yml      # Orquestração de containers
├── .env.development        # Variáveis de ambiente
└── README.md               # Instruções básicas
```

---

## 🔒 Padrões de Segurança e Boas Práticas Implementadas

### ✅ Implementado

1. **Desacoplamento**: Producer e Consumer não se comunicam diretamente
2. **Resiliência**: Consumer aguarda PostgreSQL antes de iniciar
3. **Persistência**: Mensagens no RabbitMQ são duráveis
4. **Confirmação de Entrega**: ACK/NACK para garantir processamento
5. **Prefetch Limit**: Consumer processa 1 mensagem por vez
6. **Tratamento de Erros**: Callbacks protegidos com try/except
7. **Variáveis de Ambiente**: Configurações não hardcoded
8. **Containers Isolados**: Cada serviço em seu próprio container

### 🔐 Melhorias Futuras Recomendadas

1. **Dead Letter Queue**: Para mensagens não processáveis
2. **Retry Logic**: Tentativas com backoff exponencial
3. **Monitoring**: Prometheus + Grafana para observabilidade
4. **Logging Centralizado**: ELK Stack para logs
5. **Health Checks**: Readiness/Liveness probes nos containers
6. **Rate Limiting**: Na API do produtor
7. **Autenticação/Autorização**: JWT na API do produtor
8. **Database Connection Pool**: Para melhor performance
9. **Validação de Mensagens**: Schemas mais robustos

---

## 📊 Casos de Uso

- **Sistema de Notificações**: Enviar emails/SMS assincronamente
- **Processamento de Imagens**: Upload engatilha processamento em background
- **Análise de Logs**: Ingestão em alta velocidade com processamento sob demanda
- **Fila de Jobs**: Agendamento de tarefas longas
- **Sincronização de Dados**: Entre múltiplos sistemas

---

## 🧪 Testes Implementados

Veja `test_integration.py` para testes de integração completos que cobrem:
- Envio de mensagens via API
- Consumo de mensagens da fila
- Persistência no banco de dados
- Tratamento de erros
- Validação de dados

---

## 📝 Variáveis de Ambiente

```env
# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_HOST=rabbitmq
RABBITMQ_QUEUE=message_queue

# PostgreSQL
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=sua_db
POSTGRES_HOST=db
```

---

**Autor**: Seu Nome  
**Data**: 2024  
**Versão**: 1.0.0
