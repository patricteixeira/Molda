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

## SDK Python e adapter de referência

O [`brand-runtime-adapter-sdk`](../../packages/adapter-sdk-python) oferece um
builder Python 3.12+ sob licença MIT e sem dependências de runtime. Ele não
importa nem executa o engine AGPL: valida a convenção pública, copia somente
arquivos regulares para um staging no mesmo volume, escreve o manifesto final e
publica o diretório completo de uma vez. Destinos existentes, colisões por caixa,
paths não portáveis e combinações inválidas de role/path/MIME são recusados.

O pacote instala também `brandrt-adapter-dtcg`, um adapter offline de referência
para tokens DTCG e logo SVG/PNG:

```bash
brandrt-adapter-dtcg tokens.json --logo logo.svg \
  --label "Export local" --out out/minha-marca
brandrt package-validate out/minha-marca
```

O adapter não usa rede nem recebe credenciais. Seu papel é demonstrar o contrato
completo, não inferir decisões ausentes da marca. Os testes do SDK submetem a
saída ao validator e ao intake reais do engine para impedir que as duas
implementações divirjam.

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
