# PRD — AuraLab Borborema

**Sistema de Análises Laboratoriais — Planta de Lixiviação**

| | |
|---|---|
| **Documento** | Product Requirements Document (PRD) |
| **Versão** | 1.0 — Rascunho para validação |
| **Data** | 22/05/2026 |
| **Autor (negócio)** | Caio Leite Brandão Ferreira (Eng. de Processos — Aura Borborema) |
| **Parceiro técnico (AI)** | Claude |
| **Empresa** | Aura Minerals — Unidade Borborema |
| **Status** | Aguardando validação do stakeholder |

---

## 1. Resumo Executivo

Hoje os resultados de análises do laboratório (SGS Geosol) chegam por email em alto volume (centenas/dia em picos), exigindo download manual, interpretação dos anexos Excel e digitação numa planilha consolidada. Esse processo é demorado, propenso a erros e impede visualização em tempo real.

O **AuraLab Borborema** automatiza essa cadeia ponta-a-ponta: lê os emails do laboratório, extrai dados dos anexos, consolida num banco estruturado, exibe num dashboard web acessível pelo time (engenharia, coordenação, gerência) e exporta uma planilha consolidada multi-aba sob demanda.

**Métrica de sucesso principal:** reduzir o tempo de coleta/consolidação manual de várias horas/dia para **zero intervenção humana** no caminho feliz, com dados visíveis no dashboard em até **30 minutos após a chegada do email**.

---

## 2. Contexto e Problema

### Cenário atual
- Caio recebe em sua inbox do Outlook (M365) centenas de emails/dia do laboratório SGS Geosol (domínio `@ou.sgsgeosol.com.br` e variante `@sgsgeosol.com.br`).
- Cada email tem dois anexos: um Excel (`.XLS`) e um PDF. Caio usa o Excel.
- Cada Excel segue um layout específico por **tipo de processo** (Lixiviação, Tanques, Acácia, Eluição, Eletrolise, Detox, Água de Processo, Bullion).
- Caio identifica manualmente o tipo de processo pelo **assunto**, baixa o anexo, converte ponto decimal para vírgula (locale BR), e digita numa planilha consolidada por abas.
- Há **dois fluxos** por amostra: `Preliminar` (parcial) e `Analítico` (definitivo) — o Analítico substitui o Preliminar do mesmo identificador.

### Dor
1. **Tempo:** processo manual ocupa boa parte do dia do engenheiro.
2. **Erro humano:** digitação manual pode introduzir erros.
3. **Latência:** dados só ficam visíveis depois que Caio digita.
4. **Não-compartilhamento:** planilha vive no OneDrive pessoal, sem dashboard para o time.
5. **Backlog:** não há histórico estruturado fácil de consultar.

### Stakeholders impactados
| Perfil | Papel | Como o sistema o ajuda |
|---|---|---|
| **Caio (Eng. Processos)** | Owner / Admin | Elimina trabalho manual; ganha tempo para análises de alto valor |
| **Coordenador** | Consumidor diário | Visibilidade do desempenho do beneficiamento em tempo quase real |
| **Gerente** | Tomada de decisão | KPIs gerenciais consolidados, sem depender de planilhas individuais |
| **Time de Engenharia** | Operação técnica | Acesso a dados detalhados por processo, histórico, exportação |
| **Segundo Eng. (futuro)** | Backup do Caio | Manutenção do sistema em ausências (permissão admin) |

---

## 3. Objetivo e Métricas de Sucesso

### Objetivo
Automatizar a coleta, consolidação e visualização das análises laboratoriais da planta de lixiviação, oferecendo dashboards e exportação estruturada ao time.

### Métricas de sucesso

| KPI | Meta v1 |
|---|---|
| Latência email → dashboard | ≤ 30 minutos |
| Taxa de parse bem-sucedido | ≥ 95% dos emails do domínio do lab |
| Tempo manual de coleta diário do Caio | De várias horas → **0 horas** (caminho feliz) |
| Adoção de usuários | ≥ 3 usuários ativos (Caio + coordenador + gerente) no 1º mês |
| Disponibilidade do dashboard | ≥ 95% (excluindo janelas de manutenção) |

---

## 4. Escopo

### ✅ Em escopo — v1

