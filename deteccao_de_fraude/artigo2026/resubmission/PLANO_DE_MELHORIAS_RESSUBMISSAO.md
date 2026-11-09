# Plano de Melhorias — Ressubmissão IEEE Access (Access-2026-46607)

> **Status:** só diagnóstico e plano. **Nenhum arquivo do artigo nem do código foi alterado.**
> **Analisado:** `resubmission/rejected/decision.txt` (parecer dos 3 revisores), `access.tex` (manuscrito submetido, 842 linhas), todo o `src/fraud_dt/`, os `scripts/` e os resultados em `outputs/` e `outputs/campaign/`.
> **Data:** 06/11/2026

---

## 0. Leia isto primeiro — o que muda em relação à rodada anterior

1. **O IEEE Access só permite uma ressubmissão.** A carta diz: *"If the updated manuscript is determined not to have addressed all of the previous reviewers' concerns … the article will be rejected and no further resubmissions will be allowed."* Por isso o plano trata **todos** os itens dos revisores como obrigatórios, inclusive os "minor", e para cada um prevê uma ação concreta ou uma contra-argumentação documentada.
2. **O núcleo do problema está no protocolo experimental, não no texto.** Os revisores 1 e 3 (o 3 é o mais técnico) apontam, de forma independente, as mesmas falhas. A leitura do código **confirmou todas elas** e revelou mais algumas (Seção 2). Reescrever o texto antes de refazer os experimentos seria desperdício.
3. **Os números vão mudar, e a manchete pode ficar mais fraca.** Quando o classificador passar a ser treinado entre cenários (e não por cenário), os cenários sem furto provavelmente vão gerar escalonamentos falsos, e o custo do adaptativo deve subir. A fase aleatória de amostragem deve reduzir a recall do adaptativo. É bem possível que um baseline fixo com orçamento equivalente, ou o baseline com *backfill* (log denso local e envio esparso), empate com o adaptativo ou o supere em alguma métrica. **Isso precisa ser aceito antes de começar.** Na Seção 5.3 está uma estratégia para transformar esse risco em contribuição.

---

## 1. Matriz completa: comentário → ação → esforço

Escala de esforço: **B** = baixo (≤ 1 dia) · **M** = médio (2 a 5 dias) · **A** = alto (1 a 3 semanas) · **MA** = muito alto / depende de terceiros.
Atendimento: ✅ totalmente atendível · 🟡 parcialmente · ❌ não atendível agora (ver Seção 6).

### Revisor 1

| # | Pedido | Ação no código | Ação no artigo | Esforço | Atend. |
|---|---|---|---|---|---|
| R1.1a | Abstract e Conclusão com resultados dos cenários com furto e faixas por cenário | Gerar métricas *pooled* (micro) só dos cenários com furto e faixas min–max | Reescrever Abstract e Conclusão: resultados com furto + faixas + FPR nos cenários sem furto | B (texto) depois de M (código) | ✅ |
| R1.1b | Discrepância entre a Seção VI-F (F1 0,869 / 30.635 B) e a Tabela 5 (0,843 / 32.471 B) | **Causa encontrada** (Seção 2.4): o script do Pareto usa `seed=42` nos 3 cenários e a campanha usa `seed=42+idx`. Unificar a geração de dados | Explicar a causa na resposta; com multi-seed a inconsistência desaparece | B | ✅ |
| R1.2 | Baselines com orçamento equivalente (cadências de 25 a 30 min) e um adaptativo simples sem aprendizado | Novas políticas `fixed_20/25/30/40` e `threshold_escalation` (limiar fixo de divergência relativa) | Incluir nas Tabelas 4 e 5 e na Fig. 5 | M | ✅ |
| R1.3 | Métricas por episódio: taxa de detecção, atraso mediano e máximo, duração não detectada | Definir episódio; novo módulo `episode_metrics.py` | Nova subseção de métricas, nova tabela e (opcional) uma figura de CDF do atraso | M | ✅ (ver ressalva 2.6) |
| R1.4 | ≥ 30 seeds, IC 95%, comparação pareada contra o melhor baseline com orçamento equivalente; remover claims sem suporte | Runner multi-seed paralelo, bootstrap de IC, Wilcoxon pareado | Tabelas com média ± IC, Fig. 5 com variabilidade, claims qualificados | M/A | ✅ |
| R1.5 | Protocolo explícito: métricas incluem treino? features vêm da grade nativa? classificador por cenário? regras do orquestrador? | Corrigir o protocolo (Seções 2.1 a 2.3) | Nova subseção "Evaluation protocol" + tabela/pseudocódigo do orquestrador (Seção 4) | M (código) + B (texto) | ✅ |

### Revisor 2

| # | Pedido | Ação no código | Ação no artigo | Esforço | Atend. |
|---|---|---|---|---|---|
| R2.1 | Contribuição pouco clara; o conceito de DT não está claro; existe interação físico ↔ virtual? | (Opcional, forte) demonstração HIL com 1 dispositivo real (Seção 6.2) | Reescrever as contribuições (3 no máximo, bem delimitadas); diagrama de sequência físico ↔ virtual; classificação de Kritzinger (model/shadow/twin) | B a M (texto); A (HIL) | ✅ texto / 🟡 físico |
| R2.2 | Padronizar "Eq. (1)" vs "Equation (1)" e "Fig." vs "Figure"; usar Times New Roman nas figuras | `rcParams` do matplotlib com Times / STIX | Varredura editorial | B | ✅ |
| R2.3 | A Fig. 3 (metodologia) está confusa e precisa ser reorganizada | — | Redesenhar como fluxo em 3 blocos (dados → treino/teste → avaliação de políticas), incluindo `fixed_dense` (também pedido no R3.13) | B/M | ✅ (precisa do arquivo-fonte da figura) |
| R2.4 | Mais modelos de ML na Fig. 4 (ROC) | RF, HistGradientBoosting, SVM-RBF, kNN, MLP; opcional: Isolation Forest (não supervisionado) | Nova Fig. 4 + tabela com AUROC ± IC, em protocolo entre cenários | B/M | ✅ |
| R2.5 | Analisar mais a Fig. 5; explicar como o Pareto é obtido; dá para ajustar uma curva suave? | Ordenação não dominada documentada; envoltória convexa; ajuste monotônico (ver 3.7); frentes por seed | Parágrafo de método + discussão das regiões da frente + ligação com λ₁/λ₂ (também pedido pelo R3) | B/M | 🟡 (curva suave só como visualização; ver 6.4) |

### Revisor 3

