# Protocolo do ensaio de bancada em malha fechada (gêmeo digital ↔ dispositivo forense)

**Objetivo:** responder ao R2.1 (interação físico ↔ virtual) e trocar hipóteses do modelo de custo da Seção IV-J por valores medidos. O ensaio responde a três perguntas:
1. **Custo real:** quantos bytes o dispositivo gasta por mensagem e por hora em cada cadência, e quanto custa a sinalização quando o intervalo entre envios aumenta?
2. **Laço físico:** quanto tempo passa entre a decisão do gêmeo e a primeira amostra na nova cadência? Com que confiabilidade isso acontece?
3. **Backfill:** quanto custa, em bytes e em tempo, recuperar o histórico da memória de massa quando há um alerta?

O ensaio é uma **demonstração de viabilidade com um dispositivo**. A avaliação estatística continua sendo feita por simulação, agora calibrada com os valores medidos aqui.

**Premissas confirmadas:**
- Os quatro pré-requisitos são viáveis: comando remoto de cadência, contador real de bytes, medidor com memória de massa e derivação segura.
- A cadência configurada é respeitada.
- Uma mudança de cadência em tempo real vale a partir da próxima amostragem, sem reset.

---

## 1. Informações de que preciso antes do ensaio

Com isto preparo o adaptador entre o gêmeo (Python) e o dispositivo, e os scripts de registro.

| # | Informação | Formato ideal |
|---|---|---|
| I1 | Estrutura da mensagem de telemetria periódica: campos enviados, ordem e tamanho | 2 ou 3 mensagens reais em hexadecimal, cada uma acompanhada da versão decodificada |
| I2 | Como o back-office recebe as mensagens: broker, tópicos MQTT, QoS, se há TLS | Texto curto e um exemplo de tópico |
| I3 | Como mudar a cadência: objeto/atributo DLMS (OBIS) do período de captura e do de envio; se há resposta/confirmação e o que ela contém | Um exemplo de requisição e de resposta (hex ou log) |
| I4 | Como ler a memória de massa sob demanda: requisição por intervalo de tempo ou por índice, tamanho de cada registro, quantos registros cabem por mensagem | Um exemplo de requisição e de resposta |
| I5 | Como obter os contadores do modem: bytes TX/RX, RSRP, SINR, nível de cobertura (CE/ECL), potência de transmissão. Precisa ser por comando AT, por log do firmware ou por relatório da operadora (CDR), e em qual granularidade | Comando ou procedimento, mais uma saída de exemplo |
| I6 | Medidor que fará o papel do faturamento: modelo, intervalo mínimo da memória de massa, como exportar | Modelo e um arquivo de exemplo exportado |
| I7 | Versão de firmware, modelo do modem, operadora/APN e se PSM/eDRX estão ligados ou desligados | Texto |
| I8 | Há uma segunda unidade disponível? | Sim/não. Com duas, uma roda a política fixa e a outra a adaptativa, no mesmo ramal e ao mesmo tempo |

---

## 2. Montagem

```
 Fonte/rede ──┬──────────────────────────────► [Medidor "faturamento"] ──► Cargas faturadas (banco programável)
              │      ▲                                    (memória de massa)
              │      │ dispositivo forense medindo o ramal (a montante de tudo)
              │
              └──► [Relé R_furto] ──► Carga desviada (passa pelo forense, NÃO pelo faturamento)

 Dispositivo forense ──NB-IoT──► Broker/back-office ◄──► Gêmeo digital (Python, laptop)
                                                         ├─ lê telemetria + faturamento
                                                         ├─ decide modo (basal/moderate/aggressive)
                                                         └─ envia comando de cadência / pedido de backfill

 Controlador do roteiro (CLP/relé temporizado/script) ──► R_furto e cargas faturadas, com log de cada comutação
 (Opcional) Atenuador de RF / caixa blindada no caminho da antena
 Todos os relógios sincronizados (NTP no laptop e no back-office; RTC do dispositivo acertado no início)
```