1. **Coleta automática** de emails da pasta `Resultados_Laboratório` no Outlook M365 desktop do Caio.
2. **Filtros**: emails de remetentes dos domínios `*.sgsgeosol.com.br` (com e sem `ou.`).
3. **Parsing automático** dos anexos `.XLS` para 8 processos:
   - Lixiviação (Rej./Alim)
   - TQ's 1045 (7 tanques)
   - Acácia (Sol. Rica e Over)
   - Eluição (Carvão Au/Ca)
   - Eletrolise (CE0001 e CE0002)
   - Água de Processo
   - Detox (CN WAD e Cianeto Livre)
   - Bullion (Au/Ag por barra)
4. **Identificadores aceitos**: `PM<n>`, `EC<n>`, `AB<n>`.
5. **Regra Preliminar → Analítico**: upsert pelo identificador. Analítico sempre substitui Preliminar do mesmo código.
6. **Banco de dados SQLite** local com schema por processo.
7. **Backup dos arquivos originais** (`.XLS` + `.PDF`) em pasta estruturada por ano/mês.
8. **Dashboard web** (Streamlit) seguindo identidade visual Aura Borborema (azul-marinho + coral).
9. **Login multi-usuário** com perfis Admin / Usuário.
10. **Página por processo** com:
    - Filtros (data, batelada/turno conforme o processo, indicador, ocultar vazios)
    - Tabela detalhada
    - Gráfico de série temporal
    - Download da tabela
11. **Exportação Excel multi-aba** (uma aba por processo) sob demanda.
12. **Alertas em 3 níveis** (críticos, atenção, informativo) com badge no dashboard + opção de email.
13. **KPIs gerenciais** (3 indicadores iniciais — ver §13).
14. **Reprocessamento de backlog** desde 01/01/2026 (dependente do cache do Outlook).
15. **Atualização automática** a cada 30 minutos + botão de refresh manual.
16. **Hospedagem na internet** via Streamlit Community Cloud (HTTPS, acesso pelo time).
17. **Tela de gerenciamento de usuários** (admin adiciona/remove/altera permissão).

### ❌ Fora de escopo — v1
- **Geologia** (mencionada como menu no sistema de referência, mas excluída desta versão a pedido do Caio).
- **Parsing do PDF** (sempre usar o Excel; PDF é só backup).
- **Integração com Microsoft Graph API** (planejado para v2, quando TI registrar app no Azure AD).
- **Notificações por WhatsApp/Teams** (planejado para v2).
- **Mobile nativo** (o dashboard web é responsivo, mas sem app dedicado).
- **Migração da planilha histórica atual do Caio** (parte-se do que o Outlook tem em cache).

---

## 5. Origem dos Dados — Emails do Laboratório

### 5.1 Domínios aceitos
- `*@ou.sgsgeosol.com.br` (predominante)
- `*@sgsgeosol.com.br` (sem `ou.` — visto em CC)

### 5.2 Operadores identificados
| Operador | Email | Processos típicos |
|---|---|---|
| Deyvid Lima | deyvid.lima@ou.sgsgeosol.com.br | Acácia, Lixiviação, Água de Processo |
| Anthony Silva | anthony.silva@ou.sgsgeosol.com.br | Eletrolise, Tanques, Eluição |
| Joicy Santos | joicy.santos@ou.sgsgeosol.com.br | Eletrolise |
| Maik Rocha | maik.rocha@ou.sgsgeosol.com.br | Bullion (exclusivo) |
| Augustto Resende | augusto.resende@ou.sgsgeosol.com.br | Detox |

> O sistema não trava em nomes específicos: aceita qualquer remetente dos domínios autorizados.

### 5.3 Pasta de coleta
- **Pasta:** `Resultados_Laboratório` (inbox pessoal do Caio + regra do Outlook).
- Bullion chega na inbox principal (lista direta de destinatários, não vai pra essa pasta) — sistema lê **ambas as pastas** para não perder Bullion.

### 5.4 Padrão geral do assunto

```
[External]Envio de Resultado <TIPO> <sep> <IDENTIFICADOR> <sep> <PROCESSO> <SUFIXO_OPCIONAL>
```

- `<TIPO>` ∈ {`Analítico`, `Preliminar`}
- `<IDENTIFICADOR>` ∈ {`PM<n>`, `EC<n>`, `AB<n>`}
- `<sep>` varia por operador: ` - `, ` `, `- `, ` -`, etc.
- `<SUFIXO_OPCIONAL>` varia por processo (ver tabela 5.6).