| # | Pedido | Ação no código | Ação no artigo | Esforço | Atend. |
|---|---|---|---|---|---|
| R3.M1 | Treinar **um único modelo** entre cenários; avaliar em cenário não visto (LOSO) | Refatorar `train_supervised_baseline`: treinar fora do pipeline por cenário; protocolo A (seeds de treino ≠ seeds de teste) e protocolo B (LOSO) | Nova subseção de protocolo; resultados nos dois protocolos | M/A | ✅ |
| R3.M2 | Métricas de política só em tempo *held-out* | Avaliar em realizações (seeds) inteiramente não vistas no treino; isso é mais forte que cortar 30% do tempo | Declarar explicitamente | (vem junto com R3.M1) | ✅ |
| R3.M3 | Multi-seed com IC | igual ao R1.4 | igual ao R1.4 | — | ✅ |
| R3.M4 | FPR e tempo em modos elevados nos cenários sem furto | Novas métricas: FPR, % do tempo em moderate/aggressive, nº de escalonamentos/semana | Tabela própria para cenários sem furto | B | ✅ |
| R3.M5 | Baseline "log denso local, transmissão esparsa, *backfill* no alerta" | Nova política `adaptive_backfill` e/ou `fixed_sparse_backfill` com modelo de custo de rajada (lote) | Comparar; provavelmente vira parte do método proposto (Seção 5.3) | M/A | ✅ |
| R3.M6 | O fallback BLE exige operador; custear de outra forma ou reportar separado | Mudar o modelo: sem NB-IoT → *store-and-forward* (buffer local e envio no próximo NB-IoT); BLE vira coleta manual, reportada à parte (nº de visitas) | Reescrever a Seção IV-J | B/M | ✅ |
| R3.7 | Especificar τ, pesos do motor de regras, pesos do context_aware e as regras de histerese/dwell | — (os valores estão no código; ver Seção 4) | Tabela de parâmetros + pseudocódigo | B | ✅ |
| R3.8 | Trocar as médias dos 7 cenários com zeros por métricas *pooled* dos cenários com furto; citar a redução de ~57% ao lado dos 70,5% | Agregação micro | Abstract, Tabelas 4 e 5 | B | ✅ |
| R3.9 | Convenção do critical-slot nos cenários sem furto | **Causa encontrada** (Seção 2.7): sem furto e sem alarme, o código conta *hit* = 1 | Explicar; recomendo **remover ou rebaixar** a métrica, substituída pelo atraso por episódio | B | ✅ |
| R3.10 | Detecção por cliente e *time-to-first-flag* | Avaliação estilo "frota": cada seed é um cliente-semana; regra de sinalização de cliente (≥ k flags em 24 h) | Tabela de TPR e FPR por cliente | M | ✅ |
| R3.11 | Tabelar o conjunto completo de features | — (8 features; ver Seção 4.5) | Nova tabela | B | ✅ |
| R3.12 | Encurtar a Seção VI-G e tirar a narrativa do bug O(T²) | — | Reduzir a escalabilidade a 2 ou 3 frases ou mover para o material suplementar | B | ✅ |
| R3.13 | "Table 5" → "Table 4" na VI-C; a Fig. 3 não mostra o fixed_dense; dois subtítulos iguais; placeholders do template | — | Correções editoriais (lista na Seção 3.10) | B | ✅ |
| R3.14 | Depositar código e dados publicamente (Zenodo / Code Ocean) | Depósito público no Zenodo de dados sintéticos, splits, configurações, pseudocódigo completo e resultados brutos; código só sob requisição formal (Seção 3.10) | Data Availability com DOI; contribuição reformulada; justificativa do código só na carta | M | 🟡 dados, pseudocódigo e resultados públicos; código sob requisição |
| R3.15 | Situar o trabalho na literatura de amostragem adaptativa e event-triggered; referências sugeridas | — | Nova subseção II-D + referências; trocar as fontes fracas [11], [19], [20] | B/M | ✅ |
| R3 (geral) | "Mesmo uma pequena fatia anonimizada dos dados da EDP" | Dados sintéticos aprimorados (Seção 6.1): carga de base de datasets públicos, ataques segundo a taxonomia da literatura, frota heterogênea | Justificar por que dados de campo não entram nesta fase; descrever o novo gerador e as validações de realismo | A | ❌ dados de campo nesta fase / ✅ sintético aprimorado |

---

## 2. Problemas que encontrei no código (confirmam os revisores e vão além)

Estes são os achados que **justificam refazer a campanha**. Cada um tem um arquivo e uma linha como evidência.

### 2.1 Classificador treinado por cenário, constante em 4 dos 7 cenários (R3.M1, R1.5) — **crítico**
- `src/fraud_dt/risk.py:46-76`: `train_supervised_baseline` é chamada dentro de `run_pipeline`, um cenário por vez (`pipeline.py:183`). Quando o treino tem uma só classe, `supervised_probability` vira constante: 0 nos cenários sem furto e **1 em `persistent_theft`**.
- **Consequência não percebida pelos revisores:** com a fusão *weighted* (α = 0,6) e a probabilidade supervisionada igual a 0, a probabilidade fundida máxima é 0,6 × 0,99 = **0,594 < τ_high = 0,60**. Ou seja, **o modo aggressive é matematicamente inalcançável nos cenários sem furto**. Isso explica os 17.736 B (só basal) em `normal` e `disturbance`. Em `persistent_theft`, a probabilidade fundida é sempre ≥ 0,4, a política fica sempre ≥ moderate e na prática vira aggressive o tempo todo, com o mesmo custo do denso (135.332 B).
- **Correção:** treinar um modelo único em seeds de treino de **todos** os cenários e aplicá-lo congelado nos seeds de teste (protocolo A), e fazer LOSO (protocolo B).

### 2.2 Métricas de política incluem o trecho de treino (R3.M2, R1.5) — **crítico**
- `risk.py:90`: `model.predict_proba(model_df[...])` é aplicado à série **inteira**, incluindo os 70% usados no ajuste, e `comparison.py:64-127` avalia t = 1..T.
- **Correção:** com o protocolo A, a realização de teste inteira é não vista. Não é preciso cortar o tempo, e a métrica continua cobrindo a semana completa (melhor para os episódios).

### 2.3 Features calculadas na grade nativa de 5 min, mesmo em modo basal (R1.5) — **crítico; decisão tomada**
- `features.py:31-47`: as janelas rolantes (60 e 120 min) e o `slot_recurrence` são calculados **antes** do loop fechado, sobre os 2016 ticks. No `simulator.py:384`, a observação emitida carrega esses valores. Uma amostra emitida em modo basal já "sabe" o que aconteceu nos 11 ticks não transmitidos.
- **Decisão (informada pelo autor):** o dispositivo forense é instalado em paralelo no ramal e **não tem nenhum contato com o medidor de faturamento**; os dois são independentes. Portanto a divergência forense × faturamento **só pode ser calculada no back-office/head-end**. Calcular essas features no dispositivo (edge) é fisicamente impossível.
- **Consequência para a implementação:**
  - O modo principal passa a ser `feature_mode = "emitted"`: todas as features de divergência (instantânea, média de 60 min, máximo de 120 min, recorrência horária) são calculadas **só com as amostras forenses que chegaram ao back-office**, pareadas com a leitura de faturamento do mesmo intervalo.
  - O que o dispositivo pode fazer localmente são agregados da **própria** medição (por exemplo, a energia acumulada desde o último envio ou a potência máxima no intervalo), que não dependem do medidor de faturamento. Vale incluir isso como opção (`feature_mode = "emitted+local_agg"`): o payload leva a energia do intervalo inteiro, e não só a potência instantânea. Isso é realista para um medidor com registrador de energia e reduz bastante a perda de informação em modo basal. Verificar se cabe nos 64 B.
  - O modo antigo (grade nativa completa) fica só como **limite superior** (*oracle*) numa análise de sensibilidade, identificado como não realizável.
- **Granularidade (resolvido):** os dados chegam ao back-office em intervalos, e a cadência configurada (a cada x minutos) é respeitada. Uma mudança de cadência em tempo real vale a partir da **próxima amostragem**, sem reset. Premissa adotada: a série de faturamento também está disponível em intervalos no back-office, o que permite calcular a divergência intervalar.
- **Consequências para o simulador:**
  - O comando de cadência passa a valer na amostra seguinte. Isso já é o comportamento do `MockForensicDevice` ("adjusts its future emission cadence"); basta descrevê-lo no artigo.
  - A latência do comando vem do ensaio de bancada.
  - O desalinhamento de relógio entre as duas séries entra no gerador (S6).
- **Coerência com o backfill (R3.M5):** o dispositivo separa o período de captura do período de envio e guarda o perfil em memória de massa, recuperável sob demanda. Ou seja, "capturar a 5 min e enviar a 60 min, puxando o histórico no alerta" é um modo de operação **nativo** do dispositivo. Isso torna o baseline de backfill fisicamente realista e reforça a estratégia da Seção 5.3.

### 2.12 Descrição do dispositivo no artigo
- Manter a nomenclatura atual ("certified embedded product"), por decisão do autor.
- Acrescentar à descrição do dispositivo (Seção III) as premissas que o gêmeo usa e que estão confirmadas:
  - medição independente do medidor de faturamento (instalação em paralelo no ramal, sem contato com o faturamento);
  - períodos de captura e de envio configuráveis remotamente, com a mudança valendo na amostra seguinte e sem reinicialização;
  - memória de massa com leitura sob demanda (base do backfill).

  Esforço B.

### 2.4 Causa da discrepância VI-F × Tabela 5 (R1.1b) — **resolvida**
- `scripts/run_policy_optimization.py:69`: `generate_synthetic_dataset(..., seed=seed)`, o **mesmo** seed 42 nos 3 cenários.
- `scripts/run_experiment_campaign.py:39`: `seed=args.seed + idx` (peak = 44, night = 45, intermittent = 46).
- Os dados são realizações diferentes. Na grade, com a mesma configuração (α = 0,6; 0,30; 0,60), `peak_theft` dá **F1 = 0,985**, contra **0,916** na campanha. São **7 pontos de F1 só por trocar o seed**. Isso, além de explicar a discrepância, é **a melhor evidência para a resposta** de que o multi-seed era necessário e de que diferenças de 1 ponto (0,869 × 0,878) não eram interpretáveis.

