import { useEffect, useRef, useState } from "react"
import type { DraftQuestion } from "../api/types"
import { ColorOptions } from "./options/ColorOptions"
import { FontOptions } from "./options/FontOptions"
import { IdentityOptions } from "./options/IdentityOptions"
import { LogoOptions } from "./options/LogoOptions"

interface Props {
  draftId: string
  question: DraftQuestion
  index: number
  total: number
  answers: Record<string, unknown>
  onConfirm(value: unknown): void
  onSkip(): void
  onBack(): void
  onRestart(): void
}

function automaticallySuggestedFont(question: DraftQuestion): unknown | null {
  if (question.kind !== "pick-font") return null
  return question.candidates[0]?.value ?? null
}

function validSelection(question: DraftQuestion, value: unknown): boolean {
  if (question.kind !== "review-identity") return value !== null
  if (typeof value !== "object" || value === null) return false
  const essence = (value as Record<string, unknown>).essence
  return typeof essence === "string" && essence.trim().length > 0
}

export function QuestionStep(props: Props) {
  const { draftId, question, index, total, answers, onConfirm, onSkip, onBack, onRestart } = props
  const [selection, setSelection] = useState<{ questionId: string; value: unknown } | null>(null)
  const headingRef = useRef<HTMLHeadingElement>(null)
  const storedAnswer = Object.prototype.hasOwnProperty.call(answers, question.id)
    ? answers[question.id]
    : null
  const selected =
    selection?.questionId === question.id
      ? selection.value
      : storedAnswer ?? automaticallySuggestedFont(question)
  useEffect(() => headingRef.current?.focus(), [question.id])
  const missingDetectedOptions = question.candidates.length === 0 && question.kind !== "pick-font"
  const optionProps = {
    candidates: question.candidates,
    selected,
    onSelect: (value: unknown) => setSelection({ questionId: question.id, value }),
  }

  return (
    <section className="question-step" data-testid="wizard-question">
      <p className="wizard-progress" data-testid="wizard-progress">
        Pergunta {index + 1} de {total}
      </p>
      <h2 ref={headingRef} tabIndex={-1}>
        {question.promptPt}
      </h2>
      {missingDetectedOptions ? (
        <div className="empty-question" role="alert">
          <p>O pacote não trouxe uma opção válida para esta etapa.</p>
          <p>Volte aos materiais, acrescente os arquivos que faltam e envie o pacote novamente.</p>
        </div>
      ) : (
        <>
          {question.kind === "pick-color" && (
            <ColorOptions
              key={question.id}
              recommendedCount={question.recommendedCount}
              {...optionProps}
            />
          )}
          {question.kind === "pick-font" && (
            <FontOptions
              key={question.id}
              draftId={draftId}
              questionId={question.id as "font.heading" | "font.body"}
              {...optionProps}
            />
          )}
          {question.kind === "confirm-logo" && <LogoOptions draftId={draftId} {...optionProps} />}
          {question.kind === "review-identity" && (
            <IdentityOptions key={question.id} {...optionProps} />
          )}
        </>
      )}
      <div className="action-row">
        <button
          data-testid="wizard-trocar-materiais"
          className="secondary-action"
          type="button"
          onClick={onRestart}
        >
          {missingDetectedOptions ? "Voltar aos materiais" : "Trocar materiais"}
        </button>
        {index > 0 && (
          <button data-testid="wizard-voltar" className="secondary-action" type="button" onClick={onBack}>
            Voltar
          </button>
        )}
        {!question.required && (
            <button
              data-testid="wizard-pular"
              className="secondary-action"
              type="button"
              onClick={() => {
                setSelection(null)
                onSkip()
              }}
            >
            A marca não tem
          </button>
        )}
        <button
          data-testid="wizard-confirmar"
          type="button"
          disabled={!validSelection(question, selected) || missingDetectedOptions}
          onClick={() => onConfirm(selected)}
        >
          Confirmar
        </button>
      </div>
    </section>
  )
}
