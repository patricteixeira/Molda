# Plano M5.1 — Modo Campanha

**Objetivo:** permitir que uma pessoa escreva uma mensagem uma vez e mantenha
vários formatos atualizados sem sair da marca.

## Contrato

- `Campaign` pertence a uma revisão imutável de marca;
- `CampaignPiece` liga exatamente um layout a um documento persistido;
- bindings usam fontes fechadas e ficam registrados junto da peça;
- criação e propagação são transacionais;
- update preserva IDs de documento e reexecuta o Guard;
- imagem é referenciada apenas por SHA-256 válido no storage;
- o conteúdo completo volta na API para prévia pelo renderer autoritativo;
- export final e editável reutilizam os jobs existentes.

## API

| Método | Rota | Responsabilidade |
| --- | --- | --- |
| `GET` | `/v1/brand-revisions/{id}/campaigns` | listar campanhas da revisão |
| `GET` | `/v1/campaigns/{id}` | recuperar fonte e peças |
| `POST` | `/v1/campaigns` | criar campanha e documentos |
| `PATCH` | `/v1/campaigns/{id}` | propagar mensagem para as mesmas peças |

## Interface

1. biblioteca de campanhas salvas;
2. formulário único com nome, título, mensagem, data, CTA e imagem;
3. seleção inicial de um representante por perfil;
4. uma ação primária para criar ou atualizar todas as peças;
5. prévias, findings do Guard e export por peça.

## Aceite

- criar campanha com layout social e A4 materializa dois documentos;
- alterar a fonte atualiza ambos e mantém seus IDs;
- data e CTA entram no slot secundário ou no slot de metadados;
- update inválido não deixa nenhuma peça parcialmente alterada;
- testes API usam Postgres real e testes web cobrem criação e reabertura;
- typecheck, suíte web, build, Ruff e suíte API permanecem verdes.

## Limites conscientes

- adicionar/remover formatos depois da criação fica para uma evolução com
  arquivamento e histórico explícitos;
- colaboração multiusuário e resolução de edição concorrente não pertencem a
  este corte single-tenant.