### 5.5 Variações por operador (parser deve ser tolerante)

| Operador | Estilo de separador | Exemplo |
|---|---|---|
| Deyvid | `Analítico - PM<n> - Processo - BAT-XXX` | `Analítico - PM2602455 - Over Acácia - BAT-386` |
| Anthony | `Analítico PM<n> Processo BAT-XXX` (sem hífens) | `Analítico PM2602438 LICOR-CE001 BAT-384` |
| Joicy | `Analítico- PM<n>- Processo BAT XXX` (hífen colado, espaço no BAT) | `Analítico- PM2602453- Licor CE002 BAT 472` |
| Maik (Bullion) | `Analítico - EC<n> - BULLION DD/MM/YYYY` | `Analítico - EC2600031 - BULLION 15/05/2026` |
| Augustto (Detox) | `Analítico - AB<n> - DETOX - Subtipo` (varia) | `Analítico - AB2600019 - DETOX - Cianeto WAD` |

**Estratégia técnica:** regex tolerante a separadores + matching por **palavras-chave do processo** após normalização (`upper()` + remoção de pontuação).

### 5.6 Mapeamento Processo (rótulo no assunto → tela do sistema)

| Variações no assunto | Tela / Processo | Subcategoria |
|---|---|---|
| `Sol. Rica Acácia`, `Rica Acácia` | **Acácia** | Solução Rica |
| `Over Acácia`, `Over do Acácia` | **Acácia** | Over |
| `LICOR-CE001`, `Licor CE001`, `Licor CE0001` | **Eletrolise** | CE0001 |
| `LICOR-CE002`, `Licor CE002`, `Licor CE0002` | **Eletrolise** | CE0002 |
| `Rej./Alim DD/MM TURNO: TX` | **Lixiviação** | — |
| `TQS.DIÁRIO HH:MM`, `TANQUE.DIÁRIO HH:MM` | **TQ's 1045** | — |
| `Água de Processo DD/MM` | **Água de Processo** | — |
| `CARVÃO ELUIÇÃO`, `Carvão Eluição` | **Eluição** | — |
| `BULLION DD/MM/YYYY` (com EC) | **Bullion** | Gravimetria (`GBBR-xx`) ou Hidrometalurgia (`HBBR-xx`) |
| `DETOX - Cianeto WAD`, `Cianeto Wad` (com AB) | **Detox** | CN WAD |
| `DETOX - Cianeto Livre` (com AB) | **Detox** | CN Livre |

### 5.7 Regra `Preliminar` vs `Analítico`

- Mesmo identificador (PM/EC/AB) pode chegar duas vezes: primeiro Preliminar, depois Analítico.
- **Layout do Excel é idêntico** nos dois; muda apenas a completude (Preliminar tem células vazias; Analítico está completo).
- Sistema faz **upsert**: insere/atualiza por código, e marca `status` como `preliminar` ou `final`.
- Quando o Analítico chega, status vira `final` e a linha é completada.
- Emails com prefixo `Re:` no assunto são tratados como duplicatas se o código já foi processado.

### 5.8 Tratamento de locale
- Lab envia números em padrão americano (ponto decimal).
- Parser converte tudo para `float` e armazena como número no banco.
- Conversão para vírgula só acontece na **exibição** (locale `pt-BR`).

### 5.9 Tratamento de limite de detecção (LD)
- Valores como `<0,010` ou `>50` aparecem em análises de baixa concentração (ex.: Água de Processo).
- Banco guarda em **duas colunas**:
  - `valor` (float — o número limite)
  - `flag_ld` ∈ {`igual`, `menor_que`, `maior_que`}
- Dashboard exibe com legenda explícita (bolinha cheia × bolinha vazada) — padrão visto na unidade de referência.

---

## 6. Processos Cobertos — Quadro Resumo

