"""
Módulo para comparar dados de hosts entre diferentes datas.
"""
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HostComparator:
    """Compara hosts entre diferentes datas para identificar mudanças."""
    
    @staticmethod
    def compare_hosts(current_hosts: List[Dict[str, str]], 
                     previous_hosts: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """
        Compara duas listas de hosts e identifica adições e remoções.
        
        Args:
            current_hosts: Lista de hosts da data atual
            previous_hosts: Lista de hosts da data anterior
            
        Returns:
            Dicionário com listas de hosts adicionados e removidos
        """
        # Cria sets com IDs dos hosts para comparação eficiente
        current_ids = {host['host_id'] for host in current_hosts}
        previous_ids = {host['host_id'] for host in previous_hosts}
        
        # Identifica IDs adicionados e removidos
        added_ids = current_ids - previous_ids
        removed_ids = previous_ids - current_ids
        
        # Cria dicionários para acesso rápido
        current_dict = {host['host_id']: host for host in current_hosts}
        previous_dict = {host['host_id']: host for host in previous_hosts}
        
        # Identifica hosts com mudança de IP (mesmo ID, IP diferente)
        modified_hosts = []
        for host_id in current_ids & previous_ids:
            current_ip = current_dict[host_id]['ip_address']
            previous_ip = previous_dict[host_id]['ip_address']
            current_groups = current_dict[host_id]['host_groups']
            previous_groups = previous_dict[host_id]['host_groups']
            
            if current_ip != previous_ip or current_groups != previous_groups:
                modified_hosts.append({
                    'host_id': host_id,
                    'hostname': current_dict[host_id]['hostname'],
                    'old_ip': previous_ip,
                    'new_ip': current_ip,
                    'old_groups': previous_groups,
                    'new_groups': current_groups,
                    'ip_changed': current_ip != previous_ip,
                    'groups_changed': current_groups != previous_groups
                })
        
        # Monta resultado
        result = {
            'added': [current_dict[host_id] for host_id in added_ids],
            'removed': [previous_dict[host_id] for host_id in removed_ids],
            'modified': modified_hosts,
            'total_current': len(current_hosts),
            'total_previous': len(previous_hosts)
        }
        
        logger.info(f"Comparação: {len(result['added'])} adicionados, "
                   f"{len(result['removed'])} removidos, "
                   f"{len(result['modified'])} modificados")
        
        return result
    
    @staticmethod
    def get_summary(comparison: Dict) -> Dict[str, int]:
        """
        Retorna um resumo das mudanças identificadas.
        
        Args:
            comparison: Resultado da comparação de hosts
            
        Returns:
            Dicionário com contagens de mudanças
        """
        return {
            'hosts_added': len(comparison['added']),
            'hosts_removed': len(comparison['removed']),
            'hosts_modified': len(comparison['modified']),
            'total_current': comparison['total_current'],
            'total_previous': comparison['total_previous'],
            'net_change': len(comparison['added']) - len(comparison['removed'])
        }
    
    @staticmethod
    def has_changes(comparison: Dict) -> bool:
        """
        Verifica se houve alguma mudança.
        
        Args:
            comparison: Resultado da comparação de hosts
            
        Returns:
            True se houve mudanças, False caso contrário
        """
        return (len(comparison['added']) > 0 or 
                len(comparison['removed']) > 0 or 
                len(comparison['modified']) > 0)
