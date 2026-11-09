# Proposta de Tese de Doutorado (v2 — generalização para redes com restrição de recursos)

> Esta proposta substitui, em nível de escopo, `docs/proposta_tese_doutorado.md` (v1). A v1 permanece no repositório como registro histórico e como fonte de detalhes técnicos específicos do domínio de energia, que aqui são tratados como **um estudo de caso**, não como a identidade da tese.

## 0. Por que generalizar

A v1 desta proposta era, essencialmente, "pegar o protótipo de furto de energia NB-IoT e torná-lo mais rigoroso e robusto". Isso é um bom roteiro de *pesquisa aplicada*, mas é uma base frágil para uma tese de doutorado por um motivo estrutural: a contribuição central ficava amarrada a um único domínio de aplicação (perdas não técnicas em medição de energia) e a uma única tecnologia de rede (NB-IoT). Um comitê de tese pergunta, com razão: *o que aqui é conhecimento novo e generalizável, e o que é só engenharia de um produto?*

O trabalho recente de reconstrução do artigo para o IEEE Access (ver `artigo2026/novoartigo/`) expôs, na prática, dois problemas que **não são específicos de furto de energia**:

1. **Decisão sob restrição de recursos**: o twin precisa decidir *quando e com que densidade observar* um ativo, balanceando capacidade de detecção contra custo de comunicação (bytes, latência, overhead de sinalização) — um problema estrutural de qualquer rede restrita (NB-IoT, LoRaWAN, BLE mesh, redes de sensores industriais, redes ambientais) que precise sustentar telemetria "forense" (evidência acionável, não só monitoramento).
2. **Geração de dados forenses confiáveis**: a correção mais trabalhosa feita no artigo não foi um algoritmo novo — foi *consertar o gerador de dados sintéticos* para que ele não vazasse o rótulo na própria feature de detecção, respeitasse a resolução temporal nativa, e representasse heterogeneidade real de comportamento anômalo. Esse é um problema genérico de **qualquer domínio onde dado forense real é escasso, sensível ou legalmente restrito** — que é exatamente a situação da parceria com a distribuidora (dados reais existem, mas estão sob avaliação forense/jurídica e não podem ser publicados).

A tese proposta aqui eleva esses dois problemas ao nível de **contribuição científica generalizável**, usando o caso de furto de energia como **validação concreta**, não como limite do trabalho.

## 1. Título (de trabalho)

**Decisão Adaptativa e Geração de Dados Forenses Sintéticos para Sistemas Ciberfísicos em Redes com Restrição de Recursos: um Arcabouço Generalizável, com Validação em Telemetria Forense NB-IoT para Detecção de Perdas Não Técnicas**

*(Título curto para uso corrente: "Twins Digitais Forenses para Redes Restritas".)*

## 2. Problema de pesquisa

> **Como sistemas ciberfísicos que operam sobre redes com restrição de recursos (banda, energia, custo de dados) podem tomar decisões de observação defensáveis do ponto de vista forense, quando os dados reais necessários para treinar e validar essas decisões são escassos, sensíveis ou legalmente restritos — e como a própria geração de dados sintéticos pode ser sistematizada como um método rigoroso e generalizável para preencher essa lacuna, em vez de ser tratada como um detalhe de implementação?**

Este problema tem duas metades inseparáveis. Uma política de decisão só pode ser considerada validada na medida em que os dados usados para validá-la forem confiáveis; e um gerador de dados sintéticos só é útil na medida em que produzir um problema de dificuldade realista para a política que se quer avaliar. O ciclo de rejeição do artigo (ver `artigo2026/recomendações/recomendações.txt`) demonstrou isso de forma concreta: a política de observação parecia excelente (F1 ≈ 1,0) precisamente porque o gerador de dados era falho (vazamento de rótulo) — um problema de dados mascarado como sucesso de decisão.

## 3. Os dois pilares da contribuição

