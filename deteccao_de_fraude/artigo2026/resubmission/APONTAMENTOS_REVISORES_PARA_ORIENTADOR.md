# Ressubmissão IEEE Access: apontamentos dos revisores e plano de resposta

**Manuscrito:** Access-2026-46607, "Digital-Twin-Driven Adaptive Observation for Energy-Theft Detection in NB-IoT Forensic Telemetry"
**Decisão (04/11/2026):** rejeitado na forma atual, com convite para ressubmissão. O IEEE Access permite apenas **uma** ressubmissão.

Organizei os comentários na ordem da carta. Para cada um coloquei o texto original, a tradução e o que pretendo fazer. Quando o ponto não pode ser atendido por completo, explico o motivo e como pretendo argumentar.

Situação de cada item: **[Atendido]**, **[Parcial]** (atendido em parte, com contra-argumento) ou **[Inviável agora]**.

---

## Visão geral

| Revisor | Avaliação | Pontos centrais |
|---|---|---|
| R1 | Crítico, mas construtivo; fez 5 pedidos objetivos | Números do resumo, baselines com orçamento equivalente, métricas por episódio, múltiplas seeds, detalhamento do protocolo |
| R2 | Favorável (respondeu "Yes" a todas as perguntas) | Contribuição e conceito de gêmeo digital, padronização editorial, Figs. 3, 4 e 5 |
| R3 | O mais técnico | Protocolo de treino e teste, múltiplas seeds, falsos positivos, baseline com *backfill*, custo do BLE e 9 pontos menores |

Os revisores 1 e 3 convergem no mesmo ponto: o protocolo de avaliação precisa ser mais robusto. Por isso, além de revisar o texto, vou refazer a campanha experimental com o protocolo ajustado. Com isso, os números finais devem mudar, e é provável que os ganhos fiquem mais modestos do que os da versão submetida. Em compensação, ficam mais bem fundamentados.

---

# Revisor 1

**Comentário geral (EN):**
> Framing telemetry density as a controllable resource is an interesting idea, and I appreciate the limitations section and the reporting of negative results. However, the current evidence does not support the strength of the claims made in the Abstract and Conclusion.

**PT:**
> Tratar a densidade da telemetria como um recurso controlável é uma ideia interessante, e agradeço a seção de limitações e o relato de resultados negativos. No entanto, as evidências atuais não sustentam a força das afirmações feitas no Resumo e na Conclusão.

---

### R1.1 Corrigir as afirmações principais e conciliar os números com as tabelas [Atendido]

**EN:**
> Correct the headline claims and reconcile the numbers with your own tables. The Abstract and Conclusion state that the adaptive policy retains ~91% of the F1-score and ~83% of the recall at ~30% of the communication volume. These figures come from a mean over seven scenarios, three of which contain no theft and are scored as zero by convention. According to Table 5, on the four theft-bearing scenarios the adaptive policy uses 58,186 bytes against 135,162 for fixed_dense (about 43%, not 30%). In persistent_theft there is no reduction at all (135,332 bytes in both cases), and in intermittent_evening recall falls to 0.4581. In addition, Section VI-F reports F1 = 0.869 at 30,635 bytes for the configuration used in the paper on the three grid scenarios, whereas the mean of the corresponding entries in Table 5 (intermittent_evening, peak_theft, night_theft) is approximately F1 = 0.843 at 32,471 bytes. I recommend: (a) revise the Abstract and Conclusion to report results on theft-bearing scenarios, with per-scenario ranges; (b) explain or correct the discrepancy between Section VI-F and Table 5.

**PT:**
> Corrijam as afirmações principais e conciliem os números com as próprias tabelas. O Resumo e a Conclusão dizem que a política adaptativa mantém ~91% do F1 e ~83% da recall com ~30% do volume de comunicação. Esses valores vêm de uma média sobre sete cenários, três deles sem furto e pontuados como zero por convenção. Pela Tabela 5, nos quatro cenários com furto a política adaptativa usa 58.186 bytes contra 135.162 do fixed_dense (cerca de 43%, não 30%). Em persistent_theft não há redução nenhuma (135.332 bytes nos dois casos), e em intermittent_evening a recall cai para 0,4581. Além disso, a Seção VI-F informa F1 = 0,869 com 30.635 bytes para a configuração usada no artigo nos três cenários da grade, mas a média das entradas correspondentes da Tabela 5 (intermittent_evening, peak_theft, night_theft) é de aproximadamente F1 = 0,843 com 32.471 bytes. Recomendo: (a) revisar o Resumo e a Conclusão para relatar resultados nos cenários com furto, com faixas por cenário; (b) explicar ou corrigir a discrepância entre a Seção VI-F e a Tabela 5.

**O que vou fazer:**
- **(a)** Reescrever o Resumo e a Conclusão com métricas agregadas apenas dos cenários com furto, faixas mínimo–máximo por cenário e, à parte, a taxa de falsos positivos nos cenários sem furto. As duas reduções de bytes (global e nos cenários com furto) vão aparecer no Resumo.
- **(b)** A diferença vem da inicialização das seeds: o experimento da frente de Pareto e a campanha principal não usavam a mesma configuração de geração dos dados. Unifiquei o procedimento, e na nova avaliação com múltiplas seeds os dois conjuntos de resultados partem dos mesmos dados.

**Como argumentar:** agradecer a leitura cuidadosa e explicar que a diferença veio de uma inconsistência na configuração das seeds entre os dois experimentos, já corrigida. Aproveitar o ponto para mostrar que a variação entre realizações era relevante, o que reforça a decisão de adotar múltiplas seeds com intervalos de confiança (R1.4).

