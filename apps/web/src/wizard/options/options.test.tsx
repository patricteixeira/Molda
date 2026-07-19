import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { expect, it, vi } from "vitest"
import { ApiProvider } from "../../api/context"
import type { Candidate } from "../../api/types"
import { fakeClient } from "../../test/fakeApi"
import { ColorOptions } from "./ColorOptions"
import { FontOptions, safeFontshareStylesheetUrl } from "./FontOptions"
import { LogoOptions } from "./LogoOptions"

const candidate = (value: unknown): Candidate => ({ value, score: 1, evidence: [] })

it("cores são amostras clicáveis, sem hex visível", async () => {
  const onSelect = vi.fn()
  render(
    <ColorOptions
      candidates={[candidate("#1A4D8F"), candidate("#F4A300")]}
      selected={null}
      onSelect={onSelect}
    />,
  )
  const options = screen.getAllByTestId("candidate-option")
  expect(options).toHaveLength(2)
  expect(options[0]).toHaveStyle({ backgroundColor: "#1A4D8F" })
  expect(options[0].textContent ?? "").not.toContain("#")
  await userEvent.click(options[1])
  expect(onSelect).toHaveBeenCalledWith("#F4A300")
})

it("cores abrem com a curadoria e permitem revelar a paleta inteira", async () => {
  const colors = ["#1A4D8F", "#F4A300", "#333333", "#FFFFFF"].map(candidate)
  render(
    <ColorOptions
      candidates={colors}
      recommendedCount={2}
      selected={null}
      onSelect={vi.fn()}
    />,
  )

  expect(screen.getAllByTestId("candidate-option")).toHaveLength(2)
  const toggle = screen.getByRole("button", { name: "Ver todas as cores (4)" })
  expect(toggle).toHaveAttribute("aria-expanded", "false")

  await userEvent.click(toggle)

  const revealed = screen.getAllByTestId("candidate-option")
  expect(revealed).toHaveLength(4)
  expect(revealed[2]).toHaveFocus()
  expect(
    screen.getByRole("button", { name: "Mostrar apenas as sugestões" }),
  ).toHaveAttribute("aria-expanded", "true")
})

it("mantém visível uma cor escolhida fora das recomendações ao recolher a paleta", async () => {
  const colors = ["#1A4D8F", "#F4A300", "#333333", "#FFFFFF"].map(candidate)
  render(
    <ColorOptions
      candidates={colors}
      recommendedCount={2}
      selected="#FFFFFF"
      onSelect={vi.fn()}
    />,
  )

  expect(screen.getAllByTestId("candidate-option")).toHaveLength(4)
  await userEvent.click(screen.getByRole("button", { name: "Mostrar apenas as sugestões" }))

  const visibleValues = screen
    .getAllByTestId("candidate-option")
    .map((option) => option.getAttribute("data-value"))
  expect(visibleValues).toEqual(["#1A4D8F", "#F4A300", "#FFFFFF"])
  expect(screen.getByText("Sugestões e sua escolha")).toBeInTheDocument()
})

it("fontes sem arquivo não fingem uma prévia exata", () => {
  render(
    <ApiProvider client={fakeClient()}>
      <FontOptions
        draftId="d1"
        questionId="font.heading"
        candidates={[
          candidate({ family: "Fixture Sans", weight: 700, style: "normal" }),
        ]}
        selected={null}
        onSelect={vi.fn()}
      />
    </ApiProvider>,
  )
  const sample = screen.getByTestId("font-sample")
  expect(sample.style.fontFamily).toBe("sans-serif")
  expect(sample).toHaveStyle({ fontWeight: "700" })
  expect(
    screen.getByText("Fonte encontrada no manual · amostra aproximada"),
  ).toBeInTheDocument()
})

