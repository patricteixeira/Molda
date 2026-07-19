import { expect, it } from "vitest"
import { FAKE_IR } from "../test/fakeApi"
import type { BrandIr } from "../api/types"
import {
  recommendedSurfaces,
  SURFACE_CATALOG,
  SURFACE_FAMILIES,
  surfaceForBrand,
} from "./surfaceCatalog"

function directedBrand(changes: Partial<NonNullable<BrandIr["creativeDirection"]>> = {}): BrandIr {
  return {
    ...FAKE_IR,
    creativeDirection: {
      energy: { value: 0.8, confidence: 0.8, evidenceTerms: ["dinâmica"] },
      geometry: { value: 0.9, confidence: 0.8, evidenceTerms: ["geométrica"] },
      density: { value: 0.2, confidence: 0.5, evidenceTerms: ["camadas"] },
      formality: { value: 0.7, confidence: 0.7, evidenceTerms: ["rigorosa"] },
      materiality: { value: 0.8, confidence: 0.6, evidenceTerms: ["digital"] },
      contrast: { value: 0.8, confidence: 0.7, evidenceTerms: ["impacto"] },
      composition: "modular",
      surface: "technical-grid",
      scaleContrast: 0.8,
      negativeSpace: 0.4,
      bleed: 0.6,
      surfaceDensity: 0.55,
      rationalePt: ["A marca se declara precisa."],
      ...changes,
    },
  }
}

it("oferece vinte texturas únicas distribuídas em cinco famílias", () => {
  expect(SURFACE_CATALOG).toHaveLength(20)
  expect(new Set(SURFACE_CATALOG.map((item) => item.kind)).size).toBe(20)
  expect(new Set(SURFACE_CATALOG.map((item) => item.family))).toEqual(
    new Set(SURFACE_FAMILIES.map((family) => family.id)),
  )
})

it("coloca a sugestão principal da marca antes do catálogo completo", () => {
  const recommendations = recommendedSurfaces(directedBrand())
  expect(recommendations).toHaveLength(4)
  expect(recommendations[0].kind).toBe("technical-grid")
  expect(recommendations.some((item) => item.family === "grids")).toBe(true)
})

it("não inventa recomendação sem identidade, mas mantém qualquer textura aplicável", () => {
  const brand = { ...FAKE_IR, creativeDirection: null }
  expect(recommendedSurfaces(brand)).toEqual([])
  expect(surfaceForBrand(SURFACE_CATALOG.find((item) => item.kind === "waves")!, brand)).toMatchObject({
    kind: "waves",
    colorToken: "color.primary",
  })
})
