import { type FormEvent, useEffect, useRef, useState } from "react"
import { useApi } from "../api/context"
import type { ImportResult } from "../api/types"

export function UploadStep({ onDraft }: { onDraft(result: ImportResult): void }) {
  const api = useApi()
  const [files, setFiles] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const generation = useRef(0)
  useEffect(() => () => {
    generation.current += 1
  }, [])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (files.length === 0 || busy) return
    setBusy(true)
    setError(null)
    const current = ++generation.current
    try {
      const result = await api.importBrandPackage(files)
      if (generation.current === current) onDraft(result)
    } catch (cause) {
      if (generation.current !== current) return
      setError(
        typeof cause === "object" && cause !== null && "messagePt" in cause
          ? String(cause.messagePt)
          : "Não foi possível enviar o pacote da marca.",
      )
    } finally {
      if (generation.current === current) setBusy(false)
    }
  }

  return (
    <form className="upload-step" onSubmit={submit}>
      <p className="intro-copy">
        Solte aqui o manual em PDF, os logos e as fontes da marca.
      </p>
      <label className="file-receiver" htmlFor="wizard-files">
        <span>Escolher materiais da marca</span>
        <input
          id="wizard-files"
          name="brand-package"
          data-testid="wizard-file-input"
          type="file"
          multiple
          accept=".pdf,.svg,.png,.ttf,.otf,.json"
          disabled={busy}
          onChange={(event) => setFiles(Array.from(event.currentTarget.files ?? []))}
        />
      </label>
      {files.length > 0 && (
        <ul className="file-list" aria-label="Arquivos escolhidos">
          {files.map((file) => (
            <li key={`${file.name}-${file.size}`}>{file.name}</li>
          ))}
        </ul>
      )}
      {error && <p role="alert">{error}</p>}
      <button data-testid="wizard-enviar" type="submit" disabled={files.length === 0 || busy}>
        {busy ? "Enviando pacote…" : "Enviar pacote da marca"}
      </button>
    </form>
  )
}
