import { render, screen } from "@testing-library/react"
import { expect, it } from "vitest"
import type { DraftQuestion } from "../api/types"
import { QuestionReviewRail } from "./QuestionReviewRail"

const questions: DraftQuestion[] = [
  {
    id: "identity.expression",
    kind: "review-identity",
    promptPt: "Como é a sua marca?",
    candidates: [
      {
        value: { essence: "Clareza.", personality: "", voice: "", avoid: "" },
        score: 1,
        evidence: [
          {
            sourceType: "pdf-guideline",
            page: 3,
            confidence: 0.9,
            authoritative: true,
          },
        ],
      },
    ],
    required: true,
  },
  {
    id: "color.primary",
    kind: "pick-color",
    promptPt: "Qual destas é a cor principal da marca?",
    candidates: [{ value: "#112233", score: 1, evidence: [] }],
    required: true,
  },
]

it("mostra o que já foi conferido, a decisão atual e a origem em linguagem simples", () => {
  render(<QuestionReviewRail questions={questions} currentIndex={1} answers={{ "identity.expression": {} }} />)

  expect(screen.getByText("Sobre a marca").closest("li")).toHaveTextContent("pronto")
  expect(screen.getByText("Cor principal").closest("li")).toHaveAttribute("aria-current", "step")
  expect(screen.getByText("Cor principal").closest("li")).toHaveTextContent("agora")
  expect(screen.getByText(/Não encontramos essa resposta nos arquivos/i)).toBeInTheDocument()
})

it("traduz a origem do arquivo sem mostrar nomes técnicos", () => {
  render(<QuestionReviewRail questions={questions} currentIndex={0} answers={{}} />)

  expect(screen.getByText("Manual, página 3")).toBeInTheDocument()
  expect(screen.getByText("regra clara no arquivo")).toBeInTheDocument()
})
