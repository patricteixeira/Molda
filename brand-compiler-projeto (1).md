# Compilador de marca e runtime de conformidade documental

Exato. Essa distinção torna o produto muito mais preciso.

A definição correta seria:

> **Um compilador e runtime de marca que lê um sistema visual já existente, converte suas regras em uma especificação executável, gera arquivos nativos editáveis e monitora a conformidade da marca durante a edição.**

A pesquisa já identificava que a lacuna está justamente na combinação de três capacidades: normalização do sistema visual, geração nativa de arquivos e edição contínua com validação de marca. Sua correção elimina qualquer ambiguidade sobre a primeira etapa: o sistema **não cria a identidade**, apenas a interpreta e executa.

## O produto não é um editor genérico

Não é necessário clonar Word, PowerPoint ou Canva.

Esses editores resolvem uma função diferente: manipulação de conteúdo. Seu produto deve resolver a camada situada entre o sistema de marca e o editor.

A arquitetura conceitual possui três componentes:

1. **Brand Compiler**  
   Lê o sistema visual existente e o transforma em uma representação estruturada.

2. **Document Renderer**  
   Usa essa representação para gerar `.pptx`, `.docx` e outros formatos nativos.

3. **Brand Linter/Runtime**  
   Analisa as alterações feitas pelo usuário e detecta ou corrige violações das regras da marca.

Isso é semelhante à relação entre código-fonte, compilador e linter. O design system é a especificação; o documento é o artefato compilado; o linter garante que alterações posteriores continuem válidas.

## Uma premissa precisa ser corrigida

Provavelmente não existirá um único “arquivo de design system” universal.

Na prática, uma empresa pode ter sua identidade distribuída entre:

- variáveis e estilos no Figma;
- tokens JSON;
- Tokens Studio;
- arquivos do Style Dictionary;
- PDF de brand guidelines;
- apresentações-modelo;
- templates de Word;
- pastas de logos e ícones;
- arquivos de fontes;
- bibliotecas de imagens;
- instruções escritas sobre uso de marca.

Portanto, o produto deveria aceitar um **pacote de marca**, não apenas um arquivo.

Um pacote poderia ter esta estrutura:

```text
brand-package/
├── manifest.json
├── tokens.json
├── rules.json
├── assets/
│   ├── logos/
│   ├── icons/
│   └── images/
├── templates/
│   ├── presentation.pptx
│   └── document.docx
└── references/
    └── brand-guidelines.pdf
```

Não seria obrigatório fornecer tudo. O sistema analisaria as fontes disponíveis, atribuiria níveis de confiança e informaria quais regras não conseguiu determinar.

Esse comportamento é importante: quando uma informação não existir no sistema original, o produto não deveria inventá-la silenciosamente.

## A camada central: Brand IR

O componente mais importante não será o editor. Será uma representação intermediária da marca, que pode ser chamada de **Brand IR**, `Brand Profile` ou `Executable Brand Specification`.

Esse modelo seria independente de PowerPoint, Word, Figma ou qualquer outro formato.

Exemplo simplificado:

```json
{
  "brand": {
    "name": "Empresa X",
    "version": "2.1"
  },
  "colors": {
    "primary": "#123456",
    "secondary": "#F4A300",
    "background": "#FFFFFF",
    "text": "#1A1A1A"
  },
  "typography": {
    "heading": {
      "family": "Inter",
      "weight": 700
    },
    "body": {
      "family": "Inter",
      "weight": 400
    }
  },
  "logos": {
    "primary": "assets/logos/primary.svg",
    "minimumWidth": 120,
    "clearSpace": 24
  },
  "documentRoles": {
    "title": {
      "fontRole": "heading",
      "colorRole": "primary"
    },
    "body": {
      "fontRole": "body",
      "colorRole": "text"
    }
  },
  "rules": {
    "allowUnregisteredColors": false,
    "allowUnregisteredFonts": false,
    "requireLogoOnCover": true
  }
}
```

Essa representação permite que o mesmo sistema de marca seja aplicado a vários renderizadores:

```text
Brand IR
   ├── PPTX Renderer
   ├── DOCX Renderer
   ├── PDF Exporter
   ├── Instagram 1:1 Renderer
   ├── Instagram 4:5 Renderer
   └── Stories 9:16 Renderer
```

Assim, post para Instagram não é um produto separado. É apenas outro formato de página e outro conjunto de regras de composição.

## O que “arquivo nativo editável” deve significar

Esse ponto precisa virar um requisito técnico explícito.

Um `.pptx` não pode ser apenas uma imagem colocada dentro de um slide. Um `.docx` não pode ser um conjunto de screenshots ou caixas desenhadas.

Para ser realmente nativo:

