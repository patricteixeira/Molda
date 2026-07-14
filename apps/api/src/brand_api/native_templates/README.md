# Templates nativos

Os arquivos em `v1/` são recursos imutáveis do exportador OOXML. Eles são
reconstruídos por `tools/build_native_templates.py`; não devem ser editados à
mão. Cada PPTX preserva o aspect ratio do perfil correspondente e contém o
layout nativo `Title and Content`. O DOCX contém os slots `title`, `body` e
`logo` usados pelo `one-pager-doc-a4`.
