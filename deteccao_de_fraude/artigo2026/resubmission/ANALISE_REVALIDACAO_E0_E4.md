# Análise da revalidação E0 → E4 (protocolo corrigido × submissão original)

**Branch:** `revalidacao-e0-e4` (a partir do commit `7c99f86`, marcado com a tag `v1-submission`)
**Execução:** 5 estágios × 7 cenários × 30 realizações independentes (seeds), mais 10 realizações de treino por cenário para o modelo global. Cada valor é média de 30 realizações; os colchetes são IC 95% por bootstrap.
**Tabelas completas geradas automaticamente:** `revalidacao_E0_E4_tabelas_completas.md` (nesta pasta) e `outputs/revalidation/` (CSVs por estágio).

---

## 1. Resumo executivo

1. **A implementação reproduz exatamente a submissão.** No estágio E0, a réplica 0 (mesmas seeds do artigo) gera os mesmos 14 números da Tabela 5 (F1, recall e bytes de `fixed_dense` e `adaptive` em todos os cenários). Isso garante que as diferenças abaixo vêm só das correções.
2. **Os resultados pioraram de forma gradual, sem colapsar.** Com todas as correções (E4), a média de F1 do adaptativo nos 4 cenários com furto cai de **0,8819 → 0,8072** (−8,5%) e a recall de **0,8272 → 0,7471**. A fração de bytes em relação ao denso fica praticamente igual: **43,0% → 41,2%**. A manchete do artigo ("~91% do F1 e ~83% da recall com ~30% dos bytes") passa a **83,5% do F1 e 76,1% da recall com 28,5% dos bytes** na mesma métrica de 7 cenários.
3. **As maiores perdas vêm do E3 (fase aleatória de amostragem) e do E4 (features só com amostras recebidas).** O treino global (E1) e a correção do `slot_recurrence` (E2) custaram pouco.
4. **Boa notícia para o R3.M4:** mesmo com o modelo único entre cenários, os cenários sem furto quase não geram alarmes falsos. São menos de 1 falso positivo por semana e cerca de 0,1% do tempo em modo elevado, e o custo continua sendo o do modo basal (~17,3 kB por semana).
5. **Achado crítico, novo:** nas métricas **por episódio** (R1.3), o adaptativo **não supera** uma cadência fixa com orçamento equivalente ou menor. No E4, o `fixed_30` gasta 37% menos bytes que o adaptativo e detecta mais episódios (78,6% × 71,6%), com atraso médio 9 minutos menor. A vantagem do adaptativo aparece na **cobertura da evidência**: depois que detecta, documenta densamente o furto (recall por tick 0,91 × 0,16 do `fixed_30`). É uma vantagem real, mas é outra contribuição. Isso muda o enquadramento do artigo (Seção 6).
6. **A ablação das fusões muda de conclusão.** Com o protocolo corrigido (E3/E4), `conservative_max` empata com `weighted` em F1 e tem recall e detecção de episódios maiores, com +2% de bytes. A afirmação do artigo de que `conservative_max` é "dominado" deixa de valer.

**Veredito:** o resultado não ficou "muito pior" no que o artigo media (F1 e recall por instante). Ficou **mais fraco e mais honesto**. A comparação com orçamento equivalente por episódio, porém, mostra que o argumento central precisa mudar de "detectar com menos bytes" para "detectar e **documentar** o furto com menos bytes". Isso torna o *backfill* (R3.M5) e o ajuste do período basal as próximas prioridades.

---

## 2. O que foi implementado

| Arquivo | Mudança | Comportamento padrão |
|---|---|---|
| `src/fraud_dt/synthetic.py` | Gerador em memória (`generate_synthetic_frames`) e *jitter* diário do início do furto (`onset_jitter`), num fluxo aleatório separado | Desligado: gera exatamente os dados da v1 (verificado bit a bit) |
| `src/fraud_dt/features.py` | `slot_recurrence` causal (`fix_slot_recurrence`); recomputação das features só com amostras recebidas (lote e `OnlineFeatureState` para o laço) | Desligado: cálculo da v1 |
| `src/fraud_dt/risk.py` | `FrozenSupervisedModel` (regressão logística treinada uma vez com todos os cenários e congelada); pontuação das regras por amostra | Pipeline original intocado |
| `src/fraud_dt/runtime/simulator.py` | Ganchos opcionais `first_emit_time` (fase de amostragem) e `online_scorer` (features em tempo real) | Desligados: laço da v1 |
| `src/fraud_dt/revalidation.py` (novo) | Definição dos estágios, execução por realização, métricas por episódio, agregações, testes pareados | — |
| `scripts/run_revalidation_ladder.py` (novo) | Executa a escada, grava CSVs por estágio e o resumo em Markdown | — |
| `tests/test_revalidation.py` (novo) | 7 testes, entre eles: gerador em memória = gerador em CSV; *jitter* desligado reproduz a v1; `slot_recurrence` sem dados futuros; features em tempo real = recomputação em lote; seeds de treino e de teste disjuntas; **E0 réplica 0 reproduz a Tabela 5 do artigo** | — |

