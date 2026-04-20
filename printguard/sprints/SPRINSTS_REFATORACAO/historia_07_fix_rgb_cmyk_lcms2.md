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

- [x] Adicionar `find_package(PkgConfig REQUIRED)` e `pkg_check_modules(LCMS2 REQUIRED lcms2)` no CMakeLists.txt raiz
- [x] Verificar que `liblcms2-dev` ja esta no Dockerfile (ja esta)
- [x] Linkar lcms2 na lib `printguard_fix`

### Perfil ICC

- [x] Criar diretorio `config/icc/`
- [x] Incluir perfil ICC CMYK livre (ex: `FOGRA39L.icc` ou `USWebCoatedSWOP.icc`)
- [ ] Alternativa: gerar perfil CMYK basico via lcms2 se nao houver perfil livre disponivel
  - Estado atual: nao foi necessario; foi incluido no projeto o perfil livre `GRACoL2013.icc`, copiado a partir de `GRACoL2013_CRPC6.icc`.
- [x] Documentar qual perfil foi escolhido e porque
  - Perfil escolhido: `GRACoL2013.icc`
  - Local: `config/icc/GRACoL2013.icc`
  - Motivo: mantem compatibilidade com os presets atuais do projeto (`output_intent_profile = GRACoL2013.icc`) e usa uma caracterizacao CMYK livre amplamente distribuida no sistema.

### ImageColorConvertFix (Novo)

- [x] Criar `src/fix/fixes/image_color_convert_fix.hpp/.cpp`
- [x] ID: `ImageColorConvertFix`
- [x] targets_finding_code: `PG_ERR_RGB_COLORSPACE`
- [ ] Logica:
  - [x] Iterar todas as paginas do PDF
  - [x] Para cada pagina, iterar `/Resources/XObject` procurando `/Subtype /Image`
  - [x] Para cada imagem: verificar `/ColorSpace`
  - [x] Se `/DeviceRGB` ou `/ICCBased` com 3 componentes:
    - [x] Decodificar stream de pixels via QPDF (`getStreamData`)
    - [x] Criar transformacao lcms2: `cmsCreateTransform(sRGB, TYPE_RGB_8, cmykProfile, TYPE_CMYK_8, INTENT_PERCEPTUAL, 0)`
    - [x] Transformar pixels RGB → CMYK
    - [x] Criar novo stream com dados CMYK
    - [x] Atualizar `/ColorSpace` para `/DeviceCMYK`
    - [x] Atualizar `/BitsPerComponent` se necessario
  - [x] Registrar FixRecord com contagem de imagens convertidas
- [x] Ler perfil ICC do `preset.color_policy.output_intent_profile` ou usar default

### Melhorar ConvertRgbToCmykFix existente

- [x] Substituir formula naive `rgb_to_cmyk()` por transformacao lcms2
- [x] Manter regex para detectar operadores `rg`/`RG` nos content streams
- [x] Usar mesmo perfil ICC que o ImageColorConvertFix
- [x] Preservar grays neutros como antes

### Registro

- [x] Registrar `ImageColorConvertFix` no factory `create_default_fix_engine()`
- [x] Manter `ConvertRgbToCmykFix` registrado (agora com lcms2)

### Testes

- [x] Teste: PDF com imagem RGB e convertido para CMYK
- [x] Teste: PDF com operadores RGB de stream e convertido
- [x] Teste: cores convertidas sao visuais aceitaveis (nao invertidas, nao degradadas)
- [x] Teste: PDF resultante e valido (QPDF check)
- [x] Teste: imagens grayscale nao sao tocadas
- [ ] Teste de performance: conversao de imagem grande nao excede 10s no VPS
  - Estado atual: teste automatizado com imagem RGB grande passou abaixo de 10s no ambiente atual; validacao dedicada no VPS alvo ainda nao foi executada.
- [x] Compilacao limpa

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

- [x] Imagens RGB em PDF sao convertidas para CMYK com qualidade visual aceitavel
- [x] Operadores RGB em content streams sao convertidos usando lcms2
- [x] PDF resultante valido
- [x] Compilacao limpa
- [ ] Performance aceitavel no VPS
  - Estado atual: cobertura automatizada criada e aprovada no ambiente atual; falta validacao especifica no VPS alvo.
