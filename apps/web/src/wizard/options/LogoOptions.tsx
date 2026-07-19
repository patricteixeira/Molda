import { useApi } from "../../api/context"
import type { Candidate } from "../../api/types"

interface Props {
  draftId: string
  candidates: Candidate[]
  selected: unknown
  onSelect(value: unknown): void
}

export function LogoOptions({ draftId, candidates, selected, onSelect }: Props) {
  const api = useApi()
  return (
    <div className="logo-options" role="group" aria-label="Logos encontrados">
      {candidates.map((candidate) => {
        const path = String(candidate.value)
        return (
          <button
            key={path}
            type="button"
            className="logo-option"
            data-testid="candidate-option"
            data-value={path}
            aria-pressed={selected === candidate.value}
            onClick={() => onSelect(candidate.value)}
          >
            <img
              src={api.draftAssetUrl(draftId, path)}
              alt="Opção de logo"
              width="480"
              height="240"
              loading="lazy"
              decoding="async"
            />
          </button>
        )
      })}
    </div>
  )
}
