import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { expect, it, vi } from "vitest"
import { ApiProvider } from "../api/context"
import type { DraftQuestion } from "../api/types"
import { fakeClient } from "../test/fakeApi"
import { QuestionStep } from "./QuestionStep"

const question: DraftQuestion = {
  id: "color.primary",
  kind: "pick-color",
  promptPt: "Qual destas é a cor principal da marca?",
  candidates: [
    { value: "#1A4D8F", score: 1, evidence: [] },
    { value: "#F4A300", score: 0.5, evidence: [] },
  ],
  required: true,
}

function renderStep(overrides: Partial<Parameters<typeof QuestionStep>[0]> = {}) {
  const props = {
    draftId: "d1",
    question,
    index: 0,
    total: 7,
    answers: {},
    onConfirm: vi.fn(),
    onSkip: vi.fn(),
    onBack: vi.fn(),
    onRestart: vi.fn(),
    ...overrides,
  }
  render(
    <ApiProvider client={fakeClient()}>
      <QuestionStep {...props} />
    </ApiProvider>,
  )
  return props
}

it("mostra o prompt do servidor, o progresso e confirma a seleção", async () => {
  const props = renderStep()
  expect(
    screen.getByRole("heading", { name: "Qual destas é a cor principal da marca?" }),
  ).toBeInTheDocument()
  expect(screen.getByTestId("wizard-progress")).toHaveTextContent("Passo 1 de 7")
  const confirm = screen.getByTestId("wizard-confirmar")
  expect(confirm).toBeDisabled()
  await userEvent.click(screen.getAllByTestId("candidate-option")[0])
  expect(confirm).toBeEnabled()
  await userEvent.click(confirm)
  expect(props.onConfirm).toHaveBeenCalledWith("#1A4D8F")
})

it("faz a pessoa revisar a visão da marca antes de usá-la como direção", async () => {
  const extracted = {
    essence: "Existimos para tornar sistemas complexos claros e humanos.",
    personality: "Precisa, artesanal e acessível.",
    voice: "Direta e acolhedora.",
    avoid: "Automação sem intenção.",
  }
  const props = renderStep({
    question: {
      id: "identity.expression",
      kind: "review-identity",
      promptPt: "Como é a sua marca?",
      candidates: [
        {
          value: extracted,
          score: 3,
          evidence: [
            {
              sourceType: "pdf-guideline",
              page: 2,
              confidence: 0.9,
              authoritative: true,
            },
          ],
        },
      ],
      required: true,
    },
  })

  expect(await screen.findByLabelText("Por que a marca existe")).toHaveValue(extracted.essence)
  expect(screen.getByText(/1 trecho do manual foi usado/i)).toBeInTheDocument()
  await userEvent.clear(screen.getByLabelText("Como a marca deve parecer"))
  await userEvent.type(screen.getByLabelText("Como a marca deve parecer"), "Tátil e experimental.")
  await userEvent.click(screen.getByTestId("wizard-confirmar"))

  expect(props.onConfirm).toHaveBeenCalledWith({
    ...extracted,
    personality: "Tátil e experimental.",
  })
})

it("pergunta sem candidatos oferece retorno aos materiais", async () => {
  const props = renderStep({ question: { ...question, candidates: [] } })

  expect(screen.getByRole("alert")).toHaveTextContent("Não encontramos uma opção")
  expect(screen.getByTestId("wizard-confirmar")).toBeDisabled()
  await userEvent.click(screen.getByRole("button", { name: "Voltar aos arquivos" }))
  expect(props.onRestart).toHaveBeenCalledOnce()
})

it("fonte sem candidatos continua editável pelo nome", async () => {
  const props = renderStep({
    question: {
      id: "font.body",
      kind: "pick-font",
      promptPt: "Qual fonte aparece nos textos?",
      candidates: [],
      required: true,
    },
  })

  expect(screen.queryByRole("alert")).not.toBeInTheDocument()
  await userEvent.type(screen.getByLabelText("Ou digite o nome da fonte"), "General Sans")
  await userEvent.click(screen.getByRole("button", { name: "Usar o nome digitado" }))
  const confirm = screen.getByTestId("wizard-confirmar")
  expect(confirm).toBeEnabled()
  await userEvent.click(confirm)
  expect(props.onConfirm).toHaveBeenCalledWith({
    family: "General Sans",
    weight: 400,
    style: "normal",
  })
})