**Segurança:** a derivação deve ser montada e operada por pessoal habilitado, com proteção e seccionamento. Não há intervenção em instalação de cliente.

---

## 3. Fases do ensaio

| Fase | O que fazer | Duração / repetições | Mede |
|---|---|---|---|
| **A. Custo por cadência** | Sem furto e sem o gêmeo. Cadência fixa de envio em 5, 10, 15, 20, 30 e 60 min, uma de cada vez | Pelo menos 12 mensagens por cadência (60 min ≈ 12 h; dá para rodar à noite) | Bytes por mensagem e por hora; overhead de sinalização em função do intervalo entre envios. Testa a hipótese "40 B extras quando o intervalo passa de 15 min" |
| **B. Comandos de cadência** | Sem furto. Mudanças de cadência em instantes aleatórios, cobrindo as 6 transições entre basal (60), moderate (15) e aggressive (5) | Pelo menos 30 comandos (5 por transição) | Latência do comando até a confirmação e até a 1ª amostra na nova cadência; taxa de sucesso; bytes de downlink |
| **C. Backfill** | Cadência basal; pedidos de leitura de 1, 6 e 24 h de memória de massa | 3 repetições de cada | Bytes, número de mensagens, tempo total, registros completos/faltantes |
| **D. Malha fechada** | O gêmeo opera ao vivo e comanda o dispositivo. Roteiro de furto pelo relé (abaixo) | 48 a 72 h contínuas | Traço temporal completo; atraso de detecção por episódio; bytes por modo; falsos alarmes |
| **E. Enlace degradado** | Cadência de 15 min com atenuação para atingir CE1 e depois CE2; em seguida, corte total do enlace por 1 a 2 h | 2 h por nível e 1 a 2 corte(s) | Retransmissões, latência, bytes extras; armazenamento e reenvio após o corte |
| **F. Falta de energia** | 3 desligamentos curtos (menos de 1 min) e 1 longo (mais de 5 min) | 4 eventos | Recuperação do laço; alarme de última mensagem (*last gasp*); continuidade do índice sequencial |

**Roteiro de furto da fase D** (valores sugeridos; ajustar à carga disponível):

| Episódio | Quando | Fração desviada | Representa |
|---|---|---|---|
| D1 Persistente | 6 h contínuas no dia 1 | ~30% | Desvio permanente |
| D2 Horário de ponta | 18:00–21:00 nos dias 1 e 2, com o início deslocado de 0 a 40 min por dia | ~40% | Furto agendado |
| D3 Madrugada | 00:30–04:00 | ~50% | Furto noturno |
| D4 Intermitente | Noite do dia 2: ligado por 15 a 90 min e desligado por 10 a 60 min, sorteados | ~40% | *Bypass* liga/desliga |
| D5 Sem furto com perturbação | Pelo menos 6 h com degraus e picos de carga só no lado faturado (partida de motor, carga alta temporária) | 0% | Teste de falso positivo |

Se houver segunda unidade (I8), ela roda em cadência fixa de 15 min durante toda a fase D, como baseline físico.

---

## 4. Dados a coletar (arquivos)

**Regras gerais:**
- CSV em UTF-8 e timestamps em **UTC, ISO 8601, com milissegundos**.
- Um arquivo por fonte.
- Registrar o desvio do relógio do dispositivo em relação ao NTP no início e no fim de cada fase.
- Não filtrar nem corrigir nada: mandar o bruto. O tratamento é feito na análise.

