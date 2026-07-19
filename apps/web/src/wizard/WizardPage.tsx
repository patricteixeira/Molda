import { useEffect, useReducer } from "react"
import { useNavigate } from "react-router-dom"
import { BrandEvidence } from "./BrandEvidence"
import { PublishStep } from "./PublishStep"
import { QuestionReviewRail } from "./QuestionReviewRail"
import { QuestionStep } from "./QuestionStep"
import { UploadStep } from "./UploadStep"
import { initialWizardState, wizardReducer } from "./state"

const heroByStep = {
  upload: {
    kicker: "Instalação de marca",
    title: "Traga o que já existe.",
    description: "A marca começa daqui.",
    benchLabel: "ARQUIVOS",
  },
  question: {
    kicker: "Confira sua marca",
    title: "Confira o que entendemos.",
    description: "Se algo estiver errado, é só mudar.",
    benchLabel: "CONFERÊNCIA",
  },
  publish: {
    kicker: "Para terminar",
    title: "Como sua marca se chama?",
    description: "Esse nome identifica os arquivos e modelos da marca.",
    benchLabel: "NOME DA MARCA",
  },
} as const

export function WizardPage() {
  const [state, dispatch] = useReducer(wizardReducer, initialWizardState)
  const navigate = useNavigate()

  useEffect(() => {
    if (state.step === "done") {
      navigate(`/marcas/${encodeURIComponent(state.brandRevisionId)}/kit`)
    }
  }, [navigate, state])

  const visibleStep = state.step === "done" ? "publish" : state.step
  const hero = heroByStep[visibleStep]

  return (
    <main id="main-content" className="wizard-page" data-wizard-step={visibleStep}>
      <header className="wizard-hero-copy">
        <p className="product-kicker">{hero.kicker}</p>
        <h1>{hero.title}</h1>
        <p>{hero.description}</p>
      </header>
      <div className="wizard-bench" data-stage-label={hero.benchLabel}>
        <div className="wizard-stage">
          <div hidden={state.step !== "upload"}>
            <UploadStep
              onDraft={(result) =>
                dispatch({
                  type: "draft-created",
                  draftId: result.draftId,
                  questions: result.questions,
                })
              }
            />
          </div>
          {state.step === "question" && (
            <QuestionStep
              draftId={state.draftId}
              question={state.questions[state.index]}
              index={state.index}
              total={state.questions.length}
              answers={state.answers}
              onConfirm={(value) =>
                dispatch({
                  type: "answer",
                  questionId: state.questions[state.index].id,
                  value,
                })
              }
              onSkip={() => dispatch({ type: "skip" })}
              onBack={() => dispatch({ type: "back" })}
              onRestart={() => dispatch({ type: "restart" })}
            />
          )}
          {state.step === "publish" && (
            <PublishStep
              draftId={state.draftId}
              answers={state.answers}
              onBack={() => dispatch({ type: "back" })}
              onPublished={(brandRevisionId) =>
                dispatch({ type: "published", brandRevisionId })
              }
            />
          )}
        </div>
        {state.step === "question" ? (
          <QuestionReviewRail
            questions={state.questions}
            currentIndex={state.index}
            answers={state.answers}
          />
        ) : (
          <BrandEvidence />
        )}
      </div>
    </main>
  )
}
