# Análise da Fase A: backfill, período basal e teto de evidência

**Branch:** `fase-a-backfill-basal-cap` (a partir de `revalidacao-e0-e4`)
**Estágio:** E5 = protocolo E4 (o mais realista: modelo global, realizações não vistas, fase aleatória, features só com as amostras recebidas) mais as novas políticas. 7 cenários × 30 realizações.
**Tabelas completas:** `fase_a_tabelas_completas.md` (nesta pasta) e `outputs/revalidation/E5/` (`phase_a_summary.csv`, `phase_a_paired.csv`, `runs.csv`).

---

## 1. Resumo executivo

1. **O período basal define a detecção; o adaptativo define a evidência.** Com o mesmo período basal, o adaptativo detecta os mesmos episódios, com o mesmo atraso, que uma cadência fixa daquele período (diferenças não significativas). O que ele acrescenta é **evidência**: documenta de 3 a 11 vezes mais instantes de furto.
2. **Resultado principal:** o adaptativo com basal de 15 min (`adaptive_b15`), comparado ao `fixed_short` (15 min):
   - detecta os mesmos episódios em tempo real (88,9% × 89,5%) com o mesmo atraso (11,2 × 10,6 min, p = 0,25);
   - documenta 94,6% dos instantes de furto, contra 32,9%;
   - custa **+2,9% de bytes na frota** com 5% de clientes com furto (+5,9% com 10%).

   Ele também **supera o `fixed_20` em todos os eixos**: mais barato na frota (−1,3%), detecta mais episódios (+4,9 pontos), com menor atraso (−3,1 min) e 3,9 vezes mais evidência.
3. **Backfill (R3.M5):** eleva a cobertura de evidência para 98–99% e passa a documentar mais episódios (por exemplo, 89,1% contra 80,1% com basal de 30 min). Mas os episódios extras são documentados **depois** que terminam: o atraso de detecção em tempo real não melhora. Custa +7% a +12% na frota.
4. **O baseline do revisor 3** ("registra denso, envia esparso, recupera no alerta" = `fixed_60_bf`) alcança 93,9% de evidência, perto do adaptativo, com custo de frota semelhante ao `adaptive_b60_bf`. A detecção dele é igual à do `fixed_long`. **Conclusão honesta:** o ganho de evidência pode vir da densificação em tempo real (adaptativo) ou do backfill. A vantagem do adaptativo está em ter a evidência **no momento** do alerta, com menos alarmes falsos (0,91 × 1,07 por semana) e sem depender de que o dispositivo continue íntegro para entregar o histórico.
5. **O teto de evidência resolve o custo do `persistent_theft`** (133 kB → 48 kB por semana nesse cenário), mas derruba a cobertura nos furtos de horário (pico: 86% → 64%) quando fixado em 2 h. Do jeito que está, não compensa como política padrão.
6. **Custo da frota:** como a maioria das instalações não tem furto, o custo da frota é dominado pelo período basal. O adaptativo só gasta mais onde há risco.

**Nova tese que os resultados sustentam:**
> Com o mesmo custo de frota (+3%) e a mesma detecção de uma cadência fixa, o gêmeo digital multiplica por cerca de 3 a evidência forense coletada em tempo real; o atraso de detecção é um parâmetro escolhido pela distribuidora (o período basal), não uma propriedade do método.

---

## 2. O que foi implementado

| Componente | Arquivo | Descrição |
|---|---|---|
| Backfill | `revalidation.py` (`run_variant`, `BackfillCostModel`) | A cada amostra sinalizada, o back-office pede ao dispositivo os registros de 5 min ainda não recebidos, até 2 h para trás (a janela inteira no início do alerta e as lacunas depois). As amostras recuperadas são pontuadas pelo back-office com as features calculadas sobre tudo o que foi recebido. Cada uma guarda o instante em que chegou (`known_at`), para que o atraso conte a partir da chegada |
| Custo do backfill | `BackfillCostModel` | Hipótese conservadora a calibrar na bancada: 64 B por registro (igual a uma amostra ao vivo), 16 registros por mensagem, sessão já aberta (sem RRC extra), retransmissão com probabilidade nominal. Sensibilidade: registros de 32 B |
| Período basal | `PhaseAVariant.basal_minutes` | Basal de 15, 20, 30, 40 e 60 min; moderado (15) e agressivo (5) inalterados |
| Teto de evidência | `control/orchestrator.py` (`EvidenceCapOrchestrator`) | Após 120 min contínuos em modo agressivo, cai para moderado até o risco voltar ao basal |
| Fixa com backfill | `FixedCadenceOrchestrator` | Política fixa rodando no mesmo laço, para usar a mesma lógica de backfill (baseline do R3.M5) |
| Laço | `runtime/simulator.py` (gancho `on_decision`), `features.py` (`OnlineFeatureState.ingest_past`) | As amostras recuperadas também alimentam as features das decisões seguintes |
| Métricas | `revalidation.py` | Episódios detectados **em tempo real** × **documentados** (incluindo backfill); atraso em tempo real; evidência recebida e sinalizada; falsos positivos por semana; bytes de backfill |
| Relatório | `scripts/report_phase_a.py` | Tabela resumo, frente não dominada, diferenças pareadas (Wilcoxon com Holm) e tabela por cenário |
| Testes | `tests/test_phase_a.py` | Teto de evidência; custo do lote; estado online com amostras atrasadas igual ao cálculo em lote; separação entre detecção em tempo real e tardia; `adaptive_b60` reproduz exatamente o `adaptive` padrão. Total: 29 testes passando |