| Arquivo | Quem gera | Colunas mínimas |
|---|---|---|
| `telemetria.csv` | Back-office ou script no broker | `ts_rx` (recebido no back-office), `ts_dev` (RTC do dispositivo), `seq` (índice sequencial), `tipo` (periódica/alarme/heartbeat/backfill), `p_w`, `q_var`, `v_v`, `i_a`, `e_imp_wh` (registrador de energia), `periodo_envio_min` vigente, `bytes_app` (tamanho da mensagem na aplicação) e o payload bruto em hex |
| `faturamento.csv` | Exportação do medidor "faturamento" | `ts_intervalo_fim`, `e_imp_wh` (registrador ou energia do intervalo), `p_w` se houver, `intervalo_min` |
| `referencia.csv` (opcional) | Medidor padrão do laboratório | `ts`, `p_w`, `e_imp_wh` no ramal e, se possível, na derivação |
| `roteiro.csv` (ground truth) | Controlador do relé | `ts`, `rele` (R_furto/carga_x), `estado` (on/off), `p_desviada_w` (nominal ou medida) |
| `comandos.csv` | Gêmeo/adaptador (eu gero) | `cmd_id`, `ts_envio`, `periodo_alvo_min`, `ts_resposta`, `resultado`, `bytes_downlink`, `ts_primeira_amostra_nova` |
| `backfill.csv` | Gêmeo/adaptador (eu gero) | `req_id`, `ts_pedido`, `horas_pedidas`, `n_registros_recebidos`, `n_mensagens`, `bytes_total`, `ts_fim` |
| `modem.csv` | Firmware/AT ou operadora | `ts`, `bytes_tx_acum`, `bytes_rx_acum`, `rsrp_dbm`, `sinr_db`, `ce_level`, `tx_power_dbm`, `n_rrc_conexoes` (se disponível). Se vier da operadora: um registro por sessão, com início, fim e bytes |
| `eventos.csv` | Back-office | `ts`, `evento` (alarme, *last gasp*, queda e retorno de enlace, reinício), `detalhe` |
| `gemeo_log.csv` | Gêmeo (eu gero) | `ts`, `p_regra`, `p_supervisionado`, `p_fundida`, `modo`, `decisao`, `motivo` |
| `metadados.json` | Você | Firmware, modem, operadora/APN, PSM/eDRX, local, nível de sinal médio, desvio de relógio por fase, anotações de anomalias e fotos da montagem |

Os arquivos marcados como "eu gero" saem do código do gêmeo e do adaptador, que preparo a partir das informações da Seção 1.

---

## 5. O que sai do ensaio para o artigo

1. **Tabela de custo medido × modelado:** bytes por mensagem, overhead em função do intervalo, custo por hora em cada modo e custo do backfill. Se houver diferença, o modelo da Seção IV-J é recalibrado e a campanha de simulação roda de novo com os valores medidos.
2. **Distribuição de latências:** do comando de cadência (até a confirmação e até a primeira amostra nova) e da telemetria fim a fim.
3. **Figura de traço temporal real (fase D):** carga e episódios de furto, divergência, risco fundido, modo ativo e bytes acumulados ao longo do ensaio, com uma faixa paralela do baseline fixo se houver segunda unidade.
4. **Tabela por episódio:** atraso de detecção, modo no momento da detecção e bytes gastos; falsos alarmes no período D5.
5. **Comportamento em enlace degradado e em falta de energia:** um parágrafo e números-chave.

Tamanho estimado no artigo: uma subseção ("Bench-scale closed-loop validation") com 1 figura de montagem, 1 figura de traço temporal e 1 ou 2 tabelas.

---

## 6. Cronograma sugerido

| Dia | Atividade |
|---|---|
| 0 | Envio das informações I1 a I8; eu preparo o adaptador e os scripts (2 a 4 dias) |
| 1 | Montagem, sincronização de relógios, teste rápido de ponta a ponta (1 comando, 1 backfill) |
| 1–2 | Fases A e B (dá para rodar a A à noite) |
| 2 | Fases C, E e F |
| 3–5 | Fase D (48 a 72 h contínuas) |
| 6 | Envio dos arquivos; análise e recalibração do modelo |