### 2.5 Fase de amostragem alinhada com o início do furto — **validade, não apontado pelos revisores**
- As emissões basais caem em :00 (a 1ª amostra é em 00:00 e o período é de 60 min), e as janelas de furto começam **exatamente** na hora cheia (`synthetic.py:75-91`: 18 h, 0 h). Nos dados: a primeira amostra com furto em `peak_theft` é 18:00:00, e é exatamente quando o basal amostra.
- Isso favorece artificialmente o `adaptive` e o `fixed_long`: a primeira amostra basal "pega" o início do furto. Um revisor atento pode notar isso na próxima rodada.
- **Correção:** fase inicial aleatória por seed (offset de 0 a 55 min) para todas as políticas, e início do furto com jitter (por exemplo, 18:00 ± U(0, 60) min por dia).

### 2.6 Furto intermitente gerado como Bernoulli por tick (afeta R1.3)
- `synthetic.py:85-88`: em `intermittent_evening`, cada tick de 5 min entre 18 h e 22 h tem furto com p = 0,55, de forma independente. Os "episódios contíguos" viram fragmentos de 1 ou 2 ticks, e a métrica de episódio pedida pelo R1 fica sem sentido físico (nenhuma fraude real liga e desliga a cada 5 min).
- **Recomendação:** trocar por um processo on/off semi-Markov (duração ON ~ U(15, 90) min, OFF ~ U(10, 60) min, só no período noturno). É uma mudança de gerador; declarar no artigo e na resposta. Alternativa mais barata: manter o gerador e definir o episódio como corridas unidas com *gap* ≤ 15 min. Mas o semi-Markov é mais defensável.

### 2.7 Convenção do critical-slot (R3.9) — **resolvida**
- `comparison.py:95-100`: sem furto, `true_critical_hour = -1`; sem flags, `pred = -1`; logo **hit = 1 e relaxed = 1**.
- No adaptativo: normal 1, persistent 1, peak 0, night 0, intermittent 0, disturbance 1, degraded 1, o que dá **4/7 = 0,5714**. No relaxado, os 3 erros valem 0,88 (1 h de distância), daí **0,9496**.
- Ou seja, o revisor inferiu o contrário (achou que os cenários sem furto valiam zero). Na verdade valem 1, e **nos 4 cenários com furto o hit binário é 1/4**. A métrica está inflada pelos cenários sem furto.
- **Recomendação:** remover a métrica critical-slot do corpo do artigo (ou deixá-la só nos cenários com furto, no suplemento). O atraso por episódio, pedido pelo R1, responde à mesma pergunta operacional com muito mais rigor.

### 2.8 Bug menor de vazamento em `slot_recurrence`
- `features.py:39-46`: `groupby("hour").expanding().mean().reset_index(level=0).shift(1)`. O `shift(1)` é posicional **depois** de achatar os grupos, então a 1ª linha de cada hora recebe a média da **semana inteira** da hora anterior (informação futura). Afeta 24 linhas em 2016, um impacto pequeno, mas é vazamento. Corrigir com `groupby("hour")["divergence_flag"].transform(lambda s: s.shift(1).expanding().mean())`.

### 2.9 Código morto com lógica divergente
- `policy.py:18-62` (`apply_adaptive_policy`) tem uma lógica de dwell **diferente** da do `PolicyOrchestrator` e não é usada em lugar nenhum. Remover antes de publicar o repositório, para evitar que um revisor de reprodutibilidade leia a versão errada.

### 2.10 Seleção de hiperparâmetros no mesmo dado da avaliação
- A grade do Pareto (`run_policy_optimization.py`) escolhe (α, τ) olhando os mesmos dados em que se reporta o resultado. Com o novo protocolo: **ajustar nos seeds de validação, reportar nos seeds de teste**. Os revisores não pediram isso, mas é o tipo de coisa que um Associate Editor nota.

### 2.11 Custo de downlink dos comandos
- `MockTransport.deliver` custa cada observação como um uplink, e o comando de reconfiguração não tem custo próprio. Declarar no texto que o downlink vai *piggyback* na janela RX da mesma sessão (ou custeá-lo). Esforço B.

---

## 3. Mudanças na implementação (detalhadas)

### 3.1 Nova infraestrutura experimental: avaliação "frota" multi-seed — **A** (é a base de quase tudo)
- `scripts/run_fleet_campaign.py` (novo): para cada cenário s e cada seed k, gera um cliente-semana.
  - **Seeds de treino:** por exemplo k ∈ [0, 20) → treino global do LR e dos demais modelos.
  - **Seeds de validação:** k ∈ [20, 30) → grade do Pareto e escolha de (α, τ).
  - **Seeds de teste:** k ∈ [100, 130) → **30 realizações por cenário**, todas as tabelas e figuras.
  - **LOSO:** para cada cenário s, treinar com os seeds de treino dos outros 6 cenários e testar em s.
- Paralelizar com `joblib` / `concurrent.futures`. Estimativa: cerca de 7 a 10 s por cliente-semana com as 3 fusões, ou seja, 7 × 30 ≈ 210 execuções ≈ 30 a 40 min de CPU em série, bem menos em paralelo. Inclui um manifesto JSON com seeds e hashes.
- Refatorar `run_pipeline` em: `build_features` → `score(model_congelado)` → `run_policies` → `evaluate`. O treino sai do pipeline por cenário.

### 3.2 Correções de protocolo — **M**
- Seções 2.1, 2.2, 2.3, 2.5, 2.8 e 2.9: treino global, avaliação em seed não visto, `feature_mode`, fase aleatória com jitter no início do furto, correção do `slot_recurrence`, remoção do código morto.
- Gerador semi-Markov para o intermitente (2.6).
- Atualizar os testes (`tests/`) e adicionar estes: (i) nenhum seed de teste aparece no treino; (ii) em `feature_mode="emitted"` (o modo principal, porque o dispositivo é independente do medidor de faturamento), as features de uma observação só dependem de amostras emitidas; (iii) a fase de emissão é aleatória.

### 3.3 Novos baselines de política — **M**
| Política | Descrição | Motivo |
|---|---|---|
| `fixed_20`, `fixed_25`, `fixed_30`, `fixed_40` | Cadência fixa (todas divisíveis pela grade de 5 min) | R1.2, orçamento equivalente |
| `threshold_escalation` | Sem aprendizado: se `relative_divergence > 0,08` → aggressive por N amostras; senão basal | R1.2, adaptativo simples |
| `fixed_sparse_backfill` | Basal de 60 min; no alerta (p ≥ τ_high), puxa o buffer local de 5 min das últimas H horas | R3.M5 |
| `adaptive_backfill` | O adaptativo proposto + backfill no alerta | R3.M5; candidato a método principal (5.3) |
| (opcional) `adaptive_evidence_cap` | Depois de K horas de furto confirmado em aggressive, desce para moderate (a evidência já é suficiente) | Responde ao "nenhuma economia em persistent_theft" do R1.1 |
- **Realismo do backfill:** o dispositivo separa o período de captura do de envio e guarda o perfil em memória de massa, que pode ser lida sob demanda (Seção 2.3). Portanto o backfill não é hipotético: é um modo de operação já suportado pelo hardware.
- **Modelo de custo do backfill:** um lote de n amostras de 64 B numa única conexão, com payload ≤ ~1.200 B por mensagem (verificar o limite do seu firmware / MTU NB-IoT); overhead de conexão de 40 B por lote. Documentar como hipótese.
- **Semântica de detecção com backfill:** as amostras recuperadas contam como observadas para recall e para o episódio, mas o **atraso** é medido a partir do momento do *backfill*, não da amostra. É isso que expõe o trade-off recall × atraso.

### 3.4 Modelo de transporte: BLE separado — **B/M**
- Sem NB-IoT (`link_ok=0` ou `heartbeat_ok=0`): a amostra vai para um **buffer local** e é enviada na próxima transmissão NB-IoT bem-sucedida (custo NB-IoT, latência = tempo de espera). Reportar: bytes NB-IoT (principal), atraso de entrega e, à parte, "visitas BLE necessárias" (se o buffer estourar ou a falha passar de X horas).
- Hoje o `degraded_link_no_theft` tem cerca de 40% das transmissões em BLE, ou seja, 40% de "visitas de campo" escondidas como bytes baratos. É exatamente o que o R3 criticou.

