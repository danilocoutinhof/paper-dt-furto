# Proposta de Tese de Doutorado

## Título

**Twins Digitais Adaptativos para Controle Ótimo de Observação e Detecção de Perdas Não Técnicas em Redes de Medição Inteligente NB-IoT: da Política Heurística de Único Medidor à Decisão Sequencial Robusta em Escala de Frota**

*(Título de trabalho — pode ser abreviado para "Twins Digitais Adaptativos para Detecção de Furto de Energia em Escala de Frota".)*

## 1. Origem e vínculo com o artigo/repositório atual

Esta proposta parte diretamente do artigo em preparação neste diretório —
`Energy theft probability classification with adaptive observation windows in a digital twin for NB-IoT forensic telemetry` — e do protótipo de software associado (`src/fraud_dt/`).

O artigo demonstra, em escala de **um único medidor**, com **dados sintéticos** e com uma **política heurística de observação** (histerese sobre `basal`/`moderate`/`aggressive`), que um twin digital pode:

- fundir evidências baseadas em regras e em um classificador supervisionado (`decision/fusion.py`: `weighted`, `conservative_max`, `context_aware`);
- decidir dinamicamente a densidade de observação telemétrica via um `PolicyOrchestrator`;
- registrar essa decisão como um `TelemetryReconfigurationDecision` executável por um `MockTransport` NB-IoT/BLE;
- comparar politicas fixas (`fixed_long`, `fixed_short`) contra a política adaptativa em termos de F1, recall, custo de comunicação (bytes) e acerto do "slot crítico".

Os resultados já obtidos (`outputs/run_summary.md`, `outputs/campaign/campaign_summary.md`) são o ponto de partida empírico da tese, e também expõem suas próprias limitações, que se tornam as lacunas de pesquisa da tese:

1. A política de observação é **heurística e fixa** (limiares e histerese definidos a priori), não é otimizada nem possui garantias formais de trade-off entre detecção e custo de comunicação/energia.
2. O classificador supervisionado atinge **métricas perfeitas** (`accuracy = precision = recall = f1 = roc_auc = 1.0000`) em dados sintéticos — sinal de que o problema, como gerado, é linearmente separável e não testa robustez, ruído de rótulo, adversariedade ou *drift*.
3. Todo o pipeline opera sobre **um único ativo (twin)** por vez; não há tratamento do problema em **escala de frota**, onde o orçamento de comunicação/backhaul é compartilhado entre milhares de medidores.
4. A simulação de dispositivo e transporte (`MockForensicDevice`, `MockTransport`) é local e sintética; falta **validação com firmware real** e com um canal NB-IoT/BLE físico.
5. O documento `article_alignment.md` já lista como "evolução científica planejada": modelos mais fortes de falha de rede/dispositivo, integração com traços reais de firmware, curadoria mais forte de rótulos e ingestão online — ou seja, o próprio artigo reconhece que é uma prova de conceito, não um estudo definitivo.

Uma tese de doutorado, diferentemente do artigo, não pode ser "mais do mesmo em maior escala" — precisa de uma pergunta de pesquisa mais profunda, um arcabouço teórico próprio e validação além do protótipo sintético. As lacunas (1)-(5) acima definem exatamente esse espaço.

## 2. Problema de pesquisa

> **Como um twin digital pode decidir, de forma ótima e robusta, *quando e com que densidade observar* um medidor inteligente sob incerteza de risco de fraude, restrição de comunicação/energia e adversariedade do agente fraudador — e como essa decisão individual se generaliza para uma frota de milhares de medidores com orçamento de rede compartilhado?**

O artigo resolve uma versão heurística e de único ativo desse problema. A tese propõe tratá-lo como um problema de **decisão sequencial sob incerteza com custo de observação (active/optimal sensing)**, generalizando-o para múltiplos ativos e validando-o além do domínio sintético.

## 3. Perguntas de pesquisa

- **PP1 (formalização):** Como formular o problema de reconfiguração adaptativa de telemetria como um processo de decisão sequencial (ex.: POMDP / *restless multi-armed bandit* / aprendizado por reforço com custo de ação), de modo que a política heurística atual (`PolicyOrchestrator`) seja um caso particular subótimo desse arcabouço?
- **PP2 (robustez):** Quão sensíveis são o classificador de risco e a política adaptativa a rótulos ruidosos, *concept drift* e a um fraudador adversarial que aprende a evitar detecção variando o padrão de furto (`theft_ratio`, intermitência, horário)?
- **PP3 (escala de frota):** Dado um orçamento fixo de comunicação/backhaul NB-IoT compartilhado entre *N* twins, qual política de alocação de observação entre medidores maximiza a detecção agregada de perdas não técnicas, e como ela se compara a aplicar a política de único medidor independentemente a cada um?
- **PP4 (validação física):** Os ganhos observados em simulação (síntese + mocks) se mantêm quando o pipeline é validado contra firmware e canal de transporte reais (NB-IoT com contingência BLE), com dados de campo ou *hardware-in-the-loop*?
- **PP5 (auditabilidade):** Como preservar explicabilidade e rastreabilidade forense da decisão (necessária para uso como evidência técnica em processos de recuperação de perda) quando a política heurística é substituída por um modelo aprendido?

