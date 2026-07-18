import type { BrandIr, SurfaceStyle } from "../api/types"

interface Props {
  brandIr: BrandIr
  surface: SurfaceStyle | null
  disabled?: boolean
  onSurfaceChange(surface: SurfaceStyle | null): void
  onApplyDirection(): void
}

const compositionNames = {
  contemplative: "Silêncio estruturado",
  asymmetric: "Assimetria com propósito",
  modular: "Precisão modular",
  expansive: "Escala sem contenção",
  layered: "Profundidade em camadas",
} as const

const surfaceNames = {
  "paper-grain": "Matéria de papel",
  "linear-rhythm": "Ritmo linear",
  "technical-grid": "Grade técnica",
  "point-field": "Campo de pontos",
  "concentric-rings": "Anéis concêntricos",
} as const

export function DirectionPanel({
  brandIr,
  surface,
  disabled = false,
  onSurfaceChange,
  onApplyDirection,
}: Props) {
  const direction = brandIr.creativeDirection
  const update = (patch: Partial<SurfaceStyle>) => {
    if (surface) onSurfaceChange({ ...surface, ...patch })
  }

  return (
    <section className="direction-panel" aria-labelledby="direction-panel-title">
      <p className="panel-kicker">Leitura da identidade</p>
      <h3 id="direction-panel-title">
        {direction ? compositionNames[direction.composition] : "Direção ainda sem evidência"}
      </h3>
      {direction ? (
        <>
          <p className="direction-summary">
            {direction.surface === "none"
              ? "A identidade pede que a estrutura carregue a expressão, sem textura acrescentada."
              : surfaceNames[direction.surface] + " com escala, ritmo e sangria derivados da marca."}
          </p>
          <ul className="direction-rationale">
            {direction.rationalePt.slice(0, 3).map((reason) => <li key={reason}>{reason}</li>)}
          </ul>
          <button type="button" disabled={disabled} onClick={onApplyDirection}>
            Aplicar esta direção
          </button>
        </>
      ) : (
        <p className="direction-summary">
          A identidade foi preservada, mas ainda não declara qualidades suficientes para uma
          sugestão específica. O Molda não completará essa lacuna com um preset genérico.
        </p>
      )}

      {surface ? (
        <details className="surface-controls">
          <summary>Editar superfície aplicada</summary>
          <label>
            <span>Textura</span>
            <select
              value={surface.kind}
              disabled={disabled}
              onChange={(event) =>
                update({ kind: event.currentTarget.value as SurfaceStyle["kind"] })
              }
            >
              {Object.entries(surfaceNames).map(([kind, name]) => (
                <option key={kind} value={kind}>{name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Cor</span>
            <select
              value={surface.colorToken}
              disabled={disabled}
              onChange={(event) => update({ colorToken: event.currentTarget.value })}
            >
              {Object.entries(brandIr.colors).map(([token, color]) => (
                <option key={token} value={token}>{token} · {color.value}</option>
              ))}
            </select>
          </label>
          <div className="inspector-grid inspector-grid-two">
            <label>
              <span>Opacidade</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={surface.opacity}
                disabled={disabled}
                onChange={(event) => update({ opacity: Number(event.currentTarget.value) })}
              />
            </label>
            <label>
              <span>Escala</span>
              <input
                type="number"
                min="4"
                max="512"
                value={surface.scalePx}
                disabled={disabled}
                onChange={(event) => update({ scalePx: Number(event.currentTarget.value) })}
              />
            </label>
            <label>
              <span>Peso</span>
              <input
                type="number"
                min="0.1"
                max="32"
                step="0.1"
                value={surface.weightPx}
                disabled={disabled}
                onChange={(event) => update({ weightPx: Number(event.currentTarget.value) })}
              />
            </label>
            <label>
              <span>Ângulo</span>
              <input
                type="number"
                min="-180"
                max="180"
                value={surface.angleDeg}
                disabled={disabled}
                onChange={(event) => update({ angleDeg: Number(event.currentTarget.value) })}
              />
            </label>
          </div>
          <button
            className="inspector-reset"
            type="button"
            disabled={disabled}
            onClick={() => onSurfaceChange(null)}
          >
            Remover superfície
          </button>
        </details>
      ) : null}
    </section>
  )
}
