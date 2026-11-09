# Plano de Atuação — Reconstrução Científica para IEEE Access (v2)

> Esta versão substitui a v1 (mais superficial). Inclui engenharia reversa real do código-fonte (`src/fraud_dt/`), não apenas do texto do artigo. **Nenhuma linha do novo artigo foi escrita ainda.** Este documento é só diagnóstico + plano.

---

## 0. Inventário de materiais analisados

| Diretório | Conteúdo | Status |
|---|---|---|
| `artigo2026/rejected/.../bare_jrnl_new_sample4.tex` (801 linhas) | Manuscrito completo submetido ao **IEEE JSAC** (ver `\markboth`), rejeitado | Lido integralmente |
| `artigo2026/rejected/.../fig/*.png`, `fig1.png` | 6 figuras (topologia, arquitetura, metodologia experimental, diagrama de sequência) | Inventariado; qualidade avaliada na Seção 7 |
| `artigo2026/recomendações/recomendações.txt` | Pareceres de 3 revisores (2 Reject, 1 Major Revision) | Lido integralmente |
| `artigo2026/exemplo/.../access.tex`, `ieeeaccess.cls` | Template oficial IEEE Access | Lido integralmente |
| `src/fraud_dt/*.py` (todos os módulos: `synthetic`, `features`, `risk`, `pipeline`, `policy`, `comparison`, `config`, `reporting`, `twin/`, `decision/`, `control/`, `devices/`, `actions/`, `runtime/`) | Implementação real do sistema (~1.643 linhas) | **Lido integralmente e comparado com o texto do artigo** |
| `outputs/`, `outputs/campaign/` | Resultados numéricos já gerados pelo pipeline atual | Consultado (`run_summary.md`, `campaign_summary.md`) |
| `docs/*.md` | Documentação de arquitetura, alinhamento com o artigo, mapeamento de resultados | Consultado em sessão anterior |

Não há firmware real, dataset de campo, nem material suplementar além do listado acima. Isso restringe o que pode ser corrigido nesta rodada (ver Seção 9).

---

## 1. Diagnóstico do artigo rejeitado (Subagente 1)

- **Problema de pesquisa:** telemetria de fraude em medição inteligente é tipicamente de cadência fixa; o artigo propõe tratar a densidade de observação como recurso controlável por um twin digital.
- **Hipótese central:** um twin orientado à aplicação pode usar risco de fraude estimado contextualmente para adaptar a janela de observação de telemetria forense NB-IoT, preservando desempenho de detecção e reduzindo custo de comunicação.
- **Contribuições declaradas (4):** (i) formular monitoramento como problema de controle de observação em loop fechado; (ii) twin digital orientado à aplicação com fusão de dados de faturamento/inspeção; (iii) política adaptativa de janela de observação; (iv) campanha experimental multi-cenário reprodutível.
- **Metodologia:** pipeline Python local, SQLite, 6 cenários sintéticos determinísticos de 7 dias/15 min, dois motores de risco (regras + regressão logística), 3 estratégias de fusão, orquestrador de política com histerese, transporte simulado NB-IoT/BLE.
- **Resultado central anunciado:** política adaptativa preserva >97% do F1 da monitoração densa com >50% de redução de comunicação.
- **Pontos fortes reais (confirmados por leitura do código, não só do texto):**
  - A arquitetura de loop fechado (twin → decisão → orquestrador → comando → transporte → atualização do dispositivo) **realmente existe em código** e é exercida no `SimulationRunner` (`src/fraud_dt/runtime/simulator.py`), não é só narrativa.
  - Rastreabilidade genuína: `twin_state_history.csv`, `command_plan.csv`, `transport_delivery.csv`, manifestos de execução — tudo de fato gerado pelo pipeline.
  - Geração sintética com coerência metrológica real (V, I, P, Q, S, FP e energias acumuladas coerentes entre si) — confirmado em `synthetic.py::_build_meter_state`.
- **Pontos fracos já visíveis na própria seção de limitações do artigo** (o próprio manuscrito já admite, mas não corrige): validação 100% sintética, separabilidade estatística alta demais, métrica `critical_slot_hit` rígida, `context_aware` sem vantagem consistente sobre `weighted`.