---

### R1.2 Baselines com orçamento equivalente [Atendido]

**EN:**
> Add budget-matched baselines. fixed_short (15 min) costs more than the adaptive policy (47,621 vs. 40,646 bytes), so showing that it is "dominated" is not informative. Moreover, under your cost model every transmission with a gap longer than 15 minutes pays the 40-byte signaling overhead, so cost does not scale linearly with cadence. I recommend: add fixed-cadence policies whose cost brackets that of the adaptive policy (by my estimate, roughly 25–30 min cadences), and at least one simple non-learning adaptive baseline (e.g., escalating to dense observation when the relative power divergence exceeds a fixed threshold). Include them in Tables 4 and 5 and plot them in Fig. 5 against the Pareto frontier.

**PT:**
> Acrescentem baselines com orçamento equivalente. O fixed_short (15 min) custa mais que a política adaptativa (47.621 vs. 40.646 bytes), então mostrar que ele é "dominado" não é informativo. Além disso, no modelo de custo de vocês toda transmissão com intervalo acima de 15 minutos paga o overhead de sinalização de 40 bytes, então o custo não escala linearmente com a cadência. Recomendo acrescentar políticas de cadência fixa com custo próximo ao da adaptativa (pela minha estimativa, cadências de 25 a 30 min) e pelo menos um baseline adaptativo simples, sem aprendizado (por exemplo, escalar para observação densa quando a divergência relativa de potência passar de um limiar fixo). Incluí-los nas Tabelas 4 e 5 e na Fig. 5, junto com a frente de Pareto.

**O que vou fazer:**
- Incluir políticas fixas de 20, 25, 30 e 40 min.
- Incluir uma política adaptativa por limiar fixo de divergência, sem aprendizado.
- Colocar todas nas Tabelas 4 e 5 e na Fig. 5.
- Fazer a comparação principal contra o melhor baseline com orçamento equivalente, com teste estatístico pareado.

---

### R1.3 Métricas por episódio [Atendido]

**EN:**
> Report episode-level detection metrics. Eq. (1) is an instant-level recall, which for any fixed policy is largely determined by its sampling fraction. For forensic purposes, what matters is whether each theft episode is detected and how quickly. I recommend: define a theft episode (e.g., a contiguous run of theft ticks) and report, for all policies in the four theft-bearing scenarios: the episode detection rate, the median and maximum detection delay (in minutes), and the total duration of theft that elapsed undetected.

**PT:**
> Relatem métricas de detecção por episódio. A Eq. (1) é uma recall por instante, que em qualquer política fixa é determinada em grande parte pela fração de amostragem. Para fins forenses, o que importa é se cada episódio de furto é detectado e com que rapidez. Recomendo definir um episódio de furto (por exemplo, uma sequência contígua de ticks com furto) e relatar, para todas as políticas nos quatro cenários com furto: a taxa de detecção de episódios, o atraso de detecção mediano e máximo (em minutos) e a duração total de furto não detectada.

**O que vou fazer:** definir formalmente o episódio de furto e relatar, para todas as políticas:
- a taxa de detecção de episódios;
- o atraso de detecção mediano e máximo;
- a duração total de furto não detectada.

Os resultados vão em uma nova tabela e em uma figura com a distribuição dos atrasos. Também vou refinar o gerador do cenário intermitente para produzir episódios liga/desliga com duração realista, compatíveis com a métrica por episódio, e vou descrever esse refinamento no artigo.

---

### R1.4 Múltiplas seeds com intervalos de confiança [Parcial]

**EN:**
> Provide multi-seed results with confidence intervals. All results come from a single fixed seed and one week per scenario, yet differences of about one percentage point (0.869 vs. 0.878 in Section VI-F) and a 6.4% trade-off between fusion strategies (Section VI-D) are interpreted as meaningful. I recommend: repeat the campaign with at least 30 independent seeds and report mean ± 95% confidence intervals in Tables 4, 5, and 6, and show the variability in Fig. 5. Include a paired statistical comparison between the adaptive policy and the best budget-matched fixed baseline from item 2. Remove or qualify any claim not supported by non-overlapping intervals.

**PT:**
> Apresentem resultados com múltiplas seeds e intervalos de confiança. Todos os resultados vêm de uma única seed e de uma semana por cenário, e mesmo assim diferenças de cerca de um ponto percentual (0,869 vs. 0,878 na Seção VI-F) e um trade-off de 6,4% entre estratégias de fusão (Seção VI-D) são interpretados como relevantes. Recomendo repetir a campanha com pelo menos 30 seeds independentes, relatar média ± IC de 95% nas Tabelas 4, 5 e 6 e mostrar a variabilidade na Fig. 5. Incluir uma comparação estatística pareada entre a política adaptativa e o melhor baseline fixo com orçamento equivalente do item 2. Remover ou qualificar qualquer afirmação não sustentada por intervalos não sobrepostos.

**O que vou fazer:**
- Repetir a campanha com pelo menos 30 seeds.
- Apresentar média ± IC 95% nas Tabelas 4, 5 e 6 e a dispersão na Fig. 5.
- Comparar com o melhor baseline com orçamento equivalente usando o teste de Wilcoxon pareado com correção de Holm.

**Ponto parcial:** o critério de "intervalos não sobrepostos".

