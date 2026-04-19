# Historia 07 — Fix: RGB→CMYK Completo com lcms2

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Implementar conversao RGB→CMYK completa usando LittleCMS2 (lcms2), cobrindo tanto operadores de content stream quanto imagens XObject. Este e o fix de maior valor do MVP comercial.

## Escopo da Historia

- Integrar lcms2 no build
- Criar fix de conversao de imagens RGB→CMYK
- Melhorar fix existente de operadores RGB com lcms2
- Incluir perfil ICC CMYK no projeto

## Fora do Escopo

- TAC reduction (Historia 08)
- Output Intent attachment (Historia 08)
- Conversao de spot colors (Historia 09)

## Dependencias

- **Historia 04** (arquitetura IFix)
- **Historia 05** (regras de cor para gerar findings que disparam este fix)

## Skill correspondente

`historia-07-fix-rgb-cmyk-lcms2.md`

## Checklist Tecnico

### Integrar lcms2 no CMake

- [ ] Adicionar `find_package(PkgConfig REQUIRED)` e `pkg_check_modules(LCMS2 REQUIRED lcms2)` no CMakeLists.txt raiz
- [ ] Verificar que `liblcms2-dev` ja esta no Dockerfile (ja esta)
- [ ] Linkar lcms2 na lib `printguard_fix`

### Perfil ICC

- [ ] Criar diretorio `config/icc/`
- [ ] Incluir perfil ICC CMYK livre (ex: `FOGRA39L.icc` ou `USWebCoatedSWOP.icc`)
- [ ] Alternativa: gerar perfil CMYK basico via lcms2 se nao houver perfil livre disponivel
- [ ] Documentar qual perfil foi escolhido e porque

### ImageColorConvertFix (Novo)

- [ ] Criar `src/fix/fixes/image_color_convert_fix.hpp/.cpp`
- [ ] ID: `ImageColorConvertFix`
- [ ] targets_finding_code: `PG_ERR_RGB_COLORSPACE`
- [ ] Logica:
  - [ ] Iterar todas as paginas do PDF
  - [ ] Para cada pagina, iterar `/Resources/XObject` procurando `/Subtype /Image`
  - [ ] Para cada imagem: verificar `/ColorSpace`
  - [ ] Se `/DeviceRGB` ou `/ICCBased` com 3 componentes:
    - [ ] Decodificar stream de pixels via QPDF (`getStreamData`)
    - [ ] Criar transformacao lcms2: `cmsCreateTransform(sRGB, TYPE_RGB_8, cmykProfile, TYPE_CMYK_8, INTENT_PERCEPTUAL, 0)`
    - [ ] Transformar pixels RGB → CMYK
    - [ ] Criar novo stream com dados CMYK
    - [ ] Atualizar `/ColorSpace` para `/DeviceCMYK`
    - [ ] Atualizar `/BitsPerComponent` se necessario
  - [ ] Registrar FixRecord com contagem de imagens convertidas
- [ ] Ler perfil ICC do `preset.color_policy.output_intent_profile` ou usar default

### Melhorar ConvertRgbToCmykFix existente

- [ ] Substituir formula naive `rgb_to_cmyk()` por transformacao lcms2
- [ ] Manter regex para detectar operadores `rg`/`RG` nos content streams
- [ ] Usar mesmo perfil ICC que o ImageColorConvertFix
- [ ] Preservar grays neutros como antes

### Registro

- [ ] Registrar `ImageColorConvertFix` no factory `create_default_fix_engine()`
- [ ] Manter `ConvertRgbToCmykFix` registrado (agora com lcms2)

### Testes

- [ ] Teste: PDF com imagem RGB e convertido para CMYK
- [ ] Teste: PDF com operadores RGB de stream e convertido
- [ ] Teste: cores convertidas sao visuais aceitaveis (nao invertidas, nao degradadas)
- [ ] Teste: PDF resultante e valido (QPDF check)
- [ ] Teste: imagens grayscale nao sao tocadas
- [ ] Teste de performance: conversao de imagem grande nao excede 10s no VPS
- [ ] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `CMakeLists.txt` | Adicionar lcms2 |
| `src/fix/CMakeLists.txt` | Linkar lcms2 |
| `src/fix/fixes/image_color_convert_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/convert_rgb_to_cmyk_fix.cpp` | Melhorar com lcms2 |
| `config/icc/` | Perfil ICC CMYK |
| `Dockerfile` | Verificar lcms2-dev (ja presente) |

## Riscos

- **Decodificacao de imagem**: streams podem usar filtros complexos (FlateDecod, DCTDecode, etc.). QPDF lida com a maioria, mas testar com PDFs reais.
- **Performance**: imagens grandes (300 DPI em A1) podem ser pesadas. Considerar processamento por chunks.
- **Perfil ICC**: usar perfil livre e documentar limitacoes vs perfil proprietario.

## Criterios de Aceite

- [ ] Imagens RGB em PDF sao convertidas para CMYK com qualidade visual aceitavel
- [ ] Operadores RGB em content streams sao convertidos usando lcms2
- [ ] PDF resultante valido
- [ ] Compilacao limpa
- [ ] Performance aceitavel no VPS
