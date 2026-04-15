# RELATÓRIO DE CERTIFICAÇÃO GWG 5.0 (DRY-RUN)

**Arquivo:** `/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches/Categories/1-CMYK/Test pages/Ghent_PDF-Output-Test-V50_CMYK_X4.pdf`
**Duração:** 0.57s
**Status Final:** APROVADO/AVISO

## JSON BRUTO DE SAÍDA
```json
[
  {
    "page": 3,
    "checks": [
      {
        "code": "W_IMAGE_16BIT",
        "label": "Imagens 16-bit",
        "status": "AVISO",
        "found_value": "16-bit",
        "expected_value": "8-bit",
        "title": "Aviso Técnico",
        "message": "Identificado problema técnico: W_IMAGE_16BIT",
        "action": "Revise o arquivo original ou as configurações de exportação."
      },
      {
        "code": "E_JPEG2000_FORBIDDEN",
        "label": "Compressão JPEG2000",
        "status": "ERRO",
        "found_value": "/JPXDecode",
        "expected_value": "/DCTDecode (JPEG) ou /FlateDecode",
        "title": "Aviso Técnico",
        "message": "Identificado problema técnico: E_JPEG2000_FORBIDDEN",
        "action": "Revise o arquivo original ou as configurações de exportação."
      },
      {
        "code": "W_JBIG2_LEGACY",
        "label": "Compressão JBIG2",
        "status": "AVISO",
        "found_value": "/JBIG2Decode",
        "expected_value": "/CCITTFaxDecode",
        "title": "Aviso Técnico",
        "message": "Identificado problema técnico: W_JBIG2_LEGACY",
        "action": "Revise o arquivo original ou as configurações de exportação."
      },
      {
        "code": "W_JBIG2_LEGACY",
        "label": "Compressão JBIG2",
        "status": "AVISO",
        "found_value": "/JBIG2Decode",
        "expected_value": "/CCITTFaxDecode",
        "title": "Aviso Técnico",
        "message": "Identificado problema técnico: W_JBIG2_LEGACY",
        "action": "Revise o arquivo original ou as configurações de exportação."
      }
    ]
  },
  "status",
  "codigo",
  "found_value"
]
```