## 4. Objetivos

### 4.1 Objetivo geral

Propor, formalizar e validar um arcabouço de **twins digitais com controle de observação ótimo e robusto** para detecção de perdas não técnicas em infraestrutura de medição inteligente NB-IoT, evoluindo da política heurística de único medidor (estado da arte do artigo atual) para uma política aprendida, robusta a adversariedade e escalável a frotas de medidores sob restrição de comunicação.

### 4.2 Objetivos específicos

1. Formalizar o problema de política de observação do twin como processo de decisão sequencial sob incerteza com custo de ação (comunicação/energia) e comparar analiticamente/experimentalmente contra a política de histerese heurística já implementada.
2. Propor e treinar uma política de observação aprendida (ex.: aprendizado por reforço ou otimização Bayesiana de política), preservando a interface `TelemetryReconfigurationDecision` já definida, para permitir comparação direta com os baselines do artigo.
3. Caracterizar a robustez do pipeline de decisão (fusão + política) sob três eixos: ruído/escassez de rótulo, *drift* de padrão de consumo, e adversariedade do agente fraudador (fraude que se adapta à política de observação).
4. Generalizar o problema de único twin para frota, formulando a alocação de orçamento de observação entre *N* medidores como problema de otimização sob restrição (ex.: variante de *restless bandits* ou programação inteira), e avaliar ganho relativo à aplicação independente da política individual.
5. Projetar e executar um estudo de validação com firmware/hardware real (aproveitando o ecossistema de firmware do autor: `spc-fw`, NIC, e projetos correlatos de medição/IoT) e, se possível, dados de campo de uma distribuidora parceira, para testar a transferência do simulado para o real.
6. Manter explicabilidade e trilha de auditoria (comando, decisão, estado do twin) compatíveis com uso como evidência técnica, mesmo com política aprendida no lugar da heurística.

## 5. Fundamentação teórica (linhas a desenvolver)

A tese deve se apoiar e dialogar com quatro áreas, todas já tangenciadas pelo artigo, mas nenhuma delas aprofundada teoricamente nele:

- **Detecção de perdas não técnicas / fraude em medição de energia**: métodos baseados em regras, aprendizado supervisionado e não supervisionado sobre séries temporais de consumo; o artigo já contribui aqui com a divergência forense-vs-faturamento como *feature* central.
- **Twins digitais para sistemas ciberfísicos e infraestrutura crítica**: arquitetura de estado explícito, laço fechado de decisão-ação, papel do twin como camada de controle e não apenas de espelhamento passivo — ponto já estabelecido em `docs/framework_overview.md`, mas sem lastro teórico formal.
- **Sensoriamento ativo / decisão sequencial sob custo de observação**: POMDPs, *bandits* com custo de observação, *active learning* sequencial, otimização Bayesiana de política de amostragem — arcabouço que formaliza o que hoje é feito por histerese heurística.
- **Robustez adversarial e confiabilidade de sistemas de detecção de fraude**: aprendizado sob adversário adaptativo, *concept drift*, calibração de classificadores sob desbalanceamento extremo de classes — necessário porque o artigo atual não testa nada disso (métricas perfeitas em dados sintéticos são um sinal de alerta, não de sucesso).

## 6. Metodologia proposta (trajetória de estudos/artigos)

A tese é estruturada como uma sequência de estudos, cada um publicável isoladamente, todos compartilhando a base de código e a interface de twin já implementadas neste repositório.