**Como argumentar:** todas as políticas são avaliadas nas mesmas seeds, ou seja, a comparação é pareada. Nesse caso, intervalos sobrepostos das médias não excluem uma diferença significativa, e exigir que não se sobreponham é mais conservador do que o necessário. Vou apresentar o intervalo de confiança da diferença pareada e o p-valor corrigido, e qualificar toda afirmação sem significância estatística. Isso atende ao objetivo do revisor com a estatística adequada ao desenho.

**Referências de apoio:**
- **Cumming, G., & Finch, S. (2005). "Inference by eye: Confidence intervals and how to read pictures of data."** *American Psychologist*, 60(2), 170–180. DOI: 10.1037/0003-066X.60.2.170. O artigo propõe regras práticas para ler intervalos de confiança em gráficos. Duas delas interessam aqui:
  - **Grupos independentes:** ICs de 95% que se sobrepõem em até cerca de metade da margem de erro ainda correspondem a p ≈ 0,05.
  - **Medidas repetidas (pareadas):** os ICs de cada média não servem para julgar a diferença; o correto é usar o IC da diferença pareada.

  O segundo caso é exatamente o nosso, já que todas as políticas rodam nas mesmas seeds.
- **Schenker, N., & Gentleman, J. F. (2001). "On judging the significance of differences by examining the overlap between confidence intervals."** *The American Statistician*, 55(3), 182–186. Mostra formalmente que o critério de não sobreposição é conservador, ou seja, deixa de detectar diferenças reais.

(Conferir os dados bibliográficos pelo DOI antes de usar na carta.)

---

### R1.5 Explicitar o protocolo de avaliação e a lógica de orquestração [Atendido]

**EN:**
> Specify the evaluation protocol and the orchestration logic explicitly. Several points cannot currently be determined from the text: whether the policy-level metrics are computed on the full timeline, including the 70% chronological training portion used to fit the logistic regression (Section VI-B); whether the rolling features (60/120-min windows, hour-slot recurrence) are computed from the emitted samples only or from the native 5-min grid, which matters in basal mode; whether a separate classifier is trained per scenario, which makes the classifier a constant predictor in four of the seven scenarios (Section IV-H); the PolicyOrchestrator rules (hysteresis, dwell time, return to basal), which Algorithm 1 does not show. I recommend: add a subsection (or an appendix) that answers each of these points, and a pseudo-code or table describing the orchestration rules and thresholds. If the metrics currently include training data, report them on held-out data only.

**PT:**
> Especifiquem explicitamente o protocolo de avaliação e a lógica de orquestração. Hoje não é possível determinar pelo texto: se as métricas de política são calculadas na linha do tempo inteira, incluindo os 70% cronológicos usados para treinar a regressão logística (Seção VI-B); se as features rolantes (janelas de 60/120 min, recorrência por faixa horária) são calculadas só com as amostras emitidas ou com a grade nativa de 5 min, o que importa no modo basal; se é treinado um classificador separado por cenário, o que o torna um preditor constante em quatro dos sete cenários (Seção IV-H); quais são as regras do PolicyOrchestrator (histerese, tempo de permanência, retorno ao basal), que o Algoritmo 1 não mostra. Recomendo acrescentar uma subseção (ou apêndice) que responda a cada ponto, e um pseudocódigo ou uma tabela com as regras e os limiares de orquestração. Se as métricas incluem dados de treino, relatá-las apenas em dados não vistos.

**O que vou fazer:** criar uma subseção "Evaluation protocol" que responda a cada ponto. Também vou revisar o protocolo para torná-lo mais rigoroso:
1. **Treino × avaliação:** a avaliação passa a ser feita em realizações (seeds) inteiramente independentes das usadas no treino.
2. **Features:** como o dispositivo forense é instalado em paralelo e não tem contato com o medidor de faturamento, a divergência entre os dois só pode ser calculada no back-office. As features passam a ser calculadas só com as amostras efetivamente recebidas. O dispositivo pode enviar, no próprio payload, agregados da sua medição (por exemplo, a energia acumulada no intervalo). O cálculo com a grade completa de 5 min fica apenas como limite superior, numa análise de sensibilidade.
3. **Classificador:** passa a ser um único modelo, treinado com dados de todos os cenários (ver R3.M1).
4. **Orquestrador:** pseudocódigo e tabela com os limiares (0,30/0,60), as regras de permanência e o retorno ao basal.

---

**Avaliação geral do R1 (EN):**
> In summary, the idea has merit, but the manuscript requires additional experiments and a more measured presentation of its results.

**PT:**
> Em resumo, a ideia tem mérito, mas o manuscrito precisa de experimentos adicionais e de uma apresentação mais comedida dos resultados.

---

# Revisor 2

**Comentário geral (EN):**
> This paper proposes a digital-twin-driven framework for energy-theft detection. Overall, the topic is interesting, and the experiments are thorough. However, some modules are not clearly explained, meaning the readability could be further improved.

**PT:**
> Este artigo propõe um framework baseado em gêmeo digital para detecção de furto de energia. De modo geral, o tema é interessante e os experimentos são completos. No entanto, alguns módulos não estão claramente explicados, e a legibilidade pode melhorar.

---

### R2.1 Contribuição e conceito de gêmeo digital [Atendido]

**EN:**
> The contribution of this paper is unclear, and the study appears to be an existing framework embedded with several slightly improved strategies. Furthermore, the concept of a "digital twin" is not clearly articulated. The reviewer is curious as to whether there is any interaction between the physical and virtual entities.

