import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { expect, it, vi } from "vitest"
import { ApiError } from "../api/client"
import { ApiProvider } from "../api/context"
import type { ApiClient } from "../api/types"
import { fakeClient, fakeQuoteLayout, fakeStatementLayout } from "../test/fakeApi"
import { mounts } from "../test/renderStub"
import { KitPage } from "./KitPage"

function renderKit(client: ApiClient) {
  render(
    <ApiProvider client={client}>
      <MemoryRouter initialEntries={["/marcas/brandrev_x/kit"]}>
        <Routes>
          <Route path="/marcas/:revisionId/kit" element={<KitPage />} />
          <Route path="/marcas/:revisionId/editor/:layoutId" element={<h1>Editor</h1>} />
        </Routes>
      </MemoryRouter>
    </ApiProvider>,
  )
}

it("lista os layouts com nome PT e thumbnail renderizado pela biblioteca real", async () => {
  const getKit = vi.fn(async () => [fakeStatementLayout(), fakeQuoteLayout()])
  renderKit(fakeClient({ getKit }))
  const cards = await screen.findAllByTestId("kit-card")
  expect(cards).toHaveLength(2)
  expect(screen.getByText("Frase de impacto")).toBeInTheDocument()
  expect(screen.getByText("Citação sobre foto")).toBeInTheDocument()
  await waitFor(() => expect(mounts).toHaveLength(2))
  expect(mounts[0].payloads[0].assetsBaseUrl).toBe(
    "/v1/brand-revisions/brandrev_x/assets",
  )
  expect(screen.getAllByTestId("preview-canvas")[0]).toHaveStyle({ maxWidth: "360px" })
})

it("mantém os fluxos de carrossel e Word antes da biblioteca de peças", async () => {
  renderKit(fakeClient({ getKit: vi.fn(async () => [fakeStatementLayout()]) }))

  const workflowHeading = await screen.findByRole("heading", {
    name: "Quando uma peça precisa virar sequência.",
  })
  const libraryHeading = screen.getByRole("heading", {
    name: "Escolha uma composição. Depois faça dela a sua peça.",
  })

  expect(
    workflowHeading.compareDocumentPosition(libraryHeading) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy()
  expect(screen.getByRole("link", { name: /Modo Carrossel/i })).toHaveAttribute(
    "href",
    "/marcas/brandrev_x/carrossel",
  )
  expect(screen.getByRole("link", { name: /Aplicar marca ao Word/i })).toHaveAttribute(
    "href",
    "/marcas/brandrev_x/word",
  )
})

it("coloca famílias versionadas primeiro e identifica sua versão", async () => {
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

  const cards = await screen.findAllByTestId("kit-card")
  expect(cards[0]).toHaveAttribute("data-layout-id", editorial.id)
  expect(screen.getByText("Tipográfico editorial · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Brutalismo tipográfico · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Sistema suíço · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Modernismo geométrico · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Tipografia cinética · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Construtivismo · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Editorial de moda · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Minimalismo de luxo · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Colagem editorial · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Diagrama técnico · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Produto e campanha · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Dados e evidências · v1.0.0")).toBeInTheDocument()
  expect(screen.getByText("Mockup de dispositivo · v1.0.0")).toBeInTheDocument()
})

it("clicar num layout abre o editor daquele layout", async () => {
  renderKit(fakeClient({ getKit: vi.fn(async () => [fakeStatementLayout()]) }))
  await userEvent.click(await screen.findByTestId("kit-card"))
  expect(await screen.findByRole("heading", { name: "Editor" })).toBeInTheDocument()
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
    "Este kit ainda não tem modelos disponíveis.",
  )
  expect(screen.getByRole("button", { name: "Tentar novamente" })).toBeInTheDocument()
})