## 2. Diagnóstico dos pareceres (Subagente 2)

### Classificação de todas as críticas

| Origem | Crítica (resumo) | Categoria |
|---|---|---|
| R1-1 | Terminologia "digital twin" questionável, "parece só uma plataforma de simulação" | Enquadramento/terminologia |
| R1-2 | Sem experimento real; regressão logística pode estar sobreajustada ao próprio conjunto sintético | Validade externa / overfitting |
| R1-3 | Falta análise de importância de features; sugerido testar modelo maior (2-3 camadas FC) | Profundidade experimental |
| R1-4 | Precision/recall/F1 "não são bons o suficiente" para binário; pedem ROC/AUROC | Apresentação/rigor estatístico |
| R2 (pontos fortes) | Inovação conceitual, coerência metrológica, rastreabilidade | — (preservar) |
| R2-major-1 | Cenários sintéticos "idealizados"; pedem dado real OU ruído realista (perda de pacote, drift, latência, cargas legítimas erráticas) | Validade externa |
| R2-major-2 | `critical_slot_hit` binário penaliza demais pequenos deslocamentos temporais | Metodologia de avaliação/métrica |
| R2-major-3 | `context_aware` não supera `weighted`; falta discussão/ablation | Profundidade experimental |
| R2-minor-1 | $D$ e $C$ descritos textualmente, não formalizados como função de $(s_t,a_t)$ | Rigor matemático |
| R2-minor-2 | Qualidade/resolução das figuras | Apresentação |
| R3-1 | Modo `aggressive` (5 min) não é testável porque a resolução nativa é 15 min | **Falha metodológica de fundo** |
| R3-2 | Divergência forense-faturamento é ao mesmo tempo mecanismo gerador do furto e feature de detecção → problema artificialmente fácil | **Falha metodológica de fundo** |
| R3-3 | "NB-IoT" é citado mas custo é só bytes; faltam latência, retransmissão, condição de rádio, overhead de sinalização, energia | Realismo do modelo de sistema |
| R3-4 | Utilidade formulada ($U=\lambda_1 D-\lambda_2 C$) mas nunca resolvida; pesos não determinados; sem análise de otimalidade/convergência | **Falha metodológica de fundo** |
| R3-5 | Sem análise de complexidade computacional/escalabilidade com número de medidores | Lacuna experimental |
| R3-6 | Novidade não suficientemente distinguida da literatura | Posicionamento científico |
| R3-7 | Comparação de baseline não controlada (adaptativo usa `decision_probability`, fixos usam `supervised_probability`) | **Falha de desenho experimental** |
| R3-8 | Apresentação matemática/experimental fraca; tabelas repetem o texto | Apresentação |

### Quais críticas provavelmente causaram a rejeição (não apenas "sugestões de melhoria")

As críticas **R3-1, R3-2, R3-4 e R3-7** são as mais graves porque atacam a validade interna do experimento (não apenas a redação). Um editor técnico dificilmente aceitaria o artigo sem essas quatro corrigidas, **independentemente do periódico**. R1-2/R1-4 (overfitting, métricas "boas demais") são sintoma do mesmo problema de fundo que R3-2 (circularidade de features), então corrigir R3-2 provavelmente resolve R1-2/R1-4 automaticamente.

## 3. Engenharia reversa (Subagente 3) — o que o código realmente faz vs. o que o artigo afirma

Esta seção é o resultado mais importante desta auditoria: **duas das críticas mais duras dos revisores foram confirmadas como procedentes por leitura direta do código**, com evidência de linha específica. Isso muda o tratamento delas de "questão de redação" para "correção de engenharia obrigatória".

### 3.1 Achado crítico #1 — R3-1 é procedente e mais grave do que o texto do artigo deixa transparecer

