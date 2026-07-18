import type { CSSProperties } from "react"
import type { BrandIr } from "./api/types"

export type BrandThemeStyle = CSSProperties & {
  "--brand-primary": string
  "--brand-background": string
  "--brand-text": string
  "--brand-on-primary": string
  "--brand-signal": string
  "--brand-on-signal": string
}

function normalizedHex(value: string | undefined, fallback: string): string {
  if (!value) return fallback
  const trimmed = value.trim()
  if (/^#[0-9a-f]{6}$/i.test(trimmed)) return trimmed
  if (/^#[0-9a-f]{3}$/i.test(trimmed)) {
    const [red, green, blue] = trimmed.slice(1)
    return `#${red}${red}${green}${green}${blue}${blue}`
  }
  return fallback
}

function relativeLuminance(color: string): number {
  const red = Number.parseInt(color.slice(1, 3), 16) / 255
  const green = Number.parseInt(color.slice(3, 5), 16) / 255
  const blue = Number.parseInt(color.slice(5, 7), 16) / 255
  const linear = [red, green, blue].map((channel) =>
    channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
  )
  return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722
}

function contrastRatio(first: string, second: string): number {
  const lighter = Math.max(relativeLuminance(first), relativeLuminance(second))
  const darker = Math.min(relativeLuminance(first), relativeLuminance(second))
  return (lighter + 0.05) / (darker + 0.05)
}

function readableInk(background: string): string {
  const darkInk = "#020202"
  const lightInk = "#fdfdfd"
  return contrastRatio(background, darkInk) >= contrastRatio(background, lightInk)
    ? darkInk
    : lightInk
}

function saturation(color: string): number {
  const channels = [
    Number.parseInt(color.slice(1, 3), 16),
    Number.parseInt(color.slice(3, 5), 16),
    Number.parseInt(color.slice(5, 7), 16),
  ]
  const maximum = Math.max(...channels)
  const minimum = Math.min(...channels)
  return maximum === 0 ? 0 : (maximum - minimum) / maximum
}

export function brandThemeStyle(brand: BrandIr): BrandThemeStyle {
  const primary = normalizedHex(brand.colors["color.primary"]?.value, "#d85a3a")
  const background = normalizedHex(brand.colors["color.background"]?.value, "#f1f0eb")
  const text = normalizedHex(brand.colors["color.text"]?.value, "#17191b")
  const signal = [primary, background, text].reduce((current, candidate) =>
    saturation(candidate) > saturation(current) ? candidate : current,
  )

  return {
    "--brand-primary": primary,
    "--brand-background": background,
    "--brand-text": text,
    "--brand-on-primary": readableInk(primary),
    "--brand-signal": signal,
    "--brand-on-signal": readableInk(signal),
  }
}
