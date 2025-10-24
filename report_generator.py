"""
Módulo para gerar relatórios de mudanças em hosts do Zabbix.
"""
from datetime import datetime
from typing import Dict
import logging
import os

# Não configura logging aqui - deixa para o módulo principal configurar
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Gerador de relatórios de mudanças em hosts."""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Inicializa o gerador de relatórios.
        
        Args:
            output_dir: Diretório onde os relatórios serão salvos
        """
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Diretório de relatórios criado: {output_dir}")
    
    def generate_html_report(self, comparison: Dict, current_date: str, 
                            previous_date: str) -> str:
        """
        Gera um relatório em HTML das mudanças detectadas.
        
        Args:
            comparison: Resultado da comparação de hosts
            current_date: Data atual da coleta
            previous_date: Data anterior da coleta
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zabbix_report_{current_date}_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        html_content = self._build_html_content(comparison, current_date, previous_date)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Relatório HTML gerado: {filepath}")
        return filepath
    
    def generate_text_report(self, comparison: Dict, current_date: str, 
                            previous_date: str) -> str:
        """
        Gera um relatório em texto das mudanças detectadas.
        
        Args:
            comparison: Resultado da comparação de hosts
            current_date: Data atual da coleta
            previous_date: Data anterior da coleta
            
        Returns:
            Caminho do arquivo de texto gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zabbix_report_{current_date}_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        text_content = self._build_text_content(comparison, current_date, previous_date)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        logger.info(f"Relatório de texto gerado: {filepath}")
        return filepath
    
    def _build_html_content(self, comparison: Dict, current_date: str, 
                           previous_date: str) -> str:
        """Constrói o conteúdo HTML do relatório."""
        
        has_changes = (len(comparison['added']) > 0 or 
                      len(comparison['removed']) > 0 or 
                      len(comparison['modified']) > 0)
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Hosts Zabbix - {current_date}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #e9ecef;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-item {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            font-size: 16px;
        }}
        .summary-label {{
            font-weight: bold;
            color: #666;
        }}
        .summary-value {{
            color: #007bff;
            font-size: 20px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #007bff;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .added {{
            background-color: #d4edda;
        }}
        .removed {{
            background-color: #f8d7da;
        }}
        .modified {{
            background-color: #fff3cd;
        }}
        .no-changes {{
            background-color: #d1ecf1;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            color: #0c5460;
            font-size: 18px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Relatório de Mudanças em Hosts Zabbix</h1>
        
        <div class="summary">
            <div class="summary-item">
                <span class="summary-label">Data Atual:</span>
                <span class="summary-value">{current_date}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Data Anterior:</span>
                <span class="summary-value">{previous_date}</span>
            </div>
            <br>
            <div class="summary-item">
                <span class="summary-label">Total Atual:</span>
                <span class="summary-value">{comparison['total_current']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Total Anterior:</span>
                <span class="summary-value">{comparison['total_previous']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Variação:</span>
                <span class="summary-value">{comparison['total_current'] - comparison['total_previous']:+d}</span>
            </div>
        </div>
"""
        
        if not has_changes:
            html += """
        <div class="no-changes">
            ✅ Nenhuma mudança detectada entre as datas comparadas.
        </div>
"""
        else:
            # Hosts adicionados
            if comparison['added']:
                html += f"""
        <h2>✅ Hosts Adicionados ({len(comparison['added'])})</h2>
        <table>
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
                    <td>{host['hostname']}</td>
                    <td>{host['ip_address']}</td>
                    <td>{host['host_groups']}</td>
                    <td>{templates}</td>
                </tr>
"""
                html += """
            </tbody>
        </table>
"""
            
            # Hosts removidos
            if comparison['removed']:
                html += f"""
        <h2>❌ Hosts Removidos ({len(comparison['removed'])})</h2>
        <table>
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
                    <td>{host['hostname']}</td>
                    <td>{host['ip_address']}</td>
                    <td>{host['host_groups']}</td>
                    <td>{templates}</td>
                </tr>
"""
                html += """
            </tbody>
        </table>
"""
            
            # Hosts modificados (mudança de IP)
            if comparison['modified']:
                html += f"""
        <h2>🔄 Hosts Modificados ({len(comparison['modified'])})</h2>
        <table>
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
                    <td>{host['hostname']}</td>
                    <td>IP</td>
                    <td>{host['old_ip']}</td>
                    <td>{host['new_ip']}</td>
                </tr>
"""
                    if host.get('groups_changed'):
                        html += f"""
                <tr class="modified">
                    <td>{host['host_id']}</td>
                    <td>{host['hostname']}</td>
                    <td>Grupos</td>
                    <td>{host['old_groups']}</td>
                    <td>{host['new_groups']}</td>
                </tr>
"""
                    if host.get('templates_changed'):
                        html += f"""
                <tr class="modified">
                    <td>{host['host_id']}</td>
                    <td>{host['hostname']}</td>
                    <td>Templates</td>
                    <td>{host.get('old_templates', 'N/A')}</td>
                    <td>{host.get('new_templates', 'N/A')}</td>
                </tr>
"""
                html += """
            </tbody>
        </table>
"""
        
        html += f"""
        <div class="footer">
            Relatório gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _build_text_content(self, comparison: Dict, current_date: str, 
                           previous_date: str) -> str:
        """Constrói o conteúdo de texto do relatório."""
        
        lines = []
        lines.append("=" * 80)
        lines.append("RELATÓRIO DE MUDANÇAS EM HOSTS ZABBIX")
        lines.append("=" * 80)
        lines.append(f"\nData da Comparação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append(f"Data Atual: {current_date}")
        lines.append(f"Data Anterior: {previous_date}")
        lines.append("\n" + "-" * 80)
        lines.append("RESUMO")
        lines.append("-" * 80)
        lines.append(f"Total de Hosts Atual: {comparison['total_current']}")
        lines.append(f"Total de Hosts Anterior: {comparison['total_previous']}")
        lines.append(f"Variação: {comparison['total_current'] - comparison['total_previous']:+d}")
        lines.append(f"\nHosts Adicionados: {len(comparison['added'])}")
        lines.append(f"Hosts Removidos: {len(comparison['removed'])}")
        lines.append(f"Hosts Modificados (IP): {len(comparison['modified'])}")
        
        has_changes = (len(comparison['added']) > 0 or 
                      len(comparison['removed']) > 0 or 
                      len(comparison['modified']) > 0)
        
        if not has_changes:
            lines.append("\n" + "=" * 80)
            lines.append("✅ NENHUMA MUDANÇA DETECTADA")
            lines.append("=" * 80)
        else:
            # Hosts adicionados
            if comparison['added']:
                lines.append("\n" + "=" * 80)
                lines.append(f"HOSTS ADICIONADOS ({len(comparison['added'])})")
                lines.append("=" * 80)
                lines.append(f"{'ID':<12} {'Nome':<25} {'IP':<15} {'Grupos':<25}")
                lines.append("-" * 80)
                for host in sorted(comparison['added'], key=lambda x: x['hostname']):
                    hostname = host['hostname'][:24] if len(host['hostname']) > 24 else host['hostname']
                    groups = host['host_groups'][:24] if len(host['host_groups']) > 24 else host['host_groups']
                    lines.append(f"{host['host_id']:<12} {hostname:<25} {host['ip_address']:<15} {groups:<25}")
                    templates = host.get('templates', 'N/A')
                    if templates != 'N/A':
                        lines.append(f"             Templates: {templates}")
            
            # Hosts removidos
            if comparison['removed']:
                lines.append("\n" + "=" * 80)
                lines.append(f"HOSTS REMOVIDOS ({len(comparison['removed'])})")
                lines.append("=" * 80)
                lines.append(f"{'ID':<12} {'Nome':<25} {'IP':<15} {'Grupos':<25}")
                lines.append("-" * 80)
                for host in sorted(comparison['removed'], key=lambda x: x['hostname']):
                    hostname = host['hostname'][:24] if len(host['hostname']) > 24 else host['hostname']
                    groups = host['host_groups'][:24] if len(host['host_groups']) > 24 else host['host_groups']
                    lines.append(f"{host['host_id']:<12} {hostname:<25} {host['ip_address']:<15} {groups:<25}")
                    templates = host.get('templates', 'N/A')
                    if templates != 'N/A':
                        lines.append(f"             Templates: {templates}")
            
            # Hosts modificados
            if comparison['modified']:
                lines.append("\n" + "=" * 80)
                lines.append(f"HOSTS MODIFICADOS ({len(comparison['modified'])})")
                lines.append("=" * 80)
                lines.append(f"{'ID':<15} {'Nome do Host':<30} {'Campo':<15} {'Valor Anterior':<30} {'Valor Atual':<30}")
                lines.append("-" * 80)
                for host in sorted(comparison['modified'], key=lambda x: x['hostname']):
                    if host.get('ip_changed'):
                        lines.append(f"{host['host_id']:<15} {host['hostname']:<30} {'IP':<15} {host['old_ip']:<30} {host['new_ip']:<30}")
                    if host.get('groups_changed'):
                        old_groups = host['old_groups'][:30] if len(host['old_groups']) > 30 else host['old_groups']
                        new_groups = host['new_groups'][:30] if len(host['new_groups']) > 30 else host['new_groups']
                        lines.append(f"{host['host_id']:<15} {host['hostname']:<30} {'Grupos':<15} {old_groups:<30} {new_groups:<30}")
                    if host.get('templates_changed'):
                        old_templates = host.get('old_templates', 'N/A')[:30] if len(host.get('old_templates', 'N/A')) > 30 else host.get('old_templates', 'N/A')
                        new_templates = host.get('new_templates', 'N/A')[:30] if len(host.get('new_templates', 'N/A')) > 30 else host.get('new_templates', 'N/A')
                        lines.append(f"{host['host_id']:<15} {host['hostname']:<30} {'Templates':<15} {old_templates:<30} {new_templates:<30}")
        
        lines.append("\n" + "=" * 80)
        lines.append(f"Fim do Relatório - Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
