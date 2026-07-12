import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { expect, it, vi } from "vitest"
import { ApiProvider } from "../api/context"
import { fakeClient } from "../test/fakeApi"
import { UploadStep } from "./UploadStep"

it("envia o pacote e entrega o draft", async () => {
  const user = userEvent.setup()
  const importBrandPackage = vi.fn(async () => ({ draftId: "d1", questions: [] }))
  const onDraft = vi.fn()
  render(
    <ApiProvider client={fakeClient({ importBrandPackage })}>
      <UploadStep onDraft={onDraft} />
    </ApiProvider>,
  )
  expect(screen.getByTestId("wizard-enviar")).toBeDisabled()
  const file = new File(["x"], "manual.pdf", { type: "application/pdf" })
  await user.upload(screen.getByTestId("wizard-file-input"), file)
  await user.click(screen.getByTestId("wizard-enviar"))
  expect(importBrandPackage).toHaveBeenCalledWith([file])
  await waitFor(() => expect(onDraft).toHaveBeenCalledWith({ draftId: "d1", questions: [] }))
})

it("falha da API vira alerta em PT-BR", async () => {
  const user = userEvent.setup()
  const importBrandPackage = vi.fn(async () => {
    throw Object.assign(new Error("x"), {
      messagePt: "Não foi possível falar com o servidor.",
    })
  })
  render(
    <ApiProvider client={fakeClient({ importBrandPackage })}>
      <UploadStep onDraft={vi.fn()} />
    </ApiProvider>,
  )
  await user.upload(screen.getByTestId("wizard-file-input"), new File(["x"], "manual.pdf"))
  await user.click(screen.getByTestId("wizard-enviar"))
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Não foi possível falar com o servidor.",
  )
})

it("congela a seleção de arquivos enquanto importa o pacote", async () => {
  let finish!: (result: { draftId: string; questions: [] }) => void
  const importBrandPackage = vi.fn(
    () =>
      new Promise<{ draftId: string; questions: [] }>((resolve) => {
        finish = resolve
      }),
  )
  const onDraft = vi.fn()
  render(
    <ApiProvider client={fakeClient({ importBrandPackage })}>
      <UploadStep onDraft={onDraft} />
    </ApiProvider>,
  )
  const input = screen.getByTestId("wizard-file-input")
  await userEvent.upload(input, new File(["x"], "manual.pdf"))
  await userEvent.click(screen.getByTestId("wizard-enviar"))

  expect(input).toBeDisabled()
  expect(screen.getByTestId("wizard-enviar")).toBeDisabled()

  finish({ draftId: "d1", questions: [] })
  await waitFor(() => expect(onDraft).toHaveBeenCalledOnce())
  expect(input).toBeEnabled()
})
