import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { expect, it, vi } from "vitest"
import { ApiProvider } from "../api/context"
import type { ApiClient } from "../api/types"
import { fakeCampaign, fakeClient, fakeStatementLayout } from "../test/fakeApi"
import { CampaignPage } from "./CampaignPage"

function renderCampaign(client: ApiClient) {
  render(
    <ApiProvider client={client}>
      <MemoryRouter initialEntries={["/marcas/brandrev_x/campanhas"]}>
        <Routes>
          <Route path="/marcas/:revisionId/campanhas" element={<CampaignPage />} />
        </Routes>
      </MemoryRouter>
    </ApiProvider>,
  )
}

it("cria uma fonte única e exibe a peça vinculada", async () => {
  const createCampaign = vi.fn(async (input) => ({
    ...fakeCampaign(),
    name: input.name,
    fields: input.fields,
  }))
  renderCampaign(
    fakeClient({
      getKit: vi.fn(async () => [fakeStatementLayout()]),
      createCampaign,
    }),
  )

  await screen.findByRole("heading", { name: "Modo Campanha" })
  fireEvent.change(screen.getByLabelText("Nome da campanha"), {
    target: { value: "Semana de lançamento" },
  })
  fireEvent.change(screen.getByLabelText("Título principal"), {
    target: { value: "Uma mensagem para todos" },
  })
  fireEvent.change(screen.getByLabelText("Mensagem"), {
    target: { value: "O mesmo conteúdo em cada formato." },
  })
  fireEvent.change(screen.getByLabelText("Data ou período"), {
    target: { value: "24 de julho" },
  })
  fireEvent.change(screen.getByLabelText("Chamada para ação"), {
    target: { value: "Conheça agora" },
  })
  await userEvent.click(screen.getByRole("button", { name: /Criar campanha com 1 formato/ }))

  await waitFor(() => expect(createCampaign).toHaveBeenCalledTimes(1))
  expect(createCampaign).toHaveBeenCalledWith(
    expect.objectContaining({
      name: "Semana de lançamento",
      layoutIds: ["statement-post-1x1"],
      fields: expect.objectContaining({
        headline: "Uma mensagem para todos",
        date: "24 de julho",
        cta: "Conheça agora",
      }),
    }),
  )
  expect(await screen.findByRole("status")).toHaveTextContent(
    "1 peça(s) atualizada(s) a partir da mesma mensagem.",
  )
  expect(screen.getByTestId("campaign-piece")).toBeInTheDocument()
})

it("reabre uma campanha e atualiza os mesmos documentos", async () => {
  const existing = fakeCampaign()
  const updateCampaign = vi.fn(async (_id, input) => ({
    ...existing,
    name: input.name,
    fields: input.fields,
  }))
  renderCampaign(
    fakeClient({
      getKit: vi.fn(async () => [fakeStatementLayout()]),
      listCampaigns: vi.fn(async () => [existing]),
      updateCampaign,
    }),
  )

  await userEvent.click(await screen.findByRole("button", { name: /Lançamento/ }))
  const headline = screen.getByLabelText("Título principal")
  fireEvent.change(headline, { target: { value: "Título atualizado" } })
  await userEvent.click(screen.getByRole("button", { name: /Salvar e atualizar 1 peça/ }))

  await waitFor(() => expect(updateCampaign).toHaveBeenCalledTimes(1))
  expect(updateCampaign).toHaveBeenCalledWith(
    "campaign_x",
    expect.objectContaining({
      fields: expect.objectContaining({ headline: "Título atualizado" }),
    }),
  )
})
