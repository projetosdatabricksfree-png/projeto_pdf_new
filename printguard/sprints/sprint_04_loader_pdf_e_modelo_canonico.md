> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 04 — Loader PDF e Modelo Canônico

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Implementar a capacidade de ler e interpretar a estrutura física de um arquivo PDF, transformando um arquivo binário em um modelo de objetos C++ (Modelo Canônico) que as regras possam analisar.

## Escopo da Sprint
- Integração profunda com biblioteca `QPDF`.
- Implementação de `DocumentLoader`.
- Extração de Geometria de Página (MediaBox, TrimBox, BleedBox, ArtBox, CropBox).
- Extração de Metadados (Producer, Creator, Versão PDF).
- Identificação de Espaços de Cor e Perfis ICC presentes (via links de estrutura).
- Contagem de páginas e checagem de integridade estrutural.

## Fora do escopo da Sprint
- Rasterização (renderização) de páginas.
- Análise de pixels de imagens raster.
- Alteração (fix) do conteúdo do PDF.

## Dependências
- Biblioteca `libqpdf-dev` instalada na VPS/Ambiente.
- Sprint 03 concluída para mapear dados no Modelo de Domínio.

## Entregáveis
- [x] Classe `PdfLoader` funcional.
- [x] Estrutura `DocumentModel` populada após o carregamento.
- [x] Utilitário CLI `printguard-inspect` para testes locais de carregamento.

## Checklist Técnico

### Common
- [x] Criar wrappers de erro para exceções da QPDF (via catch no PdfLoader).

### PDF
- [x] Inicializar `QPDF` handle de forma segura (RAII).
- [x] Implementar leitura de `MediaBox` e `TrimBox` por página (respeitando herança do PDF).
- [x] Implementar detecção de rotação nativa (`/Rotate`).
- [x] Extrair dicionário de `/Info`.
- [ ] Listar fontes presentes no documento (nomes e tipos).
- [ ] Listar imagens e suas proporções básicas (sem extrair pixels ainda).

### Testes
- [ ] Criar suíte de testes unitários com PDFs válidos e corrompidos.
- [ ] Testar PDFs com múltiplas páginas e tamanhos variados por página.

### Operação
- [ ] Validar consumo de memória durante o parse de um PDF de 80MB (limite do MVP).

## Arquivos e módulos impactados
- `src/pdf/`
- `include/printguard/pdf/`
- `tests/data/pdfs/` (adicionar arquivos de teste)

## Critérios de Aceite
- [x] `PdfLoader` extrai corretamente o tamanho da página em pontos (72 DPI).
- [x] O sistema identifica se um PDF é linearizado.
- [ ] O sistema retorna erro explícito para PDFs protegidos por senha.
- [ ] Consumo de memória para carregar PDF de 10 páginas não excede 500MB (limitado a metadados).

## Riscos
- PDFs com estrutura de herança complexa (Page Tree) falhando na leitura de boxes.
- Desempenho lento em arquivos com milhares de objetos internos.

## Mitigações
- Usar acesso lazy da QPDF sempre que possível.
- Limitar profundidade de busca recursiva na árvore de páginas.

## Observações de Implementação
- Não carregar o conteúdo binário dos streams de imagem nesta fase, apenas metadados do dicionário.
- Toda geometria deve ser normalizada em milímetros para facilitar a vida do motor de regras.

## Definição de pronto
- [x] código implementado
- [x] build funcionando
- [x] testes unitários de normalização concluídos
- [ ] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `70%`  
**Situação:** `Em andamento`
