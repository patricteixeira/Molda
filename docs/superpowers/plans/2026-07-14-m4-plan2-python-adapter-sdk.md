# Plano M4.2 — SDK Python e adapter DTCG de referência

**Objetivo:** transformar o contrato Brand Package 0.1 em uma superfície prática
para autores de adapters, sem acoplar código comunitário ao core AGPL.

## Decisão

O primeiro SDK oficial é um pacote Python 3.12+ sob licença MIT, sem dependências
de runtime. Ele materializa o contrato público por construção, mas não importa o
engine nem promete substituir sua validação canônica. A saída continua sendo um
diretório portátil que qualquer implementação em qualquer linguagem pode gerar.

O adapter de referência recebe um JSON DTCG local e um logo SVG/PNG. Ele é
deliberadamente offline: não possui egress, autenticação ou armazenamento de
credenciais. Assim, o recorte prova distribuição e interoperabilidade sem
antecipar a política de acesso do futuro importador Figma.

## Contratos

- `BrandPackageBuilder`: declara arquivos, papéis e media types e publica apenas
  um pacote integral;
- `brandrt-adapter-dtcg`: transforma DTCG + logo no pacote mínimo consumível;
- `brandrt package-validate`: permanece a autoridade canônica de conformidade;
- teste cruzado SDK → validator → intake: detecta divergência entre produtor e
  consumidor antes da distribuição.

## Segurança e integridade

- somente fontes regulares; symlinks são recusados na declaração e rechecados no
  momento da cópia;
- paths POSIX/NFC, extensões minúsculas, nomes reservados e colisões sem distinção
  de caixa seguem o mesmo contrato público do engine;
- máximo de 200 arquivos e 200 MiB por arquivo/conjunto;
- staging no mesmo volume, limpeza em falha e recusa de destino já existente;
- manifesto escrito depois dos bytes finais, com tamanho e SHA-256 recalculados;
- a interface de referência não possui entrada dedicada para token, URL ou
  credencial.

## Aceite

- a saída do adapter é aceita pelo validator e chega ao draft real do engine;
- traversal, role/MIME incompatível e colisão são recusados;
- uma falha de cópia não deixa destino nem staging residual;
- um destino existente nunca é alterado;
- o wheel contém typing marker e entry point, instala sem rede em venv limpa e
  executa sem dependências de terceiros;
- a fixture pública conserva o mesmo `packageSha256` entre SDK e engine.

## Próximo gate

O próximo recorte de importação é o adapter Figma. Sua prova útil exige uma fonte
real autorizada — arquivo/time, escopos e comportamento atual da API — para não
cristalizar um cliente apenas contra mocks. As demais frentes do M4 também pedem
decisões materiais: governança e distribuição da biblioteca pública, identidade
e isolamento da instância multi-tenant, ou ambiente PowerPoint Desktop para o
add-in. Nenhuma delas deve ser inferida pelo SDK.
