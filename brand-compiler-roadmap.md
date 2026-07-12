# Plano de ação — Brand Compiler

**Objetivo:** chegar a uma primeira versão demonstrável do ciclo completo:

```text
importar marca → gerar PPTX → editar → lint → corrigir → reabrir
```

Este plano assume um desenvolvedor principal, com apoio eventual de design e testes. As fases são sequenciais por dependência, não por calendário rígido.

---

## 1. Resultado que precisa existir antes de qualquer expansão

O primeiro marco não é “ter uma plataforma”. É executar este roteiro:

1. importar tokens e um template de marca;
2. compilar um Brand IR válido;
3. renderizar um deck com capa e slide de conteúdo;
4. abrir o arquivo no PowerPoint sem reparo;
5. alterar fonte, cor e posição do logo;
6. enviar novamente o arquivo;
7. detectar as três violações;
8. aplicar correções;
9. reabrir o arquivo corrigido;
10. manter texto, imagem e layout editáveis.

Esse é o **walking skeleton**. Nada de DOCX, IA, editor próprio ou colaboração antes dele.

---

## 2. Gate 0 — Preparação e prova de mecânica PPTX

### Objetivo

Eliminar o maior risco técnico antes de construir produto.

### Entregas

- repositório;
- CI;
- corpus inicial de fixtures;
- três spikes;
- quatro ADRs;
- definição de pronto do walking skeleton.

### Spike A — Clonar e preencher layout

Entrada:

- um template PPTX real com master e dois layouts.

Resultado:

- criar um novo slide baseado em layout;
- preencher título e corpo;
- inserir logo;
- salvar;
- abrir sem reparo.

Critério de aprovação:

- objetos continuam editáveis;
- o slide referencia o layout correto;
- o validator não encontra erro bloqueante.

### Spike B — Round-trip

Processo:

- abrir o arquivo gerado;
- alterar texto e formatação;
- salvar no PowerPoint;
- reler com Open XML SDK;
- reencontrar slide, shapes e roles.

Critério de aprovação:

- IDs/tags essenciais sobrevivem ou podem ser reconstruídos;
- o parser identifica a fonte e a cor alteradas.

### Spike C — Preview

Processo:

- renderizar o PPTX em PDF e PNG em container isolado.

Critério de aprovação:

- preview é reproduzível;
- falha de conversão gera diagnóstico e não invalida o PPTX estruturalmente correto.

### Saída do Gate 0

Documento `GO-NO-GO.md` com:

- o que funcionou;
- diferenças entre editores;
- limitações;
- decisão de continuar ou ajustar a tese.

---

## 3. Gate 1 — Contratos e core

### Objetivo

Criar o núcleo independente de UI, banco e editor.

### Entregas

- schemas v0.1;
- Brand IR;
- Deck Spec;
- Lint Report;
- value objects;
- token resolver;
- provenance;
- diagnostics;
- CLI de validação.

### Backlog

#### BC-001 — Inicializar monorepo

Aceite:

- solução .NET;
- app web separada;
- build único;
- lint e tests no CI;
- versionamento centralizado.

#### BC-002 — Adicionar JSON Schemas

Aceite:

- schemas em `schemas/`;
- exemplos válidos;
- exemplos inválidos de teste;
- validação no CI.

#### BC-003 — Criar tipos de domínio

Aceite:

- `BrandId`, `BrandRevisionId`, `ArtifactId`;
- `Length`, `Color`, `Bounds`, `Sha256`;
- sem strings primitivas em toda a camada core.

#### BC-004 — Implementar diagnostics

Aceite:

- código estável;
- severidade;
- path;
- source ref;
- mensagem;
- serialização JSON.

#### BC-005 — Implementar provenance

Aceite:

- todo token compilado possui source ref;
- múltiplas evidências podem coexistir;
- origem aparece na saída da CLI.

#### BC-006 — Resolver tokens DTCG

Aceite:

- tipos;
- aliases;
- chained aliases;
- ciclos;
- dimensões;
- cores;
- typography;
- deprecation;
- extensões preservadas.

#### BC-007 — CLI `package validate`

Aceite:

- valida manifesto;
- valida arquivos referenciados;
- verifica paths;
- gera diagnostics;
- exit code diferente de zero em erro.

---

## 4. Gate 2 — Importador e compilador de marca

### Objetivo

Transformar um Brand Package em Brand IR draft e publicado.

### Entregas

- secure unpacker;
- importer registry;
- DTCG importer;
- PPTX template analyzer;
- conflict resolver;
- Brand IR compiler;
- snapshot de revisão.

### Backlog