| # | Processo | Tipo | Identificador no assunto | Frequência | Métricas principais |
|---|---|---|---|---|---|
| 1 | **Lixiviação** | Por turno | `Rej./Alim DD/MM TURNO: TX` | 3 turnos/dia (08/16/23) | ALIM/RJT × SOLIDO/SOLUVEL + Recuperação CIL |
| 2 | **TQ's 1045** | Por turno | `TQS.DIÁRIO HH:MM` | 2x/dia (≈09 e 17) | ENTRADA + SAIDA por tanque (1 a 7, alguns podem ficar vazios) |
| 3 | **Acácia** | Por batelada | `Sol. Rica Acácia BAT-XXX` ou `Over Acácia BAT-XXX` | Por evento | RICA, REJEITO, EFICIÊNCIA, OVER hora-a-hora (00h–12h+) |
| 4 | **Eluição** | Por batelada | `CARVÃO ELUIÇÃO` (BAT no anexo) | Por evento | CARVAO_CARREGADO_AU/CA, CARVAO_ELUIDO_AU/CA, EFICIÊNCIA_AU/CA |
| 5 | **Eletrolise** | Por batelada × 2 células | `LICOR-CE001` / `LICOR-CE002 BAT-XXX` | Por evento | ENTRADA, SAIDA, EFICIÊNCIA por célula (CE0001 e CE0002) |
| 6 | **Água de Processo** | Amostragem livre | `Água de Processo DD/MM` | Irregular (horários quebrados) | Teor por hora — matriz dia × hora |
| 7 | **Detox** | Por evento (baixa frequência) | `DETOX - Cianeto WAD/Livre` (com AB) | ~2x/mês | ALIM/SAIDA × CN_WAD/NACN_WAD + Abatimento |
| 8 | **Bullion** | Por barra | `BULLION DD/MM/YYYY` (com EC) | Por fundição (várias barras/dia) | % Au, % Ag, origem (G/H) |

---

## 7. Arquitetura Técnica

### 7.1 Visão geral

```
┌──────────────────────────┐
│  Outlook M365 desktop    │  (PC do Caio)
│  pasta Resultados_Lab.   │
└──────────┬───────────────┘
           │ pywin32 (COM)
           ▼
┌──────────────────────────┐
│  Coletor Python (local)  │  ← roda a cada 30 min via scheduler
│  - lê emails             │
│  - extrai anexos         │
│  - faz parsing           │
│  - faz upsert no banco   │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐    ┌──────────────────────┐
│  Banco SQLite (local)    │    │  Backup XLS/PDF      │
│  - tabela por processo   │    │  OneDrive/lab/anexos │
│  - upsert por código     │    │  /<ano>/<mês>/       │
└──────────┬───────────────┘    └──────────────────────┘
           │ sync (rclone ou script) → cloud
           ▼
┌──────────────────────────────────────────────────────┐
│  Streamlit Community Cloud (internet, HTTPS)         │
│  - Login multi-usuário                               │
│  - Dashboard por processo                            │
│  - Alertas                                           │
│  - Exportação Excel multi-aba                        │
└──────────────────────────────────────────────────────┘
            ▲
            │ acessam via navegador
   ┌────────┴────────┬─────────┬──────────┐
 Caio          Coordenador  Gerente   Eng. Time
```

### 7.2 Componentes

| Componente | Tecnologia | Localização |
|---|---|---|
| **Coletor de emails** | Python + `pywin32` (COM com Outlook) | PC do Caio (local) |
| **Parser de Excel** | Python + `pandas` + `xlrd` (XLS antigo) | PC do Caio (local) |
| **Banco de dados** | SQLite | Arquivo único, sincronizado com cloud |
| **Backup arquivos** | OneDrive (estrutura ano/mês) | OneDrive — Aura Minerals |
| **Frontend** | Streamlit + `streamlit-authenticator` | Streamlit Community Cloud |
| **Sincronização banco → cloud** | Script Python via API do Streamlit ou Git push automático | PC do Caio (local) |
| **Scheduler local** | Windows Task Scheduler | PC do Caio |

### 7.3 Camada de leitura de email — isolada

A leitura de email fica num módulo separado (`email_reader.py`) com interface abstrata. Isso permite, na v2, **trocar pywin32 → Microsoft Graph API** sem mudar nenhum outro código.

```python
class EmailSource(ABC):
    def fetch_new(self, since: datetime) -> list[Email]: ...

class OutlookDesktopSource(EmailSource): ...  # v1
class MicrosoftGraphSource(EmailSource): ...  # v2 (futuro)
```

### 7.4 Por que essas escolhas

