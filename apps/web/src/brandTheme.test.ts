import { describe, expect, it } from "vitest"
import type { BrandIr } from "./api/types"
import { brandThemeStyle } from "./brandTheme"

function brandWithColors(colors: BrandIr["colors"]): BrandIr {
  return {
    schemaVersion: "0.3.0",
    brand: { name: "Marca teste" },
    revision: { id: "brandrev_test", createdAt: "2026-07-18T00:00:00Z" },
    colors,
    fonts: {},
    roles: {},
    assets: {},
    formatProfiles: [],
    diagnostics: [],
  }
}

function contrastRatio(first: string, second: string): number {
  const luminance = (color: string) => {
    const channels = [1, 3, 5].map((start) => Number.parseInt(color.slice(start, start + 2), 16) / 255)
    const linear = channels.map((channel) =>
      channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
    )
    return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722
  }
  const lighter = Math.max(luminance(first), luminance(second))
  const darker = Math.min(luminance(first), luminance(second))
  return (lighter + 0.05) / (darker + 0.05)
}

describe("brandThemeStyle", () => {
  it("projeta as cores da marca no chassi sem alterar os tokens de origem", () => {
    const style = brandThemeStyle(
      brandWithColors({
        "color.primary": { value: "#ca6b0b", evidence: [] },
        "color.background": { value: "#FCFBF8", evidence: [] },
        "color.text": { value: "#1F232A", evidence: [] },
      }),
    )

    expect(style).toEqual({
      "--brand-primary": "#ca6b0b",
      "--brand-background": "#FCFBF8",
      "--brand-text": "#1F232A",
      "--brand-on-primary": "#020202",
      "--brand-signal": "#ca6b0b",
      "--brand-on-signal": "#020202",
    })
  })

  it("usa uma base segura quando a revisão não traz os papéis canônicos", () => {
    expect(brandThemeStyle(brandWithColors({}))).toMatchObject({
      "--brand-primary": "#d85a3a",
      "--brand-background": "#f1f0eb",
      "--brand-text": "#17191b",
      "--brand-signal": "#d85a3a",
    })
  })

  it.each(["#767676", "#7b5f6f", "#f2f0e9", "#17191b"])(
    "mantém contraste AA para o sinal dinâmico %s",
    (signal) => {
      const style = brandThemeStyle(
        brandWithColors({
          "color.primary": { value: signal, evidence: [] },
          "color.background": { value: "#777777", evidence: [] },
          "color.text": { value: "#777777", evidence: [] },
        }),
      )

      expect(contrastRatio(style["--brand-signal"], style["--brand-on-signal"])).toBeGreaterThanOrEqual(4.5)
    },
  )
})