### Pilar A — Decisão adaptativa sob restrição de recursos (generalização do "PolicyOrchestrator")

Formalizar, de forma independente de domínio, o problema de decidir a densidade/regime de observação de um ativo monitorado remotamente, dado:

- um estado observacional $s_t$ (contexto do ativo, historicamente específico ao domínio, mas estruturalmente sempre decomponível em evidência direta, contexto temporal, contexto operacional/de rede);
- uma ação $a_t$ que seleciona um regime de observação, cada um com um custo de comunicação/energia associado;
- uma capacidade de detecção $D(s,a)$ e um custo $C(s,a)$, cujo trade-off é resolvido empiricamente (fronteira de Pareto) em vez de fixado a priori.

Essa formalização já existe, em versão concreta e testada, no framework `src/fraud_dt/` e no artigo IEEE Access (Seção III, Eqs. 1–3). O trabalho de tese é **abstrair essa formalização do domínio de energia**, definindo quais elementos são estruturais (o par $D(s,a)/C(s,a)$, a resolução de trade-off por fronteira de Pareto, a arquitetura de laço fechado percepção-decisão-ação) e quais são parâmetros de instância de domínio (o que conta como "evidência", o modelo de custo de rede específico, os modos de observação disponíveis).

### Pilar B — Geração de dados forenses sintéticos como método científico (generalização do `synthetic.py` corrigido)

Sistematizar, como protocolo reprodutível e independente de domínio, os critérios que um gerador de dados sintéticos forenses precisa satisfazer para produzir um problema de dificuldade realista e não circular:

1. **Não circularidade** entre o mecanismo gerador do rótulo e as *features* de detecção (o vazamento identificado e corrigido no artigo é um caso particular de um problema geral em geração de dados sintéticos para detecção de anomalias/fraude).
2. **Coerência física/metrológica** entre variáveis instantâneas e acumuladas (no caso de energia: tensão, corrente, potência, energia; em outros domínios: vazão/pressão em redes de água, temperatura/umidade em cadeia de frio, vibração/deformação em monitoramento estrutural).
3. **Heterogeneidade de severidade e comportamento** do evento anômalo (perfis de fraude `stealth`/`partial_constant`/`partial_variable`/`full_diversion` no artigo são uma instância de um princípio geral: eventos forenses reais não têm severidade nem regularidade temporal uniformes).
4. **Fidelidade à resolução temporal nativa** do sistema de observação (o bug da resolução de 15 min vs. 5 min no artigo é uma instância de um problema geral: a granularidade da geração sintética deve ser, no mínimo, tão fina quanto a granularidade da decisão que ela vai validar).
5. **Ruído independente do rótulo**, representando degradação de comunicação, deriva de sensor e comportamento legítimo mas errático.

O trabalho de tese é transformar esses cinco critérios — hoje aplicados ad hoc a um gerador de energia — em um **protocolo/checklist formal, com métricas de verificação** (ex.: testes estatísticos de vazamento label-feature, análise de sensibilidade da fronteira de Pareto à escolha do gerador) que qualquer pesquisador possa aplicar a um novo domínio de dados forenses sintéticos.

### Por que os dois pilares precisam estar na mesma tese

Um gerador de dados melhor (Pilar B) muda o que uma política de decisão (Pilar A) aparenta valer — isso já foi observado diretamente neste projeto: corrigir o gerador de dados fez o F1 agregado cair de ~0,97 para algo mais realista, e mudou qual política domina qual no plano detecção×custo. A tese propõe usar essa interação como uma **contribuição própria**: um framework onde a *sensibilidade* da política de decisão à qualidade do gerador de dados é, ela mesma, um diagnóstico de quão confiável é uma validação sintética — algo que a literatura de digital twins e de detecção de fraude raramente formaliza.

## 4. Perguntas de pesquisa

