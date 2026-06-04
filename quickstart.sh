#!/usr/bin/env bash
# Quick Start Script - Sistema de Mensageria Python

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          📨 Sistema de Mensageria - Quick Start                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is running
echo -e "${BLUE}🔍 Verificando Docker...${NC}"
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker não está rodando!${NC}"
    echo "   Inicie o Docker e tente novamente."
    exit 1
fi
echo -e "${GREEN}✅ Docker está rodando${NC}"
echo ""

# Menu principal
echo -e "${BLUE}Escolha uma opção:${NC}"
echo ""
echo "  1) 🚀 Iniciar sistema completo (Docker + testes)"
echo "  2) 🐳 Apenas iniciar Docker"
echo "  3) 🧪 Executar testes (após Docker estar rodando)"
echo "  4) 📊 Ver status dos containers"
echo "  5) 📚 Ver documentação do projeto"
echo "  6) 🧹 Parar containers e limpar"
echo "  0) ❌ Sair"
echo ""
read -p "Digite sua escolha [0-6]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🚀 Iniciando sistema completo...${NC}"
        echo ""
        echo -e "${YELLOW}Passo 1: Iniciando Docker${NC}"
        docker-compose up --build &
        DOCKER_PID=$!
        
        echo ""
        echo -e "${YELLOW}Aguardando containers iniciarem...${NC}"
        sleep 15
        
        if docker-compose ps | grep -q "Up"; then
            echo -e "${GREEN}✅ Containers iniciados com sucesso!${NC}"
            echo ""
            
            echo -e "${YELLOW}Passo 2: Instalando dependências de teste${NC}"
            pip install -r requirements-test.txt > /dev/null 2>&1
            echo -e "${GREEN}✅ Dependências instaladas${NC}"
            echo ""
            
            echo -e "${YELLOW}Passo 3: Executando testes rápidos${NC}"
            pytest test_integration.py::TestSmoke -v
            
            if [ $? -eq 0 ]; then
                echo ""
                echo -e "${GREEN}✅ Testes passou! Sistema pronto para uso${NC}"
                echo ""
                echo -e "${BLUE}URLs importantes:${NC}"
                echo "  📚 API Docs:  http://localhost:8000/docs"
                echo "  🐰 RabbitMQ:  http://localhost:15672"
                echo "  📊 PostgreSQL: localhost:5432"
                echo ""
                echo -e "${BLUE}Próximos passos:${NC}"
                echo "  • Executar todos os testes: pytest test_integration.py -v"
                echo "  • Ver logs: docker-compose logs -f consumer"
                echo "  • Parar sistema: docker-compose down"
                echo ""
                echo -e "${YELLOW}Docker rodando em background. Use 'docker-compose logs' para ver logs.${NC}"
            else
                echo -e "${RED}❌ Testes falharam!${NC}"
            fi
        else
            echo -e "${RED}❌ Falha ao iniciar containers${NC}"
            exit 1
        fi
        ;;
    
    2)
        echo ""
        echo -e "${BLUE}🐳 Iniciando Docker...${NC}"
        docker-compose up --build
        ;;
    
    3)
        echo ""
        echo -e "${BLUE}🧪 Executando testes...${NC}"
        echo ""
        
        # Check if containers are running
        if ! docker-compose ps | grep -q "Up"; then
            echo -e "${RED}❌ Containers não estão rodando!${NC}"
            echo "   Primeiro inicie os containers com: docker-compose up"
            exit 1
        fi
        
        echo -e "${YELLOW}Instalando dependências de teste...${NC}"
        pip install -r requirements-test.txt > /dev/null 2>&1
        echo -e "${GREEN}✅ Dependências instaladas${NC}"
        echo ""
        
        echo -e "${BLUE}Escolha qual teste executar:${NC}"
        echo ""
        echo "  1) 🔍 Smoke tests (3 segundos) - Quick health check"
        echo "  2) 🔍 Testes da API (5 segundos)"
        echo "  3) 🔍 Testes de integração (30 segundos)"
        echo "  4) 🔍 Testes do banco de dados (10 segundos)"
        echo "  5) 🔍 Testes de performance (30 segundos)"
        echo "  6) 🔍 Testes de erros (15 segundos)"
        echo "  7) 🔍 TODOS OS TESTES (60 segundos)"
        echo ""
        read -p "Digite sua escolha [1-7]: " test_choice
        
        case $test_choice in
            1) pytest test_integration.py::TestSmoke -v ;;
            2) pytest test_integration.py::TestProducerAPI -v ;;
            3) pytest test_integration.py::TestMessageQueueIntegration -v ;;
            4) pytest test_integration.py::TestDatabaseIntegrity -v ;;
            5) pytest test_integration.py::TestPerformance -v ;;
            6) pytest test_integration.py::TestErrorHandling -v ;;
            7) pytest test_integration.py -v ;;
            *) echo -e "${RED}Opção inválida${NC}" ;;
        esac
        ;;
    
    4)
        echo ""
        echo -e "${BLUE}📊 Status dos containers:${NC}"
        docker-compose ps
        echo ""
        echo -e "${BLUE}Últimos logs:${NC}"
        docker-compose logs --tail=10
        ;;
    
    5)
        echo ""
        echo -e "${BLUE}📚 Documentação disponível:${NC}"
        echo ""
        echo "  1) 📖 PROJECT_EXPLANATION.md  - Explicação detalhada do projeto"
        echo "  2) 🧪 test_integration.py     - Código dos testes"
        echo "  3) 🧑‍🏫 TESTING_GUIDE.md        - Guia completo de testes"
        echo "  4) 🛠️  Makefile                - Comandos facilitados"
        echo "  5) 📋 SUMMARY.md              - Resumo tudo que foi criado"
        echo ""
        read -p "Qual arquivo deseja visualizar? [1-5]: " doc_choice
        
        case $doc_choice in
            1) cat PROJECT_EXPLANATION.md ;;
            2) cat test_integration.py | head -50 ;;
            3) cat TESTING_GUIDE.md ;;
            4) cat Makefile ;;
            5) cat SUMMARY.md ;;
            *) echo -e "${RED}Opção inválida${NC}" ;;
        esac
        ;;
    
    6)
        echo ""
        echo -e "${YELLOW}Parando containers...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Containers parados${NC}"
        echo ""
        echo -e "${YELLOW}Limpando arquivos temporários...${NC}"
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
        find . -type f -name "*.pyc" -delete 2>/dev/null
        find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null
        echo -e "${GREEN}✅ Limpeza concluída${NC}"
        ;;
    
    0)
        echo -e "${GREEN}Até logo! 👋${NC}"
        exit 0
        ;;
    
    *)
        echo -e "${RED}Opção inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  Para mais informações:                            ║${NC}"
echo -e "${BLUE}║  📖 Leia PROJECT_EXPLANATION.md                                    ║${NC}"
echo -e "${BLUE}║  🧪 Leia TESTING_GUIDE.md                                          ║${NC}"
echo -e "${BLUE}║  🛠️  Use make help para ver todos os comandos                      ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
