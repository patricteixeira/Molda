import { useEffect, useRef, useState, type ChangeEvent, type JSX } from "react"
import { ApiError, contentAddressedPath } from "../api/client"
import { useApi } from "../api/context"
import type {
  BrandIr,
  LayerOverride,
  LayoutSpec,
  Slot,
  SlotValue,
  SurfaceStyle,
} from "../api/types"
import { DirectionPanel } from "./DirectionPanel"
import { exactOccurrenceCount } from "./emphasis"
import { elementArea, elementLabel, elementOpacity, elementZIndex, findEditorElement } from "./layerModel"

interface SlotFormProps {
  brandIr: BrandIr
  layout: LayoutSpec
  selectedId: string | null
  values: Record<string, SlotValue>
  overrides: Record<string, LayerOverride>
  onChange(slotId: string, value: SlotValue | null): void
  onPatch(elementId: string, patch: Partial<LayerOverride>): void
  onReset(elementId: string): void
  surface: SurfaceStyle | null
  onSurfaceChange(surface: SurfaceStyle | null): void
  onApplyDirection(): void
  disabled?: boolean
  onUploadingChange?(uploading: boolean): void
}

type UploadState =
  | { phase: "idle" }
  | { phase: "uploading" }
  | { phase: "ready" }
  | { phase: "error"; message: string }

const IDLE_UPLOAD: UploadState = { phase: "idle" }
const MAX_EDITOR_AREA_PX = 32_768

