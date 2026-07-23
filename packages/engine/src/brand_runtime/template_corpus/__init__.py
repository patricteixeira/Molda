"""API pública do laboratório de referências de templates."""

from brand_runtime.template_corpus.audit import TemplateCorpusError, audit_template_corpus
from brand_runtime.template_corpus.models import (
    TemplateCorpusManifest,
    TemplateCorpusProvenance,
    TemplateCorpusReport,
    TemplateFamilyMatch,
    TemplateGrammar,
    TemplateGrammarAxes,
    TemplatePreviewEvidence,
    TemplateReferenceAssessment,
    TemplateReferenceFile,
    TemplateReferenceManifest,
    TemplateSimilarityPair,
)

__all__ = [
    "TemplateCorpusError",
    "TemplateCorpusManifest",
    "TemplateCorpusProvenance",
    "TemplateCorpusReport",
    "TemplateFamilyMatch",
    "TemplateGrammar",
    "TemplateGrammarAxes",
    "TemplatePreviewEvidence",
    "TemplateReferenceAssessment",
    "TemplateReferenceFile",
    "TemplateReferenceManifest",
    "TemplateSimilarityPair",
    "audit_template_corpus",
]
