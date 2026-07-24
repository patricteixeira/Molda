import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { expect, it, vi } from "vitest"
import { ApiError } from "../api/client"
import { ApiProvider } from "../api/context"
import type { ApiClient, ContentSpec, LayoutSpec } from "../api/types"
import { fakeClient, fakeQuoteLayout, fakeStatementLayout } from "../test/fakeApi"
import { mounts } from "../test/renderStub"
import { KitPage } from "./KitPage"

function renderKit(client: ApiClient, entry = "/marcas/brandrev_x/kit") {
  render(
    <ApiProvider client={client}>
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route path="/marcas/:revisionId/kit" element={<KitPage />} />
          <Route path="/marcas/:revisionId/editor/:layoutId" element={<h1>Editor</h1>} />
        </Routes>
      </MemoryRouter>
    </ApiProvider>,
  )
}

function categorizedLayouts(profile = "post-4x5"): LayoutSpec[] {
  return [
    "fashion-cover",
    "product-hero",
    "brutalist-manifesto",
    "fashion-spread",
    "product-benefit",
    "evidence-comparison",
    "product-launch",
    "geometric-signal",
    "kinetic-pulse",
  ].map((id, index) => {
    const layout = fakeStatementLayout()
    layout.id = `${id}-${profile}`
    layout.namePt = id
    layout.profile = profile
    layout.recommendationRank = index + 1
    layout.recommendationBasis = "brand"
    if (/spread|benefit|comparison/.test(id)) {
      layout.slots.push({
        id: "body",
        kind: "text",
        required: true,
        area: [48, 760, 984, 160],
        fit: "shrink-within-role-range",
        role: "body",
        maxChars: 320,
      })
    }
    if (/launch|signal|pulse/.test(id)) {
      layout.slots.push({
        id: "cta",
        kind: "text",
        required: false,
        area: [48, 900, 360, 72],
        fit: "shrink-within-role-range",
        role: "caption",
        maxChars: 40,
      })
    }
    return layout
  })
}

it("lista os layouts com nomes leigos e thumbnail renderizado pela biblioteca real", async () => {
  const statement = fakeStatementLayout()
  statement.namePt = "BRUTALISMO TIPOGRÁFICO MONUMENTAL"
  statement.templateRef = {
    packageId: "typographic-brutalist",
    version: "1.0.0",
    compositionId: statement.id,
    sceneSchemaVersion: "2.0.0",
  }
  const getKit = vi.fn(async () => [statement, fakeQuoteLayout()])
  renderKit(fakeClient({ getKit }))
  const cards = await screen.findAllByTestId("kit-card")
  expect(cards).toHaveLength(2)
  expect(screen.getByText("Texto de grande impacto")).toBeInTheDocument()
  expect(screen.getByText("Citação sobre foto")).toBeInTheDocument()
  expect(screen.queryByText("BRUTALISMO TIPOGRÁFICO MONUMENTAL")).not.toBeInTheDocument()
  expect(
    screen.queryByRole("link", { name: /BRUTALISMO TIPOGRÁFICO MONUMENTAL/i }),
  ).not.toBeInTheDocument()
  await waitFor(() => expect(mounts).toHaveLength(2))
  expect(mounts[0].payloads[0].assetsBaseUrl).toBe(
    "/v1/brand-revisions/brandrev_x/assets",
  )
  expect(screen.getAllByTestId("preview-canvas")[0]).toHaveStyle({ maxWidth: "360px" })
})