it("não promete prévia exata quando o arquivo incluído não pode ser carregado", async () => {
  render(
    <ApiProvider client={fakeClient()}>
      <FontOptions
        draftId="d1"
        questionId="font.heading"
        candidates={[
          candidate({ family: "Fixture Sans", weight: 700, style: "normal", path: "fonts/fixture.ttf" }),
        ]}
        selected={null}
        onSelect={vi.fn()}
      />
    </ApiProvider>,
  )

  expect(
    await screen.findByText("Arquivo recebido, mas não conseguimos mostrar a fonte agora"),
  ).toBeInTheDocument()
})

it("distingue fontes da mesma variante quando somente uma possui arquivo", async () => {
  const onSelect = vi.fn()
  const unresolved = candidate({ family: "Fixture Sans", weight: 700, style: "normal" })
  const packaged = candidate({
    family: "Fixture Sans",
    weight: 700,
    style: "normal",
    path: "fonts/fixture-display.ttf",
  })
  render(
    <ApiProvider client={fakeClient()}>
      <FontOptions
        draftId="d1"
        questionId="font.heading"
        candidates={[unresolved, packaged]}
        selected={packaged.value}
        onSelect={onSelect}
      />
    </ApiProvider>,
  )

  const options = screen.getAllByTestId("candidate-option")
  expect(options).toHaveLength(2)
  expect(options[0]).toHaveAttribute("aria-pressed", "false")
  expect(options[1]).toHaveAttribute("aria-pressed", "true")
  expect(screen.getAllByTestId("font-sample")[0].style.fontFamily).toBe("sans-serif")
  expect(screen.getAllByTestId("font-sample")[1].style.fontFamily).toBe("sans-serif")

  await userEvent.click(options[0])
  expect(onSelect).toHaveBeenCalledWith(unresolved.value)
})

it("explica quando uma fonte Google incorporada está indisponível na prévia", async () => {
  render(
    <ApiProvider client={fakeClient()}>
      <FontOptions
        draftId="d1"
        questionId="font.heading"
        candidates={[
          candidate({
            family: "Fraunces",
            weight: 700,
            style: "normal",
            path: "resolved-fonts/fraunces.ttf",
            resource: {
              provider: "google-fonts",
              format: "ttf",
              usagePolicy: "redistributable",
              missingCodepoints: [],
              axes: [{ tag: "wght", minimum: 100, default: 900, maximum: 900 }],
            },
          }),
        ]}
        selected={null}
        onSelect={vi.fn()}
      />
    </ApiProvider>,
  )

  expect(await screen.findByText("Fonte adicionada, mas não conseguimos mostrá-la agora")).toBeInTheDocument()
})

it("só aplica e anuncia a fonte local depois que o arquivo carrega", async () => {
  const originalFontFace = Object.getOwnPropertyDescriptor(globalThis, "FontFace")
  const originalFonts = Object.getOwnPropertyDescriptor(document, "fonts")
  const fontSet = { add: vi.fn(), delete: vi.fn() }
  class LoadedFontFace {
    status = "loaded"
    load = vi.fn(async () => this)
  }
  Object.defineProperty(globalThis, "FontFace", {
    configurable: true,
    value: LoadedFontFace,
  })
  Object.defineProperty(document, "fonts", { configurable: true, value: fontSet })
  let unmount: () => void = () => undefined

  try {
    ;({ unmount } = render(
      <ApiProvider client={fakeClient()}>
        <FontOptions
          draftId="d1"
          questionId="font.heading"
          candidates={[
            candidate({
              family: "Fraunces",
              weight: 700,
              style: "normal",
              path: "resolved-fonts/fraunces.ttf",
              resource: {
                provider: "google-fonts",
                format: "ttf",
                usagePolicy: "redistributable",
                missingCodepoints: [],
                axes: [],
              },
            }),
          ]}
          selected={null}
          onSelect={vi.fn()}
        />
      </ApiProvider>,
    ))

    expect(await screen.findByText("Fonte pronta para usar · Google Fonts")).toBeInTheDocument()
    expect(screen.getByTestId("font-sample").style.fontFamily).toContain("br-preview-0")
    expect(fontSet.add).toHaveBeenCalledOnce()
  } finally {
    unmount()
    if (originalFontFace) Object.defineProperty(globalThis, "FontFace", originalFontFace)
    else Reflect.deleteProperty(globalThis, "FontFace")
    if (originalFonts) Object.defineProperty(document, "fonts", originalFonts)
    else Reflect.deleteProperty(document, "fonts")
  }
})