it("pular só existe em pergunta opcional; a primeira permite trocar os materiais", () => {
  renderStep()
  expect(screen.queryByTestId("wizard-pular")).not.toBeInTheDocument()
  expect(screen.queryByTestId("wizard-voltar")).not.toBeInTheDocument()
  expect(screen.getByTestId("wizard-trocar-materiais")).toHaveTextContent("Trocar arquivos")
})

it("pergunta opcional oferece 'A marca não tem'", async () => {
  const props = renderStep({
    question: { ...question, id: "color.secondary", required: false },
    index: 3,
  })
  await userEvent.click(screen.getByTestId("wizard-pular"))
  expect(props.onSkip).toHaveBeenCalled()
  expect(screen.getByTestId("wizard-voltar")).toBeInTheDocument()
})

it("restaura a resposta confirmada ao voltar para uma pergunta", () => {
  renderStep({ answers: { "color.primary": "#F4A300" } })

  expect(screen.getAllByTestId("candidate-option")[1]).toHaveAttribute("aria-pressed", "true")
  expect(screen.getByTestId("wizard-confirmar")).toBeEnabled()
})

it("preseleciona fonte aberta resolvida mas ainda exige confirmação", async () => {
  const value = {
    family: "Fraunces",
    weight: 700,
    style: "normal",
    path: "resolved-fonts/fraunces.ttf",
    resource: {
      provider: "google-fonts",
      format: "ttf",
      usagePolicy: "redistributable",
      missingCodepoints: [],
      axes: [],
    },
  }
  const props = renderStep({
    question: {
      id: "font.heading",
      kind: "pick-font",
      promptPt: "Qual fonte aparece nos títulos?",
      candidates: [{ value, score: 1, evidence: [] }],
      required: true,
    },
  })

  expect(screen.getByTestId("candidate-option")).toHaveAttribute("aria-pressed", "true")
  const confirm = screen.getByTestId("wizard-confirmar")
  expect(confirm).toBeEnabled()
  expect(props.onConfirm).not.toHaveBeenCalled()
  await userEvent.click(confirm)
  expect(props.onConfirm).toHaveBeenCalledWith(value)
})

it("preseleciona a primeira fonte declarada sem trocar pela próxima materializada", () => {
  const declared = { family: "Clash Display", weight: 700, style: "normal" }
  const resolved = {
    family: "Fraunces",
    weight: 400,
    style: "italic",
    path: "resolved-fonts/fraunces.ttf",
    resource: {
      provider: "google-fonts",
      format: "ttf" as const,
      usagePolicy: "redistributable" as const,
      missingCodepoints: [],
      axes: [],
    },
  }
  renderStep({
    question: {
      id: "font.heading",
      kind: "pick-font",
      promptPt: "Qual fonte aparece nos títulos?",
      candidates: [
        { value: declared, score: 1, evidence: [] },
        { value: resolved, score: 0.8, evidence: [] },
      ],
      required: true,
    },
  })

  expect(screen.getAllByTestId("candidate-option")[0]).toHaveAttribute("aria-pressed", "true")
  expect(screen.getAllByTestId("candidate-option")[1]).toHaveAttribute("aria-pressed", "false")
})

it("reinicia o estado transitório ao avançar para outro papel", async () => {
  const common = {
    draftId: "d1",
    index: 0,
    total: 2,
    answers: {},
    onConfirm: vi.fn(),
    onSkip: vi.fn(),
    onBack: vi.fn(),
    onRestart: vi.fn(),
  }
  const heading: DraftQuestion = {
    id: "font.heading",
    kind: "pick-font",
    promptPt: "Qual fonte aparece nos títulos?",
    candidates: [],
    required: true,
  }
  const body: DraftQuestion = {
    ...heading,
    id: "font.body",
    promptPt: "Qual fonte aparece nos textos?",
  }
  const { rerender } = render(
    <ApiProvider client={fakeClient()}>
      <QuestionStep {...common} question={heading} />
    </ApiProvider>,
  )
  await userEvent.type(screen.getByLabelText("Ou digite o nome da fonte"), "Clash Display")

  rerender(
    <ApiProvider client={fakeClient()}>
      <QuestionStep {...common} question={body} index={1} />
    </ApiProvider>,
  )

  expect(screen.getByLabelText("Ou digite o nome da fonte")).toHaveValue("")
})