**PT:**
> A contribuição deste artigo não está clara, e o estudo parece ser um framework já existente com algumas estratégias ligeiramente aprimoradas. Além disso, o conceito de "gêmeo digital" não está claramente articulado. O revisor gostaria de saber se há alguma interação entre as entidades física e virtual.

**O que vou fazer:**
- Reescrever as contribuições: no máximo três, bem delimitadas. A principal é tratar a densidade de observação como variável de controle em malha fechada, guiada pelo risco de furto.
- Acrescentar um diagrama de sequência físico ↔ virtual: a telemetria sobe e o comando de cadência desce.
- Enquadrar o sistema na classificação de Kritzinger et al. (modelo, sombra e gêmeo digital).

**Ponto de atenção:** na avaliação estatística (simulação), a interação com o dispositivo é emulada; a interação real é demonstrada no ensaio de bancada.

**Como argumentar:** o laço é bidirecional por concepção, já que o gêmeo envia comandos que alteram o comportamento do dispositivo, e o firmware do dispositivo forense já aceita comando de cadência. Vou fazer um ensaio de bancada em malha fechada. O gêmeo comanda por NB-IoT um dispositivo real, que aplica a nova cadência na amostra seguinte, sem reinicializar. O furto é emulado por uma derivação a montante do medidor de faturamento. A fase principal dura de 48 a 72 h, dentro de um ensaio de 5 a 6 dias. Nesse ensaio vou medir:
- os bytes reais por modo de operação, para validar o modelo de custo;
- a latência do comando de cadência;
- o custo de recuperar o histórico (*backfill*);
- um traço temporal real de carga, risco, modo e bytes.

Se o custo medido for diferente do modelado, recalibro o modelo e rodo a simulação de novo. O ensaio é uma demonstração de viabilidade com um dispositivo; a avaliação estatística continua sendo a de simulação.

---

### R2.2 Padronização e fonte das figuras [Atendido]

**EN:**
> Some expressions need to be consistent to increase the readability of the manuscript, such as "Equation (1)" versus "Eq. (1)," and "Figure 2" versus "Fig. 2". In addition, it would be better to use Times New Roman for the text in the figures.

**PT:**
> Algumas expressões precisam ser padronizadas para melhorar a legibilidade, como "Equation (1)" vs. "Eq. (1)" e "Figure 2" vs. "Fig. 2". Além disso, seria melhor usar Times New Roman no texto das figuras.

**O que vou fazer:** revisar o texto todo pelo padrão IEEE: "Fig." e "Eq." no meio da frase e por extenso só no início. Também vou regerar todas as figuras com fonte Times.

---

### R2.3 Figura 3 [Atendido]

**EN:**
> The logical structure in Figure 3 is not clear enough and needs to be reorganized and improved if possible.

**PT:**
> A estrutura lógica da Figura 3 não está clara o suficiente e precisa ser reorganizada e melhorada, se possível.

**O que vou fazer:** redesenhar a Fig. 3 como um fluxo em três blocos: geração de dados → treino/teste → avaliação das políticas. Também vou incluir o `fixed_dense`, que o R3 pediu.

---

### R2.4 Mais modelos de aprendizado de máquina na Figura 4 [Atendido]

**EN:**
> In Figure 4, additional machine learning baseline models should be introduced and analyzed.

**PT:**
> Na Figura 4, devem ser introduzidos e analisados modelos adicionais de aprendizado de máquina como baseline.

**O que vou fazer:** incluir Random Forest, Gradient Boosting, SVM-RBF, kNN e MLP e, opcionalmente, o Isolation Forest (não supervisionado). A nova Fig. 4 (ROC) e uma tabela de AUROC com IC usarão o novo protocolo.

**Como argumentar:** a regressão logística continua como motor do gêmeo porque é interpretável e leve, o que importa no contexto forense. A comparação mostra o custo dessa escolha em desempenho.

---

### R2.5 Análise da Figura 5 e método da frente de Pareto [Parcial]

**EN:**
> The results in Figure 5 require further analysis. Additionally, the method used to determine the Pareto front needs to be clarified, and it should be addressed whether a smooth curve could be fitted to it.

**PT:**
> Os resultados da Figura 5 precisam de mais análise. Além disso, o método usado para determinar a frente de Pareto precisa ser esclarecido, e deve-se discutir se uma curva suave poderia ser ajustada a ela.

**O que vou fazer:**
- Detalhar como a frente é obtida (ordenação não dominada sobre a grade de configurações).
- Discutir as regiões da frente: econômica, equilibrada e densa.
- Mostrar a dispersão entre seeds.
- Ligar a frente aos pesos λ₁/λ₂ da Eq. (3), como o R3 também pediu.

**Ponto parcial:** a curva suave.

**Como argumentar:** a frente empírica é um conjunto discreto de configurações realizáveis, e uma curva contínua sugeriria pontos de operação que não existem. A curva com justificativa teórica é a envoltória convexa, que pode ser atingida em valor esperado alternando entre configurações. Vou apresentá-la, e um ajuste suave aparece apenas como guia visual, identificado como tal.

---

# Revisor 3

**Comentário geral (EN):**
> Thank you for a clearly written paper on a practical problem. Using theft risk to control how densely a forensic device reports is a sensible idea, and I appreciated the explicit treatment of what the twin implementation does and does not satisfy. My main concerns are about evaluation design. In its current form, I cannot tell how much of the reported performance would survive deployment.

