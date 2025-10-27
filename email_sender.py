"""
Módulo para envio de emails com relatórios.
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, use_tls: bool = True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    def send_report_email(self, recipient_emails: List[str], subject: str,
                         body_html: str, body_text: str = None,
                         attachments: List[str] = None) -> bool:
        try:
            # Cria mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = ', '.join(recipient_emails)
            msg['Subject'] = subject
            
            if body_text:
                part_text = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(part_text)
            
            part_html = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part_html)
            
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        self._attach_file(msg, filepath)
                    else:
                        logger.warning(f"Arquivo não encontrado: {filepath}")
            
            logger.info(f"Conectando ao servidor SMTP: {self.smtp_server}:{self.smtp_port}")
            
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.username, self.password)
            
            logger.info(f"Enviando email para: {', '.join(recipient_emails)}")
            server.send_message(msg)
            server.quit()
            
            logger.info("✅ Email enviado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {e}", exc_info=True)
            return False
    
    def _attach_file(self, msg: MIMEMultipart, filepath: str):
        try:
            filename = os.path.basename(filepath)
            
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            logger.info(f"Arquivo anexado: {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao anexar arquivo {filepath}: {e}")
    
    def send_simple_report(self, recipient_emails: List[str], 
                          report_date: str, summary: dict,
                          has_changes: bool, comparison: dict = None,
                          report_files: List[str] = None) -> bool:
        subject = f"Relatório Zabbix - {report_date}"
        
        if not has_changes:
            subject += " - Sem Mudanças"
        elif summary['hosts_added'] > 0 or summary['hosts_removed'] > 0:
            subject += f" - {summary['hosts_added']} Adicionados, {summary['hosts_removed']} Removidos"
        
        body_html = self._build_email_body_html(report_date, summary, has_changes, comparison)
        
        body_text = self._build_email_body_text(report_date, summary, has_changes, comparison)
        
        return self.send_report_email(
            recipient_emails=recipient_emails,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            attachments=report_files
        )
    
    def _build_email_body_html(self, report_date: str, summary: dict, 
                               has_changes: bool, comparison: dict = None) -> str:
        
        status_icon = "✅" if not has_changes else "⚠️"
        status_text = "Nenhuma mudança detectada" if not has_changes else "Mudanças detectadas"
        status_color = "#28a745" if not has_changes else "#ffc107"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .status {{
            background-color: {status_color};
            color: white;
            padding: 15px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
        }}
        .content {{
            background-color: #fff;
            padding: 30px;
            border: 1px solid #ddd;
            border-top: none;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        .summary-item:last-child {{
            border-bottom: none;
        }}
        .summary-label {{
            font-weight: 600;
            color: #666;
        }}
        .summary-value {{
            font-weight: bold;
            color: #007bff;
            font-size: 18px;
        }}
        .summary-value.positive {{
            color: #28a745;
        }}
        .summary-value.negative {{
            color: #dc3545;
        }}
        .summary-value.warning {{
            color: #ffc107;
        }}
        .hosts-section {{
            margin: 30px 0;
        }}
        .hosts-section h3 {{
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #007bff;
        }}
        .host-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 14px;
        }}
        .host-table th {{
            background-color: #007bff;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: 600;
        }}
        .host-table td {{
            padding: 10px;
            border-bottom: 1px solid #dee2e6;
        }}
        .host-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .host-table tr.added {{
            background-color: #d4edda;
        }}
        .host-table tr.removed {{
            background-color: #f8d7da;
        }}
        .host-table tr.modified {{
            background-color: #fff3cd;
        }}
        .no-hosts {{
            color: #666;
            font-style: italic;
            padding: 10px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 8px 8px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Relatório Diário Zabbix</h1>
        <p style="margin: 10px 0 0 0;">Data: {report_date}</p>
    </div>
    
    <div class="status">
        {status_icon} {status_text}
    </div>
    
    <div class="content">
        <h2>Resumo das Mudanças</h2>
        
        <div class="summary">
            <div class="summary-item">
                <span class="summary-label">Total de Hosts Atual:</span>
                <span class="summary-value">{summary['total_current']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Total de Hosts Anterior:</span>
                <span class="summary-value">{summary['total_previous']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Variação:</span>
                <span class="summary-value {'positive' if summary['net_change'] > 0 else 'negative' if summary['net_change'] < 0 else ''}">{summary['net_change']:+d}</span>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-item">
                <span class="summary-label">✅ Hosts Adicionados:</span>
                <span class="summary-value positive">{summary['hosts_added']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">❌ Hosts Removidos:</span>
                <span class="summary-value negative">{summary['hosts_removed']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">🔄 Hosts Modificados:</span>
                <span class="summary-value warning">{summary['hosts_modified']}</span>
            </div>
        </div>
"""
        
        if comparison and comparison.get('added'):
            html += """
        <div class="hosts-section">
            <h3>✅ Hosts Adicionados</h3>
            <table class="host-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nome do Host</th>
                        <th>Endereço IP</th>
                        <th>Grupos</th>
                        <th>Templates</th>
                    </tr>
                </thead>
                <tbody>
"""
            for host in sorted(comparison['added'], key=lambda x: x['hostname']):
                templates = host.get('templates', 'N/A')
                html += f"""
                    <tr class="added">
                        <td>{host['host_id']}</td>
                        <td><strong>{host['hostname']}</strong></td>
                        <td>{host['ip_address']}</td>
                        <td>{host['host_groups']}</td>
                        <td>{templates}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""
        
        if comparison and comparison.get('removed'):
            html += """
        <div class="hosts-section">
            <h3>❌ Hosts Removidos</h3>
            <table class="host-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nome do Host</th>
                        <th>Endereço IP</th>
                        <th>Grupos</th>
                        <th>Templates</th>
                    </tr>
                </thead>
                <tbody>