it("mostra a biblioteca antes dos fluxos adicionais", async () => {
  renderKit(fakeClient({ getKit: vi.fn(async () => [fakeStatementLayout()]) }))

  const libraryHeading = await screen.findByRole("heading", {
    name: "Escolha pela função da peça.",
  })
  const workflowHeading = screen.getByRole("heading", {
    name: "Outros formatos",
  })

  expect(
    libraryHeading.compareDocumentPosition(workflowHeading) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy()
  expect(screen.getByRole("link", { name: "Ver modelos" })).toHaveAttribute(
    "href",
    "#modelos",
  )
  expect(screen.getByRole("link", { name: /Carrossel/i })).toHaveAttribute(
    "href",
    "/marcas/brandrev_x/carrossel",
  )
  expect(screen.getByRole("link", { name: /Aplicar marca ao Word/i })).toHaveAttribute(
    "href",
    "/marcas/brandrev_x/word",
  )
})

it("coloca famílias editáveis primeiro e usa nomes compreensíveis", async () => {
  const legacy = fakeStatementLayout()
  const editorial = fakeQuoteLayout()
  editorial.id = "typographic-ledger-post-4x5"
  editorial.namePt = "Caderno assimétrico"
  editorial.templateRef = {
    packageId: "typographic-editorial",
    version: "1.0.0",
    compositionId: editorial.id,
    sceneSchemaVersion: "2.0.0",
  }
  const brutalist = fakeQuoteLayout()
  brutalist.id = "brutalist-manifesto-post-4x5"
  brutalist.namePt = "Manifesto em bloco"
  brutalist.templateRef = {
    packageId: "typographic-brutalist",
    version: "1.0.0",
    compositionId: brutalist.id,
    sceneSchemaVersion: "2.0.0",
  }
  const swiss = fakeQuoteLayout()
  swiss.id = "swiss-rational-grid-post-4x5"
  swiss.namePt = "Grade racional"
  swiss.templateRef = {
    packageId: "swiss-system",
    version: "1.0.0",
    compositionId: swiss.id,
    sceneSchemaVersion: "2.0.0",
  }
  const geometric = fakeQuoteLayout()
  geometric.id = "geometric-orbit-post-4x5"
  geometric.namePt = "Órbita construtiva"
  geometric.templateRef = {
    packageId: "geometric-modernism",
    version: "1.0.0",
    compositionId: geometric.id,
    sceneSchemaVersion: "2.0.0",
  }
  const kinetic = fakeQuoteLayout()
  kinetic.id = "kinetic-echo-post-4x5"
  kinetic.namePt = "Eco progressivo"
  kinetic.templateRef = {
    packageId: "kinetic-typography",
    version: "1.0.0",
    compositionId: kinetic.id,
    sceneSchemaVersion: "2.0.0",
  }
  const constructivist = fakeQuoteLayout()
  constructivist.id = "constructivist-wedge-post-4x5"
  constructivist.namePt = "Corte ascendente"
  constructivist.templateRef = {
    packageId: "constructivist-dynamics",
    version: "1.0.0",
    compositionId: constructivist.id,
    sceneSchemaVersion: "2.0.0",
  }
  const fashion = fakeQuoteLayout()
  fashion.id = "fashion-cover-post-4x5"
  fashion.namePt = "Capa de ateliê"
  fashion.templateRef = {
    packageId: "fashion-editorial",
    version: "1.0.0",
    compositionId: fashion.id,
    sceneSchemaVersion: "2.0.0",
  }
  const minimal = fakeQuoteLayout()
  minimal.id = "luxury-whisper-post-4x5"
  minimal.namePt = "Sussurro monumental"
  minimal.templateRef = {
    packageId: "minimal-luxury",
    version: "1.0.0",
    compositionId: minimal.id,
    sceneSchemaVersion: "2.0.0",
  }
  const collage = fakeQuoteLayout()
  collage.id = "collage-overlap-post-4x5"
  collage.namePt = "Planos sobrepostos"
  collage.templateRef = {
    packageId: "editorial-collage",
    version: "1.0.0",
    compositionId: collage.id,
    sceneSchemaVersion: "2.0.0",
  }
  const technical = fakeQuoteLayout()
  technical.id = "technical-blueprint-post-4x5"
  technical.namePt = "Planta editorial"
  technical.templateRef = {
    packageId: "technical-diagram",
    version: "1.0.0",
    compositionId: technical.id,
    sceneSchemaVersion: "2.0.0",
  }
  const product = fakeQuoteLayout()
  product.id = "product-hero-post-4x5"
  product.namePt = "Produto em primeiro plano"
  product.templateRef = {
    packageId: "product-campaign",
    version: "1.0.0",
    compositionId: product.id,
    sceneSchemaVersion: "2.0.0",
  }
  const evidence = fakeQuoteLayout()
  evidence.id = "evidence-hero-metric-post-4x5"
  evidence.namePt = "Métrica em primeiro plano"
  evidence.templateRef = {
    packageId: "data-evidence",
    version: "1.0.0",
    compositionId: evidence.id,
    sceneSchemaVersion: "2.0.0",
  }
  const device = fakeQuoteLayout()
  device.id = "device-phone-post-4x5"
  device.namePt = "Celular editorial"
  device.templateRef = {
    packageId: "device-mockup",
    version: "1.0.0",
    compositionId: device.id,
    sceneSchemaVersion: "2.0.0",
  }
  renderKit(
    fakeClient({
      getKit: vi.fn(async () => [
        legacy,
        editorial,
        brutalist,
        swiss,
        geometric,
        kinetic,
        constructivist,
        fashion,
        minimal,
        collage,
        technical,
        product,
        evidence,
        device,
      ]),
    }),
  )

  await userEvent.click(await screen.findByRole("button", { name: /Todos os modelos/ }))
  const cards = await screen.findAllByTestId("kit-card")
  expect(cards[0]).toHaveAttribute("data-layout-id", editorial.id)
  expect(screen.getAllByText("Texto em destaque").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Texto de grande impacto").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Grade precisa").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Formas geométricas").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Texto com ritmo").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Blocos em tensão").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Imagem editorial").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Espaço e precisão").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Camadas e recortes").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Informação diagramada").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Produto em foco").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Dados em destaque").length).toBeGreaterThan(0)
  expect(screen.getAllByText("Tela em contexto").length).toBeGreaterThan(0)
})

