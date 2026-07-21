import type {
  LayerOverride,
  LayoutSpec,
  ShapeLayer,
  Slot,
  SlotValue,
  SurfaceStyle,
} from "../api/types"

const STORAGE_PREFIX = "brand-runtime:editor-draft:v1"

export interface EditorDraftState {
  values: Record<string, SlotValue>
  overrides: Record<string, LayerOverride>
  surface: SurfaceStyle | null
  addedSlots: Slot[]
  addedLayers: ShapeLayer[]
  backgroundColorToken: string | null
  assetBindings: Record<string, string>
}

interface StoredEditorDraft {
  version: 5
  values: Record<string, SlotValue>
  overrides: Record<string, LayerOverride>
  surface: SurfaceStyle | null
  addedSlots: Slot[]
  addedLayers: ShapeLayer[]
  backgroundColorToken: string | null
  assetBindings: Record<string, string>
}

const EMPTY_DRAFT: EditorDraftState = {
  values: {},
  overrides: {},
  surface: null,
  addedSlots: [],
  addedLayers: [],
  backgroundColorToken: null,
  assetBindings: {},
}

function emptyDraft(): EditorDraftState {
  return {
    ...EMPTY_DRAFT,
    values: {},
    overrides: {},
    addedSlots: [],
    addedLayers: [],
    assetBindings: {},
  }
}

function storageKey(revisionId: string, layoutId: string, scopeId?: string | null): string {
  const base = `${STORAGE_PREFIX}:${encodeURIComponent(revisionId)}:${encodeURIComponent(layoutId)}`
  return scopeId ? `${base}:scope:${encodeURIComponent(scopeId)}` : base
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function validValueForSlot(value: unknown, kind: "text" | "image" | "logo"): value is SlotValue {
  if (!isRecord(value)) return false

  if (kind === "text") {
    return (
      value.kind === "text" &&
      typeof value.text === "string" &&
      (value.emphasis === undefined ||
        value.emphasis === null ||
        typeof value.emphasis === "string")
    )
  }

  if (kind === "image") {
    return (
      value.kind === "image" &&
      typeof value.path === "string" &&
      /^sha256\/[0-9a-f]{2}\/[0-9a-f]{2}\/[0-9a-f]{64}$/.test(value.path) &&
      (value.sha256 === undefined ||
        value.sha256 === null ||
        (typeof value.sha256 === "string" && /^[0-9a-f]{64}$/.test(value.sha256)))
    )
  }

  return false
}

function validArea(value: unknown): value is [number, number, number, number] {
  return (
    Array.isArray(value) &&
    value.length === 4 &&
    value.every((item) => typeof item === "number" && Number.isFinite(item)) &&
    value[2] > 0 &&
    value[3] > 0
  )
}

function validAddedSlot(value: unknown): value is Slot {
  if (!isRecord(value) || typeof value.id !== "string" || !value.id.startsWith("user-")) {
    return false
  }
  return (
    ["text", "image", "logo"].includes(String(value.kind)) &&
    validArea(value.area) &&
    (value.kind !== "text" || typeof value.role === "string")
  )
}

function validAddedLayer(value: unknown): value is ShapeLayer {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    value.id.startsWith("user-") &&
    value.kind === "shape" &&
    (value.shape === "rectangle" || value.shape === "circle") &&
    validArea(value.area) &&
    typeof value.colorToken === "string"
  )
}