### 3.5 Novas métricas — **M**
- **Episódio** (R1.3): taxa de detecção de episódios; atraso mediano, P90 e máximo (min); minutos de furto não detectados; atraso até o 1º flag (R3.10).
- **Cenários sem furto** (R3.M4): FPR por tick, flags por semana, % do tempo em moderate e em aggressive, nº de escalonamentos.
- **Cliente** (R3.10): cliente sinalizado se houver ≥ k flags em 24 h (k ∈ {1, 3, 6}); TPR nos clientes com furto e FPR nos clientes sem furto.
- **Agregação** (R3.8, R1.1): micro (*pooled*) nos cenários com furto, mais faixas por cenário; nunca média com zeros estruturais.
- Remover ou rebaixar o critical-slot (2.7).

### 3.6 Estatística — **M**
- Média ± IC 95% por bootstrap (10.000 reamostragens sobre seeds) em todas as tabelas.
- Comparação pareada (mesmo seed = mesmos dados) do adaptativo contra o melhor baseline com orçamento equivalente e contra o backfill: **Wilcoxon signed-rank** com correção de Holm, mais tamanho de efeito (diferença mediana pareada com IC). Isso é mais adequado que o critério de "ICs não sobrepostos" sugerido pelo R1, que é conservador demais; explicar na resposta, mas reportar também o que ele pediu.
- Ablação das fusões com o mesmo teste pareado (R1.4 e R3, sobre os 6,4%).

### 3.7 Pareto (R2.5, R3 sobre a Eq. 3) — **B/M**
- Método: ordenação não dominada (minimizar bytes, maximizar F1), já implementada em `pareto_frontier()`. Documentar.
- Rodar a grade nos seeds de **validação**, marcar a configuração escolhida e reportar o desempenho dela no **teste** (com IC).
- Variabilidade: frente média ± banda entre seeds, ou a frequência com que cada configuração é não dominada nos 30 seeds.
- **Ligação com a Eq. (3):** os pontos da **envoltória convexa** da frente são exatamente os maximizadores de U = λ₁D − λ₂C para alguma razão λ₂/λ₁; a inclinação de cada aresta dá o intervalo de λ em que cada ponto é ótimo. Isso responde ao R3 ("connect the frontier to λ1/λ2") com poucas linhas de código, e fica elegante.
- **Curva suave** (R2.5): dá para ajustar uma função monotônica côncava (por exemplo F1(C) = a − b·e^(−cC), ou regressão isotônica) **só como visualização**, com a ressalva de que os pontos entre configurações não são atingíveis diretamente. Nota técnica: combinações convexas são atingíveis em valor esperado por *time-sharing* entre duas configurações, para recall e bytes (F1 não é linear). Isso justifica desenhar a envoltória convexa em vez de uma curva arbitrária.
- Adicionar todos os baselines (fixos 15 a 60, threshold, backfill) como pontos na Fig. 5 (R1.2).

### 3.8 Modelos de ML adicionais (R2.4) — **B/M**
- Logistic Regression, Random Forest, HistGradientBoosting, SVM-RBF (com probabilidade calibrada), kNN e MLP; opcional: Isolation Forest (não supervisionado, útil para argumentar sobre fraudes nunca vistas).
- Avaliar no protocolo A e no LOSO; ROC com AUROC ± IC.
- Se algum modelo for melhor, testá-lo **também no loop fechado** (pelo menos o melhor deles). Se o LR continuar como motor, justificar pela interpretabilidade e pela calibração.

### 3.9 Figuras — **B a M**
- `matplotlib`: `rcParams["font.family"]="serif"; ["font.serif"]=["Times New Roman"]; ["mathtext.fontset"]="stix"`; exportar em PDF/EPS vetorial; tamanho de 1 coluna (3,5 in).
- Fig. 1 (topologia): foi gerada com ChatGPT e não é possível trocar a fonte. **Recomendo redesenhar** (draw.io / TikZ) com Times New Roman. De quebra, sai a ressalva de figura gerada por IA nos Agradecimentos, que alguns editores veem com desconfiança.
- Figs. 2 e 3: se você tiver o arquivo-fonte (draw.io / Visio), edite nele; senão, redesenhe. Fig. 3: reorganizar em 3 blocos (Geração de dados por seed → Treino global e LOSO → Avaliação de políticas e métricas) e incluir **todas** as políticas (inclusive `fixed_dense`).
- Fig. 6 (escalabilidade): candidata a sair (R3.12).
- Novas figuras sugeridas: (i) exemplo de linha do tempo (furto real × modo × flags) num seed do intermitente; (ii) CDF do atraso de detecção por política.

### 3.10 Reprodutibilidade e depósito público (R3.14) — **M**

**Decisão do autor:** depositar publicamente os **dados sintéticos**, o **pseudocódigo** completo de geração e avaliação e os **resultados**. O **código-fonte não é publicado** nesta fase.

#### O que vai no depósito público (Zenodo, com DOI)

| Pasta | Conteúdo | Formato |
|---|---|---|
| `data/` | Séries sintéticas de cada cenário e seed: medição forense, faturamento, alarmes e rótulos de *ground truth* (furto por tick e lista de episódios com início e fim) | CSV (ou Parquet) + dicionário de dados |
| `splits/` | Manifesto das seeds de treino, validação e teste e das dobras LOSO | JSON |
| `config/` | Todos os parâmetros: gerador, features, motor de regras, pesos das fusões, limiares do orquestrador, políticas, modelo de custo e grade do Pareto | YAML/JSON (os mesmos valores das tabelas do artigo) |
| `pseudocode/` | Pseudocódigo completo e numerado das etapas (lista abaixo), em nível suficiente para reimplementação independente | PDF + Markdown |
| `results/` | Resultados brutos de **cada execução** (cenário × seed × política × fusão): métricas por tick, por episódio e por cliente, bytes, tempo em cada modo; grade do Pareto em validação e teste; saídas dos testes estatísticos; **os dados por trás de cada tabela e figura** | CSV |
| `bench/` (opcional) | Medições do ensaio de bancada (laboratório, sem dados de clientes), se a liberação for autorizada junto com o resto | CSV |
| raiz | `README` (estrutura, dicionário de dados, como ligar cada arquivo a cada tabela e figura), `LICENSE` (CC BY 4.0 para os dados), `CHECKSUMS.sha256`, `CITATION.cff` | — |

**Pseudocódigo a incluir** (um algoritmo por etapa, com entradas, saídas e parâmetros referenciados ao `config/`):
1. Gerador sintético: carga de base, injeção de furto por família de ataque, processo de episódios, ruído metrológico, desalinhamento de relógio, perturbações legítimas, alarmes e enlace.
2. Cálculo das features no back-office, só com as amostras recebidas.
3. Motor de regras e treino do modelo supervisionado (protocolos A e LOSO).
4. Estratégias de fusão (weighted, conservative_max, context_aware).
5. Orquestrador (histerese, permanência, retorno ao basal) e laço fechado gêmeo ↔ dispositivo.
6. Modelo de transporte e custo (NB-IoT, retransmissão, armazenamento e reenvio, backfill).
7. Políticas de comparação (fixas, `threshold_escalation`, backfill).
8. Métricas (tick, episódio, cliente, FPR) e agregação.
9. Estatística (bootstrap, Wilcoxon pareado com Holm) e construção da frente de Pareto e da envoltória convexa.

No artigo entram os algoritmos centrais (orquestrador e laço fechado, como Algoritmos 1 e 2). O restante fica no depósito.

**Por que isso atende ao essencial do R3.14:** qualquer leitor pode (i) conferir cada número das tabelas a partir dos resultados brutos, (ii) rodar outros métodos sobre exatamente os mesmos dados e as mesmas divisões e (iii) reimplementar o pipeline pelo pseudocódigo e pelas configurações.

#### Código-fonte
- **Não é publicado.** O código completo pode ser obtido mediante **requisição formal** aos autores e hoje não está disponível publicamente por causa de **processos internos de autorização** para liberação pública.
- **Essa informação vai só na carta-resposta.** A seção Data Availability do artigo cita apenas o depósito (dados, pseudocódigo e resultados, com o DOI).

#### Ajustes no artigo
- Na lista de contribuições, trocar "reprodutibilidade" por algo verificável com o depósito, por exemplo: *"a fully specified evaluation protocol, with the synthetic datasets, pseudocode, configuration and per-run results publicly released"*.
- Data Availability: *"The synthetic datasets, data splits, configuration files, complete pseudocode of the data generation and evaluation pipeline, and per-run results underlying all tables and figures are openly available at Zenodo (DOI: …)."*

