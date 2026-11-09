# Resumo para discussão com o orientador — proposta de tese (v2)

## Em uma frase

Proponho deslocar a tese de "um sistema de detecção de furto de energia" para **um arcabouço genérico de duas partes — decisão adaptativa sob restrição de rede, e geração rigorosa de dados forenses sintéticos —, validado em furto de energia (NB-IoT) e, se possível, em um segundo domínio de rede restrita**, para tornar a contribuição defensável como conhecimento novo e não apenas como engenharia de um produto.

## De onde isso vem

Na reconstrução do artigo rejeitado (agora preparado para o IEEE Access), os dois problemas mais sérios apontados pelos avaliadores não eram sobre energia — eram sobre **método**:

1. A política de observação era heurística, sem resolução formal do trade-off detecção×custo.
2. O gerador de dados sintéticos vazava o rótulo na própria *feature* de detecção, inflando os resultados (F1/AUROC ≈ 1,0 artificialmente).

Corrigir isso não foi "melhorar o produto de energia" — foi resolver dois problemas que aparecem em qualquer sistema de decisão forense sobre rede restrita: *quando vale a pena observar mais*, e *como validar isso quando dado real é escasso/sensível/restrito por sigilo legal* (que é literalmente a nossa situação com a distribuidora).

## A proposta em duas frases

- **Pilar A (decisão):** formalizar, de forma independente de domínio, como decidir a densidade de observação de um ativo sob restrição de banda/custo de dados, resolvendo o trade-off detecção×custo por fronteira de Pareto em vez de pesos arbitrários.
- **Pilar B (dados):** transformar os critérios que corrigimos no gerador sintético (não vazar rótulo, respeitar resolução temporal nativa, representar heterogeneidade real do evento anômalo, ruído independente do rótulo) em um **protocolo verificável**, aplicável a outros domínios de dado forense sintético.

O elo entre os dois (e a parte que acho mais interessante para uma tese): **mudar o gerador de dados muda a política ótima resultante** — já observamos isso na prática (F1 caiu de ~0,97 para algo realista depois da correção, e a política recomendada mudou). Isso pode virar um resultado próprio: usar a sensibilidade da política à qualidade do dado sintético como *diagnóstico* de quão confiável é uma validação feita só com dados sintéticos.

## Por que isso é mais forte como tese

Um comitê pergunta "o que aqui é generalizável?". Com o recorte só em energia, a resposta fica frágil. Com os dois pilares formalizados, energia vira **o estudo de caso mais aprofundado** (onde já temos protótipo, artigo e ecossistema de firmware próprio para validação física), mas a tese não depende só dele.

## O que preciso decidir com você

1. **Segundo domínio de validação (Pilar A+B fora de energia).** Candidatos que exigem só *dataset público* (sem precisar construir um segundo sistema do zero): fraude/perda em redes de água ou gás via LPWAN; adulteração de equipamento industrial monitorado por IoT restrito; monitoramento estrutural/ambiental sob restrição de banda. Qual você acha mais viável/interessante — ou prefere manter escopo 100% em energia e deixar a generalização só como discussão teórica (sem segundo estudo empírico)?
2. **Profundidade formal do Pilar A.** Vale ir até POMDP/aprendizado por reforço, ou a resolução por busca em grade + fronteira de Pareto (já implementada) é suficiente como formalização de doutorado, com RL ficando como trabalho futuro?
3. **Peso relativo dos dois pilares.** Tratá-los como igualmente centrais (como escrevi), ou você prefere um como contribuição principal e o outro como suporte metodológico?
4. **Dados reais de energia.** Mantemos a expectativa de que a liberação pela distribuidora (hoje bloqueada por processo forense/jurídico) pode acontecer dentro do prazo do doutorado, ou devo planejar 100% em torno de dados sintéticos + validação física com firmware próprio?
5. **Cronograma.** A v2 é mais ambiciosa que a v1 (dois estudos de abstração + dois domínios). Cabe em 4 anos, ou prefere que eu já corte o segundo domínio para um capítulo/piloto reduzido desde o início do planejamento?

## Documento completo

A proposta detalhada (perguntas de pesquisa, objetivos, metodologia por estudo, cronograma) está em `docs/proposta_tese_doutorado_redes_restritas.md`. A versão anterior, focada só em energia, continua em `docs/proposta_tese_doutorado.md` para referência.
