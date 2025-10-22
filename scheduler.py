"""
Script para agendar execução diária automática.
Executa a coleta e geração de relatório todos os dias em horário específico.
"""
import schedule
import time
import logging
from datetime import datetime
from main import load_config, collect_hosts, generate_comparison_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zabbix_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def daily_job():
    """Job que será executado diariamente."""
    logger.info("=" * 80)
    logger.info(f"Iniciando job diário em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        config = load_config()
        
        # Coleta hosts do dia
        logger.info("Etapa 1: Coletando hosts do Zabbix...")
        collection_date = collect_hosts(config)
        
        if collection_date:
            # Gera relatório comparativo
            logger.info("Etapa 2: Gerando relatório comparativo...")
            generate_comparison_report(config)
            
            logger.info("✅ Job diário concluído com sucesso!")
        else:
            logger.warning("⚠️ Coleta não foi realizada, relatório não gerado")
            
    except Exception as e:
        logger.error(f"❌ Erro durante execução do job diário: {e}", exc_info=True)
    
    logger.info("=" * 80)


def main():
    """Função principal do agendador."""
    # Configuração do horário de execução
    # Por padrão, executa às 6:00 da manhã todos os dias
    EXECUTION_TIME = "06:00"
    
    logger.info("=" * 80)
    logger.info("AGENDADOR DE RELATÓRIOS ZABBIX")
    logger.info("=" * 80)
    logger.info(f"Horário configurado para execução diária: {EXECUTION_TIME}")
    logger.info("Pressione Ctrl+C para interromper")
    logger.info("=" * 80)
    
    # Agenda o job
    schedule.every().day.at(EXECUTION_TIME).do(daily_job)
    
    # Opção para executar imediatamente ao iniciar
    logger.info("Deseja executar o job imediatamente? (s/n): ", )
    try:
        response = input().lower()
        if response == 's':
            logger.info("Executando job imediatamente...")
            daily_job()
    except:
        pass
    
    # Loop principal
    logger.info(f"\nAgendador ativo. Próxima execução: {schedule.next_run()}")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("Agendador interrompido pelo usuário")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
