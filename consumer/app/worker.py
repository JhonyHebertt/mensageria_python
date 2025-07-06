import pika
import psycopg2
import os
import time
import sys

# --- Funções de Conexão ---
def wait_for_service(host, port, service_name):
    """Aguarda um serviço ficar disponível."""
    print(f"Aguardando pelo serviço {service_name} em {host}:{port}...")
    while True:
        try:
            with psycopg2.connect(host=host, port=port, dbname=os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD')):
                break
        except psycopg2.OperationalError:
            time.sleep(2)
    print(f"Serviço {service_name} está pronto!")

def get_db_connection():
    """Cria e retorna uma conexão com o PostgreSQL."""
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST', 'db')
    )

def get_rabbitmq_connection():
    """Cria e retorna uma conexão com o RabbitMQ, com retentativas."""
    host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    credentials = pika.PlainCredentials(
        os.getenv('RABBITMQ_USER'),
        os.getenv('RABBITMQ_PASSWORD')
    )
    parameters = pika.ConnectionParameters(host=host, credentials=credentials)
    
    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            print("Conectado ao RabbitMQ!")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(f"Não foi possível conectar ao RabbitMQ em '{host}'. Tentando novamente em 5 segundos...")
            time.sleep(5)

# --- Lógica do Consumidor ---
def callback(ch, method, properties, body):
    """
    Função chamada quando uma mensagem é recebida.
    Ela insere a mensagem no banco de dados.
    """
    message = body.decode('utf-8')
    print(f" [x] Recebido: {message}")
    
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("INSERT INTO messages (content) VALUES (%s);", (message,))
        db_conn.commit()
        cursor.close()
        print(f" [x] Mensagem salva no banco de dados.")
        
        # Confirma ao RabbitMQ que a mensagem foi processada com sucesso.
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}", file=sys.stderr)
        # Rejeita a mensagem, mas não a re-enfileira para evitar loops infinitos de erro.
        # Em um sistema real, você poderia enviar para uma "dead-letter queue".
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        if db_conn:
            db_conn.close()

def main():
    # Aguarda o PostgreSQL iniciar antes de continuar
    wait_for_service(os.getenv('POSTGRES_HOST', 'db'), 5432, "PostgreSQL")
    
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    QUEUE_NAME = os.getenv('RABBITMQ_QUEUE', 'message_queue')
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Define que o consumidor só receberá uma mensagem por vez.
    # Isso evita que um worker pegue várias mensagens e morra no meio, perdendo todas.
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print(' [*] Aguardando por mensagens. Para sair pressione CTRL+C')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Consumidor interrompido.")
        channel.stop_consuming()
    finally:
        connection.close()
        print("Conexão com RabbitMQ fechada.")

if __name__ == '__main__':
    main()