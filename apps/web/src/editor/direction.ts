import type {
  BrandIr,
  LayerOverride,
  LayoutSpec,
  SurfaceStyle,
} from "../api/types"

export interface DirectionApplication {
  patches: Record<string, Partial<LayerOverride>>
  surface: SurfaceStyle | null
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value))
}

export function suggestedSurface(brandIr: BrandIr): SurfaceStyle | null {
  const direction = brandIr.creativeDirection
  if (!direction || direction.surface === "none") return null
  const colorToken =
    (brandIr.colors["color.primary"] && "color.primary") ||
    (brandIr.colors["color.text"] && "color.text") ||
    Object.keys(brandIr.colors)[0]
  if (!colorToken) return null
  return {
    kind: direction.surface,
    colorToken,
    opacity: clamp(0.05 + direction.surfaceDensity * 0.13, 0.04, 0.2),
    scalePx: Math.round(clamp(104 - direction.surfaceDensity * 78, 16, 112)),
    weightPx: Number(clamp(0.8 + direction.surfaceDensity * 2.2, 0.8, 3).toFixed(1)),
    angleDeg: Math.round(clamp(18 + direction.energy.value * 42, -24, 60)),
  }
}

export function directionApplication(brandIr: BrandIr, layout: LayoutSpec): DirectionApplication | null {
  const direction = brandIr.creativeDirection
  if (!direction || layout.profile === "doc-a4") return null
  const { widthPx: width, heightPx: height, safeAreaPx: safe } = layout.canvas
  const headline =
    layout.slots.find((slot) => slot.id === "headline" && slot.kind === "text") ??
    layout.slots.find((slot) => slot.kind === "text")
  const logo =
    layout.slots.find((slot) => slot.kind === "logo") ??
    layout.lockedLayers?.find((layer) => layer.kind === "asset")
  const patches: Record<string, Partial<LayerOverride>> = {}

  if (headline) {
    const role = headline.role ? brandIr.roles[headline.role] : null
    const baseSize = role?.maxSizePx ?? 72
    if (direction.composition === "contemplative") {
      patches[headline.id] = {
        area: [Math.round(width * 0.15), Math.round(height * 0.28), Math.round(width * 0.7), Math.round(height * 0.34)],
        textAlign: "center",
        fontSizePx: Math.round(baseSize * 0.86),
      }
    } else if (direction.composition === "modular") {
      patches[headline.id] = {
        area: [safe, Math.round(height * 0.18), Math.round(width * 0.58), Math.round(height * 0.46)],
        textAlign: "left",
        fontSizePx: Math.round(baseSize * (1 + direction.scaleContrast * 0.18)),
      }
    } else if (direction.composition === "expansive") {
      patches[headline.id] = {
        area: [safe, Math.round(height * 0.2), width - safe, Math.round(height * 0.5)],
        textAlign: "left",
        fontSizePx: Math.round(baseSize * (1.08 + direction.scaleContrast * 0.35)),
      }
    } else if (direction.composition === "layered") {
      patches[headline.id] = {
        area: [Math.round(width * 0.1), Math.round(height * 0.3), Math.round(width * 0.78), Math.round(height * 0.42)],
        textAlign: "left",
        fontSizePx: Math.round(baseSize * (1 + direction.scaleContrast * 0.24)),
        zIndex: 12,
      }
    } else {
      patches[headline.id] = {
        area: [safe, Math.round(height * 0.24), Math.round(width * 0.74), Math.round(height * 0.44)],
        textAlign: "left",
        fontSizePx: Math.round(baseSize * (0.95 + direction.scaleContrast * 0.2)),
      }
    }
  }

  if (logo) {
    const [, , logoWidth, logoHeight] = logo.area
    const ratio = logoHeight / logoWidth
    if (direction.composition === "expansive" || direction.composition === "layered") {
      const oversizedWidth = Math.round(width * (0.92 + direction.bleed * 0.55))
      const oversizedHeight = Math.round(oversizedWidth * ratio)
      patches[logo.id] = {
        area: [
          -Math.round(width * (0.12 + direction.bleed * 0.22)),
          Math.round(height - oversizedHeight * 0.72),
          oversizedWidth,
          oversizedHeight,
        ],
        opacity: direction.composition === "layered" ? 0.12 : 0.18,
        zIndex: 0,
      }
    } else if (direction.composition === "contemplative") {
      const calmWidth = Math.round(width * 0.14)
      patches[logo.id] = {
        area: [
          Math.round((width - calmWidth) / 2),
          Math.round(height * 0.82),
          calmWidth,
          Math.round(calmWidth * ratio),
        ],
        opacity: 1,
      }
    } else if (direction.composition === "modular") {
      const modularWidth = Math.round(width * 0.16)
      patches[logo.id] = {
        area: [
          width - safe - modularWidth,
          safe,
          modularWidth,
          Math.round(modularWidth * ratio),
        ],
        opacity: 1,
      }
    } else {
      const asymmetricWidth = Math.round(width * 0.3)
      patches[logo.id] = {
        area: [
          width - Math.round(asymmetricWidth * 0.72),
          Math.round(height * 0.72),
          asymmetricWidth,
          Math.round(asymmetricWidth * ratio),
        ],
        opacity: 0.72,
      }
    }
  }

  return { patches, surface: suggestedSurface(brandIr) }
}
