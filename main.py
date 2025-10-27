"""
Script principal para coletar hosts do Zabbix e gerar relatórios de mudanças.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import argparse

from database import DatabaseManager
from zabbix_collector import ZabbixCollector
from comparator import HostComparator
from report_generator import ReportGenerator
from email_sender import EmailSender

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zabbix_daily_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config():
    load_dotenv()
    
    config = {
        'zabbix_url': os.getenv('ZABBIX_URL'),
        'zabbix_username': os.getenv('ZABBIX_USERNAME'),
        'zabbix_password': os.getenv('ZABBIX_PASSWORD'),
        'database_path': os.getenv('DATABASE_PATH', 'zabbix_hosts.db'),
        'reports_dir': os.getenv('REPORTS_DIR', 'reports'),
        'report_format': os.getenv('REPORT_FORMAT', 'both'),
        'send_email': os.getenv('SEND_EMAIL', 'false').lower() == 'true',
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.office365.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'smtp_username': os.getenv('SMTP_USERNAME'),
        'smtp_password': os.getenv('SMTP_PASSWORD'),
        'smtp_use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
        'email_recipients': os.getenv('EMAIL_RECIPIENTS', '').split(',') if os.getenv('EMAIL_RECIPIENTS') else [],
        'email_attach_reports': os.getenv('EMAIL_ATTACH_REPORTS', 'true').lower() == 'true'
    }
    
    if not config['zabbix_url'] or not config['zabbix_username'] or not config['zabbix_password']:
        logger.error("Configurações do Zabbix não encontradas no arquivo .env")
        logger.error("Copie .env.example para .env e configure suas credenciais")
        sys.exit(1)
    
    if config['send_email']:
        if not config['smtp_username'] or not config['smtp_password']:
            logger.warning("Envio de email ativado mas credenciais SMTP não configuradas")
            logger.warning("O email não será enviado. Configure SMTP_USERNAME e SMTP_PASSWORD")
            config['send_email'] = False
        elif not config['email_recipients']:
            logger.warning("Envio de email ativado mas nenhum destinatário configurado")
            logger.warning("Configure EMAIL_RECIPIENTS no arquivo .env")
            config['send_email'] = False
    
    return config


def collect_hosts(config):
    logger.info("Iniciando coleta de hosts do Zabbix...")
    
    with ZabbixCollector(
        config['zabbix_url'],
        config['zabbix_username'],
        config['zabbix_password']
    ) as collector:
        hosts = collector.get_all_hosts()
    
    db = DatabaseManager(config['database_path'])
    collection_date = datetime.now().strftime("%Y-%m-%d")
    
    if db.check_date_exists(collection_date):
        logger.warning(f"Já existe uma coleta para a data {collection_date}")
        response = input("Deseja substituir? (s/n): ").lower()
        if response != 's':
            logger.info("Coleta cancelada pelo usuário")
            return None
    
    db.save_hosts(hosts, collection_date)
    logger.info(f"Coleta concluída: {len(hosts)} hosts salvos para {collection_date}")
    
    return collection_date


def generate_comparison_report(config, current_date=None, previous_date=None):
    logger.info("Iniciando geração de relatório comparativo...")
    
    db = DatabaseManager(config['database_path'])
    
    if current_date is None:
        current_date = datetime.now().strftime("%Y-%m-%d")
    
    if previous_date is None:
        all_dates = db.get_all_collection_dates()
        if not all_dates:
            logger.error("Nenhuma coleta encontrada no banco de dados")
            return
        
        earlier_dates = [d for d in all_dates if d < current_date]
        if not earlier_dates:
            logger.warning(f"Não há coleta anterior a {current_date} para comparação")
            logger.info("Execute a coleta novamente amanhã para gerar comparações")
            return
        
        previous_date = earlier_dates[0]
    
    logger.info(f"Comparando {current_date} com {previous_date}")
    
    current_hosts = db.get_hosts_by_date(current_date)
    previous_hosts = db.get_hosts_by_date(previous_date)
    
    if not current_hosts:
        logger.error(f"Nenhum host encontrado para a data {current_date}")
        return
    
    if not previous_hosts:
        logger.error(f"Nenhum host encontrado para a data {previous_date}")
        return
    
    comparator = HostComparator()
    comparison = comparator.compare_hosts(current_hosts, previous_hosts)
    
    summary = comparator.get_summary(comparison)
    logger.info("=" * 60)
    logger.info("RESUMO DA COMPARAÇÃO")
    logger.info("=" * 60)
    logger.info(f"Hosts adicionados: {summary['hosts_added']}")
    logger.info(f"Hosts removidos: {summary['hosts_removed']}")
    logger.info(f"Hosts modificados: {summary['hosts_modified']}")
    logger.info(f"Total atual: {summary['total_current']}")
    logger.info(f"Total anterior: {summary['total_previous']}")
    logger.info(f"Variação líquida: {summary['net_change']:+d}")
    logger.info("=" * 60)
    
    report_gen = ReportGenerator(config['reports_dir'])
    report_format = config['report_format'].lower()
    
    report_files = []
    
    if report_format in ['html', 'both']:
        html_path = report_gen.generate_html_report(comparison, current_date, previous_date)
        logger.info(f"✅ Relatório HTML gerado: {html_path}")
        report_files.append(html_path)
    
    if report_format in ['text', 'both']:
        text_path = report_gen.generate_text_report(comparison, current_date, previous_date)
        logger.info(f"✅ Relatório de texto gerado: {text_path}")
        report_files.append(text_path)
    
    if config['send_email']:
        logger.info("=" * 60)
        logger.info("Enviando relatório por email...")
        
        email_sender = EmailSender(
            smtp_server=config['smtp_server'],
            smtp_port=config['smtp_port'],
            username=config['smtp_username'],
            password=config['smtp_password'],
            use_tls=config['smtp_use_tls']
        )
        
        attachments = report_files if config['email_attach_reports'] else None
        
        success = email_sender.send_simple_report(
            recipient_emails=config['email_recipients'],
            report_date=current_date,
            summary=summary,
            has_changes=comparator.has_changes(comparison),
            comparison=comparison,
            report_files=attachments
        )
        
        if success:
            logger.info(f"📧 Email enviado para: {', '.join(config['email_recipients'])}")
        else:
            logger.error("❌ Falha ao enviar email")
    else:
        logger.info("Envio de email desabilitado (SEND_EMAIL=false)")



def main():
    parser = argparse.ArgumentParser(
        description='Coleta hosts do Zabbix e gera relatórios de mudanças'
    )
    parser.add_argument(
        '--action',
        choices=['collect', 'report', 'both'],
        default='both',
        help='Ação a executar: collect (coletar), report (relatório), both (ambos)'
    )
    parser.add_argument(
        '--current-date',
        help='Data atual para comparação (formato: YYYY-MM-DD)'
    )
    parser.add_argument(
        '--previous-date',
        help='Data anterior para comparação (formato: YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    try:
        config = load_config()
        
        if args.action in ['collect', 'both']:
            collection_date = collect_hosts(config)
            if collection_date is None and args.action == 'collect':
                return
        
        if args.action in ['report', 'both']:
            generate_comparison_report(
                config,
                args.current_date,
                args.previous_date
            )
        
        logger.info("Processo concluído com sucesso!")
        
    except KeyboardInterrupt:
        logger.info("\nProcesso interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro durante execução: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
