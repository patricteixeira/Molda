import { useEffect, useState } from "react"
import type { Candidate, IdentityExpressionValue } from "../../api/types"

interface Props {
  candidates: Candidate[]
  selected: unknown
  onSelect(value: unknown): void
}

const EMPTY: IdentityExpressionValue = {
  essence: "",
  personality: "",
  voice: "",
  avoid: "",
}

function identityValue(value: unknown): IdentityExpressionValue {
  if (typeof value !== "object" || value === null) return EMPTY
  const record = value as Record<string, unknown>
  return {
    essence: typeof record.essence === "string" ? record.essence : "",
    personality: typeof record.personality === "string" ? record.personality : "",
    voice: typeof record.voice === "string" ? record.voice : "",
    avoid: typeof record.avoid === "string" ? record.avoid : "",
  }
}

export function IdentityOptions({ candidates, selected, onSelect }: Props) {
  const initial = identityValue(selected ?? candidates[0]?.value)
  const [value, setValue] = useState(initial)

  useEffect(() => {
    const next = identityValue(selected ?? candidates[0]?.value)
    setValue(next)
    onSelect(next)
    // O candidato pertence à pergunta montada; reinicializamos apenas quando ela muda.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidates])

  const patch = (field: keyof IdentityExpressionValue, text: string): void => {
    const next = { ...value, [field]: text }
    setValue(next)
    onSelect(next)
  }
  const evidence = candidates[0]?.evidence ?? []
  const hasEvidence = evidence.length > 0

  return (
    <div className="identity-review">
      <p className="identity-review-intro">
        Suas respostas ajudam o Molda a escolher espaços, tamanhos, imagens e estilos que
        combinam com a marca.
      </p>

      <label className="identity-field identity-field-essence">
        <span>Por que a marca existe</span>
        <textarea
          required
          value={value.essence}
          placeholder="Conte de forma simples o que a marca faz e por que isso importa."
          onChange={(event) => patch("essence", event.currentTarget.value)}
        />
      </label>
      <label className="identity-field">
        <span>Como a marca deve parecer</span>
        <textarea
          value={value.personality}
          placeholder="Por exemplo: próxima, séria, ousada ou tranquila."
          onChange={(event) => patch("personality", event.currentTarget.value)}
        />
      </label>
      <label className="identity-field">
        <span>Como a marca fala</span>
        <textarea
          value={value.voice}
          placeholder="Descreva o jeito de falar com as pessoas."
          onChange={(event) => patch("voice", event.currentTarget.value)}
        />
      </label>
      <label className="identity-field identity-field-avoid">
        <span>O que não combina com a marca</span>
        <textarea
          value={value.avoid}
          placeholder="Liste estilos, palavras ou atitudes que não devem aparecer."
          onChange={(event) => patch("avoid", event.currentTarget.value)}
        />
      </label>

      {hasEvidence && (
        <p className="identity-review-source">
          {evidence.length + " trecho" + (evidence.length === 1 ? "" : "s") +
            (evidence.length === 1
              ? " do manual foi usado para montar estes textos."
              : " do manual foram usados para montar estes textos.")}
        </p>
      )}
    </div>
  )
}
