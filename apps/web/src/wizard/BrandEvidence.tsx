import { useState } from "react"

const evidence = [
  {
    name: "Manual",
    description: "O manual ajuda a entender as regras e o jeito da marca.",
  },
  {
    name: "Logo",
    description: "Os arquivos mostram quais versões do logo podem ser usadas.",
  },
  {
    name: "Fontes",
    description: "Os arquivos de fonte fazem os textos aparecerem do jeito certo.",
  },
]

const notes = [
  "Primeiro, lemos os arquivos que você enviou.",
  "Quando algo não está claro, você escolhe.",
  "Depois, suas escolhas aparecem nos modelos da marca.",
]

export function BrandEvidence() {
  const [activeEvidence, setActiveEvidence] = useState(0)
  const [activeNote, setActiveNote] = useState(0)

  const moveNote = (direction: -1 | 1) => {
    setActiveNote((current) => (current + direction + notes.length) % notes.length)
  }

  return (
    <aside className="brand-evidence" aria-label="Como usamos os arquivos da marca">
      <figure className="evidence-photo" data-motion-enter>
        <img
          src="/brand-archive.webp"
          alt="Manual, amostras de cor e arquivos da marca sobre uma mesa"
          width="1024"
          height="1536"
          loading="lazy"
          decoding="async"
        />
      </figure>

      <div className="evidence-accordion" role="group" aria-label="Arquivos usados">
        {evidence.map((item, index) => {
          const active = index === activeEvidence
          return (
            <button
              key={item.name}
              type="button"
              className="evidence-item"
              aria-expanded={active}
              data-active={active || undefined}
              onClick={() => setActiveEvidence(index)}
              onFocus={() => setActiveEvidence(index)}
            >
              <strong>{item.name}</strong>
              <span>{item.description}</span>
            </button>
          )
        })}
      </div>

      <section className="evidence-carousel" aria-label="Como funciona">
        <p aria-live="polite">{notes[activeNote]}</p>
        <div className="evidence-carousel-controls">
          <button type="button" className="text-action" onClick={() => moveNote(-1)}>
            Anterior
          </button>
          <span aria-hidden="true">
            {activeNote + 1}/{notes.length}
          </span>
          <button type="button" className="text-action" onClick={() => moveNote(1)}>
            Próxima
          </button>
        </div>
      </section>
    </aside>
  )
}