Todos os 24 testes passam (17 antigos e 7 novos). O pipeline original (`run_pipeline`, `run_experiment_campaign.py`) continua produzindo os resultados da v1.

**Como reproduzir:**
```powershell
.\.venv\Scripts\python.exe scripts\run_revalidation_ladder.py --stages E0 E1 E2 E3 E4 --replicates 30 --train-replicates 10
```
Leva cerca de 5 minutos em 21 núcleos. As seeds seguem regras fixas: teste = `42 + índice_do_cenário + 100 × réplica` (a réplica 0 é a do artigo); treino = `50000 + 1000 × índice + réplica`.

**Novidades medidas em todos os estágios, que não existiam na v1:**
- cadências fixas de 20, 25, 30 e 40 min (orçamento equivalente, R1.2);
- o mesmo detector do adaptativo (fusão `weighted`) aplicado às políticas fixas, para uma comparação justa;
- métricas por episódio (R1.3);
- taxa de falsos positivos e tempo em modo elevado nos cenários sem furto (R3.M4);
- métricas agregadas nos cenários com furto (R3.8);
- testes pareados de Wilcoxon com correção de Holm (R1.4).

---

## 3. Os estágios e o que cada um ataca

| Estágio | Mudança (cumulativa) | Por que | Revisores |
|---|---|---|---|
| **E0** | Protocolo da v1, mas com 30 seeds por cenário | Mede a variabilidade que o artigo não mostrava | R1.4, R3.M3, R1.1b |
| **E1** | Um único modelo supervisionado, treinado com realizações de treino de todos os cenários, congelado e avaliado só em realizações nunca vistas (semana inteira) | Um gêmeo implantado não sabe em que cenário está; na v1 o modelo era treinado por cenário e as métricas incluíam o trecho de treino | R3.M1, R3.M2, R1.5 |
| **E2** | `slot_recurrence` causal | A v1 vazava informação futura em ~24 linhas por semana | R1.5 (protocolo explícito) |
| **E3** | Fase de amostragem aleatória por realização (igual para todas as políticas) e início do furto deslocado de 0 a 55 min por dia | Na v1, a amostragem basal (a cada 60 min, na hora cheia) coincidia exatamente com o início do furto (18:00, 00:00), o que favorecia o adaptativo | Validade interna (não apontado pelos revisores, mas seria um risco na próxima rodada) |
| **E4** | Features de histórico calculadas só com as amostras que chegam ao back-office | O dispositivo é independente do medidor de faturamento, então a divergência só existe no back-office; na v1 a amostra basal "enxergava" os 11 ticks não transmitidos | R1.5 |

---

## 4. Comparação com a submissão, tabela a tabela

### 4.1 Tabela 4 do artigo (médias dos 7 cenários, sem furto = 0)

| | F1 adaptativo | F1 denso | Retenção de F1 | Retenção de recall | Bytes adaptativo | Bytes denso | Fração de bytes |
|---|---|---|---|---|---|---|---|
| **Artigo (v1)** | 0,5039 | 0,5545 | 90,9% | 82,9% | 40.646 | 137.835 | 29,5% |
| E0 | 0,5010 | 0,5540 | 90,4% | 83,0% | 40.255 | 137.892 | 29,2% |
| E1 | 0,4957 | 0,5561 | 89,1% | 82,9% | 40.062 | 137.892 | 29,1% |
| E2 | 0,4944 | 0,5555 | 89,0% | 82,7% | 39.889 | 137.892 | 28,9% |
| E3 | 0,4776 | 0,5525 | 86,4% | 78,2% | 39.452 | 137.894 | 28,6% |
| **E4** | **0,4613** | **0,5525** | **83,5%** | **76,1%** | **39.300** | **137.894** | **28,5%** |