it("permite digitar uma família e seleciona o resultado resolvido", async () => {
  const onSelect = vi.fn()
  const resolveDraftFont = vi.fn(async () => ({
    candidate: {
      value: { family: "General Sans", weight: 400, style: "normal" },
      score: 1,
      evidence: [],
    },
    status: "not-found" as const,
  }))
  render(
    <ApiProvider client={fakeClient({ resolveDraftFont })}>
      <FontOptions
        draftId="d1"
        questionId="font.body"
        candidates={[]}
        selected={null}
        onSelect={onSelect}
      />
    </ApiProvider>,
  )

  await userEvent.type(screen.getByLabelText("Ou digite o nome da fonte"), "  General   Sans  ")
  await userEvent.click(screen.getByRole("button", { name: "Usar o nome digitado" }))

  expect(resolveDraftFont).toHaveBeenCalledWith("d1", "font.body", "General Sans")
  expect(onSelect).toHaveBeenCalledWith({ family: "General Sans", weight: 400, style: "normal" })
  expect(screen.getByRole("status")).toHaveTextContent("O nome foi salvo")
})

it("aceita somente a URL CSS oficial e estritamente formada do Fontshare", () => {
  const resource = {
    provider: "fontshare-external",
    format: "woff2" as const,
    upstreamRef:
      "https://api.fontshare.com/v2/css?f[]=general-sans@400&display=swap",
    usagePolicy: "restricted" as const,
    missingCodepoints: [],
    axes: [],
  }
  expect(safeFontshareStylesheetUrl({ family: "General Sans", resource })).toContain(
    "api.fontshare.com/v2/css",
  )
  expect(
    safeFontshareStylesheetUrl({
      family: "General Sans",
      resource: { ...resource, upstreamRef: "https://malicioso.invalid/font.css" },
    }),
  ).toBeNull()
  expect(
    safeFontshareStylesheetUrl({
      family: "General Sans",
      resource: {
        ...resource,
        upstreamRef:
          "https://usuario@api.fontshare.com/v2/css?f[]=general-sans@400&display=swap",
      },
    }),
  ).toBeNull()
  expect(
    safeFontshareStylesheetUrl({
      family: "General Sans",
      resource: {
        ...resource,
        upstreamRef:
          "https://api.fontshare.com/v2/css?f[]=general-sans@400&display=swap&display=swap",
      },
    }),
  ).toBeNull()
})

