import { useEffect, useMemo, useState, type JSX } from "react"
import { Link, useParams } from "react-router-dom"
import { ApiError } from "../api/client"
import { useApi } from "../api/context"
import type {
  BrandIr,
  ContentSpec,
  LayerOverride,
  LayoutSpec,
  SlotValue,
  SurfaceStyle,
} from "../api/types"
import { brandThemeStyle } from "../brandTheme"
import { placeholderContent } from "../kit/placeholder"
import { Preview } from "../render/Preview"
import { ExportControls } from "./ExportControls"
import { LayerPanel } from "./LayerPanel"
import { SlotForm } from "./SlotForm"
import { clearEditorDraft, loadEditorDraft, saveEditorDraft } from "./draftStorage"
import { directionApplication } from "./direction"
import { exactOccurrenceCount } from "./emphasis"
import { editorElements, elementArea, findEditorElement } from "./layerModel"

interface EditorPageProps {
  pollIntervalMs?: number
}

interface EditorData {
  brandIr: BrandIr
  layouts: LayoutSpec[]
}

function initialSelection(layout: LayoutSpec): string | null {
  return (
    layout.slots.find((slot) => slot.id === "headline")?.id ??
    layout.slots.find((slot) => slot.kind === "text")?.id ??
    editorElements(layout)[0]?.id ??
    null
  )
}

function compactOverride(override: LayerOverride): LayerOverride | null {
  const entries = Object.entries(override).filter(([, value]) => value !== undefined)
  return entries.length > 0 ? (Object.fromEntries(entries) as LayerOverride) : null
}

function overrideSignature(override: LayerOverride | undefined): string {
  return JSON.stringify(
    Object.entries(override ?? {}).sort(([left], [right]) => left.localeCompare(right)),
  )
}