#### Texto para a carta-resposta (R3.14)
> *"We agree that reproducibility must be verifiable. In the revised version, we publicly release on Zenodo (DOI: …) the complete synthetic datasets with ground-truth labels and episode lists, the train/validation/test and leave-one-scenario-out splits, all configuration files, a complete step-by-step pseudocode of the data generation and evaluation pipeline, and the per-run results underlying every table and figure. This allows every reported number to be checked and the pipeline to be independently reimplemented on exactly the same data. The full source code is not publicly available at this time owing to ongoing internal authorization procedures for public release; it can be obtained from the authors upon formal request. The contribution statement has been reworded accordingly (Section I)."*

#### Organização interna (continua necessária)
- O projeto **não está sob git**. Antes de refatorar: `git init`, commit do estado atual e tag `v1-submission`, para conseguir regenerar os números originais na resposta.
- Ter um `scripts/reproduce_all.py` que gera, a partir das configurações, todos os arquivos de `data/` e `results/` e as figuras. Ele não é publicado, mas garante que o depósito corresponde exatamente ao artigo e permite atender rapidamente a uma requisição formal.
- Fixar as versões das dependências (`requirements.lock`) e registrar o hash do commit usado no `README` do depósito.

---

## 4. Conteúdo pronto para a nova subseção de protocolo (R1.5, R3.7, R3.11)

Valores **extraídos do código atual**, para você conferir e usar na tabela do artigo. Se algum parâmetro mudar na refatoração, atualize aqui.

### 4.1 Limiar de detecção
- τ = **0,50** (`config.py:34`, `ExperimentConfig.prediction_threshold`), aplicado a qualquer fonte de probabilidade. Probabilidades fundidas truncadas em 0,99.

### 4.2 Motor de regras (`risk.py:26-43`)
| Condição | Peso |
|---|---|
| `relative_divergence` > 0,08 | 0,35 |
| `rolling_divergence_mean` (60 min) > 0,06 | 0,20 |
| `rolling_divergence_max` (120 min) > 0,12 | 0,10 |
| `slot_recurrence` > 0,25 | 0,15 |
| alarme out-of-bounds-power ativo | 0,10 |
| alarme overcurrent ativo | 0,05 |
| `operational_penalty` > 0 | 0,05 |
| Escore = soma, truncado em [0; 0,99] | |

### 4.3 Fusão context_aware (`decision/fusion.py:43-65`)
| Contexto | Condição | w_r | w_s |
|---|---|---|---|
| electrical-dominant | alarm_score > 0 **ou** rolling_max ≥ 0,12 **ou** operational_penalty > 0 | 0,75 | 0,25 |
| temporal-dominant | slot_recurrence ≥ 0,25 **e** hora ∈ {18–23, 0–5} | 0,35 | 0,65 |
| balanced | demais casos | 0,55 | 0,45 |
> Atenção: o texto atual do artigo **não menciona** o `operational_penalty` no contexto electrical-dominant nem a restrição de horário no temporal-dominant. Corrigir.

### 4.4 PolicyOrchestrator (`control/orchestrator.py:15-25`, `twin/state.py:30-34`)
```
entrada: p = probabilidade fundida; modo atual m; dwell d (nº de eventos EMITIDOS desde a entrada em m)
1. se m = aggressive e p > τ_mod (0,30) e d < 3 → aggressive        (permanência com histerese, ≤ 3 amostras = 15 min)
2. se m = moderate   e p > 0,8·τ_mod (0,24) e d < 2 → moderate      (permanência com histerese, ≤ 2 amostras = 30 min)
3. senão: p ≥ τ_high (0,60) → aggressive (5 min)
          p ≥ τ_mod  (0,30) → moderate   (15 min)
          caso contrário    → basal      (60 min)
d ← d+1 se o modo se mantém; d ← 1 se o modo muda
a nova cadência vale a partir da última emissão (next = last_emit + período)
```
**Observação importante para o texto:** o "dwell" funciona como uma **janela máxima de histerese**, não como permanência mínima. Depois de 3 (ou 2) amostras, a histerese some e valem só os limiares, então **aggressive → basal direto** é possível. Descrever isso exatamente assim, ou mudar o desenho para uma histerese clássica (limiar de descida fixo, sem limite de dwell) antes de rodar a campanha nova. Decisão sua (Seção 7).

### 4.5 Features (R3.11) — `risk.py:14-23`, `features.py`
| # | Feature | Definição | Grupo |
|---|---|---|---|
| 1 | `relative_divergence` | max(0, (P_forense − P_fat)/P_forense) | elétrico |
| 2 | `rolling_divergence_mean` | média de (1) em janela de 60 min | elétrico |
| 3 | `rolling_divergence_max` | máximo de (1) em janela de 120 min | elétrico |
| 4 | `slot_recurrence` | fração histórica de ticks com (1) > 0,08 na mesma hora do dia (causal) | temporal |
| 5 | `alarm_score` | soma de 5 alarmes (overvoltage, undervoltage, overcurrent, last_gasp, out_of_bounds_power) | alarme |
| 6 | `operational_penalty` | ((1−link_ok)+(1−heartbeat_ok))/2 | operacional |
| 7 | `hour` | hora do dia | temporal |
| 8 | `day_of_week` | dia da semana | temporal |
> Sugestão: com o treino entre cenários, `hour` deixa o LR "decorar" os horários dos cenários. Rodar a ablação com e sem `hour`/`day_of_week` (ou codificação cíclica sin/cos) no LOSO.

### 4.6 Hipóteses de custo de comunicação (manter, mais o BLE novo)
Payload de 64 B; overhead de conexão de 40 B se o intervalo for > 15 min; retransmissão truncada (≤ 3) com p = 0,04 (nominal) / 0,35 (degradado); latência de 1.600 ms + 900 ms por retransmissão. BLE passa a ser coleta manual (3.4).

---

## 5. Mudanças no artigo (por seção)

### 5.1 Título, Abstract, Introdução — **B** (depois dos resultados novos)
- Abstract: tirar "91% do F1 e 83% da recall a 30% do volume". Colocar: resultados *pooled* nos cenários com furto (com IC), faixa por cenário, redução de bytes nos cenários com furto **e** nos sem furto (ambos, R3.8), FPR nos cenários sem furto e atraso mediano de detecção por episódio. Declarar "synthetic, N = 30 seeds per scenario, held-out".
- Contribuições: reduzir de 6 para 3 ou 4, nítidas (R2.1). Sugestão:
  1. formulação da densidade de observação forense como variável de controle guiada por risco, num twin com laço fechado explícito (com a ligação ao event-triggered sampling);
  2. política adaptativa com *backfill* sob demanda (se os resultados confirmarem; ver 5.3);
  3. protocolo de avaliação em nível de episódio e de cliente, com baselines de orçamento equivalente, multi-seed e LOSO, mais o código e os dados abertos (DOI).
- Placeholders: `\history{...}` e `\doi{10.1109/ACCESS.2017.DOI}` (linhas 26-27). O editor substitui esses campos, mas o R3 reclamou, então deixe o padrão do template atual do Access (`\doi{10.1109/ACCESS.2024.0429000}`) ou apague-os conforme a instrução do template.

### 5.2 Trabalhos relacionados — **B/M**
- Nova subseção **"Adaptive and event-triggered sampling"** (R3.15), argumentando que a política é, sim, uma forma de amostragem *event-triggered/self-triggered*. A diferença está no **gatilho**: risco forense fundido, num laço com custo de rede real, e não a variação do sinal. Assumir isso de frente desarma a crítica de "contribuição mais estreita que o enquadramento".
- Referências sugeridas pelo R3 (todas pertinentes; recomendo incluir as 6): Jokar et al. 2016 (TSG); Zheng et al. 2018 (TII); Messinis & Hatziargyriou 2018 (EPSR); Glauner et al. 2017 (IJCIS); Tao et al. 2019 (TII); Alippi et al. 2010 (TIM).
- Candidatas adicionais (**conferir DOI e dados bibliográficos antes de usar**): Åström & Bernhardsson, "Comparison of Riemann and Lebesgue sampling…", IEEE CDC 2002; Heemels, Johansson & Tabuada, "An introduction to event-triggered and self-triggered control", IEEE CDC 2012; Trihinas, Pallis & Dikaiakos, "AdaM: an adaptive monitoring framework for sampling and filtering on IoT devices", IEEE Big Data 2015; Jain & Chang, "Adaptive sampling for sensor networks", DMSN 2004; Kritzinger et al., "Digital Twin in manufacturing: a categorical literature review and classification", IFAC-PapersOnLine 2018 (para o R2.1).
- Substituir ou complementar [11] (The Scientific Temper), [19] e [20] (EJTAS), que o R3 considerou de baixo rigor. Se [19]/[20] forem os únicos exemplos de "DT de medidor", manter um deles e acrescentar Tao 2019 e Kritzinger 2018.
- Atualizar a Tabela 1 com uma linha "Event-triggered / adaptive sampling".