#### BC-010 — Secure unpacker

Aceite:

- bloqueia path traversal;
- limita bytes e entries;
- faz MIME sniff;
- rejeita macro;
- calcula hashes.

#### BC-011 — Importer registry

Interface:

```csharp
public interface IBrandSourceImporter
{
    bool CanImport(SourceArtifact source);
    Task<ImportEvidenceSet> ImportAsync(
        SourceArtifact source,
        ImportContext context,
        CancellationToken cancellationToken);
}
```

Aceite:

- adapters registrados por DI;
- diagnostics isolados por source;
- import parcial não derruba toda a execução.

#### BC-012 — PPTX template analyzer

Aceite:

- extrai page size;
- themes;
- masters;
- layouts;
- placeholders;
- nomes e IDs;
- imagens incorporadas;
- external relationships;
- macro/OLE diagnostics.

#### BC-013 — Resolver autoridade por domínio

Aceite:

- prioridade configurável;
- conflito explícito;
- valor escolhido com justificativa;
- inferência nunca vence fonte autoritativa.

#### BC-014 — Compilar Brand IR

Aceite:

- JSON válido;
- schemaVersion;
- revision;
- tokens resolvidos;
- roles;
- assets;
- profile;
- layouts;
- rules;
- provenance.

#### BC-015 — CLI `brand import`

Aceite:

```bash
brandctl brand import ./brand-package --out brand-ir.json
```

- arquivo de saída;
- diagnostics em stderr/JSON;
- exit code previsível.

---

## 5. Gate 3 — Renderer PPTX

### Objetivo

Gerar apresentações nativas usando template e layouts existentes.

### Entregas

- Deck Spec parser;
- layout resolver;
- slot binder;
- text fitter;
- asset placer;
- tagger;
- Open XML validator;
- renderer CLI.

### Backlog

#### BC-020 — Validar Deck Spec

Aceite:

- layout existe;
- campos obrigatórios;
- tipos compatíveis;
- assets resolvíveis;
- profile existe.

#### BC-021 — Layout resolver

Aceite:

- resolve por ID;
- valida purpose;
- retorna slots;
- falha explicitamente quando o profile não combina.

#### BC-022 — Clonar slide a partir de layout

Aceite:

- novo slide part;
- relationship correto;
- slide ID único;
- layout relationship preservado;
- master e theme preservados.

#### BC-023 — Preencher texto

Aceite:

- título e corpo;
- rich text básico;
- bullets simples;
- notas;
- sem converter para imagem.

#### BC-024 — Fitting

Aceite:

- min font size;
- max characters;
- shrink controlado;
- continuation slide;
- erro sem truncamento.

#### BC-025 — Colocar assets

Aceite:

- logo;
- imagem;
- contain;
- cover/crop;
- aspect ratio;
- hash/tag.

#### BC-026 — Tabelas básicas

Aceite:

- headers;
- rows;
- estilo;
- dimensões;
- overflow diagnosticado.

#### BC-027 — Tags do runtime

Aceite:

- shape name;
- alt/description;
- custom properties;
- custom XML map;
- brandRevisionId.

#### BC-028 — Open XML validation

Aceite:

- erro estrutural bloqueia saída;
- warning é registrado;
- relatório anexado ao render run.

#### BC-029 — CLI `presentation render`

Aceite:

```bash
brandctl presentation render \
  --brand brand-ir.json \
  --deck deck-spec.json \
  --out deck.pptx
```

---

## 6. Gate 4 — Parser, linter e fixer

### Objetivo

Fechar o ciclo de round-trip.

### Entregas

- Document Graph;
- style resolution;
- rule registry;
- regras P0;
- findings;
- fix operations;
- relint;
- CLI.

### Backlog

#### BC-030 — Document Graph

Aceite:

- slides;
- shapes;
- bounds;
- texto;
- runs;
- images;
- layout refs;
- tags;
- effective style.

#### BC-031 — Reencontrar roles

Aceite:

- por tag;
- por placeholder;
- por layout;
- por geometria com confidence;
- objetos não classificados preservados.

#### BC-032 — Rule registry

Aceite:

- regras carregadas por type;
- rule ID estável;
- seletor;
- execução determinística;
- rule timing.

#### BC-033 — Allowed font rule

Aceite:

- detecta direct formatting;
- detecta fonte efetiva;
- localiza run;
- oferece fix.

#### BC-034 — Allowed color rule

Aceite:

- normaliza theme color e RGB;
- trata tint/shade;
- calcula token mais próximo;
- não corrige se distância ultrapassar limite configurado.

#### BC-035 — Logo rules