- `synthetic.py:73`: `pd.date_range("2026-01-01", periods=periods, freq="15min")` — toda a série sintética nasce em grade fixa de 15 minutos.
- `config.py:17-19`: `basal_minutes=60`, `moderate_minutes=15`, `aggressive_minutes=5`.
- `devices/mock_forensic_device.py::should_emit`: `return timestamp >= self.next_emit_time`, onde `next_emit_time = last_emit_time + capture_period_minutes`.
- **Consequência real**: como as únicas marcas de tempo que existem estão espaçadas em 15 minutos, um `capture_period_minutes = 5` (modo `aggressive`) e um `capture_period_minutes = 15` (modo `moderate`) produzem **exatamente o mesmo comportamento de emissão** — o dispositivo emite em todo tick nativo em ambos os casos, porque `15 min ≥ 5 min` e `15 min ≥ 15 min` são sempre verdadeiros. Os dois modos só se distinguem do modo `basal` (60 min, que de fato salta ticks).
- **Isso significa que, no runtime fechado (`SimulationRunner`), "aggressive" e "moderate" são operacionalmente idênticos.** O artigo relata 56 amostras em `aggressive` e 28 em `moderate` (`run_summary.md`) como se fossem regimes de observação distintos, quando na prática ambos correspondem à mesma densidade real de amostragem — a distinção é só um rótulo interno do orquestrador, sem efeito observável no dado emitido.
- **Veredito:** R3-1 não é uma crítica de estilo; é uma falha de validade experimental real, documentada em código. Precisa de correção de simulação, não de resposta textual.

### 3.2 Achado crítico #2 — R3-2 é procedente e a causa raiz de R1-2/R1-4

- `synthetic.py:104`: `billing_active_power = active_power * (1.0 - theft_ratio)` — o furto é *definido* como uma redução multiplicativa direta da potência de faturamento.
- `features.py:18-20`: `divergence_power = active_power - billing_active_power`; `relative_divergence = divergence_power/active_power` — que é **algebricamente igual a `theft_ratio`** (a menos de ruído de segunda ordem no fator de potência).
- `risk.py:26-32` (motor de regras) e `pipeline.py:12-21` (`FEATURE_COLUMNS` do modelo supervisionado) usam `relative_divergence`, suas médias/máximos móveis, e `alarm_score` — que por sua vez inclui `alarm_out_of_bounds_power`, definido em `synthetic.py:124` como `divergence_ratio > 0.12`, ou seja, **outra codificação direta do mesmo `theft_ratio`**.
- **Consequência:** o rótulo (`theft_active`), o mecanismo gerador dos dados e as features de entrada do classificador são, na prática, a mesma variável observada de três formas diferentes. Isso explica de forma direta por que a regressão logística atinge `accuracy = precision = recall = f1 = roc_auc = 1.0000` (`run_summary.md`) — não é um classificador poderoso, é um problema quase determinístico por construção.
- **Veredito:** R1-2 ("overfit"), R1-4 ("métricas boas demais") e parte de R3-2 têm a mesma causa raiz, comprovada em código. Corrigir a geração sintética (introduzir fontes de ruído/incerteza desacopladas do mecanismo de rótulo) ataca as três críticas ao mesmo tempo.

### 3.3 Achado #3 — R3-4 confirmado: pesos de fusão são constantes arbitrárias, não calibradas

- `decision/fusion.py`: `WeightedProbabilityFusion(rule_weight=0.6, supervised_weight=0.4)`; `ContextAwareFusion(rule_dominant_weight=0.75, supervised_dominant_weight=0.65, balanced_rule_weight=0.55)`. Todos são literais fixos no código, sem procedimento de calibração, busca ou justificativa quantitativa. O artigo apenas descreve $U=\lambda_1 D-\lambda_2 C$ conceitualmente e nunca resolve para $\lambda_1,\lambda_2$ — confirmando que a "otimização" é, na implementação atual, um conjunto de limiares de histerese (`Thresholds.moderate_risk=0.30`, `high_risk=0.60`) escolhidos a priori, não uma política resultante de um processo de otimização.

### 3.4 Achado #4 — R3-7 confirmado, mas com boa notícia: o dado para a comparação controlada já existe

