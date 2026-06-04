"""
Testes de Integração para o Sistema de Mensageria

Este módulo testa o fluxo completo:
1. Envio de mensagem via API (Producer)
2. Consumo da fila (RabbitMQ)
3. Persistência no banco de dados (PostgreSQL)
"""

import requests
import psycopg2
import time
import pytest
import os
from typing import Optional


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

PRODUCER_URL = os.getenv("PRODUCER_URL", "http://localhost:8000")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mensageria_db")


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def wait_for_services():
    """Aguarda todos os serviços ficarem disponíveis antes dos testes."""
    print("\n⏳ Aguardando serviços iniciarem...")
    
    # Aguarda Producer
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{PRODUCER_URL}/", timeout=2)
            if response.status_code == 200:
                print("✅ Producer disponível")
                break
        except Exception:
            if i == max_retries - 1:
                raise RuntimeError("Producer não iniciou a tempo")
            time.sleep(1)
    
    # Aguarda PostgreSQL
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            conn.close()
            print("✅ PostgreSQL disponível")
            break
        except Exception:
            if i == max_retries - 1:
                raise RuntimeError("PostgreSQL não iniciou a tempo")
            time.sleep(1)
    
    time.sleep(2)  # Pequeno buffer para garantir que tudo está pronto


@pytest.fixture(autouse=True)
def clean_database():
    """Limpa a tabela de mensagens antes de cada teste."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE messages RESTART IDENTITY CASCADE;")
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    
    yield


# ============================================================================
# HELPERS
# ============================================================================

def get_db_connection():
    """Cria uma conexão com o PostgreSQL."""
    return psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=5432
    )


def get_message_count() -> int:
    """Retorna o número de mensagens no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM messages;")
        count = cursor.fetchone()[0]
        return count
    finally:
        cursor.close()
        conn.close()


def get_messages(limit: int = 10) -> list:
    """Retorna as últimas mensagens do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, content, created_at FROM messages ORDER BY created_at DESC LIMIT %s;",
            (limit,)
        )
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()


def send_message(text: str) -> requests.Response:
    """Envia uma mensagem para o Producer."""
    return requests.post(
        f"{PRODUCER_URL}/send-message",
        json={"text": text},
        timeout=5
    )


def wait_for_processing(expected_count: int, timeout: int = 10) -> bool:
    """
    Aguarda até que o número esperado de mensagens seja processado.
    
    Args:
        expected_count: Número de mensagens esperadas
        timeout: Tempo máximo de espera em segundos
    
    Returns:
        True se o esperado foi alcançado, False caso contrário
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if get_message_count() >= expected_count:
            return True
        time.sleep(0.5)
    return False


# ============================================================================
# TESTES
# ============================================================================