Aceite:

- required;
- approved hash;
- min size;
- aspect ratio;
- position em slot conhecido.

#### BC-036 — Safe area e aspect ratio

Aceite:

- bounds;
- page size;
- severity configurável;
- localização por shape.

#### BC-037 — Text overflow

Aceite:

- detecta overflow conhecido;
- não apaga nem resume;
- finding não fixável no P0.

#### BC-038 — Fix operations

Aceite:

- preconditions;
- aplicação em cópia;
- idempotência;
- validator;
- audit diff.

#### BC-039 — Relint

Aceite:

- todo fix run dispara novo lint;
- finding corrigido desaparece;
- novos findings são reportados.

#### BC-040 — CLIs `lint` e `fix`

Aceite:

```bash
brandctl presentation lint ...
brandctl presentation fix ...
```

---

## 7. Gate 5 — Plataforma web mínima

### Objetivo

Expor o ciclo já comprovado, sem criar editor próprio.

### Entregas

- autenticação;
- brands;
- upload;
- jobs;
- artifact downloads;
- render form;
- lint report;
- fix selection;
- revision history.

### Telas

1. lista de marcas;
2. importar pacote;
3. diagnostics e conflict review;
4. publicar Brand Revision;
5. criar apresentação;
6. status do render;
7. documento e revisões;
8. relatório de conformidade;
9. seleção de fixes;
10. auditoria.

### Backlog

#### BC-050 — Banco e migrations

Aceite:

- entidades do system design;
- índices por workspace;
- JSONB;
- unique constraints;
- migrations reproduzíveis.

#### BC-051 — Object storage

Aceite:

- upload streaming;
- hash;
- deduplicação;
- signed URL;
- retenção.

#### BC-052 — Job worker

Aceite:

- fila;
- retry;
- timeout;
- cancellation;
- dead-letter;
- dashboard interno.

#### BC-053 — API v1

Aceite:

- OpenAPI;
- idempotency;
- error codes;
- auth;
- resource authorization.

#### BC-054 — Web upload e import status

Aceite:

- progress;
- diagnostics;
- sem bloquear request;
- retry explícito.

#### BC-055 — Web render

Aceite:

- selecionar Brand Revision;
- escolher profile/layouts;
- enviar Deck Spec;
- baixar PPTX.

#### BC-056 — Web lint/fix

Aceite:

- upload de revisão;
- findings por slide;
- filtro por severidade;
- aplicar fixes selecionados;
- baixar nova revisão.

---

## 8. Gate 6 — Preview e editor embutido

### Objetivo

Melhorar o fluxo sem alterar a fonte canônica.

### Entregas

- PDF/thumbnails;
- preview por slide;
- ONLYOFFICE adapter;
- callback;
- force-save;
- lint automático ao salvar;
- plugin/painel inicial.

### Restrições

- integração opcional;
- core não depende do editor;
- edição embutida não muda o modelo de revisão;
- cada save material cria Document Revision;
- lint não roda a cada tecla no primeiro release.

---

## 9. Gate 7 — Open-source beta

### Objetivo

Tornar o projeto reproduzível por terceiros.

### Entregas

- licença;
- threat model;
- CONTRIBUTING;
- CODE_OF_CONDUCT;
- SECURITY;
- arquitetura;
- examples;
- fixtures sem ativos proprietários;
- Docker Compose;
- release assinada;
- SBOM;
- changelog.

### Critérios

- setup local documentado;
- demo reproduzível;
- nenhum segredo no repo;
- dependências licenciadas;
- schemas publicados;
- API versionada;
- issues de “good first issue” reais;
- política de compatibilidade.

---

## 10. Ordem de execução dos primeiros 15 itens

1. BC-001 — monorepo e CI  
2. BC-002 — schemas  
3. BC-003 — value objects  
4. Spike A — clone de layout  
5. Spike B — round-trip  
6. BC-006 — token resolver  
7. BC-012 — template analyzer  
8. BC-013 — authority resolver  
9. BC-014 — Brand IR compiler  
10. BC-020 — Deck Spec validator  
11. BC-022 — slide clone  
12. BC-023 — text fill  
13. BC-028 — Open XML validation  
14. BC-030 — Document Graph  
15. BC-033 — font rule  

Essa ordem produz evidência técnica cedo. Não priorize login, dashboard ou design visual da UI antes disso.

---

## 11. Primeiro ciclo de execução

### Bloco 1 — Fixtures e contratos

- escolher dois templates PPTX reais, com permissão;
- criar pacote ACME sintético;
- escrever Deck Spec de dois slides;
- registrar expected Brand IR;
- configurar schemas e validação.

