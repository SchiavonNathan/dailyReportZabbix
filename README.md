# 📊 Zabbix Daily Report - Relatório Diário de Hosts

Sistema automatizado para monitorar mudanças nos hosts cadastrados no Zabbix, gerando relatórios diários comparativos.

## 🎯 Funcionalidades

- ✅ Coleta diária de todos os hosts cadastrados no Zabbix (nome, IP e grupos)
- 💾 Armazenamento histórico em banco de dados SQLite
- 🔍 Comparação automática com o dia anterior
- 📝 Detecção de hosts adicionados, removidos e modificados
- 📄 Geração de relatórios em HTML e/ou texto
- 📧 Envio automático de relatórios por email (Office 365/Outlook)
- ⏰ Agendamento automático de execução diária
- 📊 Interface visual elegante nos relatórios HTML

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Acesso a um servidor Zabbix com API habilitada
- Credenciais de usuário com permissão de leitura no Zabbix

## 🚀 Instalação

### 1. Clone ou baixe o projeto

```bash
cd c:\projetos-ultra\dailyReportZabbix
```

### 2. Crie um ambiente virtual (opcional, mas recomendado)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instale as dependências

```powershell
pip install -r requirements.txt
```

### 4. Configure as credenciais

Copie o arquivo de exemplo e edite com suas credenciais:

```powershell
copy .env.example .env
notepad .env
```

Edite o arquivo `.env` com suas informações:

```env
# Configurações do Zabbix
ZABBIX_URL=http://seu-servidor-zabbix.com
ZABBIX_USERNAME=seu_usuario
ZABBIX_PASSWORD=sua_senha

# Configurações do Banco de Dados
DATABASE_PATH=zabbix_hosts.db

# Configurações de Relatórios
REPORTS_DIR=reports

# Formato de Relatório (html, text ou both)
REPORT_FORMAT=both

# Configurações de Email
SEND_EMAIL=true
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@empresa.com
SMTP_PASSWORD=sua-senha-email
SMTP_USE_TLS=true
EMAIL_RECIPIENTS=destinatario1@empresa.com,destinatario2@empresa.com
EMAIL_ATTACH_REPORTS=true
```

## 💻 Uso

### Modo Manual

#### Executar coleta e relatório (padrão)

```powershell
python main.py
```

#### Apenas coletar dados

```powershell
python main.py --action collect
```

#### Apenas gerar relatório

```powershell
python main.py --action report
```

#### Comparar datas específicas

```powershell
python main.py --action report --current-date 2025-10-21 --previous-date 2025-10-20
```

### Modo Automático (Agendado)

Para executar automaticamente todos os dias às 06:00:

```powershell
python scheduler.py
```

O agendador ficará em execução contínua e executará a coleta e geração de relatório no horário configurado.

**Para alterar o horário**, edite a variável `EXECUTION_TIME` no arquivo `scheduler.py`:

```python
EXECUTION_TIME = "08:30"  # Altere para o horário desejado
```

## 📁 Estrutura do Projeto

```
dailyReportZabbix/
│
├── main.py                 # Script principal
├── scheduler.py            # Agendador de tarefas diárias
├── database.py             # Gerenciador do banco de dados
├── zabbix_collector.py     # Coletor de dados do Zabbix
├── comparator.py           # Comparador de dados
├── report_generator.py     # Gerador de relatórios
├── requirements.txt        # Dependências do projeto
├── .env.example           # Exemplo de configuração
├── .env                   # Configurações (não versionar!)
├── README.md              # Este arquivo
│
├── zabbix_hosts.db        # Banco de dados (criado automaticamente)
├── reports/               # Relatórios gerados (criado automaticamente)
│   ├── zabbix_report_2025-10-21_120000.html
│   └── zabbix_report_2025-10-21_120000.txt
│
└── logs/
    ├── zabbix_daily_report.log
    └── zabbix_scheduler.log
```

## 📊 Exemplo de Relatório

Os relatórios gerados incluem:

### Informações Apresentadas

- 📅 **Datas comparadas** (atual e anterior)
- 📈 **Resumo estatístico**
  - Total de hosts atual e anterior
  - Variação líquida
