import pika
import os
from fastapi import FastAPI
from pydantic import BaseModel

# --- Modelos de Dados ---
class Message(BaseModel):
    text: str

# --- Configuração do FastAPI ---
app = FastAPI(
    title="API do Produtor",
    description="Esta API recebe uma mensagem e a envia para uma fila do RabbitMQ.",
    version="1.0.0"
)

# --- Configuração do RabbitMQ ---
# Usamos variáveis de ambiente para desacoplar as configurações
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
QUEUE_NAME = os.getenv('RABBITMQ_QUEUE', 'message_queue')

def get_rabbitmq_connection():
    """Cria e retorna uma conexão com o RabbitMQ."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    return pika.BlockingConnection(parameters)

# --- Endpoints da API ---
@app.post("/send-message", status_code=202)
def send_message(message: Message):
    """
    Recebe uma mensagem e a publica na fila 'message_queue' do RabbitMQ.
    """
    connection = None
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        # Garante que a fila existe. É uma operação idempotente.
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Publica a mensagem
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=message.text.encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Torna a mensagem persistente
            ))
        
        print(f" [x] Enviado '{message.text}'")
        return {"status": "message sent", "message": message.text}

    except pika.exceptions.AMQPConnectionError as e:
        return {"status": "error", "message": f"Não foi possível conectar ao RabbitMQ: {e}"}
    finally:
        if connection and not connection.is_closed:
            connection.close()

@app.get("/")
def read_root():
    return {"hello": "world, I'm the producer!"}