it("prioriza sugestões explicadas e mantém o catálogo inteiro disponível", async () => {
  const recommended = fakeStatementLayout()
  recommended.recommendationRank = 1
  recommended.recommendationBasis = "brand"
  recommended.recommendationReasonPt =
    "Organiza a informação com precisão. A leitura do manual aponta para uma expressão geométrica."
  const other = fakeQuoteLayout()
  renderKit(fakeClient({ getKit: vi.fn(async () => [other, recommended]) }))

  const cards = await screen.findAllByTestId("kit-card")
  expect(cards).toHaveLength(2)
  expect(cards.some((card) => card.getAttribute("data-layout-id") === recommended.id)).toBe(true)
  expect(screen.getByText(/A leitura do manual aponta/)).toBeInTheDocument()

  await userEvent.click(screen.getByRole("button", { name: /Todos os modelos/ }))
  expect(await screen.findAllByTestId("kit-card")).toHaveLength(2)
})

it("usa o briefing para mostrar apenas modelos do tamanho escolhido", async () => {
  const square = fakeStatementLayout()
  square.profile = "post-1x1"
  const portrait = fakeQuoteLayout()
  portrait.id = "quote-post-4x5"
  portrait.profile = "post-4x5"

  renderKit(
    fakeClient({ getKit: vi.fn(async () => [square, portrait]) }),
    "/marcas/brandrev_x/kit?objective=inform&piece=individual&channel=instagram&profile=post-4x5&action=save&visual=either",
  )

  const cards = await screen.findAllByTestId("kit-card")
  expect(cards).toHaveLength(1)
  expect(cards[0]).toHaveAttribute("data-layout-id", portrait.id)
  expect(screen.getByText("Instagram · Feed vertical · Explicar ou ensinar")).toBeInTheDocument()
  expect(screen.getByText("1 modelo disponível")).toBeInTheDocument()
  expect(screen.queryByTestId(square.id)).not.toBeInTheDocument()
  expect(screen.getByRole("link", { name: "Mudar respostas" })).toHaveAttribute(
    "href",
    "/marcas/brandrev_x/criar",
  )
})

