import { useEffect, useState } from "react"
import type { JSX } from "react"
import { Link, useParams } from "react-router-dom"
import { ApiError } from "../api/client"
import { useApi } from "../api/context"
import type { BrandIr, LayoutSpec } from "../api/types"
import { brandThemeStyle } from "../brandTheme"
import { Preview } from "../render/Preview"
import { placeholderContent } from "./placeholder"

interface KitState {
  brandIr: BrandIr
  layouts: LayoutSpec[]
}

export function KitPage(): JSX.Element {
  const { revisionId } = useParams()
  const api = useApi()
  const [kit, setKit] = useState<KitState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    setKit(null)
    setError(null)

    if (!revisionId) {
      setError("A revisão da marca não foi informada.")
      return () => {
        active = false
      }
    }

    void Promise.all([api.getBrandRevision(revisionId), api.getKit(revisionId)])
      .then(([brandIr, layouts]) => {
        if (active) setKit({ brandIr, layouts })
      })
      .catch((reason: unknown) => {
        if (!active) return
        setError(
          reason instanceof ApiError
            ? reason.messagePt
            : "Não foi possível carregar o kit da marca. Tente novamente.",
        )
      })

    return () => {
      active = false
    }
  }, [api, attempt, revisionId])

  if (error) {
    return (
      <main id="main-content" className="kit-page">
        <h1>Kit da marca</h1>
        <p role="alert">{error}</p>
        <button
          type="button"
          className="secondary-action"
          onClick={() => setAttempt((value) => value + 1)}
        >
          Tentar novamente
        </button>
      </main>
    )
  }

  if (!kit || !revisionId) {
    return (
      <main id="main-content" className="kit-page">
        <p className="loading-note" role="status">
          Carregando o kit…
        </p>
      </main>
    )
  }

  if (kit.layouts.length === 0) {
    return (
      <main id="main-content" className="kit-page">
        <h1>Kit da marca</h1>
        <p role="alert">Este kit ainda não tem modelos disponíveis.</p>
        <button
          type="button"
          className="secondary-action"
          onClick={() => setAttempt((value) => value + 1)}
        >
          Tentar novamente
        </button>
      </main>
    )
  }

  const assetsBaseUrl = api.revisionAssetsBaseUrl(revisionId)
  const headingFont = kit.brandIr.fonts["font.heading"]?.family ?? "Fonte da marca"

  return (
    <main
      id="main-content"
      className="kit-page brand-reactive-page"
      style={brandThemeStyle(kit.brandIr)}
    >
      <div className="kit-layout">
        <header className="kit-heading" data-motion-enter>
          <p className="kit-brand-name">{kit.brandIr.brand.name}</p>
          <h1>Kit da marca</h1>
          <p className="kit-intro">
            Todos os modelos usam as mesmas cores, fontes e regras. Escolha uma peça e comece.
          </p>
          <p className="kit-count">{kit.layouts.length} modelos disponíveis</p>
          <div className="brand-material-summary" aria-label="Fonte usada nos títulos">
            <span className="brand-material-swatches" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            <span>
              <small>Fonte dos títulos</small>
              <strong>{headingFont}</strong>
            </span>
          </div>
          <Link className="text-action" to="/">
            Instalar outra marca
          </Link>
        </header>

        <section className="kit-workflows" aria-labelledby="kit-workflows-title">
          <div className="kit-workflows-heading">
            <h2 id="kit-workflows-title">Uma origem. Todo o trabalho conectado.</h2>
          </div>
          <div className="kit-workflow-grid">
            <Link
              className="kit-workflow-card kit-workflow-card-primary"
              to={`/marcas/${encodeURIComponent(revisionId)}/campanhas`}
            >
              <span>
                <strong>Modo Campanha</strong>
                <small>Uma mensagem mantém post, story, apresentação e documento ligados.</small>
              </span>
              <span className="kit-workflow-action">Abrir campanha →</span>
            </Link>
            <Link
              className="kit-workflow-card"
              to={`/marcas/${encodeURIComponent(revisionId)}/word`}
            >
              <span>
                <strong>Aplicar marca ao Word</strong>
                <small>Transforme um `.docx` existente sem perder conteúdo nem edição.</small>
              </span>
              <span className="kit-workflow-action">Enviar Word →</span>
            </Link>
          </div>
        </section>

        <div
          className="kit-grid"
          data-layout-count={kit.layouts.length}
          aria-label="Modelos disponíveis"
        >
          {kit.layouts.map((layout) => (
            <Link
              key={layout.id}
              className="kit-card"
              to={`/marcas/${encodeURIComponent(revisionId)}/editor/${encodeURIComponent(layout.id)}`}
              data-layout-id={layout.id}
              data-testid="kit-card"
              aria-label={`Editar ${layout.namePt}`}
            >
              <span className="kit-proof">
                <Preview
                  brandIr={kit.brandIr}
                  layoutSpec={layout}
                  contentSpec={placeholderContent(layout, revisionId, kit.brandIr.brand.name)}
                  assetsBaseUrl={assetsBaseUrl}
                  maxWidthPx={360}
                />
              </span>
              <span className="kit-card-caption">
                <span>
                  <span>{layout.namePt}</span>
                  <span className="kit-card-action">Editar peça →</span>
                </span>
                <span className="kit-card-meta">
                  {layout.canvas.widthPx} × {layout.canvas.heightPx} px
                </span>
              </span>
            </Link>
          ))}
        </div>
      </div>
    </main>
  )
}
