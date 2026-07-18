import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { expect, it, vi } from "vitest"
import { ApiProvider } from "../api/context"
import type { ApiClient, DocxBrandJobInfo } from "../api/types"
import { fakeClient } from "../test/fakeApi"
import { DocxBrandPage } from "./DocxBrandPage"

function renderDocx(client: ApiClient) {
  render(
    <ApiProvider client={client}>
      <MemoryRouter initialEntries={["/marcas/brandrev_x/word"]}>
        <Routes>
          <Route path="/marcas/:revisionId/word" element={<DocxBrandPage />} />
        </Routes>
      </MemoryRouter>
    </ApiProvider>,
  )
}

it("mostra o plano antes de aplicar e libera a cópia editável", async () => {
  const sha = "a".repeat(64)
  const getDocxBrandJob = vi.fn(
    async (jobId: string): Promise<DocxBrandJobInfo> =>
      jobId === "job_docx_apply"
        ? {
            id: jobId,
            status: "succeeded",
            result: {
              kind: "docx-brand-apply",
              sha256: sha,
              url: `/v1/assets/${sha}`,
              format: "docx",
              filename: "proposta-com-marca.docx",
              brandResult: {
                schemaVersion: "0.1.0",
                sourceSha256: sha,
                brandedSha256: sha,
                outputFilename: "out.docx",
                appliedOperationIds: ["op-001"],
                contentPreserved: true,
                contentSha256: sha,
              },
            },
            checks: [],
          }
        : {
            id: jobId,
            status: "succeeded",
            result: {
              kind: "docx-brand-analyze",
              plan: {
                schemaVersion: "0.1.0",
                source: {
                  filename: "proposta.docx",
                  sha256: sha,
                  sizeBytes: 2048,
                  paragraphCount: 12,
                  tableCount: 1,
                  sectionCount: 2,
                },
                brandRevisionId: "brandrev_x",
                operations: [
                  {
                    id: "op-001",
                    kind: "paragraph-styles",
                    labelPt: "Aplicar hierarquia da marca a 12 parágrafos",
                    affectedCount: 12,
                  },
                ],
                warnings: [],
              },
            },
            checks: [],
          },
  )
  const requestDocxBranding = vi.fn(async () => ({ jobId: "job_docx_analysis" }))
  const requestDocxBrandApply = vi.fn(async () => ({ jobId: "job_docx_apply" }))
  renderDocx(
    fakeClient({ requestDocxBranding, requestDocxBrandApply, getDocxBrandJob }),
  )

  const file = new File(["docx"], "proposta.docx", {
    type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  })
  await userEvent.upload(await screen.findByLabelText(/Selecionar arquivo .docx/), file)
  await userEvent.click(screen.getByRole("button", { name: "Analisar antes de aplicar" }))

  expect(await screen.findByText("Aplicar hierarquia da marca a 12 parágrafos")).toBeInTheDocument()
  expect(screen.getByText("Nenhum alerta estrutural encontrado.")).toBeInTheDocument()
  expect(requestDocxBrandApply).not.toHaveBeenCalled()

  await userEvent.click(screen.getByRole("button", { name: "Aplicar e criar cópia" }))
  const download = await screen.findByRole("link", {
    name: "Baixar proposta-com-marca.docx",
  })
  expect(download).toHaveAttribute("download", "proposta-com-marca.docx")
  expect(requestDocxBrandApply).toHaveBeenCalledWith("job_docx_analysis")
})