export function EditorPage({ pollIntervalMs = 1000 }: EditorPageProps): JSX.Element {
  const api = useApi()
  const { revisionId, layoutId } = useParams()
  const [data, setData] = useState<EditorData | null>(null)
  const [values, setValues] = useState<Record<string, SlotValue>>({})
  const [overrides, setOverrides] = useState<Record<string, LayerOverride>>({})
  const [surface, setSurface] = useState<SurfaceStyle | null>(null)
  const [selectedLayerId, setSelectedLayerId] = useState<string | null>(null)
  const [zoom, setZoom] = useState(50)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [draftReady, setDraftReady] = useState(false)
  const [draftSaved, setDraftSaved] = useState(true)

  useEffect(() => {
    let active = true
    setData(null)
    setError(null)
    setValues({})
    setOverrides({})
    setSurface(null)
    setSelectedLayerId(null)
    setUploading(false)
    setExporting(false)
    setDraftReady(false)
    setDraftSaved(true)

    if (!revisionId) {
      setError("Revisão de marca não encontrada.")
      return () => {
        active = false
      }
    }

    void Promise.all([api.getBrandRevision(revisionId), api.getKit(revisionId)])
      .then(([brandIr, layouts]) => {
        if (!active) return
        const activeLayout = layouts.find((candidate) => candidate.id === layoutId)
        setData({ brandIr, layouts })
        if (activeLayout) {
          const stored = loadEditorDraft(revisionId, activeLayout)
          const sample = placeholderContent(activeLayout, revisionId, brandIr.brand.name)
          const hasStoredDraft =
            Object.keys(stored.values).length > 0 ||
            Object.keys(stored.overrides).length > 0 ||
            stored.surface !== null
          setValues(hasStoredDraft ? stored.values : sample.values)
          setOverrides(hasStoredDraft ? stored.overrides : (sample.overrides ?? {}))
          setSurface(hasStoredDraft ? stored.surface : null)
          setSelectedLayerId(initialSelection(activeLayout))
        }
        setDraftReady(true)
      })
      .catch((caught: unknown) => {
        if (!active) return
        setError(
          caught instanceof ApiError
            ? caught.messagePt
            : "Não foi possível abrir o editor.",
        )
      })

    return () => {
      active = false
    }
  }, [api, layoutId, revisionId])

  const layout = useMemo(
    () => data?.layouts.find((candidate) => candidate.id === layoutId) ?? null,
    [data, layoutId],
  )

  const contentSpec = useMemo<ContentSpec | null>(
    () =>
      revisionId && layout
        ? { layoutId: layout.id, brandRevisionId: revisionId, values, overrides, surface }
        : null,
    [layout, overrides, revisionId, surface, values],
  )

  const previewContentSpec = useMemo<ContentSpec | null>(() => {
    if (!contentSpec) return null
    const previewValues = Object.fromEntries(
      Object.entries(contentSpec.values).map(([slotId, value]) => {
        if (
          value.kind !== "text" ||
          !value.emphasis ||
          exactOccurrenceCount(value.text, value.emphasis) === 1
        ) {
          return [slotId, value]
        }
        return [slotId, { ...value, emphasis: undefined }]
      }),
    )
    return { ...contentSpec, values: previewValues }
  }, [contentSpec])

  useEffect(() => {
    if (!draftReady || !revisionId || !layout) return
    setDraftSaved(saveEditorDraft(revisionId, layout.id, values, overrides, surface))
  }, [draftReady, layout, overrides, revisionId, surface, values])

  if (error) {
    return (
      <main id="main-content" className="editor-page editor-state-page">
        <p role="alert">{error}</p>
      </main>
    )
  }

  if (!data) {
    return (
      <main id="main-content" className="editor-page editor-state-page">
        <p className="loading-note" role="status">Preparando a mesa gráfica…</p>
      </main>
    )
  }

  if (!layout || !contentSpec || !previewContentSpec || !revisionId) {
    return (
      <main id="main-content" className="editor-page editor-state-page">
        <p role="alert">Layout não encontrado neste kit.</p>
      </main>
    )
  }

  const changeValue = (slotId: string, value: SlotValue | null): void => {
    setValues((current) => {
      if (value === null) {
        const { [slotId]: _removed, ...remaining } = current
        return remaining
      }
      return { ...current, [slotId]: value }
    })
  }

  const patchOverride = (elementId: string, patch: Partial<LayerOverride>): void => {
    setOverrides((current) => {
      const nextOverride = compactOverride({ ...(current[elementId] ?? {}), ...patch })
      if (nextOverride) return { ...current, [elementId]: nextOverride }
      const { [elementId]: _removed, ...remaining } = current
      return remaining
    })
  }

  const resetLayer = (elementId: string): void => {
    setOverrides((current) => {
      const { [elementId]: _removed, ...remaining } = current
      return remaining
    })
  }

  const applyBrandDirection = (): void => {
    const application = directionApplication(data.brandIr, layout)
    if (!application) return
    setSurface(application.surface)
    setOverrides((current) => {
      const next = { ...current }
      for (const [elementId, patch] of Object.entries(application.patches)) {
        const merged = compactOverride({ ...(next[elementId] ?? {}), ...patch })
        if (merged) next[elementId] = merged
      }
      return next
    })
  }

  const restoreComposition = (): void => {
    const sample = placeholderContent(layout, revisionId, data.brandIr.brand.name)
    clearEditorDraft(revisionId, layout.id)
    setValues(sample.values)
    setOverrides(sample.overrides ?? {})
    setSurface(null)
    setSelectedLayerId(initialSelection(layout))
    setDraftSaved(true)
  }

  const selectedElement = findEditorElement(layout, selectedLayerId)
  const selectedArea = selectedElement
    ? elementArea(selectedElement, overrides[selectedElement.id])
    : null
  const sampleOverrides = placeholderContent(layout, revisionId, data.brandIr.brand.name).overrides ?? {}
  const changedLayerCount = [
    ...new Set([...Object.keys(sampleOverrides), ...Object.keys(overrides)]),
  ].filter(
      (id) => overrideSignature(overrides[id]) !== overrideSignature(sampleOverrides[id]),
    ).length

  return (
    <main
      id="main-content"
      className="editor-page brand-reactive-editor"
      style={brandThemeStyle(data.brandIr)}
    >
      <header className="editor-toolbar">
        <div className="editor-toolbar-context">
          <Link className="editor-back" to={`/marcas/${encodeURIComponent(revisionId)}/kit`}>
            <span aria-hidden="true">←</span>
            Kit
          </Link>
          <span className="editor-toolbar-rule" aria-hidden="true" />
          <div>
            <strong>{data.brandIr.brand.name}</strong>
            <span>{layout.namePt}</span>
          </div>
        </div>
        <div className="editor-toolbar-status" role="status" aria-live="polite">
          <span data-saved={draftSaved || undefined} aria-hidden="true" />
          {draftSaved ? "Salvo localmente" : "Rascunho não salvo"}
          {changedLayerCount > 0 ? <b>{changedLayerCount} ajustes</b> : null}
        </div>
        <div className="editor-toolbar-actions">
          <label className="zoom-control">
            <span>Zoom</span>
            <input
              type="range"
              min="25"
              max="100"
              step="5"
              value={zoom}
              onChange={(event) => setZoom(Number(event.currentTarget.value))}
            />
            <output>{zoom}%</output>
          </label>
          <a className="editor-export-jump" href="#export-panel">Exportar</a>
        </div>
      </header>

      <div className="editor-workbench">
        <section className="editor-preview" aria-label="Canvas da peça">
          <div className="canvas-ruler canvas-ruler-horizontal" aria-hidden="true" />
          <div className="canvas-ruler canvas-ruler-vertical" aria-hidden="true" />
          <p className="canvas-instruction">Selecione, arraste ou redimensione uma camada</p>
          <Preview
            brandIr={data.brandIr}
            layoutSpec={layout}
            contentSpec={previewContentSpec}
            assetsBaseUrl={api.revisionAssetsBaseUrl(revisionId)}
            maxWidthPx={Math.round(layout.canvas.widthPx * (zoom / 100))}
            selectedLayerId={selectedLayerId}
            selectedArea={selectedArea}
            onSelectLayer={setSelectedLayerId}
            onAreaChange={(id, area) => patchOverride(id, { area })}
          />
        </section>

        <LayerPanel
          layout={layout}
          overrides={overrides}
          selectedId={selectedLayerId}
          onSelect={setSelectedLayerId}
          onPatch={patchOverride}
          onResetAll={restoreComposition}
        />

        <SlotForm
          brandIr={data.brandIr}
          layout={layout}
          selectedId={selectedLayerId}
          values={values}
          overrides={overrides}
          onChange={changeValue}
          onPatch={patchOverride}
          onReset={resetLayer}
          surface={surface}
          onSurfaceChange={setSurface}
          onApplyDirection={applyBrandDirection}
          onUploadingChange={setUploading}
          disabled={exporting}
        />
      </div>

      <section id="export-panel" className="editor-guard-export" data-testid="editor-guard-export">
        <div className="export-panel-heading">
          <p className="panel-kicker">Saída fiel</p>
          <h2>Validar e exportar</h2>
          <p>Os ajustes do canvas são aplicados ao arquivo final.</p>
        </div>
        <ExportControls
          disabled={uploading}
          layout={layout}
          pollIntervalMs={pollIntervalMs}
          revisionId={revisionId}
          values={values}
          overrides={overrides}
          surface={surface}
          onPendingChange={setExporting}
        />
      </section>
    </main>
  )
}
