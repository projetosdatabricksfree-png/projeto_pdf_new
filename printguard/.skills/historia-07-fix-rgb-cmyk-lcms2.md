# Skill: Historia 07 — Fix RGB→CMYK Completo com lcms2

## Missao

Implementar conversao RGB→CMYK completa usando LittleCMS2, cobrindo imagens XObject e operadores de content stream.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_07_fix_rgb_cmyk_lcms2.md`

## Quando usar

Use esta skill para:
- integrar lcms2 no build
- implementar ImageColorConvertFix
- melhorar ConvertRgbToCmykFix com lcms2
- incluir perfil ICC no projeto

## Regras obrigatorias

1. Usar lcms2 para todas as conversoes de cor — NAO usar formula naive.
2. Perfil ICC deve ser carregado do disco, nao hardcoded.
3. Imagens grayscale NAO devem ser tocadas.
4. Grays neutros em operadores devem ser preservados.
5. PDF resultante DEVE ser validado via QPDF check.
6. Performance: conversao de imagem grande nao deve exceder 10s no VPS 2vCPU.

## Integracao lcms2

```cmake
find_package(PkgConfig REQUIRED)
pkg_check_modules(LCMS2 REQUIRED lcms2)
target_link_libraries(printguard_fix PRIVATE ${LCMS2_LIBRARIES})
target_include_directories(printguard_fix PRIVATE ${LCMS2_INCLUDE_DIRS})
```

## Fluxo do ImageColorConvertFix

1. Iterar paginas
2. Para cada pagina, iterar /Resources/XObject
3. Para cada imagem com /ColorSpace = /DeviceRGB ou /ICCBased (3 comp):
   a. Decodificar stream via QPDF getStreamData()
   b. Criar transform lcms2: sRGB → CMYK (perfil do preset)
   c. Transformar pixels
   d. Re-encodar stream
   e. Atualizar /ColorSpace para /DeviceCMYK
4. Registrar FixRecord

## Checklist de saida

- [ ] lcms2 integrado no CMake
- [ ] Perfil ICC incluido em config/icc/
- [ ] ImageColorConvertFix implementado
- [ ] ConvertRgbToCmykFix melhorado
- [ ] Testes com PDFs RGB
- [ ] Compilacao limpa
