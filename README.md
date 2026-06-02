# AuraLab Borborema — MVP (Fase 1)

Sistema de coleta automatica e visualizacao das analises laboratoriais
da planta de lixiviacao da **Aura Minerals — Unidade Borborema**.

## Como usar (3 passos)

### 1. Coletar emails

Com o **Outlook aberto**, rode:

```cmd
coletar_emails.bat --since-days 7
```

Opcoes:
- `--since-days N` — processa os ultimos N dias (default: 1)
- `--since 2026-01-01` — processa desde uma data especifica
- `--backlog` — processa tudo desde 01/01/2026
- `--todos-processos` — processa **todos** os 8 processos (default: so Fase 1)

### 2. Abrir o dashboard

```cmd
iniciar_dashboard.bat
```

Acesse no navegador:
- **Sua maquina:** http://localhost:8501
- **Time interno (mesma rede):** http://192.168.1.50:8501 *(IP pode variar — veja no console quando rodar)*

### 3. Pronto

Use os filtros da sidebar (periodo, data) para navegar. O sistema mostra:
- **Visao Geral:** KPIs e ultimos processamentos
- **Lixiviacao:** Au soluvel ALIM vs REJ por turno
- **Acacia:** Sol. Rica, Over e Rejeito por batelada
- **Eletrolise:** CE0001 e CE0002 (entrada/saida por hora)

## Estrutura do projeto

```
AuraLab_Borborema/
├── app/
│   ├── config.py              ← configuracoes (caminhos, dominios, processos)
│   ├── subject_parser.py      ← interpreta o assunto do email
│   ├── email_reader.py        ← le Outlook via pywin32 (camada isolada)
│   ├── parsers/
│   │   ├── base.py            ← parser generico SGS Geosol
│   │   ├── lixiviacao.py      ← parser de Lixiviacao
│   │   ├── acacia.py          ← parser de Acacia
│   │   └── eletrolise.py      ← parser de Eletrolise
│   ├── database.py            ← SQLite + upsert preliminar -> final
│   ├── collector.py           ← orquestra email -> parser -> banco
│   └── dashboard/
│       ├── streamlit_app.py   ← dashboard web
│       └── theme.py           ← identidade visual Aura
├── anexos/                    ← backup automatico dos XLS e PDF
│   └── <ano>/<mes>/
├── database/
│   └── auralab.db             ← banco SQLite
├── logs/
│   └── coletor_<data>.log     ← logs de cada execucao
├── tests/                     ← scripts de teste e diagnostico
├── coletar_emails.bat         ← atalho para rodar o coletor
├── iniciar_dashboard.bat      ← atalho para abrir o dashboard
├── requirements.txt           ← dependencias Python
├── PRD.md                     ← documento de requisitos
└── PRD.pdf                    ← PRD em PDF para leitura
```

## Fluxo end-to-end

```
┌──────────────────────────┐
│  Outlook M365 desktop    │
│  pasta Resultados_Lab.   │
└──────────┬───────────────┘
           │  pywin32 + COM
           ▼
┌──────────────────────────┐
│  Coletor Python          │
│  - le emails             │
│  - filtra por dominio    │
│  - parser assunto        │
│  - salva anexo XLS       │
│  - parser XLS            │
│  - upsert SQLite         │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐    ┌──────────────────────┐
│  SQLite                  │    │  Backup XLS+PDF      │
│  database/auralab.db     │    │  anexos/<ano>/<mes>/ │
└──────────┬───────────────┘    └──────────────────────┘
           │
           ▼
┌──────────────────────────┐
│  Streamlit dashboard     │
│  http://localhost:8501   │
└──────────────────────────┘
```

## O que esta no MVP (Fase 1)

| Funcionalidade | Status |
|---|---|
| Coleta automatica de emails da pasta `Resultados_Laboratorio` | OK |
| Parser de 8 tipos de processo (assunto) | OK |
| Parsers de XLS para Lixiviacao, Acacia, Eletrolise | OK |
| Banco SQLite com upsert Preliminar -> Final | OK |
| Backup organizado de XLS e PDF originais | OK |
| Dashboard Streamlit com identidade Aura | OK |
| Acesso via rede interna | OK |
| Logs estruturados em `logs/` | OK |

## O que falta para a Fase 2

| Funcionalidade | Quando |
|---|---|
| Parsers especificos de TQs 1045, Eluicao, Detox, Agua, Bullion | Fase 2 |
| Login multi-usuario (streamlit-authenticator) | Fase 2 |
| Alertas (3 niveis) | Fase 2 |
| KPIs gerenciais (Recuperacao CIL, Producao Au, etc.) | Fase 2 |
| Exportacao Excel multi-aba | Fase 2 |
| Reprocessamento do backlog desde 01/01/2026 | Fase 2 |
| Deploy em Streamlit Cloud (acesso pela internet) | Fase 3 |
| Migracao para Microsoft Graph API (sem precisar Outlook aberto) | Fase 3 |

## Operacao do dia a dia

### Rodar o coletor periodicamente

Para que o sistema fique atualizado sem intervencao manual, agende
o `coletar_emails.bat` no **Agendador de Tarefas do Windows**:

1. Abra "Agendador de Tarefas"
2. "Criar Tarefa Basica..."
3. Disparador: "Diariamente, a cada 30 minutos"
4. Acao: executar `coletar_emails.bat`
5. Salvar

### Compartilhar com o time interno

Quando o `iniciar_dashboard.bat` esta rodando, qualquer pessoa
**na mesma rede da Aura** pode acessar pelo IP do seu PC:

`http://<seu-ip>:8501`

Veja seu IP no console do Streamlit (linha "Network URL").

## Troubleshooting

### "Memoria ou recursos do sistema insuficientes"
O Outlook ficou sem RAM iterando a pasta. Solucao: reduzir a janela
(`--since-days 3` por exemplo).

### "Pasta nao encontrada"
Confirme que a pasta no Outlook se chama exatamente
`Resultados_Laboratório` (com acento e underline).

### "Outlook nao responde"
Reinicie o Outlook e rode novamente.

### O dashboard mostra "sem amostras"
Rode o coletor primeiro: `coletar_emails.bat --since-days 7`

### Resetar o banco
Apague `database/auralab.db` e rode o coletor de novo.

## Migracao futura para o Microsoft Graph API

Hoje usamos pywin32 + Outlook desktop, o que exige seu PC ligado
e o Outlook aberto. Para producao 24/7, troque o `OutlookDesktopSource`
em `app/email_reader.py` por uma nova `MicrosoftGraphSource` que use
a API REST do Microsoft Graph. A interface `EmailSource` ja esta
isolada justamente para essa migracao.

---

**Versao:** MVP 0.1 (Fase 1) — 23/05/2026
**Autor:** Caio Leite Brandao Ferreira + Claude (parceiro tecnico AI)