- **pywin32 + Outlook desktop:** evita chamado TI (registro de app no Azure AD).
- **SQLite:** banco de arquivo único, sem servidor, fácil de fazer backup, suficiente para o volume previsto.
- **Streamlit Community Cloud:** grátis, HTTPS automático, deploy via Git, login built-in. Maior conveniência possível sem TI.
- **`xlrd`:** anexos vêm em `.XLS` legado (não `.XLSX`); `xlrd ≤ 1.2.0` lê esse formato (versões mais novas só leem `.XLSX`, daí o pin).
- **Backup em OneDrive:** zero custo extra, já sincronizado com a conta do Caio.

---

## 8. Decisão de Hospedagem (Caio delegou)

### Decisão: **Streamlit Community Cloud** (com plano de migração)

**Por quê:**
1. ✅ **Zero TI**: deploy em minutos, sem chamado.
2. ✅ **HTTPS automático** com domínio `<app>.streamlit.app`.
3. ✅ **Login multi-usuário** via `streamlit-authenticator` (senhas hashed em arquivo YAML).
4. ✅ **Grátis** para projetos com repos privados no GitHub.
5. ✅ **Acesso por qualquer navegador** (computador, celular).

**Mitigações de risco:**
- **Confidencialidade dos dados:** repositório GitHub **privado** (apenas Caio + admin têm acesso). Banco SQLite vai no repo, sincronizado pelo PC do Caio via push automático.
- **Sensibilidade dos dados de produção da Aura:** se em algum momento o TI/jurídico considerar inadequado, **plano B documentado**: migração para Render (também grátis, mais privado) ou servidor interno Aura.
- **Limite de recursos** (1 GB RAM, hibernação após inatividade): dimensionado o suficiente para v1. Se virar problema, migrar para Streamlit for Teams (pago) ou self-hosted.

### Plano de migração (v2)
Quando a Aura validar uso de servidor interno (igual à outra unidade), migra-se o app para `http://10.137.x.x:5200` na rede da empresa. Streamlit é portátil — código não muda, só o deploy.

---

## 9. Banco de Dados — Modelo

### 9.1 Tabelas principais

```sql
-- Amostras (registro mestre)
CREATE TABLE amostras (
    codigo_amostra TEXT PRIMARY KEY,     -- "PM2602458", "EC2600031", "AB2600019"
    tipo_codigo TEXT NOT NULL,           -- "PM" | "EC" | "AB"
    processo TEXT NOT NULL,              -- "Lixiviacao" | "Tanques" | "Acacia" | ...
    subcategoria TEXT,                   -- "Sol. Rica" | "Over" | "CE0001" | "Cianeto WAD" | ...
    status TEXT NOT NULL,                -- "preliminar" | "final"
    batelada TEXT,                       -- "BAT-386" (se aplicável)
    turno TEXT,                          -- "T1" | "T2" | "T3" (se aplicável)
    data_amostra DATE NOT NULL,
    hora_amostra TIME,
    data_recebimento TIMESTAMP NOT NULL, -- quando o sistema processou
    remetente_email TEXT,
    arquivo_xls_path TEXT,               -- caminho do backup
    arquivo_pdf_path TEXT,
    versao INTEGER DEFAULT 1             -- incrementa quando Analítico atualiza Preliminar
);

-- Resultados (uma linha por métrica)
CREATE TABLE resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_amostra TEXT NOT NULL REFERENCES amostras(codigo_amostra),
    metrica TEXT NOT NULL,               -- "ALIM_CIL_SOLIDO", "RECUPERACAO_CIL", etc.
    valor REAL,
    flag_ld TEXT DEFAULT 'igual',        -- "igual" | "menor_que" | "maior_que"
    unidade TEXT,                        -- "%" | "g/t" | "mg/L"
    UNIQUE(codigo_amostra, metrica)
);

-- Usuários
CREATE TABLE usuarios (
    username TEXT PRIMARY KEY,
    nome_completo TEXT NOT NULL,
    email TEXT,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL,                -- "admin" | "user"
    ativo BOOLEAN DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log de processamento (auditoria + debugging)
CREATE TABLE processamento_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_subject TEXT,
    email_received_at TIMESTAMP,
    status TEXT,                         -- "ok" | "erro" | "ignorado_duplicata"
    erro_detalhe TEXT,
    codigo_amostra TEXT
);

-- Alertas ativos
CREATE TABLE alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nivel TEXT,                          -- "critico" | "atencao" | "info"
    processo TEXT,
    mensagem TEXT,
    codigo_amostra TEXT,
    resolvido BOOLEAN DEFAULT 0,
    resolvido_em TIMESTAMP
);
```

