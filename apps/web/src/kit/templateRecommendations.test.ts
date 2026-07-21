import { expect, it } from "vitest"
import { fakeQuoteLayout, fakeStatementLayout } from "../test/fakeApi"
import {
  recommendationIsBrandLed,
  recommendedTemplateLayouts,
} from "./templateRecommendations"

it("respeita a ordem explicável enviada pelo motor", () => {
  const first = fakeStatementLayout()
  first.recommendationRank = 2
  first.recommendationBasis = "brand"
  const second = fakeQuoteLayout()
  second.recommendationRank = 1
  second.recommendationBasis = "brand"

  expect(recommendedTemplateLayouts([first, second]).map((layout) => layout.id)).toEqual([
    second.id,
    first.id,
  ])
  expect(recommendationIsBrandLed([first, second])).toBe(true)
})

it("mantém uma amostra pequena e honesta quando ainda não há ranking", () => {
  const layouts = Array.from({ length: 12 }, (_, index) => ({
    ...fakeStatementLayout(),
    id: `layout-${index}`,
  }))

  expect(recommendedTemplateLayouts(layouts)).toHaveLength(8)
  expect(recommendationIsBrandLed(layouts)).toBe(false)
})