- texto deve continuar sendo texto;
- imagens devem continuar substituíveis;
- tabelas devem ser tabelas;
- gráficos devem ser objetos editáveis sempre que possível;
- títulos devem usar placeholders ou estilos semânticos;
- fontes e cores devem estar configuradas no tema;
- slides devem usar masters e layouts;
- documentos devem usar estilos de parágrafo e caractere;
- cabeçalhos, rodapés e numeração devem usar recursos nativos;
- o arquivo deve abrir sem mensagens de reparo;
- a edição externa não deve destruir a estrutura do documento.

Esse é um diferencial relevante contra ferramentas que “exportam para PowerPoint”, mas entregam dezenas de elementos absolutamente posicionados, difíceis de editar e sem qualquer estrutura semântica.

## Como funcionam os guardrails

“Guardrails” pode significar três níveis diferentes.

### 1. Validação posterior

O usuário edita normalmente. Ao salvar ou exportar, o sistema verifica:

- cores não autorizadas;
- fontes não autorizadas;
- tamanhos incorretos;
- hierarquia tipográfica inconsistente;
- logo ausente;
- logo deformado;
- logo menor que o permitido;
- conteúdo fora da área segura;
- contraste inadequado;
- excesso de texto;
- elementos desalinhados;
- margens incorretas.

Esse é o nível mais simples e adequado ao primeiro MVP.

### 2. Assistência durante a edição

O sistema acompanha a edição e mostra alertas:

> “Este título utiliza uma fonte fora do sistema da marca.”

> “A cor deste objeto não pertence à paleta aprovada.”

> “O logo está abaixo do tamanho mínimo.”

Também pode oferecer ações como:

- “Corrigir fonte”;
- “Usar cor mais próxima da marca”;
- “Restaurar espaçamento”;
- “Aplicar estilo de título”;
- “Substituir pelo logo oficial”.

Esse provavelmente deve ser o objetivo principal do produto.

### 3. Aplicação rígida

O sistema impede determinadas alterações:

- não permite cores externas;
- bloqueia a posição do logo;
- impede a troca de determinadas fontes;
- restringe layouts;
- bloqueia elementos institucionais.

Isso é tecnicamente mais complexo e pode tornar a edição frustrante. Deve ser configurável, não o comportamento padrão.

Uma organização poderia definir a severidade de cada regra:

```text
INFO     — recomendação
WARNING  — desvio permitido, mas sinalizado
ERROR    — precisa ser corrigido antes da exportação
LOCKED   — alteração não permitida
```

## O MVP não deveria começar com três editores

Eu não começaria simultaneamente com slides, documentos e edição de PDF.

PowerPoint e Word são dois motores de layout diferentes. Apesar de ambos utilizarem OOXML, a lógica interna é bastante distinta:

- slides são páginas de composição espacial;
- documentos são fluxos contínuos de texto;
- PDFs são representações finais de página, não um bom formato canônico de edição.

O escopo inicial mais racional é:

### MVP 1: apresentações

**Entrada:**

- tokens JSON;
- logos e assets;
- fontes ou referências de fontes;
- uma apresentação-modelo opcional;
- regras básicas da marca.

**Saída:**

- `.pptx` nativo e editável;
- PDF exportado;
- formatos 16:9, 4:3, 1:1, 4:5 e 9:16.

**Layouts iniciais:**

- capa;
- título de seção;
- título e texto;
- texto e imagem;
- duas colunas;
- citação;
- dados ou gráfico;
- encerramento.

**Guardrails iniciais:**

- fontes;
- cores;
- estilos de título;
- margens;
- alinhamento;
- uso do logo;
- excesso de conteúdo;
- dimensões e área segura.

Isso já resolve apresentações e grande parte da produção para redes sociais.

### MVP 2: edição e round-trip

O usuário:

1. gera o `.pptx`;
2. edita no navegador ou no PowerPoint;
3. envia novamente o arquivo;
4. recebe um relatório de conformidade;
5. aplica correções automáticas.

Esse round-trip é essencial. A promessa do produto não termina na primeira geração.

### MVP 3: documentos

Depois, adicionar:

- `.docx` nativo;
- estilos de título e corpo;
- capas;
- cabeçalhos e rodapés;
- tabelas;
- listas;
- citações;
- seções;
- sumário;
- paginação;
- modelos de relatório e proposta.

### PDF

PDF deveria inicialmente ser tratado como:

- exportação final;
- formato de distribuição;
- preview;
- eventualmente uma fonte auxiliar para extrair guidelines.

Não recomendaria começar com edição semântica de PDF. Isso aumentaria muito a complexidade sem fortalecer a proposta central.

## Arquitetura técnica recomendada

Uma arquitetura plausível seria:

```text
┌───────────────────────────────────┐
│ Importadores                     │
│ Figma / Tokens / PPTX / DOCX/PDF │
└────────────────┬──────────────────┘
                 │
                 ▼
┌───────────────────────────────────┐
│ Brand Normalizer                 │
│ Conflitos, aliases, semântica    │
└────────────────┬──────────────────┘
                 │
                 ▼
┌───────────────────────────────────┐
│ Brand IR                         │
│ Especificação versionada         │
└───────────┬───────────┬───────────┘
            │           │
            ▼           ▼
    PPTX Compiler   DOCX Compiler
            │           │
            └─────┬─────┘
                  ▼
┌───────────────────────────────────┐
│ Editor / Integração Office       │
└────────────────┬──────────────────┘
                 ▼
┌───────────────────────────────────┐
│ Brand Linter                     │
│ Alertas, correções e bloqueios   │
└────────────────┬──────────────────┘
                 ▼
            PDF / Imagens
```