"""
            for host in sorted(comparison['removed'], key=lambda x: x['hostname']):
                templates = host.get('templates', 'N/A')
                html += f"""
                    <tr class="removed">
                        <td>{host['host_id']}</td>
                        <td><strong>{host['hostname']}</strong></td>
                        <td>{host['ip_address']}</td>
                        <td>{host['host_groups']}</td>
                        <td>{templates}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""
        
        if comparison and comparison.get('modified'):
            html += """
        <div class="hosts-section">
            <h3>🔄 Hosts Modificados</h3>
            <table class="host-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nome do Host</th>
                        <th>Campo</th>
                        <th>Valor Anterior</th>
                        <th>Valor Atual</th>
                    </tr>
                </thead>
                <tbody>
"""
            for host in sorted(comparison['modified'], key=lambda x: x['hostname']):
                if host.get('ip_changed'):
                    html += f"""
                    <tr class="modified">
                        <td>{host['host_id']}</td>
                        <td><strong>{host['hostname']}</strong></td>
                        <td>IP</td>
                        <td>{host['old_ip']}</td>
                        <td>{host['new_ip']}</td>
                    </tr>
"""
                if host.get('groups_changed'):
                    html += f"""
                    <tr class="modified">
                        <td>{host['host_id']}</td>
                        <td><strong>{host['hostname']}</strong></td>
                        <td>Grupos</td>
                        <td>{host['old_groups']}</td>
                        <td>{host['new_groups']}</td>
                    </tr>
"""
                if host.get('templates_changed'):
                    html += f"""
                    <tr class="modified">
                        <td>{host['host_id']}</td>
                        <td><strong>{host['hostname']}</strong></td>
                        <td>Templates</td>
                        <td>{host.get('old_templates', 'N/A')}</td>
                        <td>{host.get('new_templates', 'N/A')}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""
        
        if not has_changes:
            html += """
        <p style="color: #666; margin-top: 20px; text-align: center; font-size: 16px;">
            ✅ Não há mudanças para reportar nesta data.
        </p>
"""
        else:
            html += """
        <p style="color: #666; margin-top: 30px; font-style: italic;">
            📎 Relatório automatico.
        </p>
"""
        
        html += """
    </div>
    
    <div class="footer">
        <p>Powered by zbxVision by Nathan Schiavon © 2025</p>
        <p style="margin: 5px 0 0 0; font-size: 12px;">Este é um email automático, não responda.</p>
    </div>
</body>
</html>
"""
        
        return html
    
    def _build_email_body_text(self, report_date: str, summary: dict, 
                               has_changes: bool, comparison: dict = None) -> str:
        """Constrói corpo do email em texto."""
        
        status_text = "Nenhuma mudança detectada" if not has_changes else "Mudanças detectadas"
        
        text = f"""
