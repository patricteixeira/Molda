import type { DraftQuestion, Evidence } from "../api/types"

interface Props {
  questions: DraftQuestion[]
  currentIndex: number
  answers: Record<string, unknown>
}

function decisionName(question: DraftQuestion): string {
  if (question.kind === "review-identity") return "Sobre a marca"
  if (question.id === "color.primary") return "Cor principal"
  if (question.id === "color.secondary") return "Outra cor"
  if (question.id === "color.background") return "Cor dos fundos"
  if (question.id === "color.text") return "Cor dos textos"
  if (question.id === "logo.onLight") return "Logo em fundo claro"
  if (question.id === "logo.onDark") return "Logo em fundo escuro"
  if (question.kind === "confirm-logo") return "Logo"
  if (question.id === "font.heading") return "Fonte dos títulos"
  if (question.id === "font.body") return "Fonte dos textos"
  if (question.kind === "pick-color") return "Cores"
  if (question.kind === "pick-font") return "Fontes"
  return "Outra escolha"
}

function fileName(path: string | null | undefined): string | null {
  if (!path) return null
  return path.split(/[\\/]/).pop() ?? null
}

function evidenceName(evidence: Evidence): string {
  const suffix = evidence.page ? `, página ${evidence.page}` : ""
  const asset = fileName(evidence.path)
  if (evidence.sourceType === "pdf-guideline") return `Manual${suffix}`
  if (evidence.sourceType === "svg-asset") return asset ? `Logo: ${asset}` : "Arquivo do logo"
  if (evidence.sourceType === "raster-asset") return asset ? `Imagem: ${asset}` : "Imagem da marca"
  if (evidence.sourceType === "font-file") return asset ? `Fonte: ${asset}` : "Arquivo de fonte"
  if (evidence.sourceType === "dtcg-tokens") return asset ? `Cores e estilos: ${asset}` : "Arquivo de cores e estilos"
  if (evidence.sourceType === "font-catalog") return "Site da fonte"
  if (evidence.sourceType === "manual-entry") return "Sugestão inicial"
  return asset ?? "Outro arquivo da marca"
}

function evidenceNote(evidence: Evidence): string {
  if (evidence.sourceType === "manual-entry") return "você pode mudar"
  if (evidence.sourceType === "font-catalog") return "fonte encontrada na internet"
  return evidence.authoritative ? "regra clara no arquivo" : "encontrado no arquivo"
}

function uniqueEvidence(question: DraftQuestion): Evidence[] {
  const items = question.candidates.flatMap((candidate) => candidate.evidence)
  const keyed = new Map<string, Evidence>()
  for (const item of items) {
    const key = [item.sourceType, item.path ?? "", item.page ?? ""].join(":")
    if (!keyed.has(key)) keyed.set(key, item)
  }
  return [...keyed.values()].slice(0, 3)
}

export function QuestionReviewRail({ questions, currentIndex, answers }: Props) {
  const current = questions[currentIndex]
  const evidence = current ? uniqueEvidence(current) : []

  return (
    <aside className="question-review-rail" aria-label="Passos para conferir a marca">
      <header className="review-rail-heading">
        <p>O que falta conferir</p>
        <span>{currentIndex + 1}/{questions.length}</span>
      </header>

      <ol className="review-decision-list">
        {questions.map((question, index) => {
          const answered = Object.prototype.hasOwnProperty.call(answers, question.id)
          const state = index === currentIndex ? "current" : answered || index < currentIndex ? "done" : "next"
          return (
            <li key={question.id} data-state={state} aria-current={state === "current" ? "step" : undefined}>
              <span className="review-decision-index">{String(index + 1).padStart(2, "0")}</span>
              <span>
                <strong>{decisionName(question)}</strong>
                <small>{state === "current" ? "agora" : state === "done" ? "pronto" : "depois"}</small>
              </span>
            </li>
          )
        })}
      </ol>

      <section className="current-evidence" aria-labelledby="current-evidence-title">
        <h3 id="current-evidence-title">O que encontramos</h3>
        {evidence.length > 0 ? (
          <ul>
            {evidence.map((item) => (
              <li key={[item.sourceType, item.path, item.page].join(":")}>
                <strong>{evidenceName(item)}</strong>
                <span>{evidenceNote(item)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>
            Não encontramos essa resposta nos arquivos. Escolha o que faz sentido para sua
            marca.
          </p>
        )}
      </section>
    </aside>
  )
}