### 5.3 Estratégia se o backfill vencer (importante)
O R3 praticamente aposta que o "log denso local + backfill" recupera a recall do intermitente. Se isso se confirmar, **não esconda: incorpore.** O papel do twin passa a ser decidir **quando puxar** o buffer e **quando densificar** o envio em tempo real. É um laço de controle mais rico e ainda inédito no contexto de NTL. O trade-off passa a ter três eixos: recall × bytes × **atraso de detecção** (o backfill recupera a evidência, mas só depois do alerta). Isso é cientificamente melhor que o artigo atual e responde aos R1.2, R1.3 e R3.M5 de uma vez.
Se o adaptativo puro perder para um fixo com orçamento equivalente numa métrica, reporte e discuta (o R1 elogiou exatamente o hábito de reportar resultados negativos).

### 5.4 Sistema e método — **M**
- Seção III: deixar a Eq. (3) e conectá-la à frente (envoltória convexa ↔ λ); ou encurtá-la (R3).
- Eq. (1): explicitar τ = 0,5; manter a Eq. (1) como recall por tick e **adicionar** as definições formais de episódio, atraso e detecção por cliente.
- Nova subseção **"Evaluation protocol"** (R1.5): (i) treino global em seeds disjuntos e LOSO; (ii) métricas em realizações não vistas; (iii) features calculadas no back-office só com as amostras recebidas, porque o dispositivo é independente do medidor de faturamento (o modo de grade completa só como limite superior); (iv) fase aleatória e jitter de início; (v) seleção de hiperparâmetros em validação. Mais a tabela de parâmetros (4.1 a 4.4) e o pseudocódigo do orquestrador (Algoritmo 2).
- Nova **tabela de features** (4.5).
- IV-J (custo): reescrever a parte de BLE (3.4) e declarar o custo do downlink (2.11).
- IV-G (sintético): documentar o semi-Markov e o jitter; deixar explícito que agora há N seeds.
- Remover a frase sobre o "constant-prediction fallback" (deixa de existir com o treino global).
- Digital twin (R2.1): acrescentar um diagrama de sequência físico ↔ virtual (já existe `sequence_diagram_ twin_control_loop.png` na versão JSAC e dá para reaproveitar) e a classificação de Kritzinger: com fluxo automático bidirecional = *digital twin*; sem retorno = *digital shadow*. Explicar que o fluxo virtual → físico é o comando de reconfiguração da cadência.

### 5.5 Resultados — **A** (reescrita quase completa)
Nova ordem sugerida:
1. Evidência do laço fechado (curta, com a figura de linha do tempo).
2. Classificadores: protocolo A e LOSO, ROC com 6 modelos e IC (R2.4).
3. **Cenários com furto:** tabela por cenário e *pooled* com F1, recall, detecção de episódios, atraso mediano/máx e bytes, para todas as políticas (dense, 15, 20, 25, 30, 40, 60, threshold, adaptive, backfill), média ± IC (R1.1, R1.2, R1.3, R1.4).
4. **Cenários sem furto:** FPR, % do tempo em modos elevados, escalonamentos/semana, bytes (R3.M4).
5. Nível de cliente: TPR/FPR e time-to-first-flag (R3.10).
6. Testes pareados: adaptive × melhor fixo com orçamento equivalente; adaptive × backfill (R1.4).
7. Ablação das fusões, com teste pareado (R1.4 / R3).
8. Pareto: método, frente em validação e o ponto escolhido no teste, envoltória ↔ λ, baselines como pontos (R2.5, R1.2).
9. Escalabilidade: 2 frases, figura no suplemento, sem a narrativa do bug (R3.12).
10. Limitações: atualizar (seed único sai; entram synthetic, feature_mode, BLE, sem HIL etc.).

### 5.6 Conclusão e Data Availability — **B**
- Conclusão alinhada ao novo Abstract, com números com IC e sem extrapolar.
- Data Availability: DOI do Zenodo com dados sintéticos, pseudocódigo, configurações e resultados (R3.14; texto na Seção 3.10). Sem menção ao código no artigo.

### 5.7 Varredura editorial (R2.2, R3.13) — **B**
- [ ] Padronizar "Fig." no meio da frase e "Figure" só no início de frase (ou sempre "Fig.", o padrão IEEE); "Eq. (n)" no meio da frase e "Equation (n)" no início (hoje as linhas 164 e 182 usam os dois).
- [ ] Linha 442: "The mean values in Table~\ref{tab:scenario_breakdown}" deveria ser `tab:agg_policy_results` (o "Table 5 → Table 4" apontado pelo R3).
- [ ] Subtítulos duplicados: "Computational Complexity and Scalability" nas linhas 363 e 507.
- [ ] `\history`/`\doi` (linhas 26-27).
- [ ] Fig. 3 sem `fixed_dense`.
- [ ] Fontes Times New Roman em todas as figuras.
- [ ] Revisar a consistência de nomes (`fixed_short` × "15-min fixed"), siglas definidas uma vez só, unidades (kB × bytes).
- [ ] Atualizar o `\markboth` caso o título mude.

---

## 6. Pontos que **não** dá para atender plenamente agora (e o que seria preciso)

### 6.1 Dados de campo de clientes (sugestão do R3) — ❌ nesta fase; ✅ dados sintéticos aprimorados

**Decisão:** dados de clientes da distribuidora **não entram nesta ressubmissão**, nem como fatia anonimizada nem como estatísticas agregadas.

**Justificativa (para a carta-resposta):** as análises dos dispositivos reais instalados em campo ainda estão em andamento, assim como seus desdobramentos. Publicar agora um recorte parcial anteciparia resultados ainda não consolidados e poderia interferir nesses processos. Os dados também estão sujeitos a acordos de confidencialidade com a distribuidora e à LGPD. A avaliação em campo do laço adaptativo é a próxima etapa do projeto e será relatada num trabalho próprio, quando a análise estiver concluída.

**Sugestão de redação na carta (EN):**
> *"We fully agree that field data would strengthen the evaluation. The field installations of the forensic device are still under analysis within the utility R&D project, and their outcomes have not yet been consolidated; releasing a partial subset at this stage would anticipate unconsolidated results and is further constrained by confidentiality agreements and the Brazilian data-protection law (LGPD). For this reason, field data are outside the scope of this revision. To reduce the distance to real operation, we redesigned the data generator as described below [...], and field validation of the adaptive loop is stated as the next step of the project (Section VII)."*

**Como melhorar os dados sintéticos (esforço A no total; cada item é independente):**

