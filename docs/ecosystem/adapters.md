# Adapters de importação

## Fronteira

Um adapter do M4 não é um plugin carregado dentro do processo da API. Ele roda
separadamente, lê a origem sob as permissões escolhidas pelo operador e produz
um diretório no contrato **Brand Package 0.1**. Essa fronteira permite adapters
em qualquer linguagem e impede que o core precise executar código comunitário.

O futuro importador Figma, um exportador de Tokens Studio e integrações
proprietárias podem entregar exatamente o mesmo pacote.

## Estrutura consumível

O manifesto `brand-package.json` declara a identidade e versão do adapter, uma
descrição não sensível da origem e todos os arquivos consumíveis:

```text
brand-package.json
tokens.json ou *.tokens.json
*.pdf
references/*.pdf
assets/logos/*.svg ou *.png
fonts/*.ttf ou *.otf
```

Cada arquivo tem `path`, `role`, `mediaType`, `size` e `sha256`. O manifesto não
declara a si próprio. Paths são relativos, POSIX, NFC, usam extensão minúscula,
são únicos sem distinguir maiúsculas e portáveis em Windows. Arquivos não
declarados, ausentes,
adulterados, links simbólicos e colisões são recusados.

O schema canônico está em
[`schemas/brand-package.schema.json`](../../schemas/brand-package.schema.json)
sob licença MIT. Uma implementação mínima está em
[`examples/brand-package-reference`](../../examples/brand-package-reference).

## Conformidade

Instale o engine e valide a saída antes de enviá-la para uma instância:

```bash
brandrt package-validate ./meu-pacote --out validation.json
```

Sucesso retorna código `0` e um recibo com a identidade do adapter, contagem de
arquivos, bytes e SHA-256 determinístico do conjunto. Erro de contrato ou
integridade retorna código `2` sem alterar o pacote.

A rota existente `POST /v1/brands/imports` continua aceitando pacotes informais
sem manifesto. Quando `brand-package.json` está presente, a API valida todo o
contrato imediatamente após o unpack seguro e antes de sanitizar ou publicar
qualquer asset. Assim, a adoção do ecossistema é incremental e retrocompatível.

## Responsabilidade do adapter

- nunca gravar token, URL privada ou credencial no manifesto;
- preservar a origem apenas como `source.kind` e, se útil, um `source.label`
  não sensível;
- exportar bytes estáveis e calcular SHA-256 depois da escrita final;
- não redistribuir fontes sem licença compatível;
- produzir apenas a convenção suportada. Lacunas de marca continuam sendo
  resolvidas pelo wizard, não inventadas pelo adapter.