**PT:**
> Obrigado por um artigo claramente escrito sobre um problema prático. Usar o risco de furto para controlar a densidade com que um dispositivo forense reporta é uma ideia sensata, e apreciei o tratamento explícito do que a implementação do gêmeo atende e do que não atende. Minhas principais preocupações são com o desenho da avaliação. Na forma atual, não consigo dizer quanto do desempenho relatado sobreviveria a uma implantação real.

---

## Pontos principais (Major)

### R3.M1 Classificador treinado por cenário [Atendido]

**EN:**
> The supervised baseline appears to be trained per scenario (Section IV-H). In the theft-free scenarios this produces a constant "no theft" predictor, and in persistent_theft a constant "theft" predictor. A deployed twin cannot know its scenario. Please train one model across scenarios and evaluate on held-out scenarios, for example leave-one-scenario-out.

**PT:**
> O baseline supervisionado parece ser treinado por cenário (Seção IV-H). Nos cenários sem furto, isso produz um preditor constante "sem furto", e em persistent_theft um preditor constante "furto". Um gêmeo implantado não pode saber em que cenário está. Por favor, treinem um único modelo com todos os cenários e avaliem em cenários não vistos, por exemplo com leave-one-scenario-out.

**O que vou fazer:** adotar dois protocolos de avaliação e relatá-los lado a lado:
- **(A)** um único modelo treinado com seeds de todos os cenários e avaliado em seeds independentes;
- **(B)** leave-one-scenario-out (LOSO).

**Como argumentar:** concordar que o modelo único reflete melhor a operação real. Com só 7 cenários, é esperado que o LOSO mostre queda de desempenho em alguns casos, como um modelo que nunca viu furto noturno. Isso será relatado com transparência, porque responde à pergunta do revisor sobre "quanto sobrevive" a uma implantação.

---

### R3.M2 Métricas de política no trecho de treino [Atendido]

**EN:**
> Policy-level metrics are computed over t = 1..T, which seems to include the training portion. The fixed_dense recall of 1.0000 vs a held-out classifier recall of 0.9815 in intermittent_evening suggests training data is being scored. Please report policy metrics on held-out time only.

**PT:**
> As métricas de política são calculadas sobre t = 1..T, o que parece incluir o trecho de treino. A recall de 1,0000 do fixed_dense, contra 0,9815 do classificador no teste em intermittent_evening, sugere que dados de treino estão sendo avaliados. Por favor, relatem as métricas de política apenas em tempo não visto.

**O que vou fazer:** com o protocolo A, toda a semana avaliada pertence a realizações que não foram usadas no treino. É uma separação mais forte que reservar apenas os últimos 30% do tempo, e ainda mantém a semana completa para as métricas por episódio.

---

### R3.M3 Múltiplas seeds e intervalos de confiança [Atendido]

**EN:**
> Please run multiple seeds and report confidence intervals. Given the roughly 1 s runtime per twin, this is inexpensive. Several conclusions, including the Pareto comparison and the fusion ablation, rest on differences of one to two F1 points.

**PT:**
> Por favor, rodem múltiplas seeds e relatem intervalos de confiança. Com cerca de 1 s de execução por gêmeo, isso é barato. Várias conclusões, incluindo a comparação de Pareto e a ablação da fusão, se apoiam em diferenças de um a dois pontos de F1.

**O que vou fazer:** o mesmo do R1.4: pelo menos 30 seeds, IC 95% e testes pareados. As conclusões da ablação de fusão e do Pareto passam a ser apresentadas de acordo com a significância estatística.

---

### R3.M4 Falsos positivos e tempo em modos elevados nos cenários sem furto [Atendido]

**EN:**
> Please report false-positive rate and the time spent in elevated modes for the theft-free scenarios. Setting F1 to zero there hides the most operationally relevant behavior.

**PT:**
> Por favor, relatem a taxa de falsos positivos e o tempo gasto em modos elevados nos cenários sem furto. Zerar o F1 nesses cenários esconde o comportamento operacionalmente mais relevante.

**O que vou fazer:** criar uma tabela própria para os cenários sem furto, com:
- taxa de falsos positivos;
- percentual do tempo em moderate/aggressive;
- número de escalonamentos por semana;
- bytes transmitidos.

O F1 deixa de ser apresentado nos cenários sem positivos.

---

### R3.M5 Baseline "registro denso local, transmissão esparsa, *backfill* no alerta" [Atendido]

**EN:**
> Since the device already stores historical profiles locally, please compare against a "log densely, transmit sparsely, backfill on alert" baseline, or explain why it isn't viable. This bears directly on the intermittent_evening result.

**PT:**
> Como o dispositivo já armazena perfis históricos localmente, por favor comparem com um baseline do tipo "registrar densamente, transmitir esparsamente e enviar o histórico (backfill) no alerta", ou expliquem por que ele não é viável. Isso afeta diretamente o resultado de intermittent_evening.

**O que vou fazer:** implementar o baseline com *backfill* e um modelo de custo para o envio do histórico em rajada. A sugestão é fisicamente realista: o dispositivo já separa o período de captura do período de envio e guarda o perfil em memória de massa, que pode ser lida sob demanda.

**Como argumentar:** se o *backfill* tiver bom desempenho, ele pode ser incorporado ao próprio método. O gêmeo passa a decidir quando densificar o envio em tempo real e quando solicitar o histórico armazenado, e o trade-off ganha um terceiro eixo: recall × bytes × atraso de detecção (o *backfill* recupera a evidência, mas só depois do alerta). Na carta, agradecer a sugestão como uma contribuição que ampliou o trabalho.

---

