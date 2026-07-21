# Recomendações de templates com marcas reais

Data da validação: 21 de julho de 2026.

## Objetivo

Verificar se o Molda prioriza composições coerentes com a linguagem encontrada
nos materiais da marca, sem esconder o catálogo completo nem inventar uma
linguagem visual especializada quando a evidência é insuficiente.

## Material principal

O manual `MC-DOCERIA.pdf` foi usado como caso de estresse porque suas nove
páginas são imagens achatadas e não contêm texto PDF nativo. O arquivo foi
mantido fora do repositório; somente seu hash foi registrado:

`79B81B7BC548D867890DD840D2BA4F048801E12B491078D51F6E85B375787D24`

O fluxo local importou o PDF sem diagnóstico bloqueante e recuperou por OCR em
português e inglês:

- a ideia central de "afeto em camadas";
- escrita quente e próxima;
- a restrição contra uma expressão fria e dessaturada;
- as cores `#722024`, `#F8EEE0` e `#1A1A1A`;
- Cormorant Garamond e Montserrat;
- variantes de logo para fundo claro e escuro.

Nenhuma dessas informações precisou ser marcada manualmente para que o Kit
fosse montado.

## Defeito encontrado e correção

Antes da correção, a palavra "camadas" podia sobrepor os demais sinais e levar
uma marca artesanal para famílias de dados, diagramas ou tipografia cinética.
Também havia dois erros semânticos: o campo de limites era lido como descrição
positiva e termos eram encontrados dentro de outras palavras, como `pessoal`
em `impessoal`.

A direção criativa agora:

1. separa afirmações dos limites e inverte a polaridade dos limites;
2. reconhece palavras e expressões completas;
3. prefere a expressão específica quando há sobreposição, como "baixo
   contraste" em vez de "contraste";
4. penaliza contradições fortes de energia, geometria, materialidade e
   contraste;
5. exige sinais mínimos antes de priorizar famílias especializadas.

## Matriz de marcas reais

| Marca | Base | Catálogo | Sugestões | Famílias priorizadas |
| --- | --- | ---: | ---: | --- |
| MC Doceria | linguagem da marca | 88 | 8 | colagem editorial, editorial tipográfico, campanha de produto e editorial de moda |
| Digital Artisan | linguagem da marca | 92 | 8 | campanha de produto, modernismo geométrico, editorial tipográfico e dinâmica construtivista |
| ORPHÉA | linguagem da marca | 88 | 8 | editorial tipográfico, brutalismo tipográfico, tipografia cinética e campanha de produto |
| Vita Cann Med | exploratória | 89 | 8 | editorial tipográfico, brutalismo tipográfico, sistema suíço e composição essencial |

O resultado exploratório da Vita Cann Med é intencional: a identidade persistida
contém evidência textual insuficiente para afirmar uma direção de marca. O Molda
expõe essa incerteza em vez de inventar precisão.

## Verificação de produto

No navegador, o caso MC Doceria apresentou oito sugestões em pares
principal/alternativa tanto no Kit quanto no Modo Carrossel. Os catálogos
completos permaneceram acessíveis: 88 peças no Kit e 81 composições compatíveis
com o formato do carrossel. A edição preservou:

- todas as cores confirmadas para fundo e texto;
- troca automática ou manual entre logo principal, clara e escura;
- filtro por família e retorno às sugestões;
- console sem erros no fluxo validado.

## Casos automatizados

A cobertura acrescentada prova:

- inversão de restrições e casamento por palavra completa;
- leitura de variantes masculinas e femininas em português;
- prioridade de expressões compostas;
- resultado determinístico;
- ausência de sobreajuste técnico com OCR parcial;
- manutenção dos pares principal/alternativa;
- recomendação limitada aos layouts realmente disponíveis no formato;
- fallback exploratório quando não há direção confirmável.

## Gates finais locais

- motor: 401 aprovados e 1 ignorado;
- API: 174 aprovados e 2 ignorados;
- renderizador: 85 aprovados;
- web: 171 aprovados;
- SDK Python: 6 aprovados;
- contrato de release: 11 aprovados.

Total: 848 testes aprovados, 3 ignorados, formatação, lint, typecheck e builds de
produção verdes. Os arquivos privados usados na validação não foram adicionados
ao Git.
