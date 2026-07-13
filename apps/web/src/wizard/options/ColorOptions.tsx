import { useEffect, useId, useMemo, useRef, useState } from "react"
import type { Candidate } from "../../api/types"

interface Props {
  candidates: Candidate[]
  recommendedCount?: number
  selected: unknown
  onSelect(value: unknown): void
}

export function ColorOptions({ candidates, recommendedCount, selected, onSelect }: Props) {
  const optionsId = useId()
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([])
  const focusFirstRevealed = useRef(false)
  const curatedCount = Math.min(
    candidates.length,
    Math.max(0, recommendedCount ?? candidates.length),
  )
  const visibleRecommendationCount = curatedCount > 0 ? curatedCount : candidates.length
  const hasMore = visibleRecommendationCount < candidates.length
  const selectedIndex = useMemo(
    () => candidates.findIndex((candidate) => candidate.value === selected),
    [candidates, selected],
  )
  const [expanded, setExpanded] = useState(
    selectedIndex >= visibleRecommendationCount && selectedIndex >= 0,
  )

  useEffect(() => {
    if (selectedIndex >= visibleRecommendationCount) setExpanded(true)
  }, [selectedIndex, visibleRecommendationCount])

  useEffect(() => {
    if (expanded && focusFirstRevealed.current) {
      optionRefs.current[visibleRecommendationCount]?.focus()
      focusFirstRevealed.current = false
    }
  }, [expanded, visibleRecommendationCount])

  const selectedOutsideRecommendations =
    !expanded && selectedIndex >= visibleRecommendationCount && selectedIndex >= 0
  const visible = expanded
    ? candidates
    : [
        ...candidates.slice(0, visibleRecommendationCount),
        ...(selectedOutsideRecommendations ? [candidates[selectedIndex]] : []),
      ]

  return (
    <div className="color-choice">
      <p className="option-group-label">
        {hasMore && !expanded
          ? selectedOutsideRecommendations
            ? "Recomendadas e sua escolha"
            : "Recomendadas para este uso"
          : "Paleta completa disponível"}
      </p>
      <div id={optionsId} className="color-options" role="group" aria-label="Cores propostas">
        {visible.map((candidate, index) => {
          const value = String(candidate.value)
          return (
            <button
              key={value}
              type="button"
              ref={(node) => {
                optionRefs.current[index] = node
              }}
              className="color-option"
              data-testid="candidate-option"
              data-value={value}
              aria-label={`Cor ${value}`}
              aria-pressed={selected === candidate.value}
              style={{ backgroundColor: value }}
              onClick={() => onSelect(candidate.value)}
            >
              <span className="visually-hidden">Amostra de cor</span>
            </button>
          )
        })}
      </div>
      {hasMore && (
        <button
          type="button"
          className="show-all-options"
          aria-expanded={expanded}
          aria-controls={optionsId}
          onClick={() => {
            if (!expanded) focusFirstRevealed.current = true
            setExpanded((current) => !current)
          }}
        >
          {expanded
            ? "Mostrar apenas as recomendadas"
            : `Ver paleta completa (${candidates.length})`}
        </button>
      )}
    </div>
  )
}