- **PP1 (formalização do Pilar A):** Quais elementos da formalização $D(s,a)/C(s,a)$ e da resolução por fronteira de Pareto são estruturais a qualquer problema de observação adaptativa sob restrição de rede, e quais são parâmetros de instanciação de domínio? Como uma política de decisão aprendida (ex.: RL/POMDP) se compara à política heurística de histerese em pelo menos dois domínios distintos?
- **PP2 (formalização do Pilar B):** É possível definir critérios verificáveis (não apenas qualitativos) de não circularidade e de realismo de dificuldade estatística para geradores de dados forenses sintéticos, aplicáveis a mais de um domínio?
- **PP3 (interação entre pilares):** Como a escolha do método de geração de dados sintéticos (Pilar B) afeta a fronteira de Pareto e a política ótima resultante (Pilar A)? Essa sensibilidade pode ser usada como um teste de validade de um estudo de validação sintética?
- **PP4 (generalização entre domínios):** O framework (Pilares A+B) desenvolvido e validado em telemetria forense de energia (NB-IoT) se transfere para pelo menos um segundo domínio de rede restrita com necessidade forense semelhante (ex.: fraude/vazamento em redes de água ou gás via LPWAN, adulteração de equipamento industrial via IoT restrito, conformidade ambiental) — com que adaptações?
- **PP5 (validação e escala):** Os ganhos observados em simulação se mantêm sob adversariedade (fraudador que se adapta à política), em escala de frota (orçamento de rede compartilhado entre milhares de ativos), e, no estudo de caso de energia, contra firmware/hardware real?

## 5. Objetivos

### 5.1 Objetivo geral

Propor, formalizar e validar um arcabouço generalizável para (i) decisão adaptativa de observação sob restrição de recursos de rede e (ii) geração metodologicamente rigorosa de dados forenses sintéticos, demonstrando sua aplicabilidade em telemetria forense de energia (NB-IoT) como estudo de caso primário e em pelo menos um segundo domínio de rede restrita como teste de generalização.

### 5.2 Objetivos específicos

1. Abstrair a formalização $D(s,a)/C(s,a)$ e a resolução por fronteira de Pareto (já implementadas para o domínio de energia) em um arcabouço de decisão independente de domínio, documentando explicitamente a interface entre o núcleo genérico e os parâmetros específicos de cada instância.
2. Codificar os cinco critérios de geração de dados forenses sintéticos (Seção 3, Pilar B) como um protocolo verificável, com métricas objetivas de não circularidade e de dificuldade estatística.
3. Caracterizar formalmente a interação entre os dois pilares: como mudanças no gerador de dados (Pilar B) deslocam a fronteira de Pareto e a política recomendada (Pilar A).
4. Validar o arcabouço completo no estudo de caso de telemetria forense de energia NB-IoT (base já construída em `src/fraud_dt/` e no artigo IEEE Access), incluindo robustez adversarial, escala de frota, e — na medida do possível dentro do prazo do doutorado — validação com firmware/hardware real.
5. Selecionar, em conjunto com o orientador, um segundo domínio de rede restrita com necessidade de decisão forense (candidatos: fraude/perda em redes de água ou gás via LPWAN; adulteração de equipamento industrial monitorado por IoT restrito; conformidade ambiental/emissões) e instanciar o arcabouço nesse domínio, mesmo que em escopo reduzido, para testar PP4.
6. Preservar, em ambos os pilares, uma trilha de auditoria e explicabilidade compatível com uso da decisão como evidência técnica — relevante tanto para o domínio de energia (recuperação de perda) quanto para qualquer segundo domínio forense.

## 6. Fundamentação teórica

A tese dialoga com cinco áreas — as quatro já previstas na v1, mais uma nova, explicitamente decorrente do Pilar B:

- **Sensoriamento ativo / decisão sequencial sob custo de observação**: POMDPs, *bandits* com custo de observação, otimização multiobjetivo/Pareto para trade-offs de detecção×custo — arcabouço teórico do Pilar A.
- **Metodologia de dados sintéticos e validade de simulação (*sim-to-real gap*)**: literatura sobre geração de dados sintéticos para aprendizado de máquina forense/de segurança, vazamento de rótulo (*label leakage*), e transferência simulação-realidade — arcabouço teórico do Pilar B, área nova em relação à v1, e a que mais precisa de revisão bibliográfica dedicada, já que os critérios da Seção 3 foram derivados empiricamente neste projeto e ainda não foram formalmente situados na literatura.
- **Twins digitais para sistemas ciberfísicos e infraestrutura crítica**: papel do twin como camada de decisão ativa (não só espelhamento passivo), já estabelecido em `docs/framework_overview.md`.
- **Detecção de fraude/anomalia sob restrição de comunicação em redes de sensores/IoT restritas**: não mais restrita à literatura de perdas não técnicas em energia — deve incluir literatura equivalente de outros domínios de rede restrita (água, gás, monitoramento industrial/ambiental) para sustentar PP4.
- **Robustez adversarial e confiabilidade sob incerteza**: *concept drift*, adversário adaptativo, calibração sob desbalanceamento — mantido da v1, aplicável a ambos os pilares.

## 7. Metodologia proposta (trajetória de estudos/artigos)

| Estudo | Pergunta | Entregável | Relação com o trabalho já feito |
|---|---|---|---|
| E0 — Baseline (concluído) | — | Artigo IEEE Access (`artigo2026/novoartigo/access.tex`) + protótipo `src/fraud_dt/` | Ponto de partida empírico de ambos os pilares |
| E1 — Formalização genérica do Pilar A | PP1 | Artigo metodológico: arcabouço de decisão adaptativa sob restrição de rede, independente de domínio | Abstrai `control/orchestrator.py`, `decision/`, `scripts/run_policy_optimization.py` |
| E2 — Protocolo genérico do Pilar B | PP2 | Artigo metodológico: critérios verificáveis para geração de dados forenses sintéticos não circulares | Abstrai `synthetic.py` e as correções feitas durante a reconstrução do artigo |
| E3 — Interação entre pilares | PP3 | Artigo: análise de sensibilidade da fronteira de Pareto à escolha do gerador de dados | Usa `scripts/run_policy_optimization.py` + variações controladas de `synthetic.py` |
| E4 — Segundo domínio (generalização) | PP4 | Artigo/capítulo: instanciação do arcabouço em um segundo domínio de rede restrita | Novo, a definir com o orientador; reaproveita a arquitetura de `src/fraud_dt/` como referência de implementação |
| E5 — Robustez, escala e validação física (energia) | PP5 | Artigo(s): adversariedade, escala de frota, e piloto com firmware/hardware real | Continuação direta do roteiro já mapeado na v1 (`spc-fw`, ecossistema de firmware do autor) |

Diferença estrutural em relação à v1: lá, todos os estudos aprofundavam o mesmo protótipo de energia. Aqui, **E1 e E2 são estudos de abstração/generalização** (o núcleo teórico da tese), **E3 é o elo entre eles**, e **E4/E5 são as validações** — uma em domínio novo (mostrando generalidade), outra em profundidade no domínio original (mostrando rigor).

## 8. Contribuições esperadas

- Um **arcabouço de decisão adaptativa sob restrição de recursos**, independente de domínio, com o problema de energia como instância validada e pelo menos uma segunda instância de validação.
- Um **protocolo verificável de geração de dados forenses sintéticos**, preenchendo uma lacuna metodológica real (a literatura de detecção de fraude/anomalia raramente formaliza como auditar um gerador sintético quanto a vazamento de rótulo ou dificuldade estatística realista).
- Uma **caracterização original da interação entre qualidade do dado sintético e política de decisão ótima** — um resultado que não é só "mais um sistema de detecção", mas uma contribuição metodológica sobre como avaliar sistemas de detecção.
- Evidência de **generalização entre domínios de rede restrita**, o que fortalece substancialmente a defensabilidade da tese perante um comitê (evita a crítica "isso só funciona para o seu problema específico").
- No domínio de energia especificamente: robustez adversarial, escala de frota e, na medida do possível, validação física — herdados e aprofundados da v1.

