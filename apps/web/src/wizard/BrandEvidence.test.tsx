import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"

import { BrandEvidence } from "./BrandEvidence"

describe("BrandEvidence", () => {
  it("explica os materiais e permite percorrer os princípios", async () => {
    const user = userEvent.setup()
    render(<BrandEvidence />)

    expect(screen.getByRole("img")).toHaveAttribute("src", "/brand-archive.webp")
    expect(screen.getByRole("button", { name: /Manual/ })).toHaveAttribute(
      "aria-expanded",
      "true",
    )

    await user.click(screen.getByRole("button", { name: /Logo/ }))
    expect(screen.getByRole("button", { name: /Logo/ })).toHaveAttribute(
      "aria-expanded",
      "true",
    )

    expect(
      screen.getByText("Primeiro, lemos os arquivos que você enviou."),
    ).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Próxima" }))
    expect(
      screen.getByText("Quando algo não está claro, você escolhe."),
    ).toBeInTheDocument()
  })
})