it("mostra somente formatos sociais alternativos quando a dimensão ainda não existe", async () => {
  const square = fakeStatementLayout()
  const document = fakeQuoteLayout()
  document.profile = "doc-a4"

  renderKit(
    fakeClient({ getKit: vi.fn(async () => [square, document]) }),
    "/marcas/brandrev_x/kit?objective=inform&piece=individual&channel=instagram&profile=post-4x5&action=save&visual=either",
  )

  const cards = await screen.findAllByTestId("kit-card")
  expect(cards).toHaveLength(1)
  expect(cards[0]).toHaveAttribute("data-layout-id", square.id)
  expect(screen.getByRole("status")).toHaveTextContent(
    "Exibindo outros formatos disponíveis",
  )
  expect(screen.getByText(/Mostramos os outros tamanhos disponíveis/i)).toBeInTheDocument()
})

it("não deixa modelos verticais ignorarem a escolha pelo formato quadrado", async () => {
  const square = fakeStatementLayout()
  square.profile = "post-1x1"
  const authored = Array.from({ length: 210 }, (_, index) => {
    const item = fakeQuoteLayout()
    item.id = `authorial-post-4x5-${String(index + 1).padStart(3, "0")}`
    item.namePt = `Modelo autoral ${index + 1}`
    item.profile = "post-4x5"
    item.templateRef = {
      packageId: "catalogo-autoral",
      version: "1.0.0",
      compositionId: item.id,
      sceneSchemaVersion: "2.0.0",
    }
    return item
  })

  renderKit(
    fakeClient({ getKit: vi.fn(async () => [square, ...authored]) }),
    "/marcas/brandrev_x/kit?objective=brand&piece=individual&channel=instagram&profile=post-1x1&action=none&visual=either",
  )

  const cards = await screen.findAllByTestId("kit-card")
  expect(cards).toHaveLength(1)
  expect(cards[0]).toHaveAttribute("data-layout-id", square.id)
  expect(screen.getByText("1 modelo disponível")).toBeInTheDocument()
})

it("abre orientando a escolha com três capas, três conteúdos e três fechamentos", async () => {
  renderKit(fakeClient({ getKit: vi.fn(async () => categorizedLayouts()) }))

  const cover = await screen.findByRole("region", { name: "Capa" })
  const content = screen.getByRole("region", { name: "Conteúdo" })
  const closing = screen.getByRole("region", { name: "Fechamento" })

  expect(within(cover).getAllByTestId("kit-card")).toHaveLength(3)
  expect(within(content).getAllByTestId("kit-card")).toHaveLength(3)
  expect(within(closing).getAllByTestId("kit-card")).toHaveLength(3)
  expect(screen.getByRole("button", { name: /Sugestões para a marca/ })).toHaveTextContent("9")
})

it.each(["post-1x1", "story-9x16"])(
  "mantém três capas, três conteúdos e três fechamentos no formato %s",
  async (profile) => {
    const otherProfile = profile === "post-1x1" ? "story-9x16" : "post-1x1"
    renderKit(
      fakeClient({
        getKit: vi.fn(async () => [
          ...categorizedLayouts(profile),
          ...categorizedLayouts(otherProfile),
        ]),
      }),
      `/marcas/brandrev_x/kit?objective=inform&piece=individual&channel=instagram&profile=${profile}&action=save&visual=either`,
    )

    const cover = await screen.findByRole("region", { name: "Capa" })
    const content = screen.getByRole("region", { name: "Conteúdo" })
    const closing = screen.getByRole("region", { name: "Fechamento" })

    expect(within(cover).getAllByTestId("kit-card")).toHaveLength(3)
    expect(within(content).getAllByTestId("kit-card")).toHaveLength(3)
    expect(within(closing).getAllByTestId("kit-card")).toHaveLength(3)
    expect(screen.getByRole("button", { name: /Sugestões para a marca/ })).toHaveTextContent(
      "9",
    )
    expect(screen.getByRole("button", { name: /Todos os modelos/ })).toHaveTextContent("9")
  },
)

