"""
Agendador único para relatórios diário, semanal e mensal automáticos.
"""
import schedule
import time
import logging
from datetime import datetime, timedelta
from main import load_config, collect_hosts, generate_comparison_report
from database import DatabaseManager
from comparator import HostComparator
from report_generator import ReportGenerator
from email_sender import EmailSender
import json
import unicodedata

# Classe para formatação JSON do APM
class APMJsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def remove_acentos(text):
    if not isinstance(text, str):
        return text
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')

class APMJsonFormatterNoAcento(APMJsonFormatter):
    def format(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = remove_acentos(record.msg)
        return super().format(record)

handler = logging.StreamHandler()
handler.setFormatter(APMJsonFormatterNoAcento())

file_handler = logging.FileHandler('zabbix_scheduler.log')
file_handler.setFormatter(APMJsonFormatterNoAcento())

logger = logging.getLogger()
logger.handlers = [handler, file_handler]
logger.setLevel(logging.INFO)

def get_period_dates(db, days):
    all_dates = db.get_all_collection_dates()
    if not all_dates:
        return []
    today = datetime.now().date()
    period = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    return [d for d in all_dates if d in period]


def generate_period_summary(db, dates):
    comparator = HostComparator()
    all_added = []
    all_removed = []
    all_modified = []
    
    current_hosts_final = db.get_hosts_by_date(dates[-1]) 
    previous_hosts_initial = db.get_hosts_by_date(dates[0])  
    total_current = len(current_hosts_final)
    total_previous = len(previous_hosts_initial)
    
    total_added = 0
    total_removed = 0
    total_modified = 0
    
    for i in range(1, len(dates)):
        current_hosts = db.get_hosts_by_date(dates[i])
        previous_hosts = db.get_hosts_by_date(dates[i-1])
        comp = comparator.compare_hosts(current_hosts, previous_hosts)
        total_added += len(comp['added'])
        total_removed += len(comp['removed'])
        total_modified += len(comp['modified'])
        all_added.extend(comp['added'])
        all_removed.extend(comp['removed'])
        all_modified.extend(comp['modified'])
    
    summary = {
        'hosts_added': total_added,
        'hosts_removed': total_removed,
        'hosts_modified': total_modified,
        'total_current': total_current,
        'total_previous': total_previous,
        'net_change': total_current - total_previous
    }
    comparison = {
        'added': all_added,
        'removed': all_removed,
        'modified': all_modified,
        'total_current': total_current,
        'total_previous': total_previous
    }
    return summary, comparison


def send_period_report(period_name, days):
    logger.info(f"Iniciando relatorio de {period_name}...")
    
    config = load_config()
    db = DatabaseManager(config['database_path'])
    dates = get_period_dates(db, days)
    
    if len(dates) < 2:
        logger.warning(f"Nao ha dados suficientes para gerar o relatorio de {period_name}.")
        logger.warning(f"Necessario pelo menos 2 datas, encontradas: {len(dates)}")
        return
    
    dates = sorted(dates)
    logger.info(f"Periodo: {dates[0]} a {dates[-1]} ({len(dates)} datas)")
    
    # Gera resumo do período
    summary, comparison = generate_period_summary(db, dates)
    
    # Gera relatórios
    report_gen = ReportGenerator(config['reports_dir'])
    report_format = config['report_format'].lower()
    report_files = []
    period_label = f"{period_name.capitalize()} {dates[0]} a {dates[-1]}"
    
    if report_format in ['html', 'both']:
        html_path = report_gen.generate_html_report(comparison, dates[-1], dates[0])
        report_files.append(html_path)
        logger.info(f"Relatorio HTML gerado: {html_path}")
    
    if report_format in ['text', 'both']:
        text_path = report_gen.generate_text_report(comparison, dates[-1], dates[0])
        report_files.append(text_path)
        logger.info(f"Relatorio TXT gerado: {text_path}")
    
    # Envia por email se configurado
    if config['send_email']:
        email_sender = EmailSender(
            smtp_server=config['smtp_server'],
            smtp_port=config['smtp_port'],
            username=config['smtp_username'],
            password=config['smtp_password'],
            use_tls=config['smtp_use_tls']
        )
        
        attachments = report_files if config['email_attach_reports'] else None
        subject = f"Relatorio {period_name.capitalize()} Zabbix: {dates[0]} a {dates[-1]}"
        
        email_sender.send_simple_report(
            recipient_emails=config['email_recipients'],
            report_date=period_label,
            summary=summary,
            has_changes=(summary['hosts_added'] > 0 or summary['hosts_removed'] > 0 or summary['hosts_modified'] > 0),
            comparison=comparison,
            report_files=attachments
        )
        
        logger.info(f"Email de {period_name} enviado para: {', '.join(config['email_recipients'])}")
    else:
        logger.info(f"Envio de email desabilitado para relatorio de {period_name}.")


def daily_job():
    logger.info("=" * 80)
    logger.info("Iniciando job diario...")
    logger.info("=" * 80)
    try:
        config = load_config()
        logger.info("Configuracoes carregadas com sucesso")
        
        collection_date = collect_hosts(config)
        
        if collection_date:
            logger.info(f"Coleta concluida para a data: {collection_date}")
            
            generate_comparison_report(config)
            logger.info("Relatorio diario concluido!")
        else:
            logger.warning("Coleta nao realizada, relatorio diario nao gerado.")
    except Exception as e:
        logger.error(f"Erro no job diario: {e}", exc_info=True)
    logger.info("=" * 80)

def weekly_job():
    logger.info("=" * 80)
    logger.info("Iniciando job semanal...")
    logger.info("=" * 80)
    try:
        send_period_report('semanal', 7)
        logger.info("Relatorio semanal concluido!")
    except Exception as e:
        logger.error(f"Erro no job semanal: {e}", exc_info=True)
    logger.info("=" * 80)

def monthly_job_guard():
    if datetime.now().day == 1:
        monthly_job()
    else:
        logger.debug(f"Dia {datetime.now().day} - pulando job mensal (executa apenas no dia 1)")

def monthly_job():
    logger.info("=" * 80)
    logger.info("Iniciando job mensal...")
    logger.info("=" * 80)
    try:
        send_period_report('mensal', 31)
        logger.info("Relatorio mensal concluido!")
    except Exception as e:
        logger.error(f"Erro no job mensal: {e}", exc_info=True)
    logger.info("=" * 80)


def main():
    logger.info("=" * 80)
    logger.info("Agendador de relatorios Zabbix iniciado")
    logger.info("=" * 80)
    
    # Configura os jobs
    schedule.every().day.at("06:00").do(daily_job)
    schedule.every().friday.at("18:00").do(weekly_job)
    schedule.every().day.at("08:00").do(monthly_job_guard)
    
    logger.info("Jobs configurados:")
    logger.info("  - Relatorio diario: todo dia as 06:00")
    logger.info("  - Relatorio semanal: toda sexta as 18:00")
    logger.info("  - Relatorio mensal: todo dia 1 as 08:00")
    logger.info("=" * 80)
    
    # Loop principal
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("=" * 80)
        logger.info("Agendador interrompido pelo usuario")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"Erro no loop principal: {e}", exc_info=True)


if __name__ == "__main__":
    main()