**Como reproduzir:**
```powershell
.\.venv\Scripts\python.exe scripts\run_revalidation_ladder.py --stages E5 --replicates 30
.\.venv\Scripts\python.exe scripts\report_phase_a.py
```
(cerca de 10 minutos)

---

## 3. Resultados

### 3.1 Tabela geral (4 cenários com furto agregados; sem furto = média de 3 cenários)

| Política | Bytes furto | Bytes sem furto | Detecção em tempo real | Atraso em tempo real (min) | Episódios documentados | Evidência sinalizada | FP/semana sem furto |
|---|---|---|---|---|---|---|---|
| fixed_long (60) | 17.672 | 17.176 | 0,689 | 32,8 | 0,689 | 0,081 | 1,06 |
| fixed_40 | 26.539 | 25.790 | 0,716 | 25,0 | 0,716 | 0,121 | 1,03 |
| fixed_30 | 35.260 | 34.305 | 0,786 | 20,0 | 0,786 | 0,163 | 1,52 |
| fixed_25 | 42.207 | 41.127 | 0,819 | 17,8 | 0,819 | 0,196 | 1,68 |
| fixed_short (15) | 46.352 | 49.592 | 0,895 | 10,6 | 0,895 | 0,329 | 2,34 |
| fixed_20 | 52.890 | 51.476 | 0,840 | 14,3 | 0,840 | 0,245 | 1,74 |
| **adaptive (basal 60, artigo)** | 55.827 | 17.265 | 0,716 | 29,3 | 0,716 | 0,911 | 0,91 |
| adaptive_b40 | 62.165 | 25.864 | 0,747 | 22,5 | 0,747 | 0,925 | 1,07 |
| adaptive_b30 | 68.229 | 34.345 | 0,801 | 18,4 | 0,801 | 0,933 | 1,58 |
| adaptive_b20 | 79.805 | 51.449 | 0,855 | 14,0 | 0,855 | 0,941 | 1,76 |
| **adaptive_b15** | 75.948 | 49.545 | **0,889** | **11,2** | 0,889 | **0,946** | 2,23 |
| adaptive_b60_cap | 31.724 | 17.265 | 0,716 | 28,8 | 0,716 | 0,397 | 0,91 |
| adaptive_b30_cap | 43.658 | 34.345 | 0,801 | 18,4 | 0,801 | 0,409 | 1,58 |
| adaptive_b15_cap | 51.114 | 49.545 | 0,889 | 11,0 | 0,889 | 0,419 | 2,23 |
| adaptive_b60_bf | 64.871 | 18.537 | 0,729 | 27,3 | 0,835 | 0,977 | 0,98 |
| adaptive_b30_bf | 77.286 | 36.407 | 0,799 | 18,4 | 0,891 | 0,984 | 1,68 |
| fixed_60_bf (baseline do R3) | 64.355 | 18.650 | 0,681 | 32,7 | 0,800 | 0,939 | 1,07 |
| fixed_30_bf | 80.504 | 36.339 | 0,790 | 20,3 | 0,885 | 0,973 | 1,52 |
| fixed_dense (5) | 135.344 | 141.295 | 0,987 | 1,1 | 0,987 | 0,992 | 6,42 |

**Observação:** os "bytes furto" agregados são dominados pelo `persistent_theft`. Nesse cenário, toda variante adaptativa sem teto gasta quase o mesmo que o denso (cerca de 133 kB por semana), porque o risco fica alto a semana inteira. Por isso o custo deve ser lido **na frota** (3.3) e **por cenário** (3.4).

### 3.2 Mesmo período basal: adaptativo × fixo (diferenças pareadas, cenários com furto)