### 9.2 Por que esse modelo

- **Tabela única `amostras` + `resultados`** (formato longo) facilita adição de novos processos sem alterar schema.
- **Upsert por `codigo_amostra`**: chega Preliminar → insere; chega Analítico → atualiza colunas vazias + muda `status` para `final`.
- **Histórico preservado** em `processamento_log` para auditoria.

---

## 10. Dashboard / UX

### 10.1 Layout geral (inspirado na unidade de referência, adaptado)

- **Sidebar esquerda** com menu:
  - 📊 **LABORATÓRIO**: Lixiviação, TQ's 1045, Acácia, Eluição, Eletrolise, Água de Processo, Detox, Bullion
  - ⚙️ **ADMINISTRAÇÃO**: Usuários, Sessões Ativas, Logs, Configurações
- **Header**: logo Aura Borborema + título da página + perfil do usuário logado + botão de refresh
- **Tema claro/escuro** disponível
- **Filtros padrão** no topo da página de cada processo:
  - Data Início / Data Fim
  - Período Rápido (Hoje, Ontem, Últimos 7 dias, Mês atual, Mês anterior)
  - Indicador (multi-select)
  - Batelada / Turno (quando aplicável)
  - Ocultar vazios

### 10.2 Identidade visual

- **Cores principais** (Aura Borborema):
  - Azul-marinho (`aura`) — primária — extraído do PPTX após análise
  - Coral/laranja — secundária/destaque
  - Cinza neutro — backgrounds
- **Fontes**: sans-serif limpa (Inter ou similar)
- **Logo no header**: variação azul-coral + texto `aura BORBOREMA`
- Banner discreto no rodapé: "Sistema Aura Borborema — Laboratório"

### 10.3 Componentes por tela

| Tela | Componentes principais |
|---|---|
| **Lixiviação** | Tabela `Amostras de Turno` (ALIM/RJT × SOLIDO/SOLUVEL + Recuperação) + Gráfico série temporal |
| **TQ's 1045** | Tabela com 1 coluna ENTRADA + 7 colunas SAIDA (TQ-001 a TQ-007, todas sempre presentes) |
| **Acácia** | Tabela por batelada com RICA/REJEITO/EFICIÊNCIA + colunas OVER hora-a-hora + gráfico 3 séries |
| **Eluição** | Tabela com Análise Au + Análise Ca por batelada + 2 gráficos lado a lado |
| **Eletrolise** | 2 tabelas empilhadas (CE0001 + CE0002) cada uma com gráfico próprio |
| **Água de Processo** | Tabela pivotada `dia × hora` + gráfico com legenda LD (cheia × vazada) |
| **Detox** | Tabela ALIM/SAIDA × CN_WAD/NACN_WAD + Abatimento + série temporal |
| **Bullion** | Tabela `Identidade` + `ID Externo` + Au% + Ag% + filtro por origem (G/H) |

### 10.4 Exportação Excel multi-aba

- Botão único no header: **"📥 Exportar consolidado (Excel)"**
- Gera 1 arquivo `.xlsx` com **uma aba por processo**, respeitando o período filtrado.
- Estrutura de cada aba mantém colunas equivalentes às tabelas do dashboard.

---

## 11. Login e Permissões

### 11.1 Perfis

| Perfil | Acessos |
|---|---|
| **Admin** | Tudo. Pode criar/editar/desativar usuários, alterar permissões, ver logs do sistema. |
| **User** | Acessa todos os dashboards de leitura. **Não pode** editar usuários ou ver logs do sistema. |

> v1 começa com perfis **uniformes para usuários** (todos veem o mesmo). Em v2, podemos introduzir perfis mais granulares se houver demanda (ex.: gerência vê só KPIs).

### 11.2 Implementação

- `streamlit-authenticator` com arquivo `credentials.yaml` (senhas hashed via `bcrypt`).
- Caio começa como único admin. Adiciona o 2º engenheiro como admin quando quiser.
- Recuperação de senha: admin reseta manualmente (v1 não tem fluxo automático por email).