| # | Melhoria | O que muda | Por que responde à crítica | Esforço |
|---|---|---|---|---|
| S1 | **Carga de base real e pública** | Usar curvas reais de consumo de datasets abertos (REFIT ou UK-DALE, ambos de alta resolução; agregar para 5 min) como consumo "verdadeiro" de cada cliente sintético, em vez de um perfil paramétrico. **Verificar licença e citar o dataset.** Reescalar a amplitude para níveis típicos de consumo residencial e comercial no Brasil, usando médias públicas por classe de consumo (ANEEL/EPE) | Tira a crítica de "purely synthetic": a variabilidade, a sazonalidade diária e os picos passam a ser de consumo real | M/A |
| S2 | **Ataques segundo a taxonomia da literatura** | Implementar as famílias de ataque de Jokar et al. (2016), sugerida pelo próprio R3: redução por fator constante, redução por fator variável no tempo, corte total em janelas, substituição pela média, inversão do perfil etc. Mapear cada uma para uma fraude física: desvio parcial, desvio de fase, carga agendada, *bypass* intermitente | O gerador passa a se apoiar numa referência aceita, e não em escolhas *ad hoc* | M |
| S3 | **Episódios com duração e início realistas** | Processo liga/desliga semi-Markov (Seção 2.6); início com *jitter* diário; fase de amostragem aleatória (Seção 2.5) | Torna as métricas por episódio (R1.3) fisicamente significativas | B/M |
| S4 | **Desvio por fase em clientes trifásicos** | Modelar clientes trifásicos com uma unidade forense por fase e furto em apenas uma ou duas fases | Fraude realista em clientes de maior consumo; dá uma dimensão a mais à avaliação | M |
| S5 | **Frota heterogênea com baixa prevalência** | Gerar N clientes (por exemplo 500 a 1.000 cliente-semanas), cada um com parâmetros sorteados (nível de carga, tipo de ataque, severidade de 5% a 60%, horários). Prevalência de furto baixa (por exemplo 5% a 10%), como numa população real | Torna a FPR e a métrica por cliente (R3.M4, R3.10) significativas; o LOSO passa a testar "tipo de ataque", e não "horário fixo" (Seção 6.5) | M |
| S6 | **Ruído metrológico fundamentado em normas** | Ruído do medidor de faturamento pela classe de exatidão normativa (IEC 62053-21/-22, classes 1 e 2) e do dispositivo forense por uma classe melhor; resolução de registrador; **desalinhamento de relógio** entre as duas séries (± alguns minutos) | Os parâmetros deixam de ser arbitrários (hoje 1,2%), e as tolerâncias explicam por que divergências pequenas não disparam alerta | B |
| S7 | **Perturbações legítimas mais ricas** | Geração distribuída (fluxo reverso de fotovoltaica), partida de motores, ar-condicionado, feriados e fins de semana, falta de energia (sem leitura em nenhum dos dois medidores) | Mais cenários de "divergência sem furto", que são exatamente os que geram falsos positivos | M |
| S8 | **Enlace NB-IoT com classes de cobertura** | Sortear a classe de cobertura (CE0/CE1/CE2) por cliente, com taxas de retransmissão e latência da literatura de medições NB-IoT já citada no artigo; quedas de enlace com *store-and-forward* (Seção 3.4) | Liga o custo de comunicação à heterogeneidade real de cobertura | B/M |
| S9 | **Validação do realismo do gerador** | Relatar estatísticas que comparem os dados gerados com os públicos usados (perfil diário médio, autocorrelação, distribuição de potência) e uma tabela com todos os parâmetros do gerador e a fonte de cada um | Mostra ao revisor que o gerador foi calibrado, e não inventado | B |

**Prioridade recomendada:** S3, S5, S6 e S9 (baratos e de alto impacto) → S2 → S1 (o maior ganho de credibilidade, mas o maior esforço) → S4, S7, S8, se houver tempo.

**Cuidado:** S1 e S2 juntos mudam o gerador inteiro. Manter o gerador antigo como "cenários controlados" (um teste unitário do comportamento do gêmeo, com 7 cenários interpretáveis) e usar o novo como **avaliação principal** de frota. Isso também preserva a continuidade com a versão submetida.

### 6.2 Sincronização física bidirecional real (R2.1 pergunta sobre "interação físico ↔ virtual") — 🟡
**Por quê:** o laço hoje fecha com `MockForensicDevice` e `MockTransport`.
**O que seria necessário (opcional, mas muito forte):** um **experimento de bancada em malha fechada** (*hardware-in-the-loop*) em que o gêmeo digital comanda um dispositivo forense real por NB-IoT. Esforço **A** (cerca de 1 a 2 semanas, contando a preparação). Detalhes abaixo para você avaliar a viabilidade.

#### 6.2.1 O que é preciso (checklist de viabilidade)

| Item | Para quê | Observação |
|---|---|---|
| 1 dispositivo forense (versão atual) | Equipamento sob teste | Uma unidade basta. Duas permitem rodar ao mesmo tempo uma política fixa e a adaptativa |
| SIM/eSIM NB-IoT ativo, com APN do projeto | Enlace real | É preciso acesso aos contadores do modem ou a um relatório de tráfego da operadora (CDR) para medir bytes reais |
| Back-office / broker MQTT acessível pelo gêmeo | Fechar o laço | O gêmeo (Python) assina a telemetria e publica comandos. É preciso um adaptador entre `TwinObservation` e as mensagens DLMS/COSEM |
| Cliente DLMS/COSEM capaz de **escrever o período de captura e o de envio** | Comando de cadência (basal / moderate / aggressive) | Confirmar quais objetos OBIS controlam a captura e o envio e se a escrita remota funciona com o dispositivo em operação |
| Leitura sob demanda da memória de massa | Testar o *backfill* (R3.M5) | Medir bytes e tempo para recuperar H horas de perfil |
| Um **medidor de faturamento** comum (ou o medidor padrão do laboratório fazendo esse papel) | Gerar a série de faturamento | Precisa ter memória de massa com intervalos, ou ser lido com a mesma granularidade |
| Fonte e banco de cargas programável (resistivo, com partes comutáveis) | Gerar consumo e eventos | Um relé temporizado ou um CLP liga e desliga cargas segundo um roteiro |
| **Derivação a montante do medidor de faturamento** (passa pelo dispositivo forense, mas não pelo faturamento) | Emular o furto | Ligada por relé segundo o roteiro de episódios (persistente, horário, intermitente). Montagem em bancada, com proteção e procedimento de segurança elétrica |
| Atenuador de RF ou caixa de blindagem (opcional) | Emular cobertura ruim (CE1/CE2) | Para medir retransmissões e latência em enlace degradado |
| Fonte de tempo comum (NTP no back-office; relógio do dispositivo sincronizado) | Alinhar as séries | Necessário para medir latência e o atraso de detecção |
| 24 a 72 h de bancada | Duração do ensaio | Pelo menos um ciclo diário completo para cada roteiro de furto |

**Pré-requisitos: todos confirmados pelo autor.** O comando remoto de cadência vale na amostra seguinte, sem reset; há contador real de bytes; há medidor com memória de massa; a derivação pode ser montada com segurança.

**Protocolo completo do ensaio** (informações necessárias, montagem, fases A a F, roteiro de furto, especificação dos arquivos de dados e cronograma): ver `PROTOCOLO_ENSAIO_BANCADA.md`.

#### 6.2.2 Que informações coletar

| Grupo | Medida | Uso no artigo |
|---|---|---|
| **Custo de comunicação** | Bytes de uplink e downlink por mensagem e por sessão (aplicação e camada de rede); nº de sessões/conexões RRC; bytes por hora em cada modo (basal/moderate/aggressive) | **Valida ou recalibra o modelo de custo** da Seção IV-J (64 B de payload, 40 B de overhead, limiar de 15 min). É o resultado mais valioso |
| **Comando de cadência (gêmeo → dispositivo)** | Latência entre o comando e a confirmação; tempo até a primeira amostra na nova cadência; taxa de sucesso dos comandos; bytes do downlink | Mostra a interação físico ↔ virtual real (R2.1); mede o "tempo de reação" do laço |
| **Telemetria (dispositivo → gêmeo)** | Latência fim a fim por mensagem; perda e duplicação (índice sequencial); *jitter* em relação à cadência programada | Parametriza o simulador com valores medidos |
| **Backfill** | Bytes e tempo para recuperar 1, 6 e 24 h de perfil; número de mensagens | Custo real do baseline do R3.M5 |
| **Enlace** | RSRP, SINR e classe de cobertura (CE); retransmissões; comportamento com o enlace cortado (armazenamento e reenvio) | Valida o modelo de retransmissão e o *store-and-forward* |
| **Detecção ponta a ponta** | Para cada episódio de furto emulado: instante de início (relé), instante do primeiro alerta do gêmeo, modo ativo, bytes gastos | Um gráfico de "traço temporal" real: carga, divergência, risco, modo e bytes ao longo do ensaio. É a figura que responde ao R2.1 |
| **Robustez** | Comportamento em falta de energia e retorno (alarme de *last gasp*); reinício do gêmeo durante o ensaio | Mostra que o laço se recupera |

#### 6.2.3 Como reportar
- Uma subseção curta, "Bench-scale closed-loop validation", com o esquema da montagem, uma tabela de custo medido × modelado e a figura do traço temporal.
- Deixar claro que é uma **demonstração de viabilidade com um dispositivo**, e não uma avaliação estatística: a avaliação estatística continua sendo a de simulação.
- Se os bytes medidos forem diferentes dos do modelo, **recalibrar o modelo** com os valores medidos e rodar a campanha de novo. Isso é ainda mais forte para a resposta.