| Estudo | Pergunta associada | Entregável | Relação com o repositório atual |
|---|---|---|---|
| E0 — Baseline (já concluído) | — | Artigo atual | `src/fraud_dt/` completo, `outputs/run_summary.md` |
| E1 — Formalização sequencial | PP1 | Artigo: framework POMDP/bandit para `PolicyOrchestrator` + comparação formal vs. heurística | Substituir/estender `control/orchestrator.py` mantendo a interface de `TelemetryReconfigurationDecision` |
| E2 — Robustez e adversariedade | PP2 | Artigo: avaliação sob ruído de rótulo, *drift* e fraudador adaptativo | Estender `synthetic.py` com geração adversarial e cenários de *drift*; estressar `decision/fusion.py` |
| E3 — Escala de frota | PP3 | Artigo: alocação de orçamento de observação entre *N* twins sob restrição de rede | Generalizar `runtime/simulator.py` para múltiplos `ForensicTwin` concorrentes com backhaul compartilhado |
| E4 — Validação física | PP4 | Artigo/capítulo: piloto com firmware real e/ou dados de campo | Substituir `MockForensicDevice`/`MockTransport` por integração real, aproveitando `spc-fw` e ecossistema de firmware NB-IoT/BLE do autor |
| E5 — Auditabilidade | PP5 | Capítulo/artigo curto: explicabilidade da política aprendida para uso como evidência técnica | Formalizar exportação de `twin_state_history.csv`/`command_plan.csv` como trilha auditável |

Essa sequência preserva o valor do artigo já escrito (E0) como o **baseline heurístico** contra o qual toda a tese é comparada — nenhum trabalho já feito é descartado, apenas superado de forma controlada e mensurável.

## 7. Contribuições esperadas

- Um arcabouço teórico de **política de observação de twin sob custo**, com a política heurística atual como caso particular demonstrável.
- Evidência quantitativa de **robustez (ou fragilidade) sob adversariedade e ruído**, hoje ausente do artigo (métricas perfeitas em dados sintéticos não respondem essa pergunta).
- Um método de **alocação de observação em escala de frota**, generalizando o problema de único ativo para o problema real de uma distribuidora com milhares de medidores e banda limitada.
- Validação, mesmo que parcial, contra **firmware/hardware real**, fechando a lacuna entre protótipo sintético e sistema implantável — aproveitando diretamente os projetos de firmware já existentes do autor.
- Um protocolo de **auditabilidade** compatível com uso forense/legal da decisão do twin, relevante para justificar a linha "forensic telemetry" já presente no nome do projeto.

## 8. Riscos e mitigação

- **Acesso a dados reais de campo**: pode não haver parceria com distribuidora a tempo do E4. Mitigação: E4 pode ser executado como *hardware-in-the-loop* com firmware próprio (`spc-fw`/NIC) e canal NB-IoT/BLE real, sem depender de dados de fraude reais de um cliente.
- **Complexidade do problema de frota (E3)**: otimização exata pode ser intratável em escala. Mitigação: usar relaxações conhecidas de *restless bandits*/heurísticas com garantia de aproximação, comparando contra a alocação heurística proporcional como baseline.
- **Escopo excessivo para 4 anos de doutorado**: os 5 estudos (E1–E5) são desenhados para permitir corte — E4 (validação física) pode ser reduzido a estudo piloto se o cronograma apertar, sem comprometer a tese (E1–E3 já constituem contribuição suficiente).

## 9. Cronograma indicativo (doutorado de 4 anos / 8 semestres)

| Semestre | Atividade principal |
|---|---|
| 1 | Revisão sistemática das quatro áreas teóricas; consolidação do baseline (E0) |
| 2 | Formalização sequencial (E1) — modelagem e primeiros experimentos |
| 3 | E1 — conclusão e submissão; início de E2 (robustez/adversariedade) |
| 4 | E2 — conclusão e submissão |
| 5 | E3 — formulação e simulação em escala de frota |
| 6 | E3 — conclusão e submissão; planejamento do piloto físico (E4) |
| 7 | E4 — execução do piloto (firmware/hardware real ou HIL) e E5 (auditabilidade) |
| 8 | Escrita, defesa e consolidação da tese |

## 10. Aderência ao contexto do autor

O nome dos campos de dados (`voltage_rms`, `active_power`, `alarm_last_gasp`, DLMS-facing objects) já foi escolhido no artigo para ficar próximo do domínio de firmware do autor. A tese aproveita essa escolha deliberadamente: o Estudo E4 (validação física) é viável precisamente porque o autor já mantém projetos de firmware de medição/IoT (ex.: `spc-fw`, NIC e correlatos), o que reduz o risco mais comum de teses nessa área — ficar restrita a simulação sem nunca tocar hardware real.

## 11. Observação sobre integridade científica

Esta proposta foi construída a partir da leitura direta do código e da documentação deste repositório (`README.md`, `docs/architecture.md`, `docs/framework_overview.md`, `docs/article_alignment.md`, `docs/manuscript_results_mapping.md`, `docs/data_model.md`, `outputs/run_summary.md`, `outputs/campaign/campaign_summary.md`). Não foram citadas referências bibliográficas específicas (autores/anos) para evitar citações fabricadas; a revisão de literatura formal (Seção 5) deve ser conduzida como primeira atividade do doutorado (Semestre 1 do cronograma).