| Adaptativo | Fixa equivalente | Δ detecção em tempo real | Δ atraso (min) | p (Holm) | Δ evidência | Evidência (adaptativo / fixa) |
|---|---|---|---|---|---|---|
| adaptive_b15 | fixed_short | −0,005 | +0,6 | 0,25 | +0,617 | 0,946 / 0,329 (2,9×) |
| adaptive_b30 | fixed_30 | +0,015 | −1,7 | 0,16 | +0,770 | 0,933 / 0,163 (5,7×) |
| adaptive_b60 | fixed_long | +0,027 | −3,4 | (E4: 0,036) | +0,830 | 0,911 / 0,081 (11×) |

Nenhuma diferença de detecção ou de atraso é significativa no mesmo basal. **A detecção é governada pelo período basal**, e o adaptativo não piora nem melhora isso. Todas as diferenças de evidência têm p < 10⁻⁷.

### 3.3 Custo na frota (prevalência de furto p)

Custo médio por instalação e semana = (1 − p) × bytes sem furto + p × bytes com furto.

| Comparação | p = 5% | p = 10% | Detecção | Evidência |
|---|---|---|---|---|
| adaptive_b15 × fixed_short | 50.866 × 49.430 (**+2,9%**) | +5,9% | igual | 2,9× |
| adaptive_b15 × fixed_20 | 50.866 × 51.546 (**−1,3%**) | +1,1% | adaptativo melhor (+4,9 pp, −3,1 min) | 3,9× |
| adaptive_b20 × fixed_20 | +2,6% | +5,2% | igual | 3,8× |
| adaptive_b30 × fixed_30 | +4,9% | +9,7% | igual | 5,7× |
| adaptive_b60 × fixed_long | +11,6% | +22,6% | igual | 11× |
| adaptive_b15_cap × fixed_short | +0,4% | +0,9% | igual | 1,3× |
| adaptive_b30_bf × fixed_30 | +11,9% | +17,7% | igual (tempo real); +10 pp documentados | 6,0× |
| fixed_60_bf × fixed_long | +21,7% | +34,8% | igual (tempo real); +11 pp documentados | 11,6× |

Em frotas reais a prevalência entre instalações monitoradas tende a ser baixa, a menos que o dispositivo seja instalado só em suspeitos. Com baixa prevalência, o custo extra do adaptativo é pequeno. Vale lembrar que, num programa de inspeção dirigida (instalação só em clientes suspeitos), p é alto e o custo extra cresce. Os dois casos devem aparecer no artigo.

### 3.4 Por cenário (destaques)

| Cenário | Política | Bytes | Detecção em tempo real | Atraso (min) | Evidência |
|---|---|---|---|---|---|
| peak_theft | fixed_30 | 35.271 | 1,000 | 18,0 | 0,161 |
| peak_theft | adaptive (basal 60) | 31.831 | 1,000 | 29,8 | 0,859 |
| peak_theft | adaptive_b30 | 47.849 | 1,000 | 15,1 | 0,919 |
| peak_theft | adaptive_b60_bf | 40.680 | 1,000 | 29,6 | 0,988 |
| intermittent_evening | fixed_short | 46.415 | 0,833 | 12,5 | 0,301 |
| intermittent_evening | adaptive (basal 60) | 22.594 | 0,549 | 26,3 | 0,286 |
| intermittent_evening | adaptive_b30 | 39.974 | 0,684 | 19,6 | 0,390 |
| intermittent_evening | adaptive_b30_bf | 56.767 | 0,681 | 18,9 | 0,814 |
| persistent_theft | adaptive (basal 60) | 133.251 | 1,000 | 31,5 | 0,983 |
| persistent_theft | adaptive_b60_cap | 48.314 | 1,000 | 31,5 | 0,346 |

**O intermitente continua sendo o caso difícil:** episódios curtos (no gerador da v1 são fragmentos de 5 a 30 min) favorecem quem amostra com frequência o tempo todo. Ali o backfill é o que mais ajuda na evidência (0,39 → 0,81), mas não na detecção em tempo real.

---

## 4. Leitura componente a componente

### Período basal
- **O que aconteceu:** reduzir o basal reduz o atraso e aumenta a detecção em tempo real exatamente como numa cadência fixa (60 → 15 min: atraso de 29,3 → 11,2 min; detecção de 71,6% → 88,9%), e o custo sem furto passa a ser o da fixa equivalente.
- **Por que:** antes do alerta, o adaptativo **é** uma cadência fixa no período basal. Densificar só ajuda depois da primeira detecção.
- **Implicação:** o período basal deve ser apresentado como o parâmetro que a distribuidora escolhe para o atraso tolerável. O artigo submetido fixava o basal em 60 min sem discutir isso.

