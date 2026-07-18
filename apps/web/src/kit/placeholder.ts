import type { ContentSpec, ContentValue, LayoutSpec } from "../api/types"

export const PLACEHOLDER_IMAGE =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNoaGj4DwAFhAKAjM1mJgAAAABJRU5ErkJggg=="

const TEXT_BY_ROLE: Record<string, string> = {
  heading: "Sua mensagem aqui",
  body: "Um exemplo de texto corrido para visualizar este layout.",
  caption: "Legenda",
}

const EDITORIAL_TEXT_BY_SLOT: Record<string, string> = {
  kicker: "AUTORIA NÃO É UM EFEITO.",
  headline: "É A COERÊNCIA ENTRE INTENÇÃO E FORMA.",
  index: "06",
  signature: "@sua-marca",
}

export function placeholderContent(
  layout: LayoutSpec,
  brandRevisionId: string,
  brandName = "Sua marca",
): ContentSpec {
  const values: Record<string, ContentValue> = {}
  const closure = layout.id.startsWith("editorial-closure-")
  const isEditorial =
    layout.compositionMode != null ||
    (layout.lockedLayers?.length ?? 0) > 0 ||
    layout.slots.some((slot) => slot.emphasisColorToken != null)

  for (const slot of layout.slots) {
    if (slot.kind === "logo") continue

    if (slot.kind === "image") {
      values[slot.id] = { kind: "image", path: PLACEHOLDER_IMAGE }
      continue
    }

    const sample =
      (closure && slot.id === "headline" ? brandName.toLocaleUpperCase("pt-BR") : undefined) ??
      (closure && slot.id === "tagline"
        ? "Uma postura diante da inteireza do que se cria."
        : undefined) ??
      (isEditorial ? EDITORIAL_TEXT_BY_SLOT[slot.id] : undefined) ??
      TEXT_BY_ROLE[slot.role ?? ""] ??
      TEXT_BY_ROLE.body
    const text = slot.maxChars == null ? sample : sample.slice(0, Math.max(0, slot.maxChars))
    const emphasis = closure
      ? slot.id === "tagline" && text.includes("inteireza")
        ? "inteireza"
        : undefined
      : slot.id === "headline" && slot.emphasisColorToken && text.includes("INTENÇÃO E FORMA")
        ? "INTENÇÃO E FORMA"
        : undefined
    values[slot.id] = { kind: "text", text, ...(emphasis ? { emphasis } : {}) }
  }

  return {
    layoutId: layout.id,
    brandRevisionId,
    values,
    ...(closure
      ? {
          overrides: {
            tagline: { fontSizePx: 42, fontStyle: "italic", lineHeight: 1.15 },
          },
        }
      : {}),
  }
}