### R3.M6 Custo do fallback BLE [Atendido]

**EN:**
> BLE fallback requires an operator on site, so please cost it accordingly or report it separately from NB-IoT bytes.

**PT:**
> O fallback via BLE exige um operador no local, então, por favor, custeiem isso adequadamente ou relatem separadamente dos bytes NB-IoT.

**O que vou fazer:** revisar o modelo de transporte. Sem cobertura NB-IoT, o dispositivo armazena os dados e os envia na próxima conexão (*store-and-forward*). A coleta por BLE passa a ser tratada como visita técnica, relatada à parte em número de visitas. A Seção IV-J será reescrita.

---

## Pontos menores (Minor)

### R3.7 Especificar parâmetros [Atendido]

**EN:**
> Specify τ in Eq. (1), the rule-engine scoring, the context_aware weights, and the hysteresis down-switching and dwell rules.

**PT:**
> Especifiquem τ na Eq. (1), a pontuação do motor de regras, os pesos do context_aware e as regras de rebaixamento e de permanência (dwell) da histerese.

**O que vou fazer:** incluir uma tabela de parâmetros (τ = 0,50, pesos do motor de regras, pesos do context_aware, limiares 0,30/0,60 e regras de permanência) e o pseudocódigo do orquestrador, na nova subseção de protocolo.

---

### R3.8 Substituir as médias com zeros [Atendido]

**EN:**
> Replace the zero-padded seven-scenario means with pooled metrics over theft-bearing scenarios. State the theft-bearing byte reduction (about 57%) alongside the 70.5% figure in the abstract.

**PT:**
> Substituam as médias dos sete cenários preenchidas com zeros por métricas agregadas (pooled) dos cenários com furto. Informem a redução de bytes nos cenários com furto (cerca de 57%) ao lado do valor de 70,5% no resumo.

**O que vou fazer:** usar métricas agregadas apenas dos cenários com furto, com a taxa de falsos positivos nos cenários sem furto. As duas reduções de bytes vão aparecer no Resumo, recalculadas com o novo protocolo.

---

### R3.9 Convenção do critical-slot [Atendido]

**EN:**
> Clarify how the critical-slot scores treat theft-free scenarios. A binary score of 0.5714 and a relaxed score of 0.9496 seem to use different conventions.

**PT:**
> Esclareçam como as pontuações de critical-slot tratam os cenários sem furto. Uma pontuação binária de 0,5714 e uma relaxada de 0,9496 parecem usar convenções diferentes.

**O que vou fazer:** explicitar a convenção, que é a mesma nas duas: nos cenários sem furto, a ausência de alarme conta como acerto. Como o atraso por episódio (R1.3) responde à mesma pergunta operacional de forma mais direta, proponho levar a métrica de critical-slot para o material suplementar, restrita aos cenários com furto.

---

### R3.10 Detecção por cliente e tempo até o primeiro alerta [Atendido]

**EN:**
> Consider adding customer-level detection and time-to-first-flag metrics.

**PT:**
> Considerem acrescentar métricas de detecção por cliente e de tempo até o primeiro alerta.

**O que vou fazer:** fazer uma avaliação de frota, em que cada seed representa um cliente-semana e o cliente é sinalizado quando há pelo menos k alertas em 24 h. A tabela terá a taxa de detecção por cliente, a taxa de falsos positivos e o tempo entre o início do furto e o primeiro alerta.

---

### R3.11 Tabela de features [Atendido]

**EN:**
> Tabulate the full feature set.

**PT:**
> Apresentem em tabela o conjunto completo de features.

**O que vou fazer:** incluir uma tabela com as 8 features: nome, janela, definição e local de cálculo.

---

### R3.12 Encurtar a Seção VI-G [Atendido]

**EN:**
> Shorten Section VI-G and drop the O(T²) bug-fix narrative.

**PT:**
> Encurtem a Seção VI-G e retirem a narrativa da correção do bug O(T²).

**O que vou fazer:** reduzir a seção de escalabilidade a duas ou três frases e retirar a narrativa de otimização.

---

### R3.13 Correções editoriais [Atendido]

**EN:**
> Editorial fixes: "Table 5" should be "Table 4" in Section VI-C; Fig. 3 is missing fixed_dense; two subsections are titled "Computational complexity and scalability"; the template placeholders (Volume 11, 2023; DOI ACCESS.2017) remain.

**PT:**
> Correções editoriais: "Table 5" deveria ser "Table 4" na Seção VI-C; a Fig. 3 não mostra o fixed_dense; duas subseções se chamam "Computational complexity and scalability"; os placeholders do template (Volume 11, 2023; DOI ACCESS.2017) continuam no texto.

**O que vou fazer:** corrigir todos os pontos: a referência cruzada, a inclusão do `fixed_dense` na Fig. 3, a fusão das subseções duplicadas e a atualização dos campos do template.

---

### R3.14 Disponibilizar código e dados [Parcial]

**EN:**
> Reproducibility is listed as a contribution, so please deposit the code and synthetic data publicly (e.g., Code Ocean or Zenodo) rather than offering them on request.

**PT:**
> A reprodutibilidade está listada como contribuição, então, por favor, depositem o código e os dados sintéticos publicamente (por exemplo, Code Ocean ou Zenodo), em vez de oferecê-los sob demanda.

**O que vou fazer:** publicar no Zenodo, com DOI:
- os dados sintéticos completos, com rótulos e lista de episódios;
- as divisões de treino, validação e teste;
- todos os arquivos de configuração;
- um pseudocódigo completo, passo a passo, da geração dos dados e da avaliação;
- os resultados brutos de cada execução, incluindo os dados por trás de cada tabela e figura.