export function loadEditorDraft(
  revisionId: string,
  layout: LayoutSpec,
  scopeId?: string | null,
): EditorDraftState {
  try {
    const serialized = window.localStorage.getItem(storageKey(revisionId, layout.id, scopeId))
    if (!serialized) {
      return emptyDraft()
    }

    const parsed: unknown = JSON.parse(serialized)
    if (
      !isRecord(parsed) ||
      ![1, 2, 3, 4, 5].includes(Number(parsed.version)) ||
      !isRecord(parsed.values)
    ) {
      return emptyDraft()
    }

    const addedSlots =
      (parsed.version === 4 || parsed.version === 5) && Array.isArray(parsed.addedSlots)
        ? parsed.addedSlots.filter(validAddedSlot)
        : []
    const addedLayers =
      (parsed.version === 4 || parsed.version === 5) && Array.isArray(parsed.addedLayers)
        ? parsed.addedLayers.filter(validAddedLayer)
        : []
    const slots = new Map(
      [...layout.slots, ...addedSlots].map((slot) => [slot.id, slot.kind]),
    )
    const restored: Record<string, SlotValue> = {}
    for (const [slotId, value] of Object.entries(parsed.values)) {
      const kind = slots.get(slotId)
      if (kind !== undefined && validValueForSlot(value, kind)) restored[slotId] = value
    }
    const elementIds = new Set([
      ...layout.slots.map((slot) => slot.id),
      ...(layout.lockedLayers ?? []).map((layer) => layer.id),
      ...addedSlots.map((slot) => slot.id),
      ...addedLayers.map((layer) => layer.id),
    ])
    const overrides: Record<string, LayerOverride> = {}
    if (
      [2, 3, 4, 5].includes(Number(parsed.version)) &&
      isRecord(parsed.overrides)
    ) {
      for (const [elementId, value] of Object.entries(parsed.overrides)) {
        if (elementIds.has(elementId) && isRecord(value)) {
          overrides[elementId] = value as LayerOverride
        }
      }
    }
    const surface =
      [3, 4, 5].includes(Number(parsed.version)) &&
      (parsed.surface === null || isRecord(parsed.surface))
        ? (parsed.surface as SurfaceStyle | null)
        : null
    const backgroundColorToken =
      parsed.version === 5 &&
      (parsed.backgroundColorToken === null ||
        (typeof parsed.backgroundColorToken === "string" &&
          parsed.backgroundColorToken.trim().length > 0))
        ? parsed.backgroundColorToken
        : null
    const assetElementIds = new Set(
      [
        ...[...layout.slots, ...addedSlots].filter((slot) => slot.kind === "logo"),
        ...(layout.lockedLayers ?? []).filter((layer) => layer.kind === "asset"),
      ].map((element) => element.id),
    )
    const assetBindings: Record<string, string> = {}
    if (parsed.version === 5 && isRecord(parsed.assetBindings)) {
      for (const [slotId, token] of Object.entries(parsed.assetBindings)) {
        if (assetElementIds.has(slotId) && typeof token === "string" && token.trim().length > 0) {
          assetBindings[slotId] = token
        }
      }
    }
    return {
      values: restored,
      overrides,
      surface,
      addedSlots,
      addedLayers,
      backgroundColorToken,
      assetBindings,
    }
  } catch {
    return emptyDraft()
  }
}

export function saveEditorDraft(
  revisionId: string,
  layoutId: string,
  values: Record<string, SlotValue>,
  overrides: Record<string, LayerOverride>,
  surface: SurfaceStyle | null = null,
  addedSlots: Slot[] = [],
  addedLayers: ShapeLayer[] = [],
  backgroundColorToken: string | null = null,
  assetBindings: Record<string, string> = {},
  scopeId?: string | null,
): boolean {
  try {
    const key = storageKey(revisionId, layoutId, scopeId)
    if (
      Object.keys(values).length === 0 &&
      Object.keys(overrides).length === 0 &&
      !surface &&
      addedSlots.length === 0 &&
      addedLayers.length === 0 &&
      backgroundColorToken === null &&
      Object.keys(assetBindings).length === 0
    ) {
      window.localStorage.removeItem(key)
      return true
    }

    const payload: StoredEditorDraft = {
      version: 5,
      values,
      overrides,
      surface,
      addedSlots,
      addedLayers,
      backgroundColorToken,
      assetBindings,
    }
    window.localStorage.setItem(key, JSON.stringify(payload))
    return true
  } catch {
    return false
  }
}

export function clearEditorDraft(
  revisionId: string,
  layoutId: string,
  scopeId?: string | null,
): boolean {
  try {
    window.localStorage.removeItem(storageKey(revisionId, layoutId, scopeId))
    return true
  } catch {
    return false
  }
}