RELATÓRIO DIÁRIO ZABBIX
Data: {report_date}

Status: {status_text}

=== RESUMO DAS MUDANÇAS ===

Total de Hosts Atual: {summary['total_current']}
Total de Hosts Anterior: {summary['total_previous']}
Variação: {summary['net_change']:+d}

Hosts Adicionados: {summary['hosts_added']}
Hosts Removidos: {summary['hosts_removed']}
Hosts Modificados: {summary['hosts_modified']}
"""
        
        if comparison and comparison.get('added'):
            text += f"\n{'=' * 80}\n"
            text += f"HOSTS ADICIONADOS ({len(comparison['added'])})\n"
            text += f"{'=' * 80}\n"
            text += f"{'ID':<12} {'Nome':<25} {'IP':<15} {'Grupos':<25}\n"
            text += f"{'-' * 80}\n"
            for host in sorted(comparison['added'], key=lambda x: x['hostname']):
                hostname = host['hostname'][:24] if len(host['hostname']) > 24 else host['hostname']
                groups = host['host_groups'][:24] if len(host['host_groups']) > 24 else host['host_groups']
                text += f"{host['host_id']:<12} {hostname:<25} {host['ip_address']:<15} {groups:<25}\n"
                templates = host.get('templates', 'N/A')
                if templates != 'N/A':
                    text += f"             Templates: {templates}\n"
        
        if comparison and comparison.get('removed'):
            text += f"\n{'=' * 80}\n"
            text += f"HOSTS REMOVIDOS ({len(comparison['removed'])})\n"
            text += f"{'=' * 80}\n"
            text += f"{'ID':<12} {'Nome':<25} {'IP':<15} {'Grupos':<25}\n"
            text += f"{'-' * 80}\n"
            for host in sorted(comparison['removed'], key=lambda x: x['hostname']):
                hostname = host['hostname'][:24] if len(host['hostname']) > 24 else host['hostname']
                groups = host['host_groups'][:24] if len(host['host_groups']) > 24 else host['host_groups']
                text += f"{host['host_id']:<12} {hostname:<25} {host['ip_address']:<15} {groups:<25}\n"
                templates = host.get('templates', 'N/A')
                if templates != 'N/A':
                    text += f"             Templates: {templates}\n"
        
        if comparison and comparison.get('modified'):
            text += f"\n{'=' * 80}\n"
            text += f"HOSTS MODIFICADOS ({len(comparison['modified'])})\n"
            text += f"{'=' * 80}\n"
            text += f"{'ID':<15} {'Nome do Host':<25} {'Campo':<10} {'Anterior':<20} {'Atual':<20}\n"
            text += f"{'-' * 80}\n"
            for host in sorted(comparison['modified'], key=lambda x: x['hostname']):
                hostname = host['hostname'][:24] if len(host['hostname']) > 24 else host['hostname']
                if host.get('ip_changed'):
                    text += f"{host['host_id']:<15} {hostname:<25} {'IP':<10} {host['old_ip']:<20} {host['new_ip']:<20}\n"
                if host.get('groups_changed'):
                    old_g = host['old_groups'][:19] if len(host['old_groups']) > 19 else host['old_groups']
                    new_g = host['new_groups'][:19] if len(host['new_groups']) > 19 else host['new_groups']
                    text += f"{host['host_id']:<15} {hostname:<25} {'Grupos':<10} {old_g:<20} {new_g:<20}\n"
                if host.get('templates_changed'):
                    old_t = host.get('old_templates', 'N/A')[:19] if len(host.get('old_templates', 'N/A')) > 19 else host.get('old_templates', 'N/A')
                    new_t = host.get('new_templates', 'N/A')[:19] if len(host.get('new_templates', 'N/A')) > 19 else host.get('new_templates', 'N/A')
                    text += f"{host['host_id']:<15} {hostname:<25} {'Templates':<10} {old_t:<20} {new_t:<20}\n"
        
        text += f"\n{'=' * 80}\n"
        if has_changes:
            text += "O relatório detalhado completo está anexado a este email.\n"
        else:
            text += "Não há mudanças para reportar nesta data.\n"
        
        text += f"{'=' * 80}\n"
        text += """
---
Relatório gerado automaticamente pelo sistema de monitoramento Zabbix
Este é um email automático, não responda.
"""
        return text
