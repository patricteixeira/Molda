import type { LayoutSpec } from "../api/types"

export const TEMPLATE_FAMILY_LABELS: Record<string, string> = {
  "typographic-editorial": "Texto em destaque",
  "typographic-brutalist": "Tipografia de impacto",
  "swiss-system": "Grade precisa",
  "geometric-modernism": "Formas geométricas",
  "kinetic-typography": "Ritmo tipográfico",
  "constructivist-dynamics": "Blocos em tensão",
  "fashion-editorial": "Imagem editorial",
  "minimal-luxury": "Espaço e precisão",
  "editorial-collage": "Camadas e recortes",
  "technical-diagram": "Informação diagramada",
  "product-campaign": "Produto em foco",
  "data-evidence": "Dados em destaque",
  "device-mockup": "Tela em contexto",
  "ritmo-editorial": "Ritmo editorial",
  "orbita-humana": "Órbita humana",
  "quadro-funcional": "Quadro funcional",
  "pulso-editorial": "Pulso editorial",
  "materia-franca": "Matéria franca",
  "corte-modular": "Corte modular",
  "pagina-serena": "Página serena",
  "bloco-direto": "Bloco direto",
  "coluna-inteira": "Coluna inteira",
  "ritmo-obliquo": "Ritmo oblíquo",
  "vazio-ativo": "Vazio ativo",
  "modulo-tensao": "Módulo em tensão",
  "numero-em-campo": "Número em campo",
  "escala-silenciosa": "Escala silenciosa",
  "palavra-materia": "Palavra matéria",
  "voz-em-contraste": "Voz em contraste",
  "forma-em-acao": "Forma em ação",
  "curva-humana": "Curva humana",
  "ordem-aberta": "Ordem aberta",
  "eixo-cerimonial": "Eixo cerimonial",
  "gesto-calmo": "Gesto calmo",
  "selo-editorial": "Selo editorial",
  essential: "Modelos essenciais",
}

export function templateFamilyKey(layout: LayoutSpec): string {
  return layout.templateRef?.packageId ?? "essential"
}

export function templateFamilyLabel(packageId: string): string {
  return TEMPLATE_FAMILY_LABELS[packageId] ?? packageId.replaceAll("-", " ")
}
