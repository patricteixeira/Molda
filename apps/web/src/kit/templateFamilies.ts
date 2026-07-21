import type { LayoutSpec } from "../api/types"

export const TEMPLATE_FAMILY_LABELS: Record<string, string> = {
  "typographic-editorial": "Tipográfico editorial",
  "typographic-brutalist": "Brutalismo tipográfico",
  "swiss-system": "Sistema suíço",
  "geometric-modernism": "Modernismo geométrico",
  "kinetic-typography": "Tipografia cinética",
  "constructivist-dynamics": "Construtivismo",
  "fashion-editorial": "Editorial de moda",
  "minimal-luxury": "Minimalismo de luxo",
  "editorial-collage": "Colagem editorial",
  "technical-diagram": "Diagrama técnico",
  "product-campaign": "Produto e campanha",
  "data-evidence": "Dados e evidências",
  "device-mockup": "Mockup de dispositivo",
  essential: "Modelos essenciais",
}

export function templateFamilyKey(layout: LayoutSpec): string {
  return layout.templateRef?.packageId ?? "essential"
}

export function templateFamilyLabel(packageId: string): string {
  return TEMPLATE_FAMILY_LABELS[packageId] ?? packageId.replaceAll("-", " ")
}
