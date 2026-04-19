# Skill: PrintGuard Storage & Artifacts

## Missão
Implementar e governar storage local e artefatos do PrintGuard com segurança, organização e retenção.

## Escopo
- original
- corrected
- previews
- reports
- paths
- cleanup
- checksums

## Quando usar
Use esta skill para:
- `BlobStore`
- `LocalBlobStore`
- `ArtifactPaths`
- gestão de retenção
- persistência de artefatos

## Regras obrigatórias
1. Original sempre preservado.
2. Paths determinísticos e organizados por tenant/job.
3. Escrita atômica sempre que possível.
4. Checksums registrados.
5. Limpeza automática de artefatos antigos.
6. Não permitir path traversal.

## Checklist técnico
- [ ] original salvo
- [ ] corrected salvo separadamente
- [ ] previews salvos separadamente
- [ ] reports salvos separadamente
- [ ] paths por tenant/job definidos
- [ ] checksum calculado
- [ ] artifacts persistidos no banco
- [ ] cleanup policy implementada
- [ ] acesso seguro aos arquivos
- [ ] testes de storage criados

## Layout sugerido
- originals/
- corrected/
- previews/
- reports/

## Saída esperada
- storage previsível
- auditável
- seguro para operação em VPS única