function numberValue(value: string): number | null {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function SlotForm({
  brandIr,
  layout,
  selectedId,
  values,
  overrides,
  onChange,
  onPatch,
  onReset,
  surface,
  onSurfaceChange,
  onApplyDirection,
  disabled = false,
  onUploadingChange,
}: SlotFormProps): JSX.Element {
  const api = useApi()
  const mountedRef = useRef(true)
  const uploadGenerationRef = useRef<Record<string, number>>({})
  const activeUploadsRef = useRef(new Set<string>())
  const onUploadingChangeRef = useRef(onUploadingChange)
  const [uploadStates, setUploadStates] = useState<Record<string, UploadState>>({})

  useEffect(() => {
    onUploadingChangeRef.current = onUploadingChange
  }, [onUploadingChange])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      activeUploadsRef.current.clear()
      onUploadingChangeRef.current?.(false)
    }
  }, [])

  const reportUploading = (): void => {
    onUploadingChangeRef.current?.(activeUploadsRef.current.size > 0)
  }

  const handleImage = async (slotId: string, event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0]
    event.currentTarget.value = ""
    if (!file) return

    const generation = (uploadGenerationRef.current[slotId] ?? 0) + 1
    uploadGenerationRef.current[slotId] = generation
    activeUploadsRef.current.add(slotId)
    reportUploading()
    setUploadStates((current) => ({ ...current, [slotId]: { phase: "uploading" } }))

    try {
      const uploaded = await api.uploadAsset(file)
      if (!mountedRef.current || uploadGenerationRef.current[slotId] !== generation) return
      onChange(slotId, {
        kind: "image",
        path: contentAddressedPath(uploaded.sha256),
        sha256: uploaded.sha256,
      })
      setUploadStates((current) => ({ ...current, [slotId]: { phase: "ready" } }))
    } catch (error) {
      if (!mountedRef.current || uploadGenerationRef.current[slotId] !== generation) return
      const message =
        error instanceof ApiError ? error.messagePt : "Não foi possível enviar a foto."
      setUploadStates((current) => ({ ...current, [slotId]: { phase: "error", message } }))
    } finally {
      if (mountedRef.current && uploadGenerationRef.current[slotId] === generation) {
        activeUploadsRef.current.delete(slotId)
        reportUploading()
      }
    }
  }

  const element = findEditorElement(layout, selectedId)
  if (!element) {
    return (
      <aside className="slot-form layer-inspector">
        <DirectionPanel
          brandIr={brandIr}
          surface={surface}
          disabled={disabled || layout.profile === "doc-a4"}
          onSurfaceChange={onSurfaceChange}
          onApplyDirection={onApplyDirection}
        />
        <p className="inspector-empty">Selecione uma camada no canvas ou na lista.</p>
      </aside>
    )
  }

  const override = overrides[element.id] ?? {}
  const area = elementArea(element, override)
  const opacity = elementOpacity(element, override)
  const zIndex = elementZIndex(element, override)
  const setAreaValue = (index: number, raw: string): void => {
    const parsed = numberValue(raw)
    if (parsed === null) return
    const next = [...area] as [number, number, number, number]
    next[index] = Math.round(parsed)
    if (index === 0 || index === 1) {
      next[index] = Math.max(-MAX_EDITOR_AREA_PX, Math.min(next[index], MAX_EDITOR_AREA_PX))
    }
    if (index === 2 || index === 3) {
      next[index] = Math.max(1, Math.min(next[index], MAX_EDITOR_AREA_PX))
    }
    onPatch(element.id, { area: next })
  }

  const renderTextControls = (slot: Slot) => {
    const currentValue = values[slot.id]
    const text = currentValue?.kind === "text" ? currentValue.text : ""
    const emphasis = currentValue?.kind === "text" ? (currentValue.emphasis ?? "") : ""
    const role = slot.role ? brandIr.roles[slot.role] : null
    const defaultFontToken = role?.font ?? Object.keys(brandIr.fonts)[0] ?? ""
    const fontToken = override.fontToken ?? defaultFontToken
    const font = brandIr.fonts[fontToken]
    const emphasisIsAmbiguous =
      emphasis.length > 0 && exactOccurrenceCount(text, emphasis) !== 1

    return (
      <>
        <section className="inspector-section inspector-content">
          <h3>Conteúdo</h3>
          <label htmlFor={`slot-input-${slot.id}`}>{elementLabel(slot)}</label>
          <textarea
            id={`slot-input-${slot.id}`}
            name={slot.id}
            data-testid={`slot-input-${slot.id}`}
            autoComplete="off"
            disabled={disabled}
            value={text}
            onChange={(event) =>
              onChange(
                slot.id,
                event.currentTarget.value === ""
                  ? null
                  : {
                      kind: "text",
                      text: event.currentTarget.value,
                      ...(emphasis ? { emphasis } : {}),
                    },
              )
            }
          />
          {slot.maxChars != null ? (
            <span
              className="char-counter"
              data-testid={`char-counter-${slot.id}`}
              data-over={text.length > slot.maxChars || undefined}
            >
              {text.length}/{slot.maxChars}
            </span>
          ) : null}
          {slot.emphasisColorToken ? (
            <div className="slot-emphasis-field">
              <label htmlFor={`slot-emphasis-input-${slot.id}`}>Trecho em destaque</label>
              <input
                id={`slot-emphasis-input-${slot.id}`}
                data-testid={`slot-emphasis-input-${slot.id}`}
                type="text"
                disabled={disabled || text.length === 0}
                required
                aria-required="true"
                aria-describedby={`slot-emphasis-guidance-${slot.id}`}
                value={emphasis}
                aria-invalid={emphasisIsAmbiguous || undefined}
                onChange={(event) => {
                  const nextEmphasis = event.currentTarget.value
                  onChange(slot.id, {
                    kind: "text",
                    text,
                    ...(nextEmphasis ? { emphasis: nextEmphasis } : {}),
                  })
                }}
              />
              <p id={`slot-emphasis-guidance-${slot.id}`} className="field-guidance">
                Copie exatamente uma parte da frase principal.
              </p>
              {emphasisIsAmbiguous ? (
                <p className="field-guidance field-guidance-error" role="status">
                  Faça com que o trecho apareça exatamente uma vez no texto.
                </p>
              ) : null}
            </div>
          ) : null}
        </section>

        <section className="inspector-section">
          <h3>Tipografia</h3>
          <div className="inspector-grid inspector-grid-two">
            <label>
              <span>Família</span>
              <select
                value={fontToken}
                disabled={disabled}
                onChange={(event) => onPatch(slot.id, { fontToken: event.currentTarget.value })}
              >
                {Object.entries(brandIr.fonts).map(([token, item]) => (
                  <option key={token} value={token}>{item.family}</option>
                ))}
              </select>
            </label>
            <label>
              <span>Peso</span>
              <select
                value={override.fontWeight ?? font?.weight ?? 400}
                disabled={disabled}
                onChange={(event) => onPatch(slot.id, { fontWeight: Number(event.currentTarget.value) })}
              >
                {[100, 200, 300, 400, 500, 600, 700, 800, 900].map((weight) => (
                  <option key={weight} value={weight}>{weight}</option>
                ))}
              </select>
            </label>
            <label>
              <span>Tamanho</span>
              <input
                type="number"
                min="6"
                max="1024"
                value={override.fontSizePx ?? role?.maxSizePx ?? 24}
                disabled={disabled}
                onChange={(event) => {
                  const value = numberValue(event.currentTarget.value)
                  if (value !== null) onPatch(slot.id, { fontSizePx: Math.max(6, Math.min(1024, value)) })
                }}
              />
            </label>
            <label>
              <span>Estilo</span>
              <select
                value={override.fontStyle ?? font?.style ?? "normal"}
                disabled={disabled}
                onChange={(event) =>
                  onPatch(slot.id, { fontStyle: event.currentTarget.value as "normal" | "italic" })
                }
              >
                <option value="normal">Normal</option>
                <option value="italic">Itálico</option>
              </select>
            </label>
            <label>
              <span>Entrelinha</span>
              <input
                type="number"
                min="0.5"
                max="3"
                step="0.05"
                value={override.lineHeight ?? role?.lineHeight ?? 1.2}
                disabled={disabled}
                onChange={(event) => {
                  const value = numberValue(event.currentTarget.value)
                  if (value !== null) onPatch(slot.id, { lineHeight: Math.max(0.5, Math.min(3, value)) })
                }}
              />
            </label>
            <label>
              <span>Tracking</span>
              <input
                type="number"
                min="-0.25"
                max="1"
                step="0.01"
                value={override.letterSpacingEm ?? slot.letterSpacingEm ?? 0}
                disabled={disabled}
                onChange={(event) => {
                  const value = numberValue(event.currentTarget.value)
                  if (value !== null) onPatch(slot.id, { letterSpacingEm: Math.max(-0.25, Math.min(1, value)) })
                }}
              />
            </label>
          </div>
          <div className="inspector-grid inspector-grid-two">
            <label>
              <span>Cor</span>
              <select
                value={override.colorToken ?? ""}
                disabled={disabled}
                onChange={(event) =>
                  onPatch(slot.id, { colorToken: event.currentTarget.value || null })
                }
              >
                <option value="">Padrão do layout</option>
                {Object.entries(brandIr.colors).map(([token, item]) => (
                  <option key={token} value={token}>{token} · {item.value}</option>
                ))}
              </select>
            </label>
            <label>
              <span>Caixa</span>
              <select
                value={override.textTransform ?? slot.textTransform ?? "none"}
                disabled={disabled}
                onChange={(event) =>
                  onPatch(slot.id, { textTransform: event.currentTarget.value as "none" | "uppercase" })
                }
              >
                <option value="none">Como digitado</option>
                <option value="uppercase">Maiúsculas</option>
              </select>
            </label>
          </div>
          <div className="segmented-control" role="group" aria-label="Alinhamento do texto">
            {(["left", "center", "right"] as const).map((align) => (
              <button
                key={align}
                type="button"
                data-active={(override.textAlign ?? slot.textAlign ?? "left") === align || undefined}
                onClick={() => onPatch(slot.id, { textAlign: align })}
                disabled={disabled}
              >
                {align === "left" ? "Esq." : align === "center" ? "Centro" : "Dir."}
              </button>
            ))}
          </div>
        </section>
      </>
    )
  }

  const uploadState = uploadStates[element.id] ?? IDLE_UPLOAD
  const canFit = ["image", "logo", "asset"].includes(element.kind)
  const canColor = ["text", "shape", "motif"].includes(element.kind)

  return (
    <form className="slot-form layer-inspector" onSubmit={(event) => event.preventDefault()}>
      <DirectionPanel
        brandIr={brandIr}
        surface={surface}
        disabled={disabled || layout.profile === "doc-a4"}
        onSurfaceChange={onSurfaceChange}
        onApplyDirection={onApplyDirection}
      />
      <div className="panel-heading inspector-heading">
        <div>
          <p className="panel-kicker">Propriedades</p>
          <h2>{elementLabel(element)}</h2>
        </div>
        <span className="element-kind">{element.kind}</span>
      </div>

      {element.kind === "text" ? renderTextControls(element) : null}

      {element.kind === "image" ? (
        <section className="inspector-section">
          <h3>Imagem</h3>
          <input
            id={`slot-image-input-${element.id}`}
            data-testid={`slot-image-input-${element.id}`}
            type="file"
            accept="image/png,image/jpeg"
            disabled={disabled || uploadState.phase === "uploading"}
            onChange={(event) => void handleImage(element.id, event)}
          />
          {uploadState.phase === "uploading" ? <p role="status">Enviando imagem…</p> : null}
          {uploadState.phase === "ready" ? <p role="status">Foto pronta.</p> : null}
          {uploadState.phase === "error" ? <p role="alert">{uploadState.message}</p> : null}
        </section>
      ) : null}

      {(canColor || canFit || element.kind === "motif") && element.kind !== "text" ? (
        <section className="inspector-section">
          <h3>Aparência</h3>
          {canColor ? (
            <label>
              <span>Cor</span>
              <select
                value={override.colorToken ?? ""}
                disabled={disabled}
                onChange={(event) =>
                  onPatch(element.id, { colorToken: event.currentTarget.value || null })
                }
              >
                <option value="">Padrão do layout</option>
                {Object.entries(brandIr.colors).map(([token, item]) => (
                  <option key={token} value={token}>{token} · {item.value}</option>
                ))}
              </select>
            </label>
          ) : null}
          {canFit ? (
            <label>
              <span>Encaixe</span>
              <select
                value={override.fit ?? ("fit" in element ? element.fit : "contain") ?? "contain"}
                disabled={disabled}
                onChange={(event) =>
                  onPatch(element.id, { fit: event.currentTarget.value as "contain" | "cover" })
                }
              >
                <option value="contain">Conter</option>
                <option value="cover">Cobrir</option>
              </select>
            </label>
          ) : null}
          {element.kind === "motif" ? (
            <div className="inspector-grid inspector-grid-two">
              <label>
                <span>Traço</span>
                <input
                  type="number"
                  min="0.1"
                  max="20"
                  step="0.1"
                  value={override.strokeWidthPx ?? element.strokeWidthPx}
                  onChange={(event) => {
                    const value = numberValue(event.currentTarget.value)
                    if (value !== null) onPatch(element.id, { strokeWidthPx: value })
                  }}
                />
              </label>
              <label>
                <span>Intervalo</span>
                <input
                  type="number"
                  min="1"
                  max="256"
                  value={override.spacingPx ?? element.spacingPx}
                  onChange={(event) => {
                    const value = numberValue(event.currentTarget.value)
                    if (value !== null) onPatch(element.id, { spacingPx: value })
                  }}
                />
              </label>
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="inspector-section">
        <h3>Posição e dimensões</h3>
        <p className="field-guidance">
          Valores negativos criam sangria; largura e altura podem ultrapassar o canvas.
        </p>
        <div className="inspector-grid inspector-grid-four">
          {(["X", "Y", "L", "A"] as const).map((label, index) => (
            <label key={label}>
              <span>{label}</span>
              <input
                type="number"
                min={index < 2 ? -MAX_EDITOR_AREA_PX : 1}
                max={MAX_EDITOR_AREA_PX}
                value={area[index]}
                disabled={disabled}
                onChange={(event) => setAreaValue(index, event.currentTarget.value)}
              />
            </label>
          ))}
        </div>
      </section>

      <section className="inspector-section">
        <h3>Camada</h3>
        <label className="range-field">
          <span>Opacidade</span>
          <input
            type="range"
            min="0"
            max="100"
            value={Math.round(opacity * 100)}
            disabled={disabled}
            onChange={(event) => onPatch(element.id, { opacity: Number(event.currentTarget.value) / 100 })}
          />
          <output>{Math.round(opacity * 100)}%</output>
        </label>
        <div className="inspector-grid inspector-grid-two">
          <label>
            <span>Ordem</span>
            <input
              type="number"
              min="0"
              max="20"
              value={zIndex}
              disabled={disabled}
              onChange={(event) => {
                const value = numberValue(event.currentTarget.value)
                if (value !== null) onPatch(element.id, { zIndex: Math.max(0, Math.min(20, Math.round(value))) })
              }}
            />
          </label>
          <label className="toggle-field">
            <span>Visível</span>
            <input
              type="checkbox"
              checked={!override.hidden}
              disabled={disabled}
              onChange={(event) => onPatch(element.id, { hidden: !event.currentTarget.checked })}
            />
          </label>
        </div>
      </section>

      <button
        type="button"
        className="inspector-reset"
        disabled={disabled || !overrides[element.id]}
        onClick={() => onReset(element.id)}
      >
        Restaurar esta camada
      </button>
    </form>
  )
}
