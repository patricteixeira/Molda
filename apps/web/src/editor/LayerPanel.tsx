import type { JSX } from "react"
import type { LayerOverride, LayoutSpec } from "../api/types"
import {
  editorElements,
  elementGlyph,
  elementLabel,
  elementZIndex,
  isStructuralElement,
  type EditorElement,
} from "./layerModel"

interface LayerPanelProps {
  layout: LayoutSpec
  overrides: Record<string, LayerOverride>
  selectedId: string | null
  onSelect(id: string): void
  onPatch(id: string, patch: Partial<LayerOverride>): void
  onResetAll(): void
}

function ordered(elements: EditorElement[], overrides: Record<string, LayerOverride>) {
  return [...elements].sort((a, b) => {
    const z = elementZIndex(b, overrides[b.id]) - elementZIndex(a, overrides[a.id])
    return z || a.id.localeCompare(b.id, "pt-BR")
  })
}

export function LayerPanel({
  layout,
  overrides,
  selectedId,
  onSelect,
  onPatch,
  onResetAll,
}: LayerPanelProps): JSX.Element {
  const elements = editorElements(layout)
  const main = ordered(elements.filter((element) => !isStructuralElement(element)), overrides)
  const structure = ordered(elements.filter(isStructuralElement), overrides)
  const selected = elements.find((element) => element.id === selectedId)
  const selectedZ = selected ? elementZIndex(selected, overrides[selected.id]) : 0

  const renderLayer = (element: EditorElement) => {
    const override = overrides[element.id]
    const hidden = override?.hidden ?? false
    const active = element.id === selectedId
    return (
      <li key={element.id} className="layer-row" data-selected={active || undefined}>
        <button
          type="button"
          className="layer-visibility"
          aria-label={`${hidden ? "Mostrar" : "Ocultar"} ${elementLabel(element)}`}
          aria-pressed={!hidden}
          onClick={() => onPatch(element.id, { hidden: !hidden })}
        >
          {hidden ? "OFF" : "ON"}
        </button>
        <button
          type="button"
          className="layer-select"
          onClick={() => onSelect(element.id)}
          aria-current={active ? "true" : undefined}
        >
          <span className="layer-glyph" aria-hidden="true">{elementGlyph(element)}</span>
          <span>{elementLabel(element)}</span>
        </button>
      </li>
    )
  }

  return (
    <aside className="layer-panel" aria-label="Camadas da composição">
      <div className="panel-heading">
        <div>
          <p className="panel-kicker">Composição</p>
          <h2>Camadas</h2>
        </div>
        <span className="layer-count">{elements.length}</span>
      </div>

      <ol className="layer-list">{main.map(renderLayer)}</ol>

      {structure.length > 0 ? (
        <details className="layer-structure">
          <summary>Estrutura técnica <span>{structure.length}</span></summary>
          <ol className="layer-list">{structure.map(renderLayer)}</ol>
        </details>
      ) : null}

      <div className="layer-panel-footer">
        <div className="layer-order" role="group" aria-label="Ordem da camada selecionada">
          <span>Ordem</span>
          <button
            type="button"
            disabled={!selected || selectedZ >= 20}
            onClick={() => selected && onPatch(selected.id, { zIndex: Math.min(20, selectedZ + 1) })}
            aria-label="Trazer camada para frente"
          >
            +
          </button>
          <button
            type="button"
            disabled={!selected || selectedZ <= 0}
            onClick={() => selected && onPatch(selected.id, { zIndex: Math.max(0, selectedZ - 1) })}
            aria-label="Enviar camada para trás"
          >
            -
          </button>
        </div>
        <button type="button" className="layer-reset-all" onClick={onResetAll}>
          Restaurar composição
        </button>
      </div>
    </aside>
  )
}
