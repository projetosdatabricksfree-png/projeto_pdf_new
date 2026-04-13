"""
Hardcoded message table for the Validador agent.

100% deterministic. Zero AI. Zero RAG.
Each error/warning code maps to localized messages in pt-BR, en-US, es-ES.

RULE 2 (Anti-RAG): NEVER use LLM to generate these messages.
"""
from __future__ import annotations

MESSAGES: dict[str, dict[str, dict[str, str]]] = {
    "pt-BR": {
        # ─── Papelaria Plana ──────────────────────────────────────────
        "E001_DIMENSION_MISMATCH": {
            "titulo": "❌ Dimensões Incorretas",
            "descricao": "O arquivo não corresponde a nenhum padrão dimensional reconhecido.",
            "acao": "Verifique o tamanho do documento no software de design e ajuste para o formato correto.",
        },
        "E002_MISSING_BLEED": {
            "titulo": "❌ Sangria Ausente",
            "descricao": "O arquivo não possui sangria (bleed). Isso causará filetes brancos nas bordas após o corte.",
            "acao": "Configure uma sangria de 2mm a 3mm em todos os lados do documento.",
        },
        "E003_INSUFFICIENT_BLEED": {
            "titulo": "⚠️ Sangria Insuficiente",
            "descricao": "A sangria configurada é menor que 2mm.",
            "acao": "Aumente a sangria para no mínimo 2mm.",
        },
        "E004_INSUFFICIENT_SAFETY_MARGIN": {
            "titulo": "❌ Margem de Segurança Insuficiente",
            "descricao": "Elementos importantes estão muito próximos da borda de corte.",
            "acao": "Mantenha textos e logos a pelo menos 3mm da borda interna.",
        },
        "E005_LOW_RESOLUTION": {
            "titulo": "❌ Resolução Insuficiente",
            "descricao": "A resolução das imagens está abaixo de 300 DPI. O resultado final ficará borrado.",
            "acao": "Substitua as imagens por versões de alta resolução (mínimo 300 DPI).",
        },
        "E006_RGB_COLORSPACE": {
            "titulo": "❌ Cores em RGB",
            "descricao": "O arquivo contém cores no modelo RGB. Impressão offset usa CMYK.",
            "acao": "Converta todas as cores para CMYK ou Pantone antes de enviar.",
        },
        "E007_EXCESSIVE_INK_COVERAGE": {
            "titulo": "❌ Excesso de Tinta",
            "descricao": "A cobertura total de tinta excede o limite do substrato. Isso causará repasse e manchas.",
            "acao": "Reduza a densidade das cores. Verifique o perfil de cor utilizado.",
        },
        "E008_NON_EMBEDDED_FONTS": {
            "titulo": "❌ Fontes Não Incorporadas",
            "descricao": "Existem fontes que não estão incorporadas ao arquivo.",
            "acao": "Incorpore todas as fontes ao exportar o PDF, ou converta-as em curvas.",
        },
        "E009_NFC_ZONE_VIOLATION": {
            "titulo": "❌ Área de Chip Invadida",
            "descricao": "Elementos gráficos estão sobre a área do chip NFC/RFID. Isso danificará o chip.",
            "acao": "Mova todos os elementos para fora da zona central de 30mm x 20mm.",
        },
        "E010_HAIRLINE_DETECTED": {
            "titulo": "❌ Linhas Muito Finas",
            "descricao": "Foram encontradas linhas com espessura inferior a 0,25pt. Elas serão invisíveis após impressão.",
            "acao": "Aumente a espessura de todas as linhas para no mínimo 0,25pt.",
        },
        # ─── Editoriais ──────────────────────────────────────────────
        "E001_SPINE_WIDTH_MISMATCH": {
            "titulo": "❌ Lombada Incorreta",
            "descricao": "A largura da lombada no arquivo não corresponde ao cálculo baseado na quantidade de páginas e gramatura.",
            "acao": "Recalcule a lombada: (Total de Páginas ÷ 2) × Espessura do Papel em mícrons.",
        },
        "E002_GUTTER_INVASION": {
            "titulo": "❌ Invasão da Área de Cola",
            "descricao": "Conteúdo está dentro dos 10mm da lombada (área de colagem). Será destruído pelo processo de encadernação.",
            "acao": "Recue todos os elementos a pelo menos 10mm da margem interna (lombada).",
        },
        "E003_RICH_BLACK_IN_TEXT": {
            "titulo": "❌ Preto Rico em Texto",
            "descricao": "Textos contêm \"Rich Black\" (combinação de CMYK). Isso causa borramento nas letras.",
            "acao": "Use apenas 100% K (Preto puro) em textos e elementos finos.",
        },
        "E004_NON_EMBEDDED_FONTS": {
            "titulo": "❌ Fontes Não Incorporadas",
            "descricao": "Fontes não estão incorporadas ao arquivo editorial.",
            "acao": "Incorpore todas as fontes ao exportar o PDF.",
        },
        "E005_ACTIVE_TRANSPARENCY": {
            "titulo": "⚠️ Transparência Ativa",
            "descricao": "O arquivo contém transparências ativas incompatíveis com PDF/X-1a.",
            "acao": "Achate as transparências ao exportar ou use PDF/X-4.",
        },
        "E007_COVER_OVERLAP_MISSING": {
            "titulo": "⚠️ Sobreposição de Capa Insuficiente",
            "descricao": "A capa não possui sobreposição suficiente (mín. 7mm) sobre o bloco de páginas.",
            "acao": "Ajuste a largura da capa para incluir 7mm de sobreposição em cada lado.",
        },
        # ─── Dobraduras ──────────────────────────────────────────────
        "E001_NO_FOLD_MARKS": {
            "titulo": "⚠️ Marcas de Dobra Ausentes",
            "descricao": "Arquivo multipágina detectado sem marcas de dobra/vinco.",
            "acao": "Adicione marcas de vinco no arquivo ou indique as posições de dobra.",
        },
        "E002_CREEP_COMPENSATION_MISSING": {
            "titulo": "❌ Compensação de Vinco Ausente",
            "descricao": "Os painéis internos do folder têm a mesma largura dos externos. Ao dobrar, o conteúdo vai extrapolar as bordas.",
            "acao": "Reduza o painel central em 2mm a 3mm para compensar a dobra.",
        },
        "E003_CONTENT_CROSSING_FOLD": {
            "titulo": "❌ Elemento Atravessa Dobra",
            "descricao": "Um elemento gráfico atravessa a linha de vinco, o que causará corte visual indesejado.",
            "acao": "Nenhum elemento crítico deve cruzar as linhas de dobra.",
        },
        "E004_MECHANICAL_SCORE_REQUIRED": {
            "titulo": "❌ Vinco Mecânico Obrigatório",
            "descricao": "O papel escolhido (>150g) exige vinco mecânico antes da dobra. Sem ele, o revestimento vai rachar.",
            "acao": "Solicite o vinco mecânico prévio ou escolha um papel mais leve (<150g).",
        },
        "E005_UV_VARNISH_ON_REVERSE": {
            "titulo": "❌ Verniz UV no Verso",
            "descricao": "Verniz UV foi detectado no reverso do postal. Isso impede a escrita e a colagem.",
            "acao": "Remova o verniz UV do reverso. Aplique apenas no anverso.",
        },
        "E006_GRAIN_DIRECTION_MISMATCH": {
            "titulo": "❌ Direção da Fibra Incorreta",
            "descricao": "A dobra está configurada contra a direção da fibra do papel. Isso causará rachaduras no revestimento.",
            "acao": "Ajuste a orientação da dobra para ser paralela à fibra do papel.",
        },
        "E007_RGB_COLORSPACE": {
            "titulo": "❌ Cores em RGB",
            "descricao": "O arquivo contém cores no modelo RGB.",
            "acao": "Converta todas as cores para CMYK ou Pantone.",
        },
        "E008_LOW_RESOLUTION": {
            "titulo": "❌ Resolução Insuficiente",
            "descricao": "A resolução está abaixo de 300 DPI.",
            "acao": "Substitua as imagens por versões de alta resolução (mín. 300 DPI).",
        },
        "E009_MISSING_BLEED": {
            "titulo": "❌ Sangria Ausente",
            "descricao": "O arquivo não possui sangria nos painéis.",
            "acao": "Configure sangria de 2mm a 3mm em todos os painéis.",
        },
        "E010_NON_EMBEDDED_FONTS": {
            "titulo": "❌ Fontes Não Incorporadas",
            "descricao": "Fontes não estão incorporadas ao arquivo.",
            "acao": "Incorpore todas as fontes ao exportar o PDF.",
        },
        # ─── Cortes Especiais ────────────────────────────────────────
        "E001_NO_DIE_CUT_LAYER": {
            "titulo": "❌ Camada de Faca Ausente",
            "descricao": "Não foi encontrada uma camada de corte (faca) no arquivo.",
            "acao": "Crie uma camada nomeada \"Faca\" ou \"CutContour\" com a linha de corte em vetor.",
        },
        "E002_FACA_OVERPRINT_MISSING": {
            "titulo": "❌ Overprint da Faca Desativado",
            "descricao": "A camada de faca não está com Overprint ativado. O RIP irá interpretar como uma cor, gerando fios brancos.",
            "acao": "Selecione a camada de faca e ative o atributo \"Overprint\" nas propriedades de cor.",
        },
        "E003_OPEN_DIE_CUT_PATH": {
            "titulo": "❌ Linha de Corte Aberta",
            "descricao": "A linha de faca não é um caminho fechado. A máquina de corte não conseguirá executar.",
            "acao": "Feche todos os caminhos vetoriais da faca de corte.",
        },
        "E004_DIE_CUT_SELF_INTERSECTION": {
            "titulo": "❌ Auto-Interseção na Faca",
            "descricao": "A linha de faca possui auto-interseção. A máquina de corte pode travar.",
            "acao": "Corrija a geometria da faca para eliminar cruzamentos.",
        },
        "E005_FACA_TOO_THIN": {
            "titulo": "⚠️ Faca Muito Fina",
            "descricao": "A espessura da linha de faca é inferior a 0,1pt.",
            "acao": "Aumente a espessura da faca para entre 0,1pt e 0,25pt.",
        },
        "E006_INSUFFICIENT_BLEED_OUTSIDE_DIE": {
            "titulo": "❌ Sangria Insuficiente além da Faca",
            "descricao": "A arte não sangra 2mm além da linha de faca.",
            "acao": "Estenda a arte 2mm para fora da linha de corte.",
        },
        "E007_INSUFFICIENT_LABEL_SPACING": {
            "titulo": "❌ Espaçamento Insuficiente entre Rótulos",
            "descricao": "Os rótulos estão a menos de 3mm de distância entre si. Não será possível descascar/separar.",
            "acao": "Aumente o espaçamento entre rótulos para no mínimo 3mm.",
        },
        "E008_INSUFFICIENT_TRAPPING": {
            "titulo": "⚠️ Trapping Insuficiente",
            "descricao": "A sobreposição entre cores adjacentes é menor que 0,05mm.",
            "acao": "Configure trapping de 0,05mm a 0,1mm entre cores adjacentes.",
        },
        "E009_BRAND_COLOR_DEVIATION": {
            "titulo": "⚠️ Desvio de Cor de Marca",
            "descricao": "A variação colorimétrica (ΔE) excede 2.0 em relação ao padrão de marca.",
            "acao": "Ajuste os valores CMYK para que o ΔE fique abaixo de 2.0.",
        },
        "E010_WRONG_PDF_STANDARD": {
            "titulo": "⚠️ Padrão PDF Incorreto",
            "descricao": "O arquivo não está em conformidade com PDF/X-4.",
            "acao": "Re-exporte o arquivo no padrão PDF/X-4.",
        },
        "E011_LOW_RESOLUTION": {
            "titulo": "❌ Resolução Insuficiente",
            "descricao": "A resolução está abaixo de 300 DPI.",
            "acao": "Substitua as imagens por versões de alta resolução.",
        },
        "E012_RGB_COLORSPACE": {
            "titulo": "❌ Cores em RGB",
            "descricao": "O arquivo contém cores no modelo RGB.",
            "acao": "Converta todas as cores para CMYK.",
        },
        "E013_NON_EMBEDDED_FONTS": {
            "titulo": "❌ Fontes Não Incorporadas",
            "descricao": "Fontes não estão incorporadas ao arquivo.",
            "acao": "Incorpore todas as fontes ao exportar o PDF.",
        },
        # ─── Projetos CAD ────────────────────────────────────────────
        "E001_SCALE_DEVIATION": {
            "titulo": "❌ Desvio de Escala",
            "descricao": "O arquivo apresenta desvio de escala superior a 0,1%. Isso invalida a precisão do projeto técnico.",
            "acao": "Reconfigure o documento para escala 1:1 e re-exporte.",
        },
        "E002_HAIRLINE_DETECTED": {
            "titulo": "❌ Linhas de CAD Invisíveis",
            "descricao": "Foram encontradas linhas com espessura inferior a 0,25pt. Serão invisíveis na plotagem.",
            "acao": "Aumente todas as linhas para no mínimo 0,25pt.",
        },
        "E003_BINDING_MARGIN_INSUFFICIENT": {
            "titulo": "❌ Margem de Encadernação Insuficiente",
            "descricao": "A margem lateral é menor que 15mm. A perfuração para Wire-O irá cortar elementos críticos.",
            "acao": "Aumente a margem lateral para no mínimo 15mm.",
        },
        "E004_RGB_COLORSPACE": {
            "titulo": "❌ Cores em RGB",
            "descricao": "O arquivo contém cores RGB. Plotagem técnica requer Grayscale ou CMYK.",
            "acao": "Converta para Grayscale ou CMYK.",
        },
        "E005_WRONG_PDF_STANDARD": {
            "titulo": "⚠️ Padrão PDF Incorreto",
            "descricao": "O arquivo não está em conformidade com PDF/X-1a.",
            "acao": "Re-exporte no padrão PDF/X-1a.",
        },
        "E006_RASTER_LOW_RESOLUTION": {
            "titulo": "⚠️ Imagem Raster Baixa Resolução",
            "descricao": "Imagem raster embutida possui resolução inferior a 300 DPI.",
            "acao": "Substitua a imagem por versão de alta resolução.",
        },
        "E007_PHYSICAL_DILATION_EXCEEDED": {
            "titulo": "❌ Dilatação Física Excedida",
            "descricao": "A dilatação do arquivo excede 0,1%, comprometendo a escala de engenharia.",
            "acao": "Recalibre o arquivo e re-exporte em escala 1:1.",
        },
        # ─── Avisos Gerais ───────────────────────────────────────────
        "W001_EXCESSIVE_BLEED": {
            "titulo": "⚠️ Sangria Excessiva",
            "descricao": "A sangria configurada é maior que 3mm. Não é um erro, mas gera desperdício de material.",
            "acao": "Reduza a sangria para 3mm se possível.",
        },
        "W001_CONTENT_NEAR_FOLD": {
            "titulo": "⚠️ Conteúdo Próximo ao Vinco",
            "descricao": "Elementos estão a menos de 5mm de uma linha de dobra. Podem ser cortados visualmente.",
            "acao": "Afaste elementos a pelo menos 5mm das linhas de dobra.",
        },
        "W001_PAGE_COUNT_NOT_MULTIPLE_OF_4": {
            "titulo": "⚠️ Páginas Não Múltiplo de 4",
            "descricao": "A contagem de páginas não é múltipla de 4. Cadernos offset exigem múltiplos de 4.",
            "acao": "Ajuste a paginação para múltiplo de 4 ou considere impressão digital.",
        },
        "W001_NON_STANDARD_FORMAT": {
            "titulo": "⚠️ Formato Não Padronizado",
            "descricao": "O formato do documento não corresponde a nenhuma norma ISO padrão.",
            "acao": "Verifique se o formato é intencional.",
        },
        "W001_FACA_TOO_THICK": {
            "titulo": "⚠️ Faca Muito Grossa",
            "descricao": "A espessura da linha de faca excede 0,25pt.",
            "acao": "Reduza para entre 0,1pt e 0,25pt.",
        },
        "W002_UV_VARNISH_MISSING_FRONT": {
            "titulo": "⚠️ Verniz UV Ausente no Anverso",
            "descricao": "Recomenda-se aplicar verniz UV no anverso de postais para proteção e acabamento.",
            "acao": "Considere adicionar verniz UV no anverso.",
        },
        "W002_TIGHT_SAFETY_MARGIN": {
            "titulo": "⚠️ Margem de Segurança Apertada",
            "descricao": "A margem de segurança está entre 3mm e 3,5mm. Risco em guilhotinas com variação.",
            "acao": "Se possível, aumente para 4mm ou mais.",
        },
        "W002_ASYMMETRIC_MIRROR_PAGES": {
            "titulo": "⚠️ Páginas Espelhadas Assimétricas",
            "descricao": "As margens internas e externas não estão espelhadas corretamente.",
            "acao": "Verifique a configuração de margens espelhadas no software de layout.",
        },
        "W002_EXCESSIVE_TRAPPING": {
            "titulo": "⚠️ Trapping Excessivo",
            "descricao": "A sobreposição entre cores excede 0,1mm.",
            "acao": "Reduza o trapping para no máximo 0,1mm.",
        },
        "W002_LEGEND_AREA_EMPTY": {
            "titulo": "⚠️ Área de Legenda Vazia",
            "descricao": "A área de legenda/carimbo está vazia conforme NBR 13142.",
            "acao": "Adicione o carimbo na área designada.",
        },
        "W003_BORDERLINE_RESOLUTION": {
            "titulo": "⚠️ Resolução Borderline",
            "descricao": "A resolução está exatamente em 300 DPI — aceitável mas não ideal para impressão premium.",
            "acao": "Se possível forneça imagens com 350 DPI ou mais.",
        },
        "W003_CREEP_NOT_ADJUSTED": {
            "titulo": "⚠️ Compensação de Escada Ausente",
            "descricao": "Caderno com muitas páginas sem compensação de creep (efeito escada).",
            "acao": "Aplique compensação de creep de 3mm nos cadernos.",
        },
        "W004_THIN_LINE": {
            "titulo": "⚠️ Linha Fina Detectada",
            "descricao": "Linha entre 0,25pt e 0,5pt detectada. Pode sumir em impressões finas.",
            "acao": "Considere aumentar para no mínimo 0,5pt.",
        },
        # ─── GWG Output Suite 5.0 — OPM / Overprint ─────────────────
        "E_OPM_WRONG": {
            "titulo": "❌ OPM Incorreto (Modo de Overprint)",
            "descricao": "ExtGState com Overprint ativo possui OPM=0. Com OPM=0, a fidelidade colorimétrica do overprint não é garantida — as cores spot podem ser substituídas incorretamente pelo RIP.",
            "acao": "Configure OPM=1 em todos os ExtGState que tenham overprint ativo (/OP true).",
        },
        "E_WHITE_OVERPRINT": {
            "titulo": "❌ White Overprint Detectado",
            "descricao": "Objeto com cor CMYK (0,0,0,0) tem overprint ativo. Este objeto é invisível mas sobrepõe as tintas abaixo, causando 'buracos' indetectáveis no ecrã que aparecem na impressão.",
            "acao": "Desative o overprint em objetos com cor CMYK (0,0,0,0) ou remova os objetos brancos invisíveis.",
        },
        "W_GRAY_OVERPRINT": {
            "titulo": "⚠️ Gray Overprint Detectado",
            "descricao": "Objeto K-only (escala de cinzas) com overprint ativo. Com OPM=0, as tintas CMY subjacentes podem aparecer através do objeto.",
            "acao": "Verifique se o overprint é intencional. Se não, desative. Se sim, confirme OPM=1.",
        },
        # ─── GWG Output Suite 5.0 — Compressão de Imagem ────────────
        "W_JPEG2000": {
            "titulo": "⚠️ Compressão JPEG 2000 Detectada",
            "descricao": "O arquivo contém imagens comprimidas com JPXDecode (JPEG 2000). Muitos RIPs de produção têm suporte limitado ou defeituoso para este formato.",
            "acao": "Re-exporte as imagens em JPEG (DCTDecode) ou sem compressão (FlateDecode). Recomendação GWG: evitar JPX em PDFs de impressão.",
        },
        "W_JBIG2": {
            "titulo": "⚠️ Compressão JBIG2 Detectada",
            "descricao": "O arquivo contém imagens comprimidas com JBIG2Decode. Este formato tem cobertura de patentes e suporte inconsistente em RIPs.",
            "acao": "Re-exporte as imagens bitmaps em FlateDecode (ZIP) ou CCITT Group 4.",
        },
        "W_16BIT_IMAGE": {
            "titulo": "⚠️ Imagem de 16 bits Detectada",
            "descricao": "O arquivo contém imagens com BitsPerComponent=16. A maioria dos RIPs de produção processa apenas 8 bits por canal.",
            "acao": "Reduza as imagens para 8 bits por canal antes de exportar o PDF.",
        },
        # ─── GWG Output Suite 5.0 — Transparência ───────────────────
        "W_BLEND_MODES": {
            "titulo": "⚠️ Modos de Fusão Não-Standard",
            "descricao": "O arquivo contém modos de fusão (Blend Modes) que não fazem parte do conjunto standard de 16 modos do PDF. Estes modos não são interpretados de forma consistente por todos os RIPs.",
            "acao": "Substitua os modos de fusão não-standard por modos standard (Normal, Multiply, Screen, Overlay, etc.).",
        },
        "W_SOFT_MASK": {
            "titulo": "⚠️ Soft Mask (Canal Alpha) Detectado",
            "descricao": "O arquivo contém Soft Masks (SMask), que criam transparência por canal alfa. Fluxos PDF/X-1a não suportam SMask.",
            "acao": "Achate as transparências antes de exportar para PDF/X-1a. Para PDF/X-4, verifique se o RIP suporta SMask.",
        },
        "W_OPACITY": {
            "titulo": "⚠️ Objetos com Opacidade Parcial",
            "descricao": "O arquivo contém objetos com opacidade inferior a 100% (ca ou CA < 1.0 no ExtGState).",
            "acao": "Achate as transparências ou confirme que o fluxo de impressão suporta PDF/X-4 com transparência.",
        },
        # ─── GWG Output Suite 5.0 — Perfis ICC ──────────────────────
        "E_NO_OUTPUT_INTENT": {
            "titulo": "❌ OutputIntent Ausente",
            "descricao": "O arquivo não possui OutputIntent no catálogo PDF. Para conformidade com PDF/X-4 e GWG, um OutputIntent com perfil ICC é obrigatório.",
            "acao": "Re-exporte o PDF com um OutputIntent adequado (ex: ISO Coated v2 300% / FOGRA39).",
        },
        "W_ICC_V4": {
            "titulo": "⚠️ Perfil ICC Versão 4",
            "descricao": "O arquivo contém perfis ICC versão 4 (v4). RIPs antigos e alguns sistemas de gestão de cor podem rejeitar ou interpretar incorretamente perfis ICC v4.",
            "acao": "Se o fluxo de impressão tiver RIPs antigos, substitua por perfis ICC versão 2 (ex: FOGRA39 v2).",
        },
        # ─── GWG Output Suite 5.0 — DeviceN / Cores Spot ────────────
        "E_DEVICEN_CONV": {
            "titulo": "❌ Conversão de DeviceN para RGB Detectada",
            "descricao": "Um espaço de cor /Separation ou /DeviceN tem como AlternateSpace um espaço RGB (DeviceRGB/CalRGB). Isto significa que as cores spot foram convertidas para RGB durante a exportação — fidelidade de impressão perdida.",
            "acao": "Re-exporte o arquivo garantindo que os espaços DeviceN/Separation mantêm AlternateSpace CMYK ou preservam as cores spot.",
        },
        "W_DEVICEN_CMYK_ALT": {
            "titulo": "⚠️ DeviceN com AlternateSpace CMYK",
            "descricao": "Um espaço de cor /DeviceN usa AlternateSpace CMYK sem nomes de tinta. Pode indicar conversão acidental de cores spot para processo.",
            "acao": "Verifique se os nomes das tintas spot estão correctamente especificados no array /DeviceN.",
        },
        # ─── GWG Output Suite 5.0 — Fontes (GWG) ────────────────────
        "W_COURIER_SUBSTITUTION": {
            "titulo": "⚠️ Substituição por Courier Detectada",
            "descricao": "Uma ou mais fontes têm 'courier' no nome base, indicando substituição automática pelo exportador quando a fonte original não estava disponível. O resultado visual pode diferir do original.",
            "acao": "Instale as fontes originais e re-exporte o PDF, ou converta todas as fontes em curvas antes de exportar.",
        },
    },

    "en-US": {
        "E001_DIMENSION_MISMATCH": {
            "titulo": "❌ Dimension Mismatch",
            "descricao": "The file does not match any recognized dimensional standard.",
            "acao": "Check document size in your design software and adjust to the correct format.",
        },
        "E002_MISSING_BLEED": {
            "titulo": "❌ Missing Bleed",
            "descricao": "The file has no bleed. This will cause white borders after trimming.",
            "acao": "Add 2mm to 3mm bleed on all sides of the document.",
        },
        "E003_INSUFFICIENT_BLEED": {
            "titulo": "⚠️ Insufficient Bleed",
            "descricao": "The configured bleed is less than 2mm.",
            "acao": "Increase bleed to at least 2mm.",
        },
        "E004_INSUFFICIENT_SAFETY_MARGIN": {
            "titulo": "❌ Insufficient Safety Margin",
            "descricao": "Important elements are too close to the trim edge.",
            "acao": "Keep text and logos at least 3mm from the inner edge.",
        },
        "E005_LOW_RESOLUTION": {
            "titulo": "❌ Low Resolution",
            "descricao": "Image resolution is below 300 DPI. The output will appear blurry.",
            "acao": "Replace images with high-resolution versions (minimum 300 DPI).",
        },
        "E006_RGB_COLORSPACE": {
            "titulo": "❌ RGB Color Space",
            "descricao": "The file contains RGB colors. Offset printing requires CMYK.",
            "acao": "Convert all colors to CMYK or Pantone before submitting.",
        },
        "E007_EXCESSIVE_INK_COVERAGE": {
            "titulo": "❌ Excessive Ink Coverage",
            "descricao": "Total ink coverage exceeds the substrate limit. This will cause set-off and smearing.",
            "acao": "Reduce color density. Check the color profile being used.",
        },
        "E008_NON_EMBEDDED_FONTS": {
            "titulo": "❌ Non-Embedded Fonts",
            "descricao": "Some fonts are not embedded in the file.",
            "acao": "Embed all fonts when exporting the PDF, or convert them to outlines.",
        },
        "E009_NFC_ZONE_VIOLATION": {
            "titulo": "❌ NFC Zone Violation",
            "descricao": "Graphic elements overlay the NFC/RFID chip area. This will damage the chip.",
            "acao": "Move all elements outside the central 30mm x 20mm zone.",
        },
        "E010_HAIRLINE_DETECTED": {
            "titulo": "❌ Hairline Detected",
            "descricao": "Lines thinner than 0.25pt were found. They will be invisible after printing.",
            "acao": "Increase all line widths to at least 0.25pt.",
        },
        "E001_SPINE_WIDTH_MISMATCH": {
            "titulo": "❌ Spine Width Mismatch",
            "descricao": "The spine width does not match the calculation based on page count and paper weight.",
            "acao": "Recalculate spine: (Total Pages ÷ 2) × Paper Thickness in microns.",
        },
        "E002_GUTTER_INVASION": {
            "titulo": "❌ Gutter Invasion",
            "descricao": "Content is within 10mm of the spine (glue area). It will be destroyed during binding.",
            "acao": "Move all elements at least 10mm from the inner margin (spine).",
        },
        "E003_RICH_BLACK_IN_TEXT": {
            "titulo": "❌ Rich Black in Text",
            "descricao": "Body text uses Rich Black (CMYK mix). This causes blurring in text.",
            "acao": "Use only 100% K (pure black) for text and thin elements.",
        },
        "E002_CREEP_COMPENSATION_MISSING": {
            "titulo": "❌ Missing Creep Compensation",
            "descricao": "Inner panels have the same width as outer panels. Content will overflow when folded.",
            "acao": "Reduce the center panel by 2mm to 3mm to compensate for fold creep.",
        },
        "E003_CONTENT_CROSSING_FOLD": {
            "titulo": "❌ Content Crossing Fold",
            "descricao": "A graphic element crosses the fold line, causing unwanted visual cuts.",
            "acao": "No critical elements should cross fold lines.",
        },
        "E004_MECHANICAL_SCORE_REQUIRED": {
            "titulo": "❌ Mechanical Score Required",
            "descricao": "Paper weight >150gsm requires mechanical scoring before folding.",
            "acao": "Request mechanical scoring or choose lighter paper (<150gsm).",
        },
        "E001_NO_DIE_CUT_LAYER": {
            "titulo": "❌ Missing Die Cut Layer",
            "descricao": "No die-cut layer was found in the file.",
            "acao": "Create a layer named 'CutContour' with the vector cut line.",
        },
        "E002_FACA_OVERPRINT_MISSING": {
            "titulo": "❌ Die Cut Overprint Missing",
            "descricao": "The die-cut layer does not have Overprint enabled.",
            "acao": "Select the die-cut layer and enable Overprint.",
        },
        "E001_SCALE_DEVIATION": {
            "titulo": "❌ Scale Deviation",
            "descricao": "The file has a scale deviation greater than 0.1%.",
            "acao": "Set document to 1:1 scale and re-export.",
        },
        "E002_HAIRLINE_DETECTED": {
            "titulo": "❌ CAD Hairline Detected",
            "descricao": "Lines thinner than 0.25pt were found. They will be invisible when plotted.",
            "acao": "Increase all lines to at least 0.25pt.",
        },
        "E003_BINDING_MARGIN_INSUFFICIENT": {
            "titulo": "❌ Binding Margin Insufficient",
            "descricao": "Side margin is less than 15mm. Wire-O perforation will cut critical elements.",
            "acao": "Increase side margin to at least 15mm.",
        },
        "W001_EXCESSIVE_BLEED": {
            "titulo": "⚠️ Excessive Bleed",
            "descricao": "Bleed is greater than 3mm. Not an error, but wastes material.",
            "acao": "Reduce bleed to 3mm if possible.",
        },
        "W001_CONTENT_NEAR_FOLD": {
            "titulo": "⚠️ Content Near Fold",
            "descricao": "Elements are within 5mm of a fold line.",
            "acao": "Move elements at least 5mm from fold lines.",
        },
        "W003_BORDERLINE_RESOLUTION": {
            "titulo": "⚠️ Borderline Resolution",
            "descricao": "Resolution is exactly 300 DPI — acceptable but not ideal for premium printing.",
            "acao": "If possible, provide images at 350 DPI or higher.",
        },
    },

    "es-ES": {
        "E001_DIMENSION_MISMATCH": {
            "titulo": "❌ Dimensiones Incorrectas",
            "descricao": "El archivo no corresponde a ningún estándar dimensional reconocido.",
            "acao": "Verifique el tamaño del documento en el software de diseño.",
        },
        "E002_MISSING_BLEED": {
            "titulo": "❌ Sangrado Ausente",
            "descricao": "El archivo no tiene sangrado. Esto causará bordes blancos tras el corte.",
            "acao": "Configure un sangrado de 2mm a 3mm en todos los lados del documento.",
        },
        "E003_INSUFFICIENT_BLEED": {
            "titulo": "⚠️ Sangrado Insuficiente",
            "descricao": "El sangrado configurado es menor a 2mm.",
            "acao": "Aumente el sangrado a un mínimo de 2mm.",
        },
        "E005_LOW_RESOLUTION": {
            "titulo": "❌ Resolución Insuficiente",
            "descricao": "La resolución de las imágenes es inferior a 300 DPI.",
            "acao": "Sustituya las imágenes por versiones de alta resolución (mínimo 300 DPI).",
        },
        "E006_RGB_COLORSPACE": {
            "titulo": "❌ Colores en RGB",
            "descricao": "El archivo contiene colores en modelo RGB. La impresión offset usa CMYK.",
            "acao": "Convierta todos los colores a CMYK o Pantone antes de enviar.",
        },
        "E008_NON_EMBEDDED_FONTS": {
            "titulo": "❌ Fuentes No Incorporadas",
            "descricao": "Hay fuentes que no están incorporadas al archivo.",
            "acao": "Incorpore todas las fuentes al exportar el PDF.",
        },
        "E002_FACA_OVERPRINT_MISSING": {
            "titulo": "❌ Overprint de Troquel Desactivado",
            "descricao": "La capa de troquel no tiene Overprint activado.",
            "acao": "Seleccione la capa de troquel y active Overprint.",
        },
        "W001_EXCESSIVE_BLEED": {
            "titulo": "⚠️ Sangrado Excesivo",
            "descricao": "El sangrado es mayor a 3mm. No es un error, pero genera desperdicio.",
            "acao": "Reduzca el sangrado a 3mm si es posible.",
        },
        "W003_BORDERLINE_RESOLUTION": {
            "titulo": "⚠️ Resolución Límite",
            "descricao": "La resolución es exactamente 300 DPI — aceptable pero no ideal.",
            "acao": "Si es posible, proporcione imágenes a 350 DPI o más.",
        },
    },
}


