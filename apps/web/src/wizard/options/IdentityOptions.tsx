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

  return (
    <div className="identity-review">
      <p className="identity-review-intro">
        Esta leitura orienta escala, ritmo, vazio, textura e estrutura. Revise livremente: o
        manual é a origem, mas a palavra final é sua.
      </p>

      <label>
        <span>Essência e propósito</span>
        <textarea
          required
          value={value.essence}
          placeholder="Por que esta marca existe e que transformação ela busca?"
          onChange={(event) => patch("essence", event.currentTarget.value)}
        />
      </label>
      <label>
        <span>Personalidade e valores</span>
        <textarea
          value={value.personality}
          placeholder="Como ela se comporta? Que qualidades precisam aparecer?"
          onChange={(event) => patch("personality", event.currentTarget.value)}
        />
      </label>
      <label>
        <span>Tom e linguagem</span>
        <textarea
          value={value.voice}
          placeholder="Como a marca fala e que sensação sua voz transmite?"
          onChange={(event) => patch("voice", event.currentTarget.value)}
        />
      </label>
      <label>
        <span>O que a marca evita</span>
        <textarea
          value={value.avoid}
          placeholder="Que clichês, posturas ou sensações não pertencem a ela?"
          onChange={(event) => patch("avoid", event.currentTarget.value)}
        />
      </label>

      <p className="identity-review-source">
        {evidence.length > 0
          ? evidence.length + " trecho" + (evidence.length === 1 ? "" : "s") +
            " do manual sustentam esta leitura."
          : "O manual não trouxe uma declaração textual clara. Preencha com a visão real da marca."}
      </p>
    </div>
  )
}
