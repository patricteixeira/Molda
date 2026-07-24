import { expect, it } from "vitest"
import { fakeStatementLayout } from "../test/fakeApi"
import { templateDisplayName } from "./templateFamilies"

it("mantém nomes técnicos internos fora da linguagem apresentada ao usuário", () => {
  const layout = fakeStatementLayout()
  layout.namePt = "Brutalismo tipográfico — Manifesto monumental"
  layout.templateRef = {
    packageId: "typographic-brutalist",
    version: "1.0.0",
    compositionId: layout.id,
    sceneSchemaVersion: "2.0.0",
  }

  expect(templateDisplayName(layout)).toBe("Texto de grande impacto")
})

it("preserva nomes diretos dos modelos essenciais", () => {
  const layout = fakeStatementLayout()

  expect(templateDisplayName(layout)).toBe("Frase de impacto")
})
