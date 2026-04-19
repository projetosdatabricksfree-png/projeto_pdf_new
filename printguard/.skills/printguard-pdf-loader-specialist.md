# Skill: PrintGuard PDF Loader Specialist

## Missão
Implementar, revisar ou corrigir o módulo de carregamento e inspeção estrutural de PDFs.

## Escopo
- QPDF
- parsing estrutural
- páginas
- boxes
- rotação
- output intent
- imagens
- metadados
- integridade mínima do documento

## Quando usar
Use esta skill para:
- `PdfLoader`
- `QpdfAdapter`
- `DocumentModel`
- regras que dependem de geometria ou estrutura básica do PDF

## Regras obrigatórias
1. Não criar parser PDF próprio do zero.
2. Isolar dependência de QPDF atrás de adapter.
3. Falhar de forma segura em PDFs inválidos.
4. Respeitar timeouts e limites operacionais.
5. Coletar warnings sem derrubar o processo sempre que possível.
6. Diferenciar erro estrutural fatal de warning tolerável.

## Checklist técnico
- [ ] leitura de page count
- [ ] leitura de MediaBox
- [ ] leitura de TrimBox
- [ ] leitura de BleedBox
- [ ] leitura de CropBox quando existir
- [ ] leitura de rotação
- [ ] leitura de output intent
- [ ] leitura de metadados principais
- [ ] enumeração básica de imagens
- [ ] enumeração básica de color spaces
- [ ] falha segura para PDF corrompido
- [ ] timeout de parse respeitado

## Alertas importantes
- PDFs reais são irregulares; não assuma boxes sempre presentes.
- Não assumir que TrimBox ou BleedBox existem.
- Não acoplar o resto do sistema diretamente à API crua do QPDF.
- Não alocar estruturas gigantes sem necessidade.

## Saída esperada
- modelo canônico consistente
- erros e warnings bem classificados
- pontos cegos documentados