**Leitura:** a manchete enfraquece cerca de 7 pontos percentuais em F1 e 7 em recall, e a economia de bytes se mantém. Os revisores já pediram que essa métrica de 7 cenários com zeros saia do Resumo (R1.1a, R3.8). Ela fica aqui só para comparar com o artigo.

### 4.2 Tabela 5 do artigo (média dos 4 cenários com furto)

| | F1 adaptativo | Recall adaptativo | F1 denso | Recall denso | Bytes adaptativo | Bytes denso | Fração |
|---|---|---|---|---|---|---|---|
| **Artigo (v1)** | 0,8819 | 0,8272 | 0,9703 | 0,9984 | 58.186 | 135.162 | 43,0% |
| E0 | 0,8767 [0,8720; 0,8811] | 0,8278 | 0,9694 | 0,9971 | 57.552 | 135.340 | 42,5% |
| E1 | 0,8674 [0,8619; 0,8726] | 0,8155 | 0,9732 | 0,9840 | 57.160 | 135.340 | 42,2% |
| E2 | 0,8652 [0,8608; 0,8695] | 0,8128 | 0,9722 | 0,9832 | 56.857 | 135.340 | 42,0% |
| E3 | 0,8358 [0,8310; 0,8409] | 0,7672 | 0,9670 | 0,9813 | 56.122 | 135.344 | 41,5% |
| **E4** | **0,8072 [0,7994; 0,8153]** | **0,7471** | **0,9670** | **0,9813** | **55.827** | **135.344** | **41,2%** |

**Por cenário (Tabela 5 do artigo × E4):**

| Cenário | F1 adapt. v1 | F1 adapt. E4 | Recall adapt. v1 | Recall adapt. E4 | Bytes adapt. v1 | Bytes adapt. E4 | F1 denso v1 | F1 denso E4 |
|---|---|---|---|---|---|---|---|---|
| persistent_theft | 1,0000 | 0,9913 | 1,0000 | 0,9829 | 135.332 | 133.251 | 1,0000 | 0,9995 |
| peak_theft | 0,9159 | 0,9036 | 0,8625 | 0,8588 | 30.324 | 31.831 | 0,9264 | 0,9701 |
| night_theft | 0,9928 | 0,9160 | 0,9881 | 0,8618 | 41.884 | 35.632 | 0,9976 | 0,9804 |
| intermittent_evening | 0,6189 | **0,4179** | 0,4581 | **0,2849** | 25.204 | 22.594 | 0,9572 | 0,9178 |
| normal | 0 | 0 | 0 | 0 | 17.736 | 17.701 | 0 | 0 |
| disturbance_without_theft | 0 | 0 | 0 | 0 | 17.736 | 17.733 | 0 | 0 |
| degraded_link_no_theft | 0 | 0 | 0 | 0 | 16.304 | 16.360 | 0 | 0 |

### 4.3 Tabela 6 do artigo (ablação das fusões, média dos 7 cenários)

| | weighted F1 / bytes | conservative_max F1 / bytes | context_aware F1 / bytes |
|---|---|---|---|
| **Artigo (v1)** | 0,5039 / 40.646 | 0,4828 / 41.105 | 0,4714 / 37.622 |
| E0 | 0,5010 / 40.255 | 0,4839 / 40.715 | 0,4691 / 37.423 |
| E2 | 0,4944 / 39.889 | 0,4854 / 40.390 | 0,4651 / 37.137 |
| E3 | 0,4776 / 39.452 | **0,4808** / 40.278 | 0,4510 / 36.823 |
| **E4** | 0,4613 / 39.300 | **0,4673** / 40.034 | 0,4330 / 36.594 |

Nos cenários com furto agregados (E4), `weighted` tem F1 0,9482 [0,9461; 0,9504] e `conservative_max` 0,9490 [0,9471; 0,9508]: empate estatístico. Mas `conservative_max` tem recall maior (0,927 × 0,911) e gasta 2% mais bytes.

---

## 5. Análise estágio a estágio

### E0: várias seeds com o protocolo da v1
- **O que aconteceu:** a média de 30 realizações (F1 0,8767 nos 4 cenários com furto) fica um pouco abaixo do valor do artigo (0,8819). O valor do artigo está no limite superior do IC, ou seja, a seed usada era ligeiramente favorável, mas representativa.
- **Variabilidade por cenário (adaptativo):** `peak_theft` F1 de 0,9585 [0,9476; 0,9686]; `intermittent_evening` de 0,5767 [0,5606; 0,5925]. A variação entre seeds é da mesma ordem das diferenças que o artigo interpretava (por exemplo, 0,869 × 0,878 na Seção VI-F). Isso confirma a crítica do R1.4/R3.M3.
- **Por que:** cada seed sorteia dias sem furto, perfis de fraude e ruídos diferentes.
- **Revisores:** R1.4 e R3.M3 (várias seeds e IC), R1.1b (a discrepância VI-F × Tabela 5 era um efeito de seed).