### Backfill
- **O que aconteceu:**
  - a evidência sobe para 0,98–0,99;
  - os episódios documentados sobem cerca de 10 pontos percentuais;
  - a detecção e o atraso em tempo real praticamente não mudam;
  - o custo extra sem furto é pequeno (+1,3 a +2 kB por semana, de backfills disparados por alarmes falsos).
- **Por que:** ele recupera o que o dispositivo já tinha medido, mas só depois de um alerta. Os episódios curtos que ocorreram antes do alerta passam a ser documentados, tarde.
- **Comparação com o baseline do R3 (`fixed_60_bf`):**
  - evidência de 0,939, contra 0,977 do `adaptive_b60_bf`;
  - documenta 80,0% dos episódios, contra 83,5%;
  - detecção em tempo real de 68,1%, contra 72,9%;
  - custo de frota praticamente igual.

  O adaptativo com backfill é ligeiramente melhor em tudo, mas a diferença é pequena. A resposta ao R3 deve reconhecer que o baseline sugerido é forte e mostrar que a combinação dos dois é a melhor configuração.
- **Sensibilidade ao tamanho do registro:** com registros de 32 B, o custo do backfill cai pela metade. O `fixed_60_bf` passaria de 64 kB para 41 kB por semana com furto. A bancada precisa medir o tamanho real de um registro de memória de massa.

### Teto de evidência (2 h)
- **O que aconteceu:**
  - resolve o custo do `persistent_theft` (−64%);
  - derruba a evidência nos furtos de horário, que duram cerca de 4 h e passam a ter metade do período em modo moderado: evidência agregada de 0,91 → 0,40;
  - combinado com o backfill, o ganho de custo some, porque o backfill volta a puxar os registros que o teto deixou de enviar.
- **Implicação:** como regra fixa de 2 h, não compensa. Duas opções melhores para testar:
  - teto mais longo (6–12 h), só para furto que persiste por dias;
  - teto com coleta diária da memória de massa (o dispositivo guarda 90 dias, então a evidência densa pode ser recuperada uma vez por dia, em lote).

### Alarmes falsos
Todas as variantes adaptativas têm menos (ou tantos) falsos positivos por semana nos cenários sem furto quanto a fixa equivalente (por exemplo, b15: 2,23 contra 2,34 do `fixed_short`). Quanto mais amostras, mais oportunidades de alarme falso; o denso tem 6,4 por semana.

---

## 5. O que muda no artigo

1. **Contribuição reformulada:** o gêmeo digital não reduz o atraso de detecção, que é definido pelo período basal. Ele **coleta evidência forense densa só onde e quando há risco**, a um custo de frota próximo ao de uma cadência fixa com a mesma detecção. Com basal de 15 min: mesma detecção do `fixed_short`, 2,9× mais evidência, +2,9% de bytes na frota (p = 5%).
2. **Três eixos no Pareto:** bytes (na frota, com prevalência explícita) × atraso de detecção × cobertura de evidência. Isso responde ao R2.5 e ao R3 sobre a Eq. (3): λ₁/λ₂ passam a ponderar atraso e evidência contra custo.
3. **Período basal como parâmetro de projeto**, com uma tabela "basal × atraso × custo".
4. **Backfill como extensão do método** (adaptativo + backfill) e o `fixed_60_bf` do R3 reportado como baseline forte, com a comparação honesta.
5. **Resultado negativo assumido:** o teto de 2 h não compensa (o R1 elogiou o relato de resultados negativos).
6. **A dependência do modelo de custo** (janela de reaproveitamento RRC de 15 min, 64 B por registro) declarada e coberta pela bancada.

---

## 6. Limitações e próximos passos

- **Gerador da v1:** os episódios intermitentes são fragmentos curtos. O gerador semi-Markov (S3) vai mudar os números do `intermittent_evening` e pode favorecer o adaptativo, com episódios mais longos.
- **Modelo de custo não calibrado:** a janela RRC de 15 min explica por que o `fixed_short` é tão barato. Se a janela real for menor, o custo das cadências de 15 min sobe; a bancada resolve.
- **Limiares e α não reajustados para cada basal.** O Pareto da Fase B deve incluir o basal como parâmetro, ajustado em seeds de validação.
- **Teto de evidência:** testar teto longo e coleta diária em lote.
- **Persistent_theft:** a política ideal para furto contínuo provavelmente é "detecta, coleta X horas densas e passa a confiar na memória de massa"; vale um parágrafo de discussão.

**Próximo passo recomendado:** Fase B (LOSO, `threshold_escalation`, Pareto com basal × α × limiares em validação e teste, store-and-forward), já usando a métrica de frota e os três eixos definidos aqui.
