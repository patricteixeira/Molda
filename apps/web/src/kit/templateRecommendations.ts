import type { LayoutSpec } from "../api/types"

export type TemplateCatalogMode = "recommended" | "all"

export function recommendedTemplateLayouts(
  layouts: LayoutSpec[],
  limit = 8,
): LayoutSpec[] {
  const ranked = layouts
    .filter((layout) => layout.recommendationRank != null)
    .sort(
      (left, right) =>
        (left.recommendationRank ?? Number.MAX_SAFE_INTEGER) -
        (right.recommendationRank ?? Number.MAX_SAFE_INTEGER),
    )
  return (ranked.length > 0 ? ranked : layouts).slice(0, limit)
}

export function recommendationIsBrandLed(layouts: LayoutSpec[]): boolean {
  return layouts.some((layout) => layout.recommendationBasis === "brand")
}