- `pipeline.py:185-198`: o próprio pipeline **já avalia cada política (`fixed_long`, `fixed_short`, `adaptive`) sob as duas fontes de probabilidade (`risk_probability`, `supervised_probability`)**, além de avaliar a política adaptativa também sob `decision_probability` por estratégia de fusão. Esses resultados **já estão salvos** em `outputs/policy_comparison.csv` e `outputs/campaign/campaign_policy_comparison.csv`.
- O problema apontado por R3 não é de dado faltante, é de **narrativa do artigo**: o texto usa a comparação mais favorável (`adaptive/decision_probability/weighted` vs. `fixed_short/supervised_probability`) como resultado-manchete, sem primeiro mostrar a comparação isolada e controlada (mesma fonte de probabilidade em todas as políticas) que já está calculada.
- **Veredito:** correção de baixo custo (reanálise + reescrita), não exige novo experimento.

### 3.5 Achado #5 — R3-3 confirmado: custo de comunicação é um proxy trivial

- `comparison.py:11,49`: `communication_bytes = observed_samples * payload_bytes_per_sample` (constante = 64 bytes/amostra, `config.py:26`). Não há modelagem de latência, retransmissão, overhead de sinalização NB-IoT, nem custo energético.
- `devices/mock_transport.py`: a escolha NB-IoT vs. BLE depende só de `link_ok`/`heartbeat_ok` (flags aleatórias sintéticas com ~3%/2% de falha) — não há nenhum parâmetro de rede real (RSRP/SNR, tempo de conexão NB-IoT, número de retransmissões, duração de PSM/eDRX etc.).
- **Veredito:** confirmado; é a lacuna mais cara de corrigir tecnicamente (Bloco A, alto esforço).

### 3.6 Inconsistência de documentação vs. código (achado lateral, não crítica de revisor, mas relevante para reprodutibilidade)

- `docs/architecture.md` e `docs/framework_overview.md` descrevem os módulos como estando em `src/fraud_dt/twin/`, `decision/`, `control/`, `actions/`, `devices/`, `runtime/` — **isso está correto** (confirmado via `Glob`), mas um `find` superficial pode sugerir uma estrutura só "flat"; qualquer describe futuro do "reprodutibilidade" deve usar `Glob`/estrutura real, não a listagem superficial. Não é uma crítica dos revisores, mas é relevante para a seção de reprodutibilidade do novo artigo (R nenhum, mas boa prática).

## 4. Contribuição científica real (Subagente 4)

