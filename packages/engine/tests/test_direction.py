from brand_runtime.intake.direction import derive_creative_direction
from brand_runtime.ir.models import BrandIdentity


def _identity(**updates: str) -> BrandIdentity:
    values = {
        "essence": "Marca com propósito claro.",
        "personality": "",
        "voice": "",
        "avoid": "",
        "evidence": [],
    }
    values.update(updates)
    return BrandIdentity(**values)


def test_restricoes_invertem_o_sinal_em_vez_de_descrever_a_marca():
    direction = derive_creative_direction(
        _identity(
            personality="Afetuosa, artesanal, acolhedora e delicada.",
            avoid="Nunca rígida, técnica ou impessoal.",
        )
    )

    assert direction is not None
    assert direction.geometry.value < 0
    assert direction.formality.value < 0
    assert direction.materiality.value < 0
    assert "não rigida" in direction.geometry.evidence_terms


def test_termos_sao_palavras_completas_e_nao_pedacos_de_outras_palavras():
    direction = derive_creative_direction(
        _identity(
            essence="Uma experiência calma e próxima.",
            avoid="Impessoal jamais.",
        )
    )

    assert direction is not None
    assert direction.energy.evidence_terms == ["calma"]
    assert direction.formality.evidence_terms == ["proxima"]


def test_direcao_da_doceria_preserva_camadas_sem_virar_tecnica():
    direction = derive_creative_direction(
        _identity(
            essence=(
                "Afeto em camadas. Um bolo se constrói com calma, cuidado e ordem, "
                "camada por camada."
            ),
            personality="Afetuosa, artesanal, acolhedora e delicada.",
            voice="Escrita quente e próxima.",
            avoid="Nunca fria, dessaturada, rígida ou impessoal.",
        )
    )

    assert direction is not None
    assert direction.composition == "layered"
    assert direction.surface == "paper-grain"
    assert direction.energy.value < 0
    assert direction.geometry.value < 0
    assert direction.formality.value < 0
    assert direction.materiality.value < 0
    assert direction.contrast.value < 0


def test_marca_editorial_le_masculinos_e_rejeicao_de_baixo_contraste():
    direction = derive_creative_direction(
        _identity(
            personality=(
                "Autoral, preciso, artesanal e técnico. Editorial, geométrico e tipográfico. "
                "Papel quente e grid visível."
            ),
            voice="Preciso e sóbrio, sem floreio.",
            avoid="Nunca aplicar diretamente sobre fundo de baixo contraste.",
        )
    )

    assert direction is not None
    assert direction.geometry.value > 0
    assert direction.materiality.value < 0
    assert direction.contrast.value > 0
    assert direction.contrast.evidence_terms == ["não baixo contraste"]
