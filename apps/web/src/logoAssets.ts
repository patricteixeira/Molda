import type { BrandIr } from "./api/types"

const SEMANTIC_LABELS: Record<string, string> = {
  "logo.primary": "Principal",
  "logo.onLight": "Escura · para fundo claro",
  "logo.onDark": "Clara · para fundo escuro",
}

const SEMANTIC_ORDER = ["logo.primary", "logo.onLight", "logo.onDark"]

function humanize(value: string): string {
  const words = value
    .replace(/([a-zà-ÿ])([A-ZÀ-Ý])/g, "$1 $2")
    .replace(/[._-]+/g, " ")
    .trim()
  return words ? `${words.charAt(0).toLocaleUpperCase("pt-BR")}${words.slice(1)}` : value
}

export function logoAssetLabel(brandIr: BrandIr, token: string): string {
  const semantic = SEMANTIC_LABELS[token]
  if (semantic) return semantic
  const filename = brandIr.assets[token]?.path.split("/").at(-1)?.replace(/\.[^.]+$/, "")
  return humanize(filename || token.replace(/^logo\./, ""))
}

export function logoAssetTokens(brandIr: BrandIr): string[] {
  return Object.keys(brandIr.assets)
    .filter((token) => token.startsWith("logo."))
    .sort((left, right) => {
      const leftRank = SEMANTIC_ORDER.indexOf(left)
      const rightRank = SEMANTIC_ORDER.indexOf(right)
      if (leftRank >= 0 || rightRank >= 0) {
        if (leftRank < 0) return 1
        if (rightRank < 0) return -1
        return leftRank - rightRank
      }
      return logoAssetLabel(brandIr, left).localeCompare(
        logoAssetLabel(brandIr, right),
        "pt-BR",
      )
    })
}

export function uniqueLogoCount(brandIr: BrandIr): number {
  return new Set(logoAssetTokens(brandIr).map((token) => brandIr.assets[token].sha256)).size
}

export function hasAutomaticLogoPair(brandIr: BrandIr): boolean {
  return "logo.onLight" in brandIr.assets && "logo.onDark" in brandIr.assets
}