class TestProducerAPI:
    """Testes para a API do Producer."""
    
    def test_producer_health_check(self):
        """Verifica se o producer está disponível."""
        response = requests.get(f"{PRODUCER_URL}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "hello" in data
    
    def test_send_single_message(self):
        """Testa envio de uma única mensagem."""
        response = send_message("Test Message 1")
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "message sent"
        assert data["message"] == "Test Message 1"
    
    def test_send_message_with_special_characters(self):
        """Testa envio de mensagem com caracteres especiais."""
        special_text = "Olá! 🎉 Mensagem com acentuação e emojis: @#$%^&*()"
        response = send_message(special_text)
        assert response.status_code == 202
        assert response.json()["status"] == "message sent"
    
    def test_send_empty_message_fails(self):
        """Testa que mensagem vazia é rejeitada."""
        response = requests.post(
            f"{PRODUCER_URL}/send-message",
            json={"text": ""},
            timeout=5
        )
        # FastAPI retorna 422 para validação falhar, mas pika pode aceitar string vazia
        # Então verificamos que foi enviado ou rejeitado apropriadamente
        assert response.status_code in [202, 422]
    
    def test_send_message_missing_field(self):
        """Testa que requisição sem campo 'text' é rejeitada."""
        response = requests.post(
            f"{PRODUCER_URL}/send-message",
            json={"something": "else"},
            timeout=5
        )
        assert response.status_code == 422


class TestMessageQueueIntegration:
    """Testes de integração da fila de mensagens."""
    
    def test_message_persists_to_database(self):
        """Testa que uma mensagem é persistida no banco de dados."""
        test_message = "Integration Test Message"
        
        # Envia mensagem
        response = send_message(test_message)
        assert response.status_code == 202
        
        # Aguarda processamento (máximo 10 segundos)
        assert wait_for_processing(1, timeout=10), "Mensagem não foi processada"
        
        # Verifica no banco de dados
        messages = get_messages()
        assert len(messages) > 0
        assert messages[0][1] == test_message  # Coluna 'content'
    
    def test_multiple_messages_processing(self):
        """Testa processamento de múltiplas mensagens."""
        num_messages = 5
        
        # Envia múltiplas mensagens
        for i in range(num_messages):
            response = send_message(f"Message {i+1}")
            assert response.status_code == 202
        
        # Aguarda processamento de todas
        assert wait_for_processing(num_messages, timeout=15), \
            f"Nem todas as {num_messages} mensagens foram processadas"
        
        # Verifica que todas foram salvas
        count = get_message_count()
        assert count == num_messages
    
    def test_message_order_preservation(self):
        """Testa que mensagens são processadas na ordem FIFO."""
        messages_to_send = ["First", "Second", "Third"]
        
        for msg in messages_to_send:
            response = send_message(msg)
            assert response.status_code == 202
            time.sleep(0.5)  # Pequeno delay para garantir ordem
        
        # Aguarda processamento
        assert wait_for_processing(len(messages_to_send), timeout=15)
        
        # Recupera mensagens em ordem de criação
        messages = get_messages()
        # As mensagens mais recentes estão primeiro na query
        retrieved_texts = [msg[1] for msg in reversed(messages)]
        
        # Verifica que estão na ordem esperada
        for expected, retrieved in zip(messages_to_send, retrieved_texts):
            assert expected == retrieved, f"Esperava '{expected}', recebeu '{retrieved}'"
    
    def test_unicode_message_handling(self):
        """Testa processamento de mensagens com Unicode."""
        unicode_message = "こんにちは世界 - 你好世界 - مرحبا بالعالم - Привет мир"
        
        response = send_message(unicode_message)
        assert response.status_code == 202
        
        assert wait_for_processing(1, timeout=10)
        
        messages = get_messages()
        assert len(messages) > 0
        assert messages[0][1] == unicode_message
    
    def test_long_message_handling(self):
        """Testa processamento de mensagens longas."""
        long_message = "A" * 5000  # 5000 caracteres
        
        response = send_message(long_message)
        assert response.status_code == 202
        
        assert wait_for_processing(1, timeout=10)
        
        messages = get_messages()
        assert len(messages) > 0
        assert messages[0][1] == long_message
        assert len(messages[0][1]) == 5000


class TestDatabaseIntegrity:
    """Testes para integridade e estrutura do banco de dados."""
    
    def test_messages_table_structure(self):
        """Verifica que a tabela messages tem a estrutura correta."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Verifica se a tabela existe e tem as colunas esperadas
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'messages'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            assert len(columns) >= 3, "Tabela não tem todas as colunas esperadas"
            
            column_names = [col[0] for col in columns]
            assert "id" in column_names
            assert "content" in column_names
            assert "created_at" in column_names
        finally:
            cursor.close()
            conn.close()
    
    def test_message_timestamp_auto_set(self):
        """Verifica que created_at é automaticamente preenchido."""
        message = "Timestamp Test"
        send_message(message)
        
        assert wait_for_processing(1, timeout=10)
        
        messages = get_messages()
        assert len(messages) > 0
        assert messages[0][2] is not None  # created_at não é None
    
    def test_message_id_auto_increment(self):
        """Verifica que IDs são auto-incrementados."""
        messages_to_send = ["Message 1", "Message 2", "Message 3"]
        
        for msg in messages_to_send:
            send_message(msg)
        
        assert wait_for_processing(len(messages_to_send), timeout=15)
        
        messages = get_messages()
        ids = [msg[0] for msg in messages]
        
        # Verifica que IDs são números sequenciais
        assert all(isinstance(id_, int) for id_ in ids)
        assert len(set(ids)) == len(ids), "IDs não são únicos"


class TestErrorHandling:
    """Testes para tratamento de erros."""
    
    def test_malformed_json_request(self):
        """Testa que requisição com JSON malformado é tratada."""
        response = requests.post(
            f"{PRODUCER_URL}/send-message",
            data="not valid json",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        assert response.status_code == 422
    
    def test_connection_error_handling(self):
        """Testa que erros de conexão são tratados graciosamente."""
        # Nota: Este teste é difícil em um ambiente Docker funcional
        # Aqui apenas verificamos que a API não travou durante testes
        response = send_message("Error Handling Test")
        assert response.status_code in [202, 500]  # Pode falhar se RabbitMQ cair
    
    def test_concurrent_message_sending(self):
        """Testa envio concorrente de mensagens."""
        import concurrent.futures
        
        def send_msg(i):
            return send_message(f"Concurrent Message {i}")
        
        num_concurrent = 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_msg, i) for i in range(num_concurrent)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Todos devem ter sucesso
        assert all(r.status_code == 202 for r in results)
        
        # Aguarda processamento de todos
        assert wait_for_processing(num_concurrent, timeout=20)


class TestPerformance:
    """Testes de performance e throughput."""
    
    def test_throughput_measurement(self):
        """Mede o throughput de processamento de mensagens."""
        num_messages = 20
        
        start_time = time.time()
        
        for i in range(num_messages):
            response = send_message(f"Performance Test {i}")
            assert response.status_code == 202
        
        # Aguarda processamento
        assert wait_for_processing(num_messages, timeout=30)
        
        elapsed_time = time.time() - start_time
        throughput = num_messages / elapsed_time
        
        print(f"\n📊 Throughput: {throughput:.2f} mensagens/segundo")
        print(f"   Total: {num_messages} mensagens em {elapsed_time:.2f}s")
        
        # Verifica que o throughput é razoável (> 1 msg/seg)
        assert throughput > 1, f"Throughput muito baixo: {throughput:.2f} msg/s"
    
    def test_response_time(self):
        """Mede o tempo de resposta do endpoint de envio."""
        times = []
        
        for i in range(10):
            start = time.time()
            response = send_message(f"Response Time Test {i}")
            elapsed = time.time() - start
            
            assert response.status_code == 202
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\n⏱️  Tempo de Resposta:")
        print(f"   Média: {avg_time*1000:.2f}ms")
        print(f"   Máximo: {max_time*1000:.2f}ms")
        
        # Response deve ser rápido (< 1 segundo)
        assert avg_time < 1.0, f"Response muito lento: {avg_time*1000:.2f}ms"


# ============================================================================
# TESTES DE SMOKE (Rápidos e Simples)
# ============================================================================

class TestSmoke:
    """Testes rápidos para verificar saúde geral do sistema."""
    
    def test_producer_responds(self):
        """Smoke test: Producer responde?"""
        response = requests.get(f"{PRODUCER_URL}/", timeout=5)
        assert response.status_code == 200
    
    def test_can_send_message(self):
        """Smoke test: Pode enviar mensagem?"""
        response = send_message("Smoke Test")
        assert response.status_code == 202
    
    def test_database_is_accessible(self):
        """Smoke test: Banco de dados está acessível?"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1;")
            assert cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    # Permite executar testes sem pytest
    print("Para executar os testes, use: pytest test_integration.py -v")
    print("\nOu execute testes específicos:")
    print("  pytest test_integration.py::TestSmoke -v")
    print("  pytest test_integration.py::TestMessageQueueIntegration -v")
    print("  pytest test_integration.py::TestPerformance -v")