- ✅ **Hosts Adicionados** (ID, Nome, IP)
- ❌ **Hosts Removidos** (ID, Nome, IP)
- 🔄 **Hosts Modificados** (mudança de IP)

### Formatos Disponíveis

1. **HTML**: Relatório visual com cores e formatação
2. **TXT**: Relatório em texto simples para logs

## 🔧 Configurações Avançadas

### Alterar formato do relatório

No arquivo `.env`, altere:

```env
REPORT_FORMAT=html      # Apenas HTML
REPORT_FORMAT=text      # Apenas texto
REPORT_FORMAT=both      # Ambos (padrão)
```

### Alterar caminho do banco de dados

```env
DATABASE_PATH=C:\dados\zabbix_hosts.db
```

### Alterar diretório de relatórios

```env
REPORTS_DIR=C:\relatorios\zabbix
```

### Configurar envio de email

Para **Office 365/Outlook**:
```env
SEND_EMAIL=true
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@empresa.com
SMTP_PASSWORD=sua-senha
SMTP_USE_TLS=true
EMAIL_RECIPIENTS=destinatario1@empresa.com,destinatario2@empresa.com
EMAIL_ATTACH_REPORTS=true
```

Para **Gmail** (requer senha de app):
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

Para **outro servidor SMTP**:
```env
SMTP_SERVER=smtp.seu-servidor.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**Múltiplos destinatários**: Separe os emails com vírgula:
```env
EMAIL_RECIPIENTS=email1@empresa.com,email2@empresa.com,email3@empresa.com
```

**Desabilitar envio de email**:
```env
SEND_EMAIL=false
```

## 🔄 Agendamento no Windows (Task Scheduler)

Para executar automaticamente no Windows sem manter o terminal aberto:

1. Abra o **Agendador de Tarefas** (Task Scheduler)
2. Crie uma nova tarefa
3. Configure para executar diariamente às 06:00
4. Ação: Executar programa
   - Programa: `C:\caminho\para\python.exe`
   - Argumentos: `C:\projetos-ultra\dailyReportZabbix\main.py`
   - Iniciar em: `C:\projetos-ultra\dailyReportZabbix`

## 📝 Logs

Os logs são salvos automaticamente:

- `zabbix_daily_report.log` - Log de execuções do script principal
- `zabbix_scheduler.log` - Log do agendador automático

## ⚠️ Solução de Problemas

### Erro de conexão com Zabbix

```
Erro ao conectar ao Zabbix
```

**Solução**: Verifique a URL, usuário e senha no arquivo `.env`

### Nenhuma coleta anterior para comparação

```
Não há coleta anterior para comparação
```

**Solução**: Execute a coleta por pelo menos 2 dias consecutivos para gerar comparações

### Módulo não encontrado

```
ModuleNotFoundError: No module named 'pyzabbix'
```

**Solução**: Instale as dependências com `pip install -r requirements.txt`

### Erro ao enviar email

```
SMTPAuthenticationError: Username and Password not accepted
```

**Solução para Office 365**: 
- Verifique se o email e senha estão corretos
- Para contas com autenticação multifator (MFA), crie uma senha de app
- Verifique se a conta tem permissão para SMTP

**Solução para Gmail**:
- Ative "Acesso a apps menos seguros" ou use senha de app
- Crie senha de app em: https://myaccount.google.com/apppasswords

### Email não chega

**Solução**:
1. Verifique a pasta de spam/lixo eletrônico
2. Confirme que `SEND_EMAIL=true` no .env
3. Verifique se `EMAIL_RECIPIENTS` está configurado corretamente
4. Revise os logs em `zabbix_daily_report.log` para detalhes do erro

## 🤝 Contribuindo

Sinta-se à vontade para:

1. Reportar bugs
2. Sugerir melhorias
3. Enviar pull requests

## 📄 Licença

Este projeto é de uso livre para fins educacionais e corporativos.

## 👤 Autor

Desenvolvido para monitoramento automatizado de infraestrutura Zabbix.

## 📞 Suporte

Para dúvidas ou problemas:

1. Verifique os logs em `zabbix_daily_report.log`
2. Consulte a documentação do Zabbix API
3. Revise as configurações no arquivo `.env`

---

**Última atualização**: Outubro de 2025
