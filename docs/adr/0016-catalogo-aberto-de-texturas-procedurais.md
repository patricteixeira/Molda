# ADR 0016 — Catálogo aberto de texturas procedurais

- Status: aceito
- Data: 2026-07-19
- Decisores: produto e engenharia do Molda

## Contexto

O contrato inicial de direção criativa oferecia cinco superfícies procedurais.
Elas provavam a portabilidade entre preview, exportação web e PPTX, mas a
interface as escondia num seletor de texto. A pessoa não conseguia comparar a
materialidade das opções e marcas diferentes chegavam a um repertório visual
estreito demais.

Ao mesmo tempo, uma recomendação útil não pode virar uma prateleira fechada. O
Molda orienta pela identidade confirmada, mas a decisão final continua sendo da
pessoa. O catálogo também precisa permanecer local, determinístico e compatível
com uma instalação open source sem serviços pagos ou arquivos externos.

## Decisão

### Duas portas para o mesmo catálogo

O editor apresenta duas entradas simultâneas:

1. **Para esta marca:** quatro texturas ordenadas pelos eixos confirmados de
   energia, geometria, densidade, formalidade, materialidade e contraste. A
   sugestão principal já presente na direção da marca recebe prioridade.
2. **Todas as texturas:** o catálogo completo permanece acessível, organizado
   por famílias e sem qualquer bloqueio baseado na recomendação.

Sem direção criativa confirmada, o Molda não inventa uma recomendação. A
interface explica a ausência e mantém todas as opções disponíveis.

### Vocabulário portátil

O Content Spec passa a aceitar vinte texturas em cinco famílias:

- **Papel e matéria:** grão de papel, fibras aparentes, papel com fragmentos,
  pincel seco e fragmentos minerais.
- **Linhas e tramas:** ritmo linear, linhas de tela, hachura diagonal, hachura
  cruzada e trama têxtil.
- **Grades e módulos:** grade técnica, papel milimetrado, grade isométrica e
  tabuleiro modular.
- **Pontos e impressão:** campo de pontos e retícula de impressão.
- **Curvas e movimento:** anéis concêntricos, curvas de nível, raios e ondas
  abertas.

Cada opção continua sendo uma primitiva, não um estilo pronto de marca. Cor,
transparência, tamanho, espessura e rotação permanecem editáveis depois da
escolha.

### Paridade de saída

- O renderer web gera todas as texturas com gradientes CSS fechados e sem
  recursos de rede.
- O renderer PPTX rasteriza apenas a textura com Pillow; texto, logo e imagens
  continuam nativos e editáveis.
- A mesma `SurfaceStyle` é preservada no rascunho, no Content Spec, no Guard e
  nos jobs de exportação.
- A geração é determinística: o mesmo contrato produz os mesmos bytes na
  textura nativa.
- O Guard conhece uma estimativa de cobertura para cada textura e continua
  emitindo orientação, nunca veto estético.

## Consequências

- O catálogo pode crescer apenas quando preview, validação, Guard e PPTX forem
  atualizados no mesmo conjunto de mudanças.
- Recomendações não são persistidas como uma nova verdade sobre a marca; elas
  são derivadas da revisão ativa e podem evoluir sem migrar documentos.
- Texturas continuam fora do fluxo DOCX A4 até existir um contrato próprio para
  fundos contínuos e paginação.
- Não há upload de textura arbitrária nesta decisão. Imagens continuam podendo
  ocupar camadas livres; o catálogo cobre superfícies portáteis e ajustáveis.

## Alternativas rejeitadas

- **Mostrar apenas quatro recomendações:** transformaria orientação em
  proibição implícita.
- **Vinte imagens PNG empacotadas:** aumentaria peso, dificultaria recoloração e
  criaria diferenças entre preview e exportação.
- **CSS ou SVG livre fornecido pelo usuário:** ampliaria a superfície de ataque
  e quebraria a validação fechada do Content Spec.
- **Gerar textura por API externa:** adicionaria custo, rede e dependência
  incompatíveis com o núcleo self-hosted.