### E1: modelo global congelado, avaliado em realizações não vistas
- **O que aconteceu:**
  - O F1 do adaptativo nos cenários com furto caiu pouco: 0,8767 → 0,8674 (−0,009).
  - Em `persistent_theft` o F1 deixou de ser exatamente 1,0 (0,9979), porque o modelo não é mais um preditor constante "sempre furto".
  - Nos cenários sem furto surgem alarmes falsos, mas raros: FPR de 0,01% e 0,27 falso positivo por semana no adaptativo, contra 3,5 por semana no denso; tempo em modo elevado de 0,1%.
  - O denso perdeu recall no `intermittent_evening` (0,993 → 0,947), porque o modelo deixou de ser ajustado àquele cenário.
- **Por que caiu pouco:** a divergência elétrica é um sinal forte e genérico, e o modelo global aprende com ela sem precisar saber o cenário. A AUROC do classificador nas semanas de teste continua entre 0,997 e 0,9999.
- **Melhorou ou piorou:** piorou levemente na detecção, mas o protocolo agora é defensável. O temor do plano (muitos escalonamentos falsos nos cenários sem furto) **não se confirmou**, o que é um bom resultado para a carta.
- **Revisores:** R3.M1 (modelo único entre cenários), R3.M2 e R1.5 (métricas só em dados não vistos), R3.M4 (passa a existir FPR medível nos cenários sem furto).

### E2: `slot_recurrence` causal
- **O que aconteceu:** variação desprezível (F1 de 0,8674 → 0,8652, dentro do IC).
- **Por que:** o vazamento afetava só a primeira amostra de cada hora (24 de 2016 por semana), e a feature tem peso pequeno no modelo.
- **Melhorou ou piorou:** neutro. Corrige um vazamento que um revisor de reprodutibilidade encontraria no código.
- **Revisores:** R1.5 (protocolo correto e explícito).

### E3: fase de amostragem aleatória e *jitter* no início do furto
- **O que aconteceu:** a segunda maior queda. F1 0,8652 → 0,8358 e recall 0,8128 → 0,7672. Nos cenários com horário fixo a queda é clara:
  - `peak_theft`: recall de 0,939 → 0,848;
  - `night_theft`: recall de 0,926 → 0,856.

  O atraso médio por episódio dobrou (12,4 → 24,8 min).
- **Por que:** na v1, o modo basal amostrava exatamente às 18:00 e às 00:00, os mesmos instantes em que o furto começava. A primeira amostra basal sempre "pegava" o início do furto. Com a fase aleatória, a espera média até a primeira amostra basal passa a ser de cerca de 30 min, como seria na prática.
- **Melhorou ou piorou:** piorou, porque a v1 tinha uma vantagem artificial. É a correção mais importante para a validade interna, mesmo sem ter sido pedida.
- **Revisores:** nenhum pedido direto. Antecipa uma crítica provável e reforça a honestidade das métricas por episódio (R1.3).

### E4: features só com as amostras recebidas no back-office
- **O que aconteceu:** F1 0,8358 → 0,8072. A queda está concentrada no `intermittent_evening`: F1 de 0,527 → 0,418, recall de 0,381 → 0,285 e tempo em modo elevado de 11,1% → 7,3%. Nos demais cenários com furto a variação ficou dentro do IC. Nos sem furto, os falsos positivos subiram um pouco (0,57 → 0,91 por semana).
- **Por que:** em modo basal o back-office recebe uma amostra por hora. A média móvel de 60 min e a recorrência horária ficam baseadas em uma ou duas amostras, e a divergência de um único instante decide sozinha. Num furto intermitente, a amostra basal cai muitas vezes num intervalo "desligado", e o gêmeo demora mais a escalar.
- **Melhorou ou piorou:** piorou, mas agora reflete o que o sistema real consegue fazer, já que o dispositivo não tem acesso ao medidor de faturamento.
- **Revisores:** R1.5 (como as features rolantes são calculadas em modo basal).

---

## 6. Achado crítico: comparação com orçamento equivalente e por episódio

### 6.1 Por instante, o adaptativo "vence" qualquer cadência fixa, mas a métrica é enviesada