it("só chama a prévia Fontshare de oficial depois da permissão e carregamento real", async () => {
  const original = Object.getOwnPropertyDescriptor(document, "fonts")
  const fontSet = {
    add: vi.fn(),
    delete: vi.fn(),
    load: vi.fn(async () => [{ status: "loaded" } as FontFace]),
    check: vi.fn(() => true),
  }
  Object.defineProperty(document, "fonts", { configurable: true, value: fontSet })
  const external = candidate({
    family: "General Sans",
    weight: 400,
    style: "normal",
    resource: {
      provider: "fontshare-external",
      format: "woff2",
      upstreamRef:
        "https://api.fontshare.com/v2/css?f[]=general-sans@400&display=swap",
      licenseId: "ITF-FFL-1.0",
      usagePolicy: "restricted",
      missingCodepoints: [],
      axes: [],
    },
  })

  try {
    render(
      <ApiProvider client={fakeClient()}>
        <FontOptions
          draftId="d1"
          questionId="font.body"
          candidates={[external]}
          selected={external.value}
          onSelect={vi.fn()}
        />
      </ApiProvider>,
    )
    expect(screen.getByTestId("font-sample").style.fontFamily).toBe("sans-serif")
    expect(
      screen.getByText("A fonte pode ser mostrada pelo site Fontshare"),
    ).toBeInTheDocument()

    await userEvent.click(
      screen.getByRole("checkbox", {
        name: "Mostrar esta fonte como ela realmente é usando o site Fontshare",
      }),
    )
    const stylesheet = await waitFor(() => {
      const link = document.head.querySelector<HTMLLinkElement>(
        'link[data-font-provider="fontshare"]',
      )
      expect(link).not.toBeNull()
      return link as HTMLLinkElement
    })
    expect(stylesheet.referrerPolicy).toBe("no-referrer")
    fireEvent.load(stylesheet)

    expect(await screen.findByText("Fonte pronta para mostrar · Fontshare")).toBeInTheDocument()
    expect(screen.getByTestId("font-sample").style.fontFamily).toContain("General Sans")
    expect(fontSet.load).toHaveBeenCalledWith(
      '400 16px "General Sans"',
      "A tipografia da sua marca",
    )

    await userEvent.click(
      screen.getByRole("checkbox", {
        name: "Mostrar esta fonte como ela realmente é usando o site Fontshare",
      }),
    )
    expect(screen.getByTestId("font-sample").style.fontFamily).toBe("sans-serif")
    expect(
      screen.getByText("A fonte pode ser mostrada pelo site Fontshare"),
    ).toBeInTheDocument()
  } finally {
    if (original) Object.defineProperty(document, "fonts", original)
    else Reflect.deleteProperty(document, "fonts")
  }
})

it("não declara uma prévia Fontshare exata quando nenhuma face foi carregada", async () => {
  const original = Object.getOwnPropertyDescriptor(document, "fonts")
  const fontSet = {
    add: vi.fn(),
    delete: vi.fn(),
    load: vi.fn(async () => [] as FontFace[]),
    check: vi.fn(() => true),
  }
  Object.defineProperty(document, "fonts", { configurable: true, value: fontSet })
  const external = candidate({
    family: "General Sans",
    weight: 400,
    style: "normal",
    resource: {
      provider: "fontshare-external",
      format: "woff2",
      upstreamRef: "https://api.fontshare.com/v2/css?f[]=general-sans@400&display=swap",
      usagePolicy: "restricted",
      missingCodepoints: [],
      axes: [],
    },
  })

  try {
    render(
      <ApiProvider client={fakeClient()}>
        <FontOptions
          draftId="d1"
          questionId="font.body"
          candidates={[external]}
          selected={external.value}
          onSelect={vi.fn()}
        />
      </ApiProvider>,
    )
    await userEvent.click(
      screen.getByRole("checkbox", {
        name: "Mostrar esta fonte como ela realmente é usando o site Fontshare",
      }),
    )
    const stylesheet = await waitFor(() => {
      const link = document.head.querySelector<HTMLLinkElement>(
        'link[data-font-provider="fontshare"]',
      )
      expect(link).not.toBeNull()
      return link as HTMLLinkElement
    })
    fireEvent.load(stylesheet)

    expect(
      await screen.findByText("Não foi possível mostrar a fonte do Fontshare agora"),
    ).toBeInTheDocument()
    expect(screen.getByTestId("font-sample").style.fontFamily).toBe("sans-serif")
  } finally {
    if (original) Object.defineProperty(document, "fonts", original)
    else Reflect.deleteProperty(document, "fonts")
  }
})

it("logo é renderizado de verdade a partir do draft", () => {
  render(
    <ApiProvider client={fakeClient()}>
      <LogoOptions
        draftId="d1"
        candidates={[candidate("assets/logos/logo.svg")]}
        selected={null}
        onSelect={vi.fn()}
      />
    </ApiProvider>,
  )
  const image = screen.getByRole("img", { name: "Opção de logo" })
  expect(image).toHaveAttribute("src", "/v1/drafts/d1/assets/assets/logos/logo.svg")
})
