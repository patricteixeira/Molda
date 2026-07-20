import { expect, test } from "@playwright/test"
import { execFileSync } from "node:child_process"
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const here = path.dirname(fileURLToPath(import.meta.url))
const FIX = path.join(here, ".fixtures")
const PKG = path.join(FIX, "acme-package")

function enginePython(): string {
  const candidates = [
    process.env.ENGINE_PYTHON,
    path.resolve(here, "../../../packages/engine/.venv/Scripts/python.exe"),
    path.resolve(here, "../../../packages/engine/.venv/bin/python"),
  ].filter((candidate): candidate is string => Boolean(candidate))
  const executable = candidates.find((candidate) => fs.existsSync(candidate))
  if (!executable) throw new Error("Python do engine não encontrado para validar o export.")
  return executable
}

function validateOutput(kind: "png" | "pdf" | "pptx" | "docx", file: string): void {
  execFileSync(
    enginePython(),
    [path.join(here, "fixtures", "validate_output.py"), kind, file],
    { stdio: "inherit" },
  )
}

test("walking skeleton M1/M2: instalar → confirmar → kit → slots → guard → exportar", async ({
  page,
}) => {
  await page.goto("/")
  const intake = page.getByTestId("wizard-file-input")
  await intake.setInputFiles(path.join(PKG, "assets", "logos", "logo.svg"))
  await intake.setInputFiles(path.join(PKG, "manual.pdf"))
  await intake.setInputFiles(path.join(PKG, "fonts", "fixture-sans-bold.ttf"))
  await expect(page.getByText("arquivos escolhidos", { exact: false })).toContainText(
    "3 arquivos escolhidos",
  )
  await page.getByTestId("wizard-enviar").click()

  await expect(page.getByTestId("wizard-question")).toContainText(
    "Como é a sua marca?",
  )
  await page
    .getByLabel("O que a marca entrega às pessoas")
    .fill("Uma marca ousada e dinâmica que transforma sistemas em autonomia.")
  await page
    .getByLabel("Que impressão a marca deve deixar")
    .fill("Geométrica, precisa, técnica e confiável.")
  await page
    .getByLabel("Como a marca conversa com as pessoas")
    .fill("Direta, clara e acessível.")
  await page
    .getByLabel("O que nunca deve aparecer na marca")
    .fill("Urgência artificial, exagero e promessas vazias.")
  await page.getByTestId("wizard-confirmar").click()

  await expect(page.getByTestId("wizard-question")).toContainText(
    "Qual destas é a cor principal da marca?",
  )
  for (let index = 0; index < 8; index += 1) {
    const visible = await page
      .getByTestId("wizard-question")
      .isVisible()
      .catch(() => false)
    if (!visible) break
    await page.getByTestId("candidate-option").first().click()
    await page.getByTestId("wizard-confirmar").click()
  }
  await expect(page.getByTestId("wizard-question")).not.toBeVisible()

  await page.getByTestId("wizard-brand-name").fill("ACME")
  await page.getByTestId("wizard-publicar").click()

  await expect(page).toHaveURL(/\/marcas\/brandrev_[0-9a-f]+\/kit/)
  await expect(page.getByTestId("kit-card")).toHaveCount(13)
  const kitUrl = page.url()

  await page.locator('[data-testid="kit-card"][data-layout-id="quote-post-1x1"]').click()
  await expect(page.getByRole("heading", { name: "Escala sem contenção" })).toBeVisible()
  await page.getByRole("button", { name: "Aplicar esta sugestão" }).click()
  await expect(page.getByText("Ajustar Grade técnica")).toBeVisible()
  await expect(page.locator('.preview-canvas [data-surface-kind="technical-grid"]')).toBeVisible()
  await page.getByRole("button", { name: "Ver todas as 20 texturas" }).click()
  await page
    .getByTestId("surface-option")
    .filter({ hasText: "Curvas de nível" })
    .last()
    .click()
  await expect(page.getByText("Ajustar Curvas de nível")).toBeVisible()
  await expect(page.locator('.preview-canvas [data-surface-kind="topographic"]')).toBeVisible()

  await page.getByRole("button", { name: "Citação", exact: true }).click()
  const quoteSelection = page.getByTestId("canvas-selection")
  const quoteBox = await quoteSelection.boundingBox()
  if (!quoteBox) throw new Error("Seleção da citação não recebeu geometria visível.")
  const quoteX = page.getByRole("spinbutton", { name: "X", exact: true })
  const initialQuoteX = Number(await quoteX.inputValue())
  await page.mouse.move(quoteBox.x + quoteBox.width / 2, quoteBox.y + quoteBox.height / 2)
  await page.mouse.down()
  await page.mouse.move(quoteBox.x + quoteBox.width / 2 + 48, quoteBox.y + quoteBox.height / 2 + 24)
  await page.mouse.up()
  await expect.poll(async () => Number(await quoteX.inputValue())).not.toBe(initialQuoteX)

  await page.getByRole("button", { name: "Logo", exact: true }).click()
  await page.getByRole("spinbutton", { name: "X", exact: true }).fill("-180")
  await page.getByRole("spinbutton", { name: "Y", exact: true }).fill("760")
  await page.getByRole("spinbutton", { name: "L", exact: true }).fill("1600")
  await page.getByRole("spinbutton", { name: "A", exact: true }).fill("900")
  await expect(page.getByTestId("canvas-selection")).toHaveAttribute("data-layer", "logo")
  await expect(page.getByRole("spinbutton", { name: "X", exact: true })).toHaveValue("-180")
  await expect(page.getByRole("spinbutton", { name: "L", exact: true })).toHaveValue("1600")

  await page.getByRole("button", { name: "Citação", exact: true }).click()
  await page.getByTestId("slot-input-quote").fill("A".repeat(200))
  await expect(page.getByTestId("char-counter-quote")).toHaveAttribute("data-over", "true")
  await page.getByRole("button", { name: "Foto", exact: true }).click()
  const lowUpload = page.waitForResponse(
    (response) => response.url().endsWith("/v1/assets") && response.request().method() === "POST",
  )
  await page.getByTestId("slot-image-input-photo").setInputFiles(path.join(FIX, "photos", "low.png"))
  await lowUpload
  await expect(page.getByText("Foto pronta.")).toBeVisible()
  await page.getByTestId("exportar-png").click()
  await expect(
    page.locator('[data-testid="guard-item"][data-check-id="text-length"]'),
  ).toBeVisible()
  await expect(
    page.locator('[data-testid="guard-item"][data-check-id="image-resolution"]'),
  ).toBeVisible()

  await page.getByRole("button", { name: "Citação", exact: true }).click()
  await page.getByTestId("slot-input-quote").fill("Menos é mais.")
  await page.getByRole("button", { name: "Foto", exact: true }).click()
  const okUpload = page.waitForResponse(
    (response) => response.url().endsWith("/v1/assets") && response.request().method() === "POST",
  )
  await page.getByTestId("slot-image-input-photo").setInputFiles(path.join(FIX, "photos", "ok.png"))
  await okUpload
  await expect(page.getByText("Foto pronta.")).toBeVisible()
  await page.getByTestId("exportar-png").click()
  const pngLink = page.getByTestId("download-link")
  await expect(pngLink).toBeVisible({ timeout: 120_000 })
  const pngDownload = page.waitForEvent("download")
  await pngLink.click()
  const pngPath = path.join(FIX, "out-post.png")
  await (await pngDownload).saveAs(pngPath)
  validateOutput("png", pngPath)

  await page.getByTestId("exportar-pptx").click()
  await expect(page.getByTestId("export-status")).toContainText("PPTX pronto", {
    timeout: 120_000,
  })
  const pptxLink = page.getByTestId("download-link")
  await expect(pptxLink).toHaveAttribute("download", /\.pptx$/)
  const pptxDownload = page.waitForEvent("download")
  await pptxLink.click()
  const pptxPath = path.join(FIX, "out-post.pptx")
  await (await pptxDownload).saveAs(pptxPath)
  validateOutput("pptx", pptxPath)

  await expect(page.getByText("Confira o arquivo que voltou")).toBeVisible()
  await page.getByTestId("roundtrip-file").setInputFiles(pptxPath)
  await page.getByTestId("roundtrip-analyze").click()
  await expect(page.getByText("Tudo no lugar. O arquivo voltou sem desvios.")).toBeVisible({
    timeout: 120_000,
  })

  await page.goto(kitUrl)
  await page.locator('[data-testid="kit-card"][data-layout-id="one-pager-doc-a4"]').click()
  await page.getByTestId("slot-input-title").fill("Relatório do mês")
  await page.getByRole("button", { name: "Texto", exact: true }).click()
  await page
    .getByTestId("slot-input-body")
    .fill("Um documento simples produzido dentro dos trilhos da marca.")
  await page.getByTestId("exportar-pdf").click()
  const pdfLink = page.getByTestId("download-link")
  await expect(pdfLink).toBeVisible({ timeout: 120_000 })
  const pdfDownload = page.waitForEvent("download")
  await pdfLink.click()
  const pdfPath = path.join(FIX, "out-doc.pdf")
  await (await pdfDownload).saveAs(pdfPath)
  validateOutput("pdf", pdfPath)

  await page.getByTestId("exportar-docx").click()
  await expect(page.getByTestId("export-status")).toContainText("DOCX pronto", {
    timeout: 120_000,
  })
  const docxLink = page.getByTestId("download-link")
  await expect(docxLink).toHaveAttribute("download", /\.docx$/)
  const docxDownload = page.waitForEvent("download")
  await docxLink.click()
  const docxPath = path.join(FIX, "out-doc.docx")
  await (await docxDownload).saveAs(docxPath)
  validateOutput("docx", docxPath)
})