it("carrega catálogos grandes em blocos e permite buscar qualquer modelo", async () => {
  const layouts = Array.from({ length: 30 }, (_, index) => {
    const item = fakeStatementLayout()
    item.id = `catalog-layout-${String(index + 1).padStart(2, "0")}`
    item.namePt = index === 29 ? "Modelo distante" : `Modelo ${index + 1}`
    return item
  })
  renderKit(fakeClient({ getKit: vi.fn(async () => layouts) }))

  await userEvent.click(
    await screen.findByRole("button", { name: /Todos os modelos/ }),
  )
  expect(await screen.findAllByTestId("kit-card")).toHaveLength(24)
  expect(screen.getByText("Mostrando 24 de 30 modelos")).toBeInTheDocument()

  await userEvent.type(screen.getByLabelText("Buscar modelo"), "Modelo distante")

  const filtered = await screen.findAllByTestId("kit-card")
  expect(filtered).toHaveLength(1)
  expect(filtered[0]).toHaveAttribute("data-layout-id", "catalog-layout-30")
  expect(screen.getByText("Mostrando 1 de 1 modelos")).toBeInTheDocument()
})

it("clicar num layout abre o editor daquele layout", async () => {
  renderKit(fakeClient({ getKit: vi.fn(async () => [fakeStatementLayout()]) }))
  await userEvent.click(await screen.findByTestId("kit-card"))
  expect(await screen.findByRole("heading", { name: "Editor" })).toBeInTheDocument()
})

it("testa o título em todas as prévias e o leva para o editor", async () => {
  renderKit(fakeClient({ getKit: vi.fn(async () => [fakeStatementLayout()]) }))

  const input = await screen.findByLabelText("Texto de teste")
  await userEvent.type(input, "Nova coleção disponível")

  await waitFor(() => {
    const payload = mounts.at(-1)?.payloads.at(-1) as
      | { contentSpec: ContentSpec }
      | undefined
    expect(payload?.contentSpec.values.headline).toEqual({
      kind: "text",
      text: "Nova coleção disponível",
    })
  })
  expect(screen.getByTestId("kit-card")).toHaveAttribute(
    "href",
    "/marcas/brandrev_x/editor/statement-post-1x1?headline=Nova%20cole%C3%A7%C3%A3o%20dispon%C3%ADvel",
  )
})

it("expõe falha da API em PT-BR", async () => {
  renderKit(
    fakeClient({
      getKit: vi.fn(async () => {
        throw new ApiError(503, "O kit está temporariamente indisponível.")
      }),
    }),
  )
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "O kit está temporariamente indisponível.",
  )
})

it("oferece nova tentativa e recupera uma falha transitória", async () => {
  const getKit = vi
    .fn()
    .mockRejectedValueOnce(new ApiError(503, "O kit está temporariamente indisponível."))
    .mockResolvedValueOnce([fakeStatementLayout()])
  renderKit(fakeClient({ getKit }))

  expect(await screen.findByRole("alert")).toHaveTextContent("temporariamente indisponível")
  await userEvent.click(screen.getByRole("button", { name: "Tentar novamente" }))

  expect(await screen.findByTestId("kit-card")).toHaveAttribute(
    "data-layout-id",
    "statement-post-1x1",
  )
  expect(getKit).toHaveBeenCalledTimes(2)
})

it("explica quando o kit não tem layouts e permite tentar novamente", async () => {
  renderKit(fakeClient({ getKit: vi.fn(async () => []) }))

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Esta marca ainda não tem modelos disponíveis.",
  )
  expect(screen.getByRole("button", { name: "Tentar novamente" })).toBeInTheDocument()
})