Com o mesmo detector, o adaptativo tem F1 por instante entre 0,46 e 0,82 maior que qualquer cadência fixa (p < 10⁻⁸). Esse ganho, porém, é **estrutural**: a recall por instante de uma política fixa é limitada pela fração de amostragem (o `fixed_30` vê 1 de cada 6 ticks e não passa de ~16%). O adaptativo amostra a cada 5 min justamente durante o furto. É exatamente a crítica do **R1.3**: a recall por instante mede densidade de amostragem, não capacidade de detecção.

### 6.2 Por episódio, o adaptativo não supera cadências fixas mais baratas (E4)

| Política (mesmo detector) | Bytes/cenário | Episódios detectados | Atraso médio (min) | Furto não detectado (min/semana) |
|---|---|---|---|---|
| fixed_dense (5 min) | 135.344 | 98,7% | 1,1 | 10 |
| **adaptive (weighted)** | **55.827** | **71,6%** | **29,3** | **261** |
| fixed_20 | 52.890 | 84,0% | 14,3 | 133 |
| fixed_short (15 min) | 46.352 | 89,5% | 10,6 | 96 |
| fixed_25 | 42.207 | 81,9% | 17,8 | 157 |
| fixed_30 | 35.260 | 78,6% | 20,0 | 183 |
| fixed_40 | 26.539 | 71,6% | 25,0 | 233 |
| fixed_long (60 min) | 17.672 | 68,9% | 32,8 | 290 |

(Arquivo `outputs/revalidation/E4/theft_pooled.csv`, fonte `fused_weighted_probability` para as fixas. Diferença pareada de atraso adaptativo − fixed_30: +9,3 min [7,0; 11,7], p de Holm = 1×10⁻⁷. O `fixed_short` não aparece entre os "mais próximos em bytes" das tabelas automáticas, mas gasta 17% menos que o adaptativo e detecta 18 pontos percentuais a mais de episódios. A detecção pela cadência de 15 min supera a da de 20 min porque, no gerador da v1, os episódios intermitentes são curtos.)

Por cenário (E4, adaptativo × `fixed_30`, que gastam bytes parecidos em `peak` e `night`):

| Cenário | Episódios detectados (adapt. / fixed_30) | Atraso médio (adapt. / fixed_30) | Bytes (adapt. / fixed_30) |
|---|---|---|---|
| peak_theft | 100% / 100% | 29,8 / 18,0 min | 31.831 / 35.271 |
| night_theft | 100% / 100% | 34,5 / 17,8 min | 35.632 / 35.267 |
| intermittent_evening | 54,9% / 66,1% | 26,3 / 21,5 min | 22.594 / 35.256 |
| persistent_theft | 100% / 100% | 31,5 / 19,5 min | **133.251** / 35.243 |

**Interpretação:**
- O que determina a **detecção e o atraso** é a cadência *antes* do alerta. O adaptativo fica em basal (60 min) até detectar, então detecta como o `fixed_long`. O ganho dele vem só **depois** da detecção.
- O que o adaptativo entrega e as fixas não entregam é a **cobertura da evidência**: depois do alerta, ele documenta ~91% dos instantes de furto (recall por instante), contra 16% a 25% das fixas de custo parecido. Em contexto forense isso tem valor próprio, porque é a evidência do furto que sustenta o processo de recuperação de receita.
- No `persistent_theft` o adaptativo gasta o mesmo que o denso (sem economia), porque não há regra para "já documentei o bastante". É o ponto já levantado pelo R1.1.
- Em E0–E2 (protocolo da v1), `fixed_25` e `fixed_40` já empatavam com o adaptativo no atraso e na detecção de episódios a um custo menor. A diferença só não aparecia porque o artigo não media episódios.

### 6.3 Consequências para o artigo
1. **Reenquadrar a contribuição:** o resultado defensável não é "o adaptativo detecta como o denso com 30% dos bytes", e sim "o adaptativo alcança **cobertura de evidência** próxima à do denso com ~41% dos bytes, mantendo falsos alarmes desprezíveis nos cenários sem furto". O atraso de detecção deve ser assumido como o custo: ele é governado pelo período basal.
2. **Tornar o período basal um parâmetro do Pareto** (por exemplo, basal de 20, 30, 40 e 60 min). Um adaptativo com basal de 30 min deve igualar o `fixed_30` no atraso e manter a cobertura densa depois do alerta, com custo intermediário.
3. **Implementar o *backfill* (R3.M5) como próxima prioridade.** Ele ataca exatamente a fraqueza encontrada: ao detectar, o dispositivo envia o histórico de 5 min guardado na memória de massa, recuperando a evidência do início do episódio sem aumentar o custo antes do alerta. Isso pode tornar o adaptativo com backfill dominante tanto em cobertura quanto em custo.
4. **Teto de evidência** (`adaptive_evidence_cap`): depois de K horas de furto documentado, voltar para o modo moderado, resolvendo o custo do `persistent_theft`.
5. **Reportar as métricas por episódio como métrica principal** (R1.3) e a recall por instante como "cobertura da evidência", explicando a diferença.

