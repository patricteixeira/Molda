import type { PropsWithChildren } from "react"
import { Link, useLocation } from "react-router-dom"

export function AppChrome({ children }: PropsWithChildren) {
  const { pathname } = useLocation()
  const editorMatch = pathname.match(/^\/marcas\/([^/]+)\/editor\//)
  const revisionAreaMatch = pathname.match(/^\/marcas\/([^/]+)\/(kit|campanhas|word)$/)
  const revisionId = revisionAreaMatch?.[1]
  const area = revisionAreaMatch?.[2]
  const currentArea =
    area === "kit"
      ? "Kit"
      : area === "campanhas"
        ? "Campanhas"
        : area === "word"
          ? "Word"
          : pathname === "/"
            ? "Instalação"
            : "Página não encontrada"
  const contextHref = revisionId && area !== "kit" ? `/marcas/${encodeURIComponent(revisionId)}/kit` : "/"
  const contextLabel = revisionId && area !== "kit" ? "Kit" : pathname === "/" ? "Instalar marca" : "Instalação"

  if (editorMatch) {
    return <div className="app-shell app-shell-editor">{children}</div>
  }

  return (
    <div className="app-shell">
      <header className="app-nav">
        <Link className="wordmark" to="/" aria-label="Molda, início">
          <span className="wordmark-mark" aria-hidden="true">
            <span>m</span>
            <span>d</span>
          </span>
          <span>Molda</span>
        </Link>
        <nav className="app-nav-links" aria-label="Navegação principal">
          <Link to={contextHref} aria-current={pathname === "/" ? "page" : undefined}>
            {contextLabel}
          </Link>
          {pathname !== "/" && <span className="app-route-current" aria-current="page">{currentArea}</span>}
          <span className="app-runtime-status">
            <span aria-hidden="true" />
            Runtime local
          </span>
        </nav>
      </header>
      {children}
      <footer className="app-footer">
        <p>
          <span>Marca não é arquivo.</span>
          <span>É decisão em execução.</span>
        </p>
        <div className="app-footer-meta">
          <p>Open source / AGPL-3.0</p>
          <p>Self-hosted / dados sob seu controle</p>
        </div>
      </footer>
    </div>
  )
}
