# Skill: QPDF PDF Structure

## Missão
Usar QPDF corretamente para leitura, inspeção estrutural e escrita segura de PDFs no PrintGuard.

## Quando usar
Use esta skill ao mexer em:
- `QpdfAdapter`
- `PdfLoader`
- `PdfWriter`
- boxes
- catálogo
- páginas
- output intent
- recursos do PDF
- escrita do corrigido

## Regras obrigatórias
1. QPDF é a base estrutural; não criar parser próprio.
2. Encapsular QPDF atrás de adapter.
3. Tratar PDFs inválidos com falha segura.
4. Nunca sobrescrever original.
5. Validar o PDF gerado após write.
6. Não espalhar detalhes internos de QPDF por todo o projeto.

## Checklist técnico
- [ ] leitura de page tree
- [ ] leitura de boxes
- [ ] leitura de metadata relevante
- [ ] leitura de output intent
- [ ] acesso a recursos básicos
- [ ] escrita segura em arquivo temporário
- [ ] validação do output gerado
- [ ] tratamento de erro estrutural

## Alertas
- PDF real é inconsistente; boxes podem faltar.
- Não assumir árvore de objetos “bonita”.
- Não tratar warning como fatal sem motivo.

## Saída esperada
Integração sólida com QPDF, útil para análise e fix.
