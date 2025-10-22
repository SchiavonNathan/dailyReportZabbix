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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zabbix_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

# Função para remover acentos de strings
def remove_acentos(text):
    if not isinstance(text, str):
        return text
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')

# Substitui configuração de logging para padrão APM JSON
logging.basicConfig(handlers=[]) 
handler = logging.StreamHandler()
handler.setFormatter(APMJsonFormatter())
logger = logging.getLogger()
logger.handlers = [handler]
logger.setLevel(logging.INFO)

# File handler para log persistente (opcional, formato APM)
file_handler = logging.FileHandler('zabbix_scheduler.log')
file_handler.setFormatter(APMJsonFormatter())
logger.addHandler(file_handler)

# Patch no logger para remover acentos das mensagens
class APMJsonFormatterNoAcento(APMJsonFormatter):
    def format(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = remove_acentos(record.msg)
        return super().format(record)

handler.setFormatter(APMJsonFormatterNoAcento())
file_handler.setFormatter(APMJsonFormatterNoAcento())

def get_period_dates(db, days):
    all_dates = db.get_all_collection_dates()
    if not all_dates:
        return []
    today = datetime.now().date()
    period = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    return [d for d in all_dates if d in period]


def generate_period_summary(db, dates):
    comparator = HostComparator()
    total_added = 0
    total_removed = 0
    total_modified = 0
    total_current = 0
    total_previous = 0
    all_added = []
    all_removed = []
    all_modified = []
    for i in range(1, len(dates)):
        current_hosts = db.get_hosts_by_date(dates[i])
        previous_hosts = db.get_hosts_by_date(dates[i-1])
        comp = comparator.compare_hosts(current_hosts, previous_hosts)
        total_added += len(comp['added'])
        total_removed += len(comp['removed'])
        total_modified += len(comp['modified'])
        total_current = comp['total_current']
        total_previous = comp['total_previous']
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
    logger.info(f"Iniciando relatório de {period_name}...")
    config = load_config()
    db = DatabaseManager(config['database_path'])
    dates = get_period_dates(db, days)
    if len(dates) < 2:
        logger.warning(f"Não há dados suficientes para gerar o relatório de {period_name}.")
        return
    dates = sorted(dates)
    summary, comparison = generate_period_summary(db, dates)
    report_gen = ReportGenerator(config['reports_dir'])
    report_format = config['report_format'].lower()
    report_files = []
    period_label = f"{period_name.capitalize()} {dates[0]} a {dates[-1]}"
    if report_format in ['html', 'both']:
        html_path = report_gen.generate_html_report(comparison, dates[-1], dates[0])
        report_files.append(html_path)
    if report_format in ['text', 'both']:
        text_path = report_gen.generate_text_report(comparison, dates[-1], dates[0])
        report_files.append(text_path)
    if config['send_email']:
        email_sender = EmailSender(
            smtp_server=config['smtp_server'],
            smtp_port=config['smtp_port'],
            username=config['smtp_username'],
            password=config['smtp_password'],
            use_tls=config['smtp_use_tls']
        )
        attachments = report_files if config['email_attach_reports'] else None
        subject = f"📊 Relatório {period_name.capitalize()} Zabbix: {dates[0]} a {dates[-1]}"
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
        logger.info(f"Envio de email desabilitado para relatório de {period_name}.")


def daily_job():
    logger.info("Iniciando job diário...")
    config = load_config()
    collection_date = collect_hosts(config)
    if collection_date:
        generate_comparison_report(config)
        logger.info("✅ Relatório diário concluído!")
    else:
        logger.warning("⚠️ Coleta não realizada, relatório diário não gerado.")

def weekly_job():
    send_period_report('semanal', 7)

def monthly_job_guard():
    if datetime.now().day == 1:
        monthly_job()

def monthly_job():
    send_period_report('mensal', 31)


def main():
    logger.info("Agendador de relatórios diário, semanal e mensal iniciado.")
    # Diário: todo dia às 06:00
    schedule.every().day.at("06:00").do(daily_job)
    # Semanal: toda sexta às 18:00
    schedule.every().friday.at("18:00").do(weekly_job)
    # Mensal: todo dia às 08:00, mas só executa se for dia 1
    schedule.every().day.at("08:00").do(monthly_job_guard)
    logger.info("Relatório diário: todo dia às 06:00")
    logger.info("Relatório semanal: toda sexta às 18:00")
    logger.info("Relatório mensal: todo dia 1 às 08:00")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