Para a implementação:

- **frontend:** React ou Next.js;
- **schema da marca:** JSON Schema compatível, quando possível, com DTCG Design Tokens;
- **motor OOXML:** C# com Open XML SDK é uma opção particularmente forte para manipulação estrutural de PPTX e DOCX;
- **serviço de regras:** TypeScript, C# ou uma DSL declarativa;
- **editor embutido:** adapter para ONLYOFFICE ou Collabora;
- **armazenamento:** arquivos nativos mais Brand IR versionado;
- **preview:** serviço de renderização de páginas e slides;
- **fila de processamento:** necessária para importação, geração de preview e exportação;
- **testes:** comparação estrutural dos arquivos e renderização visual automatizada.

O motor de documentos deveria ser separado da interface. Assim, outras aplicações podem utilizar a tecnologia por API ou CLI.

## A parte mais difícil não é a geração inicial

Os maiores riscos técnicos são outros.

### Interpretação de regras implícitas

Tokens informam que uma cor existe, mas não necessariamente dizem:

- quando ela deve ser usada;
- quanto espaço deve existir em torno do logo;
- quais combinações são proibidas;
- quais layouts são aprovados;
- como um gráfico deve ser estilizado;
- quanto texto cabe em uma composição.

Por isso, tokens precisam ser complementados com templates, exemplos e regras semânticas.

### Compatibilidade OOXML

PPTX e DOCX têm muitas particularidades. Gerar um arquivo que abre é relativamente fácil. Gerar um arquivo bem estruturado, editável, interoperável e preservável em múltiplos editores é muito mais difícil.

Será necessário manter uma suíte de arquivos de referência e testes de regressão.

### Edição contínua

Validar um arquivo depois de salvo é simples em comparação com monitorar cada alteração em tempo real. Diferentes editores expõem níveis diferentes de acesso ao documento.

A arquitetura deve suportar três formas de integração:

- validação de arquivo após salvamento;
- plugin ou painel lateral dentro do editor;
- editor web embutido com integração própria.

### Licenciamento de fontes e ativos

Uma ferramenta open source não pode presumir que pode redistribuir fontes comerciais junto com o pacote de marca. O sistema deve distinguir:

- fonte instalada localmente;
- fonte hospedada e licenciada;
- fonte incorporável;
- fonte apenas referenciada;
- fallback autorizado.

### Conflitos no próprio sistema de marca

É comum encontrar:

- cores diferentes no PDF e no Figma;
- templates antigos;
- logos desatualizados;
- fontes ausentes;
- estilos duplicados;
- regras contraditórias.

O importador precisa exibir conflitos e permitir que alguém escolha a fonte de verdade.

## O diferencial competitivo

O diferencial não será simplesmente “usar IA para criar documentos”. Isso já está se tornando uma commodity.

O ativo defensável seria:

- um Brand IR bem projetado;
- importadores para diferentes sistemas;
- alta fidelidade OOXML;
- regras de conformidade declarativas;
- capacidade de corrigir violações;
- round-trip de arquivos;
- compatibilidade com editores existentes;
- biblioteca comunitária de adapters;
- testes visuais e estruturais;
- sistema de versionamento de marca.

A IA pode ajudar em tarefas como:

- classificar estilos;
- identificar hierarquias;
- converter guidelines escritas em regras;
- escolher layouts;
- resumir conteúdo;
- adaptar um documento para outro formato.

Mas a conformidade não deve depender exclusivamente de IA. Regras de marca importantes devem ser determinísticas, auditáveis e reproduzíveis.

## Formulação final do projeto

Uma descrição mais precisa para o repositório seria:

> Plataforma open source que importa sistemas visuais existentes, normaliza suas regras em um perfil de marca executável e gera documentos nativos editáveis com validação contínua de conformidade.

Ou, de forma mais curta:

> **Open-source brand compiler and document compliance runtime.**

O núcleo do produto é este fluxo:

```text
Sistema de marca existente
        ↓
Interpretação e normalização
        ↓
Brand IR versionado
        ↓
Geração nativa de PPTX/DOCX
        ↓
Edição pelo usuário
        ↓
Validação e correção contínuas
```

A decisão estratégica mais importante é começar como **motor de marca para arquivos existentes**, não como nova suíte de produtividade. O primeiro marco deveria ser um PPTX verdadeiramente nativo, gerado a partir de uma marca existente, editado pelo usuário e validado novamente sem perder sua estrutura. Esse resultado isolado já demonstra a tese central do projeto.