Com isso, qualquer leitor confere todos os números e consegue reimplementar o pipeline sobre exatamente os mesmos dados. A seção Data Availability do artigo cita esse depósito, e a contribuição de "reprodutibilidade" passa a ser descrita como protocolo totalmente especificado, com dados e resultados públicos.

**Código-fonte:** fica disponível mediante requisição formal aos autores. Hoje não está disponível publicamente por causa de processos internos de autorização para liberação pública. Essa explicação vai só na carta-resposta, não no artigo.

**Como argumentar:** o depósito atende ao objetivo do pedido, que é poder verificar e reproduzir os resultados, e o código continua acessível por requisição formal.

---

### R3.15 Literatura de amostragem adaptativa e acionada por eventos [Atendido]

**EN:**
> Situate the policy against event-triggered and adaptive sampling work, and consider the additional references suggested in the review form.

**PT:**
> Situem a política em relação aos trabalhos de amostragem acionada por eventos e de amostragem adaptativa, e considerem as referências adicionais sugeridas no formulário de revisão.

**O que vou fazer:** criar uma subseção em Trabalhos Relacionados sobre amostragem adaptativa e acionada por eventos, e acrescentar a linha correspondente na Tabela 1. Vou incluir as referências sugeridas que são pertinentes:
- Alippi 2010 (amostragem adaptativa);
- Jokar 2016 e Zheng 2018 (detecção de furto);
- Messinis 2018 e Glauner 2017 (revisões de perdas não técnicas);
- Tao 2019 (gêmeo digital).

**Como argumentar:** a proposta se diferencia da amostragem por limiar em dois pontos: (i) o gatilho é uma probabilidade de furto, e não a variação do próprio sinal; (ii) o objetivo é a qualidade da evidência forense, e não a reconstrução do sinal ou a economia de energia.

---

## Avaliação complementar do R3 (formulário de revisão)

### R3.A Escopo da contribuição [Parcial]

**EN:**
> The contribution is narrower than the framing suggests, though. The decision logic is a weighted average of a rule score and a logistic regression, mapped to three modes through two thresholds. That is essentially threshold-based event-triggered sampling, and the paper doesn't relate it to the existing adaptive and event-triggered sampling literature in sensor networks. All of the evidence is also synthetic, from one seed per scenario, so the contribution currently amounts to a well-documented architecture plus a simulation study. It is not yet a validated method.

**PT:**
> A contribuição é mais estreita do que o enquadramento sugere. A lógica de decisão é uma média ponderada de uma pontuação de regras e de uma regressão logística, mapeada em três modos por dois limiares. Isso é essencialmente amostragem acionada por eventos com limiar, e o artigo não a relaciona à literatura existente de amostragem adaptativa e acionada por eventos em redes de sensores. Além disso, toda a evidência é sintética, de uma seed por cenário, então a contribuição hoje se resume a uma arquitetura bem documentada mais um estudo de simulação. Ainda não é um método validado.

**O que vou fazer:** apresentar as contribuições de forma mais precisa:
1. a formulação do problema, com a densidade de observação como controle guiado por risco no contexto forense;
2. um protocolo de avaliação rigoroso (múltiplas seeds, entre cenários, com orçamento equivalente e por episódio);
3. a caracterização do trade-off detecção × comunicação.

**Como argumentar:** a simplicidade dos componentes é uma escolha de projeto. Em contexto forense, a decisão precisa ser interpretável e auditável, e o processamento precisa ser leve. A contribuição está na formulação do laço e na avaliação, e não na sofisticação do classificador.

---

### R3.B Dados de campo da distribuidora [Inviável nesta fase]

**EN:**
> The forensic use case is credible and the utility partnership is a strength. The paper would be much stronger with even a small, anonymized slice of the EDP field data.

**PT:**
> O caso de uso forense é crível e a parceria com a distribuidora é um ponto forte. O artigo ficaria muito mais forte com uma fatia, mesmo pequena e anonimizada, dos dados de campo da EDP.

**Decisão:** dados de clientes não entram nesta ressubmissão, nem em recorte anonimizado nem em estatísticas agregadas.

**Por quê:** as análises dos dispositivos reais instalados em campo, e os desdobramentos delas, ainda estão em andamento. Publicar agora um recorte parcial anteciparia resultados não consolidados e poderia interferir nesses processos. Os dados também estão sujeitos à confidencialidade com a distribuidora e à LGPD. A validação em campo do laço adaptativo fica como próxima etapa do projeto, para um trabalho próprio.

**O que vou fazer no lugar:** aprimorar o gerador de dados sintéticos para aproximá-lo da operação real:
- **Carga de base real:** curvas de consumo de datasets públicos (REFIT ou UK-DALE, agregadas a 5 min), reescaladas para níveis típicos de consumo no Brasil.
- **Ataques da literatura:** famílias de ataque segundo a taxonomia de Jokar et al. (2016), uma das referências sugeridas pelo próprio revisor, mapeadas para fraudes físicas (desvio parcial, desvio de fase, carga agendada, *bypass* intermitente).
- **Episódios realistas:** duração e início variáveis, com fase de amostragem aleatória.
- **Frota heterogênea com baixa prevalência de furto:** centenas de cliente-semanas com parâmetros sorteados, o que dá sentido à taxa de falsos positivos e às métricas por cliente.
- **Ruído e tolerâncias com base em norma:** classes de exatidão (IEC 62053), resolução dos registradores e desalinhamento de relógio entre os dois medidores.
- **Mais perturbações legítimas:** geração fotovoltaica, partida de motores, feriados e faltas de energia.
- **Enlace NB-IoT por classe de cobertura:** com armazenamento e reenvio quando o enlace cai.
- **Validação do gerador:** tabela com todos os parâmetros e a fonte de cada um, mais estatísticas que comparem os dados gerados com os dados públicos.

