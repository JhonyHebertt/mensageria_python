# Mensageria com Docker, RabbitMQ e PostgreSQL

Este projeto demonstra uma arquitetura de mensageria utilizando **FastAPI** (produtor), **RabbitMQ** (broker), **PostgreSQL** (banco de dados) e **Python** (consumidor), tudo orquestrado com **Docker Compose**.

## Visão Geral

- **Producer (FastAPI):** Recebe mensagens via API HTTP e publica na fila do RabbitMQ.
- **RabbitMQ:** Gerencia a fila de mensagens.
- **Consumer:** Consome mensagens da fila e armazena no PostgreSQL.
- **PostgreSQL:** Armazena as mensagens recebidas.

## Estrutura

```
.
├── consumer/
│   └── app/
│       └── worker.py
├── producer/
│   └── app/
│       └── main.py
├── db/
│   └── init.sql
├── docker-compose.yml
├── .env
├── .gitignore
```

## Como rodar

1. **Configure o arquivo `.env`**  
   Já existe um exemplo no repositório. Ajuste as variáveis conforme necessário.

2. **Suba os containers:**
   ```sh
   docker-compose up --build
   ```

3. **Acesse a API do produtor:**  
   - Documentação automática: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Envie mensagens via endpoint `/send-message`.

4. **Acompanhe os logs:**  
   ```sh
   docker-compose logs -f consumer
   ```

## Exemplo de uso

Envie uma mensagem usando `curl`:
```sh
curl -X POST http://localhost:8000/send-message -H "Content-Type: application/json" -d '{"text": "Olá, mundo!"}'
```