# App web do brand-runtime

Wizard de instalação, kit, editor por slots, Modo Campanha e aplicação de marca
em Word. O chrome usa tipografia local do produto; as fontes da marca ficam
contidas nas provas renderizadas.

```powershell
cd apps/web
npm ci
npm run dev
npm test
npm run typecheck
npm run build
```

O Vite encaminha `/v1` para a API local e injeta o convite `dev-token` apenas
no ambiente de desenvolvimento. Em produção, essa responsabilidade pertence ao
proxy nginx da stack Docker.

## Fluxos principais

Alertas criativos aparecem como **Orientações da marca** e nunca desabilitam a
exportação. A pessoa pode voltar ao campo sugerido ou baixar a peça como está.

O editor aceita sangria real: logo, texto e imagem podem ter coordenadas
negativas ou dimensões maiores que o canvas, por arraste, redimensionamento ou
campos numéricos. A borda do canvas representa o corte final, não uma barreira
de criação. O painel **Direção da marca** usa a identidade confirmada para
propor estrutura, contraste de escala, espaço vazio e superfície procedural.
Se o sinal semântico for fraco, não apresenta um preset universal disfarçado de
sugestão personalizada.

O painel de texturas mostra quatro sugestões explicadas quando existe direção
confirmada e mantém as 20 opções acessíveis por família. Escolher fora da
recomendação não gera bloqueio. Todos os padrões são locais, procedurais e
preservados nas exportações compatíveis.

- `/marcas/{revisionId}/campanhas`: cria e reabre campanhas, edita a mensagem
  central, mostra todas as prévias vinculadas e exporta cada documento.
- `/marcas/{revisionId}/word`: separa upload, plano e aplicação em três etapas;
  o download só aparece depois da prova de preservação do worker.

Ambos os fluxos usam labels visíveis, feedback assíncrono anunciado, alvo mínimo
para toque, foco visível e uma ação primária por etapa. Opções avançadas ficam
fora do caminho inicial.

## Direção visual

O chrome do Molda é monocromático e editorial. Ele não herda cores da revisão
ativa: a matéria da marca aparece apenas nas provas, amostras, canvas e arquivos
exportados. Newsreader cria a voz editorial; Archivo organiza navegação,
formulários e controles; a fonte monoespaçada fica restrita a medidas e valores.
Superfícies são retas e grupos usam alinhamento e regras, sem cards decorativos.

A especificação vigente está em
[`docs/design/2026-07-19-mesa-de-provas.md`](../../docs/design/2026-07-19-mesa-de-provas.md).
A matriz de breakpoints, interações e gates inspecionados está em
[`docs/design/2026-07-19-validacao-visual.md`](../../docs/design/2026-07-19-validacao-visual.md).

## E2E

O roteiro E2E atravessa o sistema real: intake, confirmação da marca, kit,
guard e exportação PNG/PDF/PPTX/DOCX. Ele gera todas as fixtures em tempo de
execução e reabre os arquivos editáveis para verificar texto, imagem e estilos
nativos.

```powershell
# na raiz do repositório
$env:BRANDRT_DB_PASSWORD = "troque-por-uma-senha-local-segura"
docker compose up -d --build

# uma vez, em apps/web
npx playwright install chromium

# a cada validação, em apps/web
npm run e2e
```

O ambiente virtual de `packages/engine` precisa existir. Se estiver em outro
local, defina `ENGINE_PYTHON` com o caminho do executável Python.