### Bloco 2 — Mecânica PPTX

- analisar package parts;
- clonar layout;
- inserir slide;
- preencher placeholder;
- inserir logo;
- validar e abrir.

### Bloco 3 — Round-trip

- editar no PowerPoint;
- salvar;
- parsear;
- registrar diferenças;
- ajustar tags redundantes.

### Bloco 4 — Primeira regra

- trocar fonte;
- detectar run;
- produzir finding;
- aplicar `set-font-family`;
- validar;
- relint.

### Bloco 5 — Demo gravável

- executar CLI do início ao fim;
- guardar inputs e outputs;
- documentar comandos;
- registrar limitações observadas.

---

## 12. Definition of Done por feature

Uma feature só está pronta quando:

- tem contrato de entrada e saída;
- tem unit test;
- tem fixture;
- tem diagnostic de falha;
- tem log estruturado;
- não altera artefato original;
- passou no Open XML Validator quando gera arquivo;
- passou no round-trip relevante;
- está documentada;
- não depende de estado local invisível.

---

## 13. Métricas de validação

### Técnicas

- arquivos gerados que abrem sem reparo;
- taxa de render bem-sucedido;
- taxa de import bem-sucedido;
- duração de jobs;
- precisão e recall por regra;
- auto-fix bem-sucedido;
- preservação de tags no round-trip;
- diferença visual.

### Produto

- tempo para importar uma marca;
- quantidade de conflitos que exigem decisão;
- quantidade de slides gerados sem edição estrutural;
- violações encontradas após edição;
- fixes aceitos;
- revisões até aprovação.

Não use “quantidade de documentos gerados” como métrica de qualidade.

---

## 14. Go/no-go gates

### Gate A — OOXML

Continuar apenas se:

- o template for preservado;
- o slide for nativo;
- o arquivo abrir sem reparo;
- o round-trip for possível.

### Gate B — Brand IR

Continuar apenas se:

- cinco pacotes diferentes puderem ser representados;
- conflitos forem explicáveis;
- schema não estiver acoplado ao PPTX.

### Gate C — Linter

Continuar apenas se:

- violações semeadas forem localizadas;
- falsos positivos forem controláveis;
- fix for idempotente.

### Gate D — Editor embutido

Integrar apenas se:

- callback e versionamento forem confiáveis;
- licenciamento for aceitável;
- lint pós-save funcionar;
- o adapter não contaminar o core.

---

## 15. Plano de DOCX depois do MVP

DOCX entra somente depois do Gate 7.

Ordem:

1. Brand IR já existente;
2. adicionar Document Profile;
3. template `.docx`;
4. styles e theme analyzer;
5. content controls e placeholders;
6. renderer;
7. WordprocessingML parser;
8. linter de styles;
9. headers, footers e pagination;
10. ONLYOFFICE/Word round-trip.

Não tente reutilizar o layout engine de slides diretamente. Documento de fluxo contínuo é outro domínio.

---

## 16. Plano para formatos sociais

Após o renderer 16:9:

- criar profiles separados;
- usar templates separados por proporção;
- mapear o mesmo Deck Spec para uma composição equivalente;
- permitir regras por profile;
- gerar PPTX separado;
- exportar PNG/PDF;
- tratar crop e safe area como regras.

O sistema deve chamar isso de **adaptação de layout**, não simples resize. Conteúdo precisa ser recomposto.

---

## 17. O que não fazer

- não começar por login e billing;
- não criar editor canvas próprio;
- não aceitar “qualquer PDF” como promessa do MVP;
- não usar screenshot como slide;
- não chamar imagem de gráfico editável;
- não esconder conflitos;
- não mutar arquivos originais;
- não misturar Brand IR com schema de UI;
- não criar DSL genérica de regras antes de haver cinco regras reais;
- não adotar microserviços;
- não usar IA para decidir conformidade;
- não adicionar DOCX antes do round-trip PPTX.

---

## 18. Próximo commit recomendado

O primeiro pull request deve conter apenas:

```text
README.md
SYSTEM_DESIGN.md
ROADMAP.md
schemas/
examples/
adr/
Directory.Build.props
BrandCompiler.sln
src/BrandCompiler.Core/
src/BrandCompiler.Cli/
tests/Contract/
.github/workflows/ci.yml
```

Comandos do CI:

```text
dotnet restore
dotnet build --no-restore
dotnet test --no-build
validar JSON Schemas
validar exemplos
```

A segunda pull request deve ser o Spike A. Isso mantém a discussão arquitetural separada da prova OOXML.