---

## 7. Mapa: pedido do revisor → evidência produzida

| Pedido | Evidência nesta revalidação | Situação |
|---|---|---|
| R1.1a e R3.8 (números dos cenários com furto, faixas e redução de ~57%) | Tabelas 4.2 (média dos 4), agregado e por cenário com IC; redução de bytes nos cenários com furto: 58,8% (E4) | Pronto para o texto |
| R1.1b (discrepância VI-F × Tabela 5) | E0: variação entre seeds da mesma ordem da discrepância | Explicado |
| R1.2 (baselines com orçamento equivalente) | Cadências de 20, 25, 30 e 40 min com o mesmo detector; testes pareados | Feito, mas o resultado exige reenquadrar (Seção 6) |
| R1.2 (adaptativo simples sem aprendizado) | **Ainda não implementado** (`threshold_escalation`) | Pendente |
| R1.3 (métricas por episódio) | Detecção, atraso médio e máximo, minutos não detectados | Feito; o gerador intermitente ainda é Bernoulli por tick (episódios unidos por *gap* ≤ 15 min) |
| R1.4 e R3.M3 (várias seeds, IC, teste pareado) | 30 seeds, bootstrap, Wilcoxon com Holm | Feito |
| R1.5 (protocolo explícito) | E1, E2 e E4 implementam e documentam cada ponto | Feito (falta redigir) |
| R3.M1 (modelo único, avaliação em cenários não vistos) | Modelo global em realizações não vistas (E1) | Feito; **LOSO ainda pendente** |
| R3.M2 (métricas só em dados não vistos) | E1 em diante | Feito |
| R3.M4 (FPR e tempo elevado sem furto) | FPR ≤ 0,07%, < 1 falso positivo por semana, ~0,1% do tempo elevado | Feito; resultado favorável |
| R3.M5 (backfill) | — | Pendente, e agora prioritário |
| R3.M6 (BLE) | — | Pendente (o custo do BLE continua no modelo) |
| R3.9 (critical-slot) | Métrica não calculada na escada; substituída pelo atraso por episódio | Decisão tomada |

---

## 8. Limitações desta revalidação

- O **gerador continua o da v1** (furto intermitente sorteado a cada tick, perfil de carga paramétrico). Os episódios do `intermittent_evening` são fragmentos unidos por *gap* ≤ 15 min (~23 por semana). Com o gerador semi-Markov (plano, item S3), os números por episódio desse cenário vão mudar.
- **Os limiares (α = 0,6; 0,30/0,60) não foram reajustados** no protocolo novo. O Pareto precisa ser refeito em seeds de validação, com o período basal como parâmetro.
- **O LOSO não foi rodado.** O E1 usa um modelo global avaliado em realizações novas dos mesmos 7 cenários (protocolo A do plano).
- **O custo de comunicação ainda usa o modelo da v1** (BLE barato, sem *store-and-forward*). O ensaio de bancada vai recalibrar esse modelo.
- A **AUROC do classificador continua muito alta** (> 0,997). O problema de classificação é fácil nos dados sintéticos, e um revisor pode notar. As melhorias do gerador (S1, S2, S5, S7) devem torná-lo mais realista.

## 9. Próximos passos sugeridos (em ordem)

1. Backfill (`adaptive_backfill` e `fixed_sparse_backfill`) e teto de evidência, medidos no protocolo E4.
2. Período basal como parâmetro (20, 30, 40, 60 min) e Pareto refeito em seeds de validação, reportado nas de teste, com custo e atraso como eixos.
3. Baseline sem aprendizado (`threshold_escalation`) e LOSO.
4. Gerador semi-Markov para o intermitente; depois, as demais melhorias do gerador.
5. Modelo de transporte com *store-and-forward*, recalibrado com a bancada.

As mudanças estão no branch `revalidacao-e0-e4` e **ainda não foram commitadas**.