Os sete cenários atuais continuam como "cenários controlados", por serem fáceis de interpretar, e a avaliação principal passa a ser a da frota.

**Como argumentar:** concordar que dados de campo fortaleceriam a avaliação. Explicar que as análises de campo ainda não estão consolidadas e que há restrições de confidencialidade, mostrar o que foi feito para aproximar a avaliação da operação real e registrar a validação em campo como próxima etapa. O revisor tratou o ponto como algo que fortaleceria o artigo, e não como exigência. Sugestão de texto para a carta:
> *"We fully agree that field data would strengthen the evaluation. The field installations of the forensic device are still under analysis within the utility R&D project, and their outcomes have not yet been consolidated; releasing a partial subset at this stage would anticipate unconsolidated results and is further constrained by confidentiality agreements and the Brazilian data-protection law (LGPD). For this reason, field data are outside the scope of this revision. To reduce the distance to real operation, we redesigned the data generator [...], and field validation of the adaptive loop is stated as the next step of the project."*

---

### R3.C Referências [Atendido]

**EN:**
> A few are from lower-rigor venues ([11], [19], [20]) and could be replaced or supplemented with stronger sources. The coverage is missing three things: foundational NTL work, a standard digital-twin reference, and the adaptive-sampling literature, which is the closest prior art to the core idea.

**PT:**
> Algumas referências vêm de veículos de menor rigor ([11], [19], [20]) e poderiam ser substituídas ou complementadas por fontes mais sólidas. Faltam três coisas na cobertura: trabalhos fundamentais de perdas não técnicas (NTL), uma referência-padrão de gêmeo digital e a literatura de amostragem adaptativa, que é o trabalho anterior mais próximo da ideia central.

**O que vou fazer:** substituir ou complementar as referências [11], [19] e [20]. Para cobrir as três lacunas, uso as referências do R3.15 e Kritzinger et al. (2018) para a taxonomia de gêmeos digitais.

---

### R3.D Equação (3) [Atendido]

**EN:**
> Eq. (3) is introduced and then set aside, so either connect the frontier to λ1/λ2 or shorten it.

**PT:**
> A Eq. (3) é introduzida e depois deixada de lado, então ou liguem a frente de Pareto a λ1/λ2, ou a encurtem.

**O que vou fazer:** ligar a frente de Pareto aos pesos λ₁/λ₂. Cada ponto da envoltória convexa corresponde ao ótimo da Eq. (3) para uma faixa de razões λ₁/λ₂. Assim a equação passa a servir para escolher o ponto de operação conforme o custo relativo, para a distribuidora, entre bytes transmitidos e detecção perdida.

---

# Pontos que não podem ser atendidos integralmente

| Ponto | Situação | Argumento |
|---|---|---|
| Dados de campo (R3.B) | Inviável nesta fase | Análises de campo ainda não consolidadas, confidencialidade e LGPD; gerador sintético aprimorado (carga real pública, ataques da literatura, frota); validação em campo como próxima etapa |
| Interação física do gêmeo (R2.1) | Atendido em bancada | Ensaio em malha fechada com dispositivo real (custo medido, latência do comando, traço temporal); validação em campo como próxima etapa |
| Intervalos não sobrepostos (R1.4) | Parcial | Comparação pareada nas mesmas seeds: o IC da diferença e o teste de Wilcoxon com Holm são o critério adequado |
| Curva suave no Pareto (R2.5) | Parcial | A frente é discreta; a envoltória convexa é a curva justificável, e o ajuste suave aparece só como guia visual |
| LOSO com 7 cenários (R3.M1) | Atendido, com ressalva | A queda em alguns cenários é esperada e será relatada |

# Pontos para conversarmos

1. **Resultados mais modestos:** com o protocolo revisado, os números do resumo devem mudar. O artigo passa a se apoiar mais no rigor da avaliação do que no tamanho do ganho.
2. **Backfill:** se o baseline sugerido pelo R3 for competitivo, a proposta é incorporá-lo ao método.
3. **Features no back-office:** como o dispositivo forense é independente do medidor de faturamento, a comparação entre os dois acontece no back-office, com os dados que chegam em intervalos. A cadência configurada é respeitada e as mudanças valem na amostra seguinte, sem reinicialização.
4. **Melhorias do gerador sintético:** quais entram nesta rodada? Minha proposta é episódios realistas, frota heterogênea, ruído com base em norma, validação do gerador e ataques da literatura; a carga de base real, se houver tempo.
5. **Ensaio de bancada:** é viável, e os pré-requisitos estão atendidos (comando remoto de cadência, contador real de bytes, medidor com memória de massa e derivação segura). O protocolo está pronto: fases de custo por cadência, comandos, backfill, malha fechada com roteiro de furto, enlace degradado e falta de energia.
6. **Publicação do código:** proposta: dados sintéticos, pseudocódigo e resultados públicos no Zenodo; o código fica disponível por requisição formal, por causa dos processos internos de autorização (essa explicação vai só na carta).