| Pergunta | Resposta honesta |
|---|---|
| O que existe de novo? | A arquitetura de software explícita de um twin que trata densidade de observação como variável de decisão, com componentes de estado, decisão, orquestração, comando e transporte todos implementados e testados (não é só um classificador). |
| Isso é sustentado pelos resultados? | Parcialmente. A arquitetura é real (Seção 3 confirma). O ganho numérico declarado (>97% do F1 com -50% de comunicação) **não é confiável no estado atual** porque decorre de um problema artificialmente fácil (Achado #2) e de uma comparação não isolada (Achado #4). |
| É uma implementação ou conhecimento científico novo? | Hoje, majoritariamente uma implementação de engenharia bem instrumentada com uma política de controle heurística. Não há, ainda, solução formal de otimização, análise de convergência, nem modelo de custo de rede realista — exatamente o que R3-4/R3-3/R3-6 apontam. |
| Como fortalecer sem inventar? | (a) Tornar o problema estatisticamente não-trivial (Bloco A); (b) resolver explicitamente o trade-off $D$ vs. $C$ com um procedimento real (grid search / fronteira de Pareto) em vez de pesos fixos; (c) modelar custo de rede com parâmetros NB-IoT publicados na literatura; (d) declarar explicitamente, sem exagero, que a contribuição é a **arquitetura de controle de observação + evidência comparativa controlada**, não um "framework ótimo provado". |
| Termos a evitar sem evidência | "novel", "state-of-the-art", "unprecedented", "optimal" — nenhum será usado sem comparação/prova direta. |

## 5. Estado da arte — lacunas a investigar (Subagentes 5/6)

A revisão bibliográfica do artigo original já é estruturada (estratégia de busca com 3 queries, PRISMA-like, 31 trabalhos) — **isso deve ser preservado e atualizado, não recomeçado do zero**. Ações pendentes para a Fase 4 de execução (ainda não realizadas nesta auditoria):

1. Buscar literatura específica sobre **modelagem de custo NB-IoT realista** (latência, retransmissão, PSM/eDRX, overhead de sinalização) para fundamentar o novo modelo de transporte (ataca R3-3).
2. Buscar literatura sobre **detecção de furto de energia sob ruído/adversariedade** (packet loss, sensor drift, concept drift) para justificar o novo gerador sintético mais realista (ataca R2-major-1, R3-2).
3. Buscar literatura sobre **métricas de localização temporal relaxadas** (ex.: IoU/decaimento gaussiano em detecção de eventos temporais, "temporal tolerance windows" em detecção de anomalias) para fundamentar a nova métrica de `critical_slot_hit` (ataca R2-major-2).
4. Buscar literatura sobre **POMDP/bandits com custo de observação** ou métodos de otimização de política mais simples (grid search documentado, busca em fronteira de Pareto) aplicáveis sem exigir uma reformulação de pesquisa inteira — para responder de forma proporcional a R3-4 sem prometer mais do que o escopo permite.
5. Reforçar a tabela de posicionamento (`tab:rw_comparison`, já existente e bem estruturada) com 1-2 referências mais recentes se aparecerem nas buscas acima (ataca R3-6).

**Regra**: nenhuma referência será adicionada sem ter sido de fato encontrada por busca (Consensus/fontes confiáveis). Esta seção será executada na Fase 4, com resultados reportados de forma verificável (título, ano, veículo).

## 6. Metodologia e reprodutibilidade (Subagente 7)

Pontos já bons (preservar): seeds determinísticos, `requirements.txt`, manifestos de execução, CLI reprodutível, SQLite versionado por execução.

Lacunas a corrigir no novo artigo:
- Não há descrição do hardware/ambiente de execução (mesmo sendo simulação local, o artigo deve declarar SO, versão de Python, principais versões de bibliotecas — os manifestos já capturam isso em `run_manifest.json`, só falta reportar no texto).
- `train_supervised_baseline` faz split 70/30 **sequencial no tempo** (não é k-fold, não há intervalo de confiança, não há repetição com múltiplas seeds) — isso precisa ser declarado explicitamente como limitação ou corrigido com múltiplas seeds/repetições (ver Seção 8).
- Não há teste de significância estatística nem intervalo de confiança em nenhuma métrica reportada.

## 7. Avaliação experimental — o que falta (Subagente 8)

Distinguindo claramente o que já existe do que precisa ser produzido:

| Já existe (reaproveitar) | Precisa ser recalculado (pipeline já suporta, é reanálise) | Precisa de código novo | Fora de escopo nesta rodada (declarar como limitação) |
|---|---|---|---|
| Coerência metrológica da síntese | Comparação controlada política × fonte de probabilidade (Achado #4) | Resolução temporal nativa mais fina + reamostragem para modos de observação (Achado #1) | Validação com dado real de campo |
| Traceabilidade (state history, command plan, transport log) | — | Fontes de ruído desacopladas do rótulo (packet loss, sensor drift, perfis legítimos erráticos) (Achado #2) | Piloto com firmware/hardware real |
| 3 estratégias de fusão implementadas e testáveis | — | Modelo de custo NB-IoT realista (latência, retransmissão, overhead, energia) (Achado #5) | — |
| Métricas de detecção (precision/recall/F1) | Curvas ROC/AUROC por cenário (dado já existe via `predict_proba`, só falta plotar) | Métrica `critical_slot_hit` relaxada/gaussiana | — |
| — | — | Resolução explícita do trade-off $D$/$C$ (grid search sobre $\lambda_1,\lambda_2$ ou sobre limiares) | Prova formal de otimalidade/convergência |
| — | — | Benchmark de complexidade/escalabilidade (tempo/memória × N twins simultâneos) | — |
| — | — | Importância de features (coeficientes padronizados + permutation importance) e baseline MLP pequeno | — |

**Regra dura reforçada**: nenhum número acima será fabricado. Cada célula da coluna "precisa de código novo" só entra no artigo depois de o script correspondente rodar e gerar output verificável em `outputs/`.

## 8. Matriz de rastreabilidade completa

| # | Comentário | Válida? | Evidência | Ação corretiva | Seção afetada | Experimento novo? | Literatura nova? | Mudança de metodologia? | Reformular contribuição? | Verificação |
|---|---|---|---|---|---|---|---|---|---|---|
| R1-1 | Terminologia "digital twin" | Parcialmente | Loop fechado existe em código (Seção 3) mas é local/simulado | Seção explícita de critérios de digital twin + reconhecimento honesto do estágio atual | Introduction, Methods | Não | Sim (definição formal de DT) | Não | Sim (framing) | Trecho novo cita critérios e mapeia componente→critério |
| R1-2 | Overfitting | **Sim, confirmada** | Achado #2 (Seção 3.2) | Ruído desacoplado do rótulo no gerador sintético | Methods, Results | Sim | Sim | Sim | Não | AUROC deixa de ser 1.0 nos novos cenários |
| R1-3 | Feature importance / MLP | Válida, viável | `FEATURE_COLUMNS` existe, fácil de instrumentar | Coeficientes padronizados + permutation importance + MLP pequeno como baseline extra | Results | Sim | Não | Não | Não | Nova tabela/figura de importância + linha de métrica do MLP |
| R1-4 | ROC/AUROC | Válida, barata | `predict_proba` já calculado | Gerar curvas ROC por cenário | Results | Reanálise | Não | Não | Não | Figura de ROC no artigo, com AUROC < 1 nos cenários corrigidos |
| R2-major-1 | Realismo sintético | **Sim, confirmada** | Achado #2 | Mesmo que R1-2 (ruído realista) | Methods | Sim | Sim | Sim | Sim (declarar limite de validade externa) | Cenários com ruído reduzem separabilidade perfeita |
| R2-major-2 | `critical_slot_hit` rígido | **Sim, confirmada** | Seção 3, `comparison.py:51-55` mostra bucket por hora, top-1 rígido | Métrica relaxada (janela/gaussiana) reportada ao lado da binária | Methods, Results | Reanálise + função nova | Sim | Sim | Não | Duas métricas lado a lado, discussão explícita |
| R2-major-3 | `context_aware` sem vantagem | **Sim, confirmada** | `campaign_summary.md`: context_aware ligeiramente abaixo de weighted | Ablation controlado das regras de troca de peso + discussão honesta | Results, Discussion | Sim (ablation) | Não | Não | Sim (reconhecer limite da estratégia) | Tabela de ablation nova |
| R2-minor-1 | $D,C$ não formalizados | Válida, barata | Texto atual só descreve | Formalizar $D(s_t,a_t)$, $C(s_t,a_t)$ antes da equação de utilidade | Methods | Não | Não | Sim (rigor) | Não | Equações novas no texto |
| R2-minor-2 | Qualidade de figuras | Válida | Fig. PNG originais em baixa resolução | Reexportar em vetor/alta resolução | Figuras | Não | Não | Não | Não | Novas figuras nítidas |
| R3-1 | Resolução `aggressive` | **Sim, confirmada e mais grave que o texto sugere** | Achado #1 (Seção 3.1) | Regerar série em resolução nativa mais fina + reamostragem por modo, ou remover/justificar limite mínimo de granularidade | Methods, Data generation | Sim | Não | Sim | Sim (declarar granularidade mínima defensável) | `should_emit` produz densidades distintas por modo, verificável por contagem de amostras |
| R3-2 | Circularidade feature/rótulo | **Sim, confirmada, é a causa raiz de R1-2/R1-4** | Achado #2 (Seção 3.2) | Ruído realista + eventual ofuscação parcial do sinal de divergência | Methods, Data generation | Sim | Sim | Sim | Sim | Métricas deixam de ser perfeitas de forma consistente |
| R3-3 | Custo NB-IoT superficial | **Sim, confirmada** | Achado #5 (Seção 3.5) | Modelo de custo com latência/retransmissão/overhead/energia baseado em parâmetros de literatura | Methods, System model | Sim | Sim | Sim | Não | Nova tabela de parâmetros de rede + métricas de latência/energia reportadas |
| R3-4 | Utilidade não resolvida | **Sim, confirmada** | Achado #3 (Seção 3.3) | Grid search / fronteira de Pareto sobre $(\lambda_1,\lambda_2)$ ou sobre limiares de histerese, com curva custo×detecção | Methods, Results | Sim | Sim (breve) | Sim | Sim (declarar como heurística otimizada empiricamente, não prova formal) | Curva de Pareto no artigo |
| R3-5 | Sem análise de complexidade | **Sim, confirmada** | Nenhuma menção no texto nem instrumentação no código | Big-O do pipeline por evento + benchmark empírico variando N twins | Methods, Results | Sim | Não | Não | Não | Tabela/figura tempo×memória vs. N |
| R3-6 | Novidade pouco distinguida | Parcialmente válida | Tabela `tab:rw_comparison` já existe mas é genérica | Parágrafo de "declaração de novidade" + reforço da tabela | Related Work | Não | Sim (reforço pontual) | Não | Sim | Novo parágrafo explícito |
| R3-7 | Comparação de baseline confundida | **Sim, confirmada** | Achado #4 (Seção 3.4) — dado já existe | Reescrever a narrativa de resultados usando a comparação isolada primeiro | Results | Reanálise apenas | Não | Sim (desenho experimental) | Não | Tabela fatorial política×fonte no texto principal, não só em anexo |
| R3-8 | Apresentação matemática/tabelas fracas | Válida | Comparação direta texto vs. tabelas do `.tex` (redundância confirmada) | Auditoria de todas as tabelas; equações formalizadas (idem R2-minor-1) | Todo o artigo | Não | Não | Não | Não | Nenhuma tabela deve repetir 1:1 o parágrafo adjacente |

## 9. Riscos de nova rejeição se nada além do template for trocado

Simulando um parecer "cego" (Subagente 13) sobre uma versão que fosse **só reformatada** para IEEE Access sem tocar no Bloco A:
- Um revisor técnico repetiria R3-1, R3-2, R3-4 e R3-7 quase palavra por palavra, porque são verificáveis a partir dos próprios números do artigo (ex.: AUROC=1.0 é visível no texto atual).
- IEEE Access aceita menor ineditismo, mas seus revisores ainda usam checklist de rigor metodológico e reprodutibilidade — as falhas de desenho experimental encontradas na Seção 3 não são "questão de venue".
- **Conclusão do Editor-chefe simulado (Subagente 14):** não recomendar submissão sem antes executar pelo menos os itens R3-1, R3-2, R3-4 (parcial) e R3-7 do Bloco A. Os demais itens do Bloco A (R3-3, R3-5) fortalecem substancialmente o artigo mas são menos fatais isoladamente.

## 10. Estrutura preliminar do novo artigo (Subagente 9, mapeada ao template `ieeeaccess.cls`)

1. **Abstract** (150–250 palavras, sem exagero de contribuição, com números atualizados após Bloco A)
2. **Introduction** — problema, lacuna, hipótese, 4 contribuições (revisadas para refletir o que é realmente sustentado)
3. **Related Work** — reaproveitar as 3 subseções e a tabela comparativa existentes, com reforço de novidade (R3-6) e literatura nova (Seção 5)
4. **System Model and Problem Formulation** — reformular com $D(s_t,a_t)$, $C(s_t,a_t)$ explícitos (R2-minor-1) e resolução real do trade-off (R3-4)
5. **Materials and Methods**
   - 5.1 Digital-twin criteria and scope (resposta estruturada a R1-1)
   - 5.2 Synthetic data generation with realistic noise (resposta a R2-major-1/R3-2)
   - 5.3 Native temporal resolution and observation modes (resposta a R3-1)
   - 5.4 Risk engines and feature importance (resposta a R1-3)
   - 5.5 Probability fusion strategies (mantém, com ablation nova — R2-major-3)
   - 5.6 NB-IoT/BLE transport and communication-cost model (resposta a R3-3)
   - 5.7 Computational complexity and scalability (resposta a R3-5)
6. **Experimental Campaign** — cenários (mantém 6, talvez +1 cenário de ruído puro sem furto para estresse), design fatorial explícito política×fonte de probabilidade (R3-7)
7. **Results and Discussion**
   - Curvas ROC/AUROC (R1-4)
   - Comparação controlada primeiro, comparação "melhor caso" depois, claramente rotuladas (R3-7)
   - Métrica `critical_slot_hit` binária e relaxada lado a lado (R2-major-2)
   - Curva de Pareto detecção×custo (R3-4)
   - Complexidade/escalabilidade (R3-5)
   - Ablation do `context_aware` (R2-major-3)
8. **Threats to Validity / Limitations** (seção nova, explícita — honestidade sobre o que não foi resolvido: dado real de campo, prova formal de otimalidade)
9. **Conclusion**
10. **Acknowledgment, References, Biographies** (padrão IEEE Access)

## 11. Sequenciamento de execução a partir daqui

1. **Fase 2 (próxima):** decisões do usuário (Seção 12) + início do Bloco A de código (prioridade: R3-1 → R3-2 → R3-7[reanálise] → R2-major-2 → R1-3/R1-4 → R3-4 → R3-3 → R3-5).
2. **Fase 3:** regeração completa de `outputs/` e `outputs/campaign/` com o pipeline corrigido.
3. **Fase 4:** busca bibliográfica direcionada (Seção 5) com ferramenta de pesquisa acadêmica.
4. **Fase 5:** redação do novo manuscrito em `novoartigo/` usando `ieeeaccess.cls`.
5. **Fase 6:** auditoria seção-a-seção contra a matriz da Seção 8 (nenhum item pode ficar sem marca de "resolvido/onde/evidência").
6. **Fase 7:** revisão cega simulada (Subagente 13) + parecer de editor-chefe simulado (Subagente 14); iterar até que as melhorias sejam incrementais.
7. **Fase 8:** checklist de conformidade IEEE Access (abstract, biografias, `\history`, `\doi`, figuras vetoriais, formato de referências).

## 12. Decisões que preciso de você antes de tocar em código

1. **Escopo do Bloco A**: aprovo executar todos os 5 itens de código (R3-1, R3-2, R3-3, R3-4, R3-5) antes da reescrita, ou priorizamos primeiro os mais baratos/decisivos (R3-1, R3-2, R3-7-reanálise, R2-major-2, R1-3/R1-4) e deixamos R3-3/R3-4/R3-5 para uma segunda iteração?
2. **Ambição da resolução de R3-4**: aceito uma solução pragmática (grid search / fronteira de Pareto sobre os pesos e limiares, documentada e reproduzível) em vez de uma prova formal de otimalidade (que exigiria escopo de pesquisa muito maior)?
3. **Dados reais**: confirma que não há nenhum dado de campo disponível (nem parcial) para esta rodada, mantendo 100% síntese realista aprimorada?
4. **Autoria/afiliações**: mantemos exatamente as mesmas do artigo rejeitado no novo template ACCESS?
5. **Novo cenário de estresse**: aprova adicionar um 7º cenário sintético (ruído puro, sem furto, com falhas de comunicação mais frequentes) para sustentar a análise de robustez pedida por R2-major-1, ou mantemos os 6 cenários originais e só injetamos ruído dentro deles?

Respostas:
1 - aprovo executar todos os 5 itens de código.
2 - aceito uma solução pagmática (grid search / fronteira de Pareto sobre os pesos e limiares, documentada e reproduzível).
3 - Embora existam dados de campo, inicialmente vamos atuar com dados sintéticos, pois a análise decampo atualmente passa por aprovação forense junto a distribuidora para determinar e executar ações corretivas em clientes com indícios de fraude, não permitindo ainda publicidade dos dados reais.
4 - Autoria e afiliações mantém igual.
5 - Aceito incluir um 7º cenário.

Nota.: Considerar que o dispositivo é alimentado pela própria energia elétrica da rede da distribuidora, então não cabe uma análise de consumo de energia, ele é disponível full time, e o maior interesse das companhias elétricas é identificar furto a baixo custo de consumo de dados. Embora o dispositivo embarcado já exista e seja brevemente citado no artigo, não é tema do trabalho de pesquisa. apenas considerar que ele existe, é funcional, certificado respeitando:
IEC 61000-4-5
IEC 61000-4-4
IEC 61000-4-11
IEC 61000-4-6

Considerar que ele atende aos requisitos de classe de erro equivalente ao medidor do cliente, que é um produto discreto para prover os dados forenses mas ainda assim não ser facilmente detectado pelo cliente. E que os clientes que fraudam usam de diversos artifícios, como fraude em horários específicos, com desvio de consumo total ou parcial, a depender da hora e do dia.