Se não der tempo, a resposta é textual: diagrama de sequência, classificação de Kritzinger e declaração honesta do escopo (que o R3 elogiou).

### 6.3 "Remover qualquer claim sem ICs não sobrepostos" (R1.4) — 🟡 contra-argumentar
ICs não sobrepostos é um critério conservador demais para comparações **pareadas** (os mesmos seeds em todas as políticas): duas médias podem ter ICs sobrepostos e ainda assim uma diferença pareada claramente significativa. Atender o espírito: reportar o IC da **diferença pareada** e o Wilcoxon com Holm, e qualificar todo claim com p ≥ 0,05. Explicar isso educadamente na resposta.

**Referências para sustentar o argumento (citar na carta e, se couber, na subseção de estatística):**
- **Cumming, G., & Finch, S. (2005). "Inference by eye: Confidence intervals and how to read pictures of data."** *American Psychologist*, 60(2), 170–180. DOI: 10.1037/0003-066X.60.2.170.
  - Grupos independentes: ICs de 95% com sobreposição de até cerca de metade da margem de erro ainda correspondem a p ≈ 0,05.
  - **Medidas repetidas/pareadas:** os ICs das médias individuais não servem para julgar a diferença; deve-se usar o IC da diferença pareada. Esse é o nosso caso (mesmas seeds para todas as políticas).
- **Schenker, N., & Gentleman, J. F. (2001). "On judging the significance of differences by examining the overlap between confidence intervals."** *The American Statistician*, 55(3), 182–186. Demonstração formal de que o critério de não sobreposição é conservador, isto é, tem baixo poder para detectar diferenças reais.
- Os dados bibliográficos foram citados de memória: conferir pelo DOI antes de usar.

### 6.4 "Ajustar uma curva suave à frente de Pareto" (R2.5) — 🟡
A frente empírica é um conjunto discreto de configurações. Uma curva contínua sugere pontos de operação que talvez não existam. Atender com: (i) a envoltória convexa (atingível em valor esperado por *time-sharing* entre configurações, como explicado em 3.7) e (ii) um ajuste monotônico côncavo marcado como "guia visual", justificando na resposta.

### 6.5 LOSO com só 7 cenários
Com 7 cenários, cada um com um padrão temporal próprio, o LOSO vai mostrar degradação forte em alguns cenários (por exemplo, sem nunca ter visto `night_theft`, o modelo pode não generalizar o horário). **Isso é o resultado esperado e deve ser reportado.** O R3 quer justamente saber "quanto sobrevive". Reportar os protocolos A e B lado a lado. Se quiser reforçar: gerar variantes de cenário (janelas de horário sorteadas por cliente) para que o LOSO teste "tipo de fraude" e não "horário".

---

## 7. Decisões que dependem de você (antes de começar o código)

1. **Granularidade (Seção 2.3):** *resolvido.* Os dados chegam em intervalos, a cadência configurada é respeitada e a mudança vale na amostra seguinte, sem reset. As features são calculadas no back-office com as amostras recebidas.
2. **Histerese (Seção 4.4):** manter o desenho atual (janela máxima de 3/2 amostras) e descrevê-lo com exatidão, ou trocar por uma histerese clássica (limiar de descida e dwell **mínimo**)? Trocar é mais defensável, mas muda os resultados; como tudo será rerodado de qualquer forma, o custo é baixo.
3. **Gerador do intermitente:** trocar para semi-Markov (recomendado) ou manter o Bernoulli com definição de episódio por *gap*?
4. **Dados sintéticos aprimorados (6.1):** *já definido* que não haverá dados de clientes. **Falta decidir** quais melhorias S1 a S9 entram (recomendado: S3, S5, S6 e S9, mais S2; S1 se houver tempo).
5. **Bancada em malha fechada (6.2):** *viável; os 4 pré-requisitos foram confirmados.* Próximo passo: enviar as informações I1 a I8 de `PROTOCOLO_ENSAIO_BANCADA.md` para eu preparar o adaptador.
6. **Código aberto:** *resolvido.* Os dados sintéticos, o pseudocódigo e os resultados vão para um depósito público; o código fica disponível só por requisição formal, com a justificativa apenas na carta (Seção 3.10).
7. **Arquivos-fonte das Figs. 1 a 3** (draw.io/Visio)? Se não existirem, elas serão redesenhadas.

---

## 8. Roteiro de execução sugerido

| Fase | Conteúdo | Esforço | Depende de |
|---|---|---|---|
| 0 | `git init` + tag `v1-submission`; respostas às decisões da Seção 7 | B | — |
| 1 | Correções de protocolo (2.1 a 2.3, 2.5, 2.6, 2.8, 2.9) + testes | M | Decisões 1 a 3 |
| 2 | Infraestrutura de frota multi-seed, treino global, LOSO (3.1) | A | Fase 1 |
| 3 | Novos baselines de política, incluindo backfill (3.3), e modelo BLE/store-and-forward (3.4) | M | Fase 2 |
| 4 | Métricas de episódio, cliente e FPR (3.5); estatística (3.6) | M | Fase 2 |
| 5 | Pareto em validação/teste + envoltória/λ (3.7); modelos de ML adicionais (3.8) | M | Fases 2 a 4 |
| 6 | **Rodar a campanha completa → analisar → decidir o enquadramento** (5.3) | M | Fases 3 a 5 |
| 1b | Gerador sintético aprimorado (6.1: S3, S5, S6 e S9 no mínimo) | M/A | Decisão 4 |
| 6a | Bancada em malha fechada (6.2): adaptador → ensaio de 5 a 6 dias → recalibração do modelo de custo. Pode correr em paralelo com as Fases 1 a 5; a campanha final (Fase 6) usa o modelo recalibrado | A | Informações I1 a I8 |
| 6b | (opcional) Carga de base real S1 | A | Decisão 4 |
| 7 | Figuras novas em Times New Roman; redesenho das Figs. 1 e 3 (3.9) | M | Fase 6 |
| 8 | Reescrita do artigo (Seção 5) + varredura editorial (5.7) | A | Fase 6 |
| 9 | Depósito no Zenodo: dados sintéticos, splits, configurações, pseudocódigo e resultados, com DOI (3.10) | M | Fase 6 |
| 10 | **Response to Reviewers** (preocupação → resposta → ação, item a item, citando seção e linha) + **Highlighted PDF** (todas as mudanças em amarelo, inclusive as gramaticais) + manuscrito limpo (LaTeX e PDF) | M | Fase 8 |

**Estimativa total:** cerca de 6 a 8 semanas com o gerador aprimorado (1b) e a bancada (6a) correndo em paralelo; cerca de 8 a 10 semanas se incluir também a carga de base real (6b).

### Checklist de entrega (exigido pela carta)
- [ ] Response to reviewers no template do IEEE Access (a) preocupação, (b) resposta, (c) ação, para **cada** item das listas acima (R1: 5; R2: 5; R3: 6 major + 9 minor)
- [ ] Highlighted PDF com todas as mudanças em amarelo
- [ ] Manuscrito limpo em LaTeX + PDF
- [ ] Sem mudança na lista de autores (se houver, é preciso o formulário de byline change)
- [ ] Conferir o "Resubmission Checklist" anexo ao e-mail (não está na pasta; vale salvar junto)

---

## 9. Evidências numéricas úteis para a carta-resposta

- Adaptativo × denso nos cenários com furto (resultado atual, seed único): 58.186 × 135.162 B = **43% do volume (−57%)**, como apontado pelos R1 e R3. Reconhecer.
- `persistent_theft`: o custo do adaptativo é igual ao do denso (135.332 B) porque o classificador por cenário é constante = 1 (2.1).
- Cenários sem furto: o aggressive é inalcançável (fusão ≤ 0,594 < 0,60) por causa do classificador constante = 0 (2.1). Esse é o motivo dos 17.736 B.
- A discrepância VI-F × Tabela 5 vem de seeds diferentes (2.4). `peak_theft` com a mesma configuração: F1 0,985 (seed 42) × 0,916 (seed 44).
- Critical-slot: os cenários sem furto contam como acerto (1,0); nos 4 cenários com furto, o hit binário do adaptativo é 1/4 (2.7).
- Primeira amostra basal coincide com o início do furto (18:00:00), por alinhamento de fase (2.5). Corrigido proativamente; mencionar na resposta como melhoria adicional mostra rigor.