---

## 12. Alertas — 3 Níveis

### 12.1 🔴 Críticos (anomalia operacional / compliance)
- Eficiência de Eletrolise fora da faixa esperada (a calibrar com Caio — ex.: < 0% ou < 30%)
- Recuperação CIL abaixo de meta (ex.: < 80%)
- Cianeto WAD na saída do Detox acima de limite ambiental (definir limite com Caio)
- Tanque (TQ-001..007) sem nenhuma amostra há mais de 24h

### 12.2 🟡 Atenção (qualidade do dado)
- PM em status `preliminar` há mais de 12h sem Analítico chegar
- Email do domínio do laboratório que **não conseguiu ser parseado** (precisa intervenção manual)
- Valor fora de outlier estatístico (> 3σ da média móvel de 7 dias)

### 12.3 🔵 Informativo (rotina)
- Resumo diário às 07:00 (envio por email): X emails processados, Y pendentes, Z em preliminar
- Bullion fundido no dia anterior: total g Au, total g Ag

### 12.4 Onde notificar
- ✅ **Badge no dashboard** (sempre, em todos os níveis)
- ✅ **Email diário** (resumo informativo + atenções)
- ✅ **Email imediato** apenas para 🔴 críticos
- ⏳ WhatsApp/Teams — v2

---

## 13. KPIs Gerenciais (v1 — 3 indicadores)

| KPI | Fórmula | Onde aparece |
|---|---|---|
| **Recuperação Metalúrgica CIL (%)** | `(ALIM_CIL_SOLUVEL − RJT_CIL_SOLUVEL) / ALIM_CIL_SOLUVEL × 100` | Tela Lixiviação + Home (média 7d / 30d) |
| **Produção de Ouro acumulada (g)** | Soma de `(% Au × peso_barra)` no Bullion (do período) | Tela Bullion + Home |
| **Eficiência de Eluição (%)** | `(CARVAO_CARREGADO_AU − CARVAO_ELUIDO_AU) / CARVAO_CARREGADO_AU × 100` | Tela Eluição + Home |

> ⚠️ A **fórmula de Produção de Ouro** depende do **peso da barra** — esse dado vem no Excel do Bullion (a confirmar quando inspecionarmos o anexo). Se não vier, ficamos só com o **teor (%)** sem produção absoluta.

> Comparativo vs **meta** fica para v2 (após Caio cadastrar metas mensais).

---

## 14. Backup e Auditoria

### 14.1 Estrutura de pastas do OneDrive

```
OneDrive - Aura Minerals/
└── Documentos/
    └── AuraLab_Borborema/
        ├── PRD.md                      ← este documento
        ├── anexos/
        │   └── <ano>/<mês>/
        │       ├── PM2602458.XLS
        │       ├── PM2602458.PDF
        │       ├── EC2600031.XLS
        │       ├── EC2600031.PDF
        │       └── ...
        ├── database/
        │   └── auralab.db              ← banco SQLite
        └── logs/
            └── coletor_<ano-mês-dia>.log
```

### 14.2 Política de retenção
- **Anexos**: indefinida (compactar pastas > 1 ano se necessário)
- **Logs**: rotação mensal, retenção de 12 meses
- **Banco**: backup diário antes do processamento (snapshot em `database/backups/`)

---

## 15. Roadmap por Fases