# ─── Summary templates ───────────────────────────────────────────────────────

SUMMARY_TEMPLATES: dict[str, dict[str, str]] = {
    "pt-BR": {
        "REPROVADO": "Este arquivo NÃO pode ser enviado para impressão. Corrija os erros listados e reenvie para nova validação.",
        "APROVADO_COM_RESSALVAS": "Este arquivo pode ser enviado, mas revise os avisos para garantir o melhor resultado.",
        "APROVADO": "Arquivo aprovado. Pronto para impressão.",
    },
    "en-US": {
        "REPROVADO": "This file CANNOT be sent for printing. Fix the listed errors and resubmit.",
        "APROVADO_COM_RESSALVAS": "This file can be sent, but review the warnings for best results.",
        "APROVADO": "File approved. Ready for printing.",
    },
    "es-ES": {
        "REPROVADO": "Este archivo NO puede enviarse a impresión. Corrija los errores y reenvíe.",
        "APROVADO_COM_RESSALVAS": "Este archivo puede enviarse, pero revise las advertencias.",
        "APROVADO": "Archivo aprobado. Listo para impresión.",
    },
}

STATUS_LABELS: dict[str, dict[str, str]] = {
    "pt-BR": {
        "REPROVADO": "REPROVADO",
        "APROVADO_COM_RESSALVAS": "APROVADO COM RESSALVAS",
        "APROVADO": "APROVADO",
    },
    "en-US": {
        "REPROVADO": "FAILED",
        "APROVADO_COM_RESSALVAS": "APPROVED WITH WARNINGS",
        "APROVADO": "APPROVED",
    },
    "es-ES": {
        "REPROVADO": "RECHAZADO",
        "APROVADO_COM_RESSALVAS": "APROBADO CON OBSERVACIONES",
        "APROVADO": "APROBADO",
    },
}


def get_message(
    code: str,
    locale: str = "pt-BR",
) -> dict[str, str]:
    """Retrieve the localized message for an error/warning code.

    Falls back to pt-BR if the code is not found in the requested locale.

    Args:
        code: Error or warning code (e.g., 'E002_MISSING_BLEED').
        locale: Target locale ('pt-BR', 'en-US', 'es-ES').

    Returns:
        Dictionary with titulo, descricao, acao.
    """
    locale_messages = MESSAGES.get(locale, MESSAGES["pt-BR"])
    msg = locale_messages.get(code)

    if msg is None:
        # Fallback to pt-BR
        msg = MESSAGES["pt-BR"].get(code)

    if msg is None:
        return {
            "titulo": f"⚠️ {code}",
            "descricao": f"Código de verificação: {code}",
            "acao": "Consulte o manual de pré-flight para detalhes.",
        }

    return msg