## 9. Riscos e mitigação

- **Escopo ainda maior que a v1 (2 domínios + 2 estudos de abstração)**: mitigação — E4 (segundo domínio) pode ser executado em escopo reduzido, inclusive reaproveitando um *dataset* público de outro domínio de rede restrita já existente na literatura (não é necessário construir um segundo sistema completo do zero); se o cronograma apertar, E4 pode virar um estudo piloto/capítulo curto em vez de artigo completo, sem comprometer a tese (E1–E3, no domínio de energia, já constituem contribuição suficiente).
- **Segundo domínio inexistente ou de difícil acesso**: mitigação — a escolha de E4 deve ser feita com o orientador já na Seção 12 (resumo para discussão), priorizando um domínio com dataset público disponível (ex.: monitoramento de redes de água, séries de vibração estrutural) em vez de um domínio que exigiria nova coleta de campo.
- **Risco de diluição**: generalizar demais pode enfraquecer a profundidade em cada domínio. Mitigação — o domínio de energia permanece como estudo de caso *primário e aprofundado* (com todos os estudos E0, E1, E2, E3, E5); o segundo domínio (E4) é deliberadamente mais leve, servindo para testar generalização, não para ser um segundo estudo completo.
- **Dados reais de energia**: como já registrado na v1, dados de campo existem via parceria com distribuidora, mas estão sob avaliação forense/jurídica; a tese continua validando com dados sintéticos rigorosos (Pilar B) enquanto essa liberação não ocorre.

## 10. Cronograma indicativo (doutorado de 4 anos / 8 semestres)

| Semestre | Atividade principal |
|---|---|
| 1 | Revisão bibliográfica das cinco áreas (Seção 6), com ênfase na área nova (metodologia de dados sintéticos/*sim-to-real*); consolidação do baseline (E0) |
| 2 | E1 — formalização genérica do Pilar A |
| 3 | E1 — conclusão e submissão; início de E2 (protocolo do Pilar B) |
| 4 | E2 — conclusão e submissão; decisão final do segundo domínio (E4) com o orientador |
| 5 | E3 — interação entre pilares (sensibilidade da fronteira de Pareto ao gerador de dados) |
| 6 | E3 — conclusão e submissão; início de E4 (segundo domínio) |
| 7 | E4 — conclusão; E5 — robustez adversarial e escala de frota (domínio de energia) |
| 8 | E5 — validação física (se viável) ou consolidação como capítulo de limitações; escrita e defesa da tese |

## 11. Aderência ao contexto do autor

Mantido da v1: o ecossistema de firmware de medição/IoT do autor (`spc-fw`, NIC e projetos correlatos) viabiliza a validação física (E5) no domínio de energia, reduzindo o risco mais comum de teses nessa área — ficar restrita a simulação. A generalização proposta aqui não abandona essa vantagem; ela a preserva como o estudo de caso primário e mais aprofundado, ao mesmo tempo em que constrói, ao redor dele, uma contribuição científica que não depende só dele.

## 12. Observação sobre integridade científica

Esta proposta foi construída a partir da leitura direta do repositório (`src/fraud_dt/`, `artigo2026/novoartigo/access.tex`, `artigo2026/recomendações/recomendações.txt`, `docs/*.md`) e da v1 desta proposta. Os cinco critérios do Pilar B (Seção 3) foram derivados empiricamente das correções reais feitas durante a reconstrução do artigo para o IEEE Access, não de uma revisão de literatura ainda não realizada — essa revisão (Seção 6) é a primeira atividade formal do doutorado. Nenhuma referência bibliográfica específica foi citada aqui para evitar citação fabricada; o segundo domínio de validação (E4) ainda não foi escolhido e deve ser definido em conjunto com o orientador (ver resumo em `docs/resumo_orientador_tese.md`).