| Fase | Entregáveis | Estimativa | Critério de aceite |
|---|---|---|---|
| **🟢 Fase 1 — MVP local** | Coletor + parsers de 3 processos prioritários (Lixiviação, Acácia, Eletrolise) + banco SQLite + dashboard Streamlit local + backup de arquivos + senha única | **2–3 dias úteis** | Dashboard rodando no PC do Caio mostrando dados reais dos 3 processos; backup funcionando |
| **🟡 Fase 2 — Sistema completo** | Parsers dos demais processos (TQ's, Eluição, Detox, Água, Bullion) + login multi-usuário + 3 KPIs + alertas + exportação Excel multi-aba + reprocessamento backlog | **+5–7 dias úteis** | Todos os 8 processos visíveis; ≥ 3 usuários cadastrados; export funcional; backlog desde 01/01/2026 processado |
| **🔵 Fase 3 — Deploy internet** | Configuração no Streamlit Cloud + sincronização banco PC ↔ cloud + HTTPS + documentação operacional | **+2–3 dias úteis** | Time acessando via `https://auralab-borborema.streamlit.app` autenticado |

> **Cronograma total: ~2 semanas úteis** para a solução completa, com valor demonstrável já no fim da Fase 1.

---

## 16. Premissas e Riscos

| # | Premissa / Risco | Mitigação |
|---|---|---|
| P1 | PC do Caio fica ligado durante o horário comercial com Outlook aberto | Aceitar como limitação v1; migrar para Microsoft Graph API em v2 |
| P2 | Cache do Outlook M365 guarda emails do período de backlog (≥ desde 01/01/2026) | Caso falte algum mês, ajustar configuração do Outlook ou processar em lotes |
| R1 | Lab altera template do Excel de um processo | Alertas 🟡 sinalizam parse failure; parser modular permite ajuste rápido |
| R2 | Streamlit Cloud fora do ar | Dashboard local no PC do Caio continua funcionando (resiliência) |
| R3 | Confidencialidade dos dados em cloud externa | Repo GitHub privado; plano B pra Render ou servidor interno se TI questionar |
| R4 | Volume de backlog (milhares de emails) saturar memória | Processamento em lotes (100 emails por vez) com checkpoint |
| R5 | Eficiências negativas reais vs erro de leitura (visto em Eletrolise BAT_354 = -4,91%) | Alerta de atenção; não bloqueia gravação, mas sinaliza no dashboard para revisão humana |
| R6 | Tanques eventualmente fora de operação (quebra de eixo) | Colunas dos 7 tanques sempre presentes; vazios são legítimos (`NULL`) |

---

## 17. Critérios de Aceite Globais

Para considerar a v1 entregue:

- [ ] Coletor lê automaticamente da pasta `Resultados_Laboratório` a cada 30 min
- [ ] Pelo menos **95% dos emails do domínio do lab são parseados sem erro**
- [ ] Os 8 processos têm sua tela funcional com tabela + gráfico
- [ ] Login funcional com pelo menos 3 usuários cadastrados
- [ ] Botão de exportação gera Excel multi-aba corretamente
- [ ] Identidade visual Aura Borborema aplicada
- [ ] Dashboard acessível pela internet via Streamlit Cloud
- [ ] Backup de XLS/PDF organizado no OneDrive
- [ ] Pelo menos 3 alertas configurados e funcionando
- [ ] Os 3 KPIs aparecem no dashboard
- [ ] Caio consegue adicionar/remover usuários sem suporte técnico
- [ ] Documentação operacional escrita (como rodar, como troubleshoot)

---

## 18. Próximos Passos

1. **Caio revisa este PRD** e devolve correções/aprovação.
2. Após aprovação:
   - Início da **Fase 1** (2-3 dias úteis)
   - Setup de ambiente Python + instalação de dependências
   - Implementação do coletor + parsers prioritários
   - Demo intermediária pra Caio validar antes da Fase 2
3. **Reuniões de checkpoint**: a cada entrega de fase, alinhar próximos passos.

---

## Anexo A — Glossário

| Termo | Significado |
|---|---|
| ALIM | Alimentação |
| RJT | Rejeito |
| CIL | Carbon-In-Leach (processo de lixiviação com carvão ativado) |
| OVER | Overflow / Solução transbordada (saída do reator) |
| CE0001 / CE0002 | Células de eletrólise 1 e 2 |
| CN | Cianeto |
| NaCN | Cianeto de sódio |
| WAD | Weak Acid Dissociable (cianeto fracamente dissociável — métrica ambiental) |
| BAT | Batelada (lote de processamento) |
| TQ | Tanque |
| LD | Limite de detecção do equipamento analítico |
| g/t | Gramas por tonelada (teor de ouro em sólidos) |
| mg/L | Miligramas por litro (concentração em soluções) |
| Bullion | Barra de ouro/prata fundida (produto final metalúrgico) |
| GBBR | Barra de Bullion via Gravimetria |
| HBBR | Barra de Bullion via Hidrometalurgia |
| PM/EC/AB | Prefixos dos identificadores únicos de amostras enviados pelo laboratório SGS Geosol |

---

**Fim do PRD v1.0 — aguardando validação do Caio.**
