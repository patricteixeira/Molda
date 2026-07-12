import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { expect, it, vi } from "vitest"
import { ApiProvider } from "../api/context"
import type { ApiClient, DraftQuestion } from "../api/types"
import { fakeClient } from "../test/fakeApi"
import { WizardPage } from "./WizardPage"

const questions: DraftQuestion[] = [
  {
    id: "color.primary",
    kind: "pick-color",
    promptPt: "Qual destas é a cor principal da marca?",
    candidates: [{ value: "#1A4D8F", score: 1, evidence: [] }],
    required: true,
  },
  {
    id: "logo.primary",
    kind: "confirm-logo",
    promptPt: "Este é o logo oficial da marca?",
    candidates: [{ value: "assets/logos/logo.svg", score: 1, evidence: [] }],
    required: true,
  },
]

function renderWizard(client: ApiClient) {
  render(
    <ApiProvider client={client}>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<WizardPage />} />
          <Route path="/marcas/:revisionId/kit" element={<h1>Kit da marca</h1>} />
        </Routes>
      </MemoryRouter>
    </ApiProvider>,
  )
}

it("roteiro completo: upload → uma pergunta por vez → publicar → kit", async () => {
  const user = userEvent.setup()
  const importBrandPackage = vi.fn(async () => ({ draftId: "d1", questions }))
  const compileDraft = vi.fn(async () => ({ brandRevisionId: "brandrev_e2e" }))
  renderWizard(fakeClient({ importBrandPackage, compileDraft }))

  await user.upload(screen.getByTestId("wizard-file-input"), new File(["x"], "manual.pdf"))
  await user.click(screen.getByTestId("wizard-enviar"))

  expect(await screen.findByText("Qual destas é a cor principal da marca?")).toBeInTheDocument()
  expect(screen.queryByText("Este é o logo oficial da marca?")).not.toBeInTheDocument()
  await user.click(screen.getAllByTestId("candidate-option")[0])
  await user.click(screen.getByTestId("wizard-confirmar"))

  expect(await screen.findByText("Este é o logo oficial da marca?")).toBeInTheDocument()
  await user.click(screen.getAllByTestId("candidate-option")[0])
  await user.click(screen.getByTestId("wizard-confirmar"))

  await user.type(screen.getByTestId("wizard-brand-name"), "ACME")
  await user.click(screen.getByTestId("wizard-publicar"))
  await waitFor(() =>
    expect(compileDraft).toHaveBeenCalledWith(
      "d1",
      { "color.primary": "#1A4D8F", "logo.primary": "assets/logos/logo.svg" },
      "ACME",
    ),
  )
  expect(await screen.findByRole("heading", { name: "Kit da marca" })).toBeInTheDocument()
})
