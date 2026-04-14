"""
GWG Error Messages — Humanization Layer.
Maps technical error codes to clear, actionable messages for print operators.
"""

ERROR_MAP = {
    # Sprint 1
    "E_TAC_EXCEEDED": {
        "title": "Limite de Cores Excedido (TAC)",
        "message": "O arquivo tem áreas com muita tinta ({found}), o que pode causar borrões ou demora na secagem.",
        "action": "Reduza a cobertura de tinta para no máximo {expected} usando perfis ICC adequados."
    },
    "E006_FORBIDDEN_COLORSPACE": {
        "title": "Espaço de Cor Não Permitido",
        "message": "Foram encontrados objetos em {found}, mas este perfil exige {expected}.",
        "action": "Converta o arquivo para CMYK ou CMYK+Spot antes de enviar."
    },
    "E008_NON_EMBEDDED_FONTS": {
        "title": "Fontes Não Incorporadas",
        "message": "Existem fontes que não foram incluídas no PDF. Isso altera a aparência do texto na impressão.",
        "action": "Gere o PDF novamente selecionando a opção 'Incorporar todas as fontes'."
    },
    
    # Sprint 2
    "E_BLACK_TEXT_NO_OVERPRINT": {
        "title": "Preto Pequeno Sem Sobreposição",
        "message": "Texto preto pequeno ({found}) está configurado para 'vazar' o fundo.",
        "action": "Ative a sobreimpressão (Overprint) para o preto 100% para evitar falhas de registro."
    },
    "E_OPM_MISSING": {
        "title": "Modo de Sobreimpressão (OPM) Incorreto",
        "message": "O modo OPM=0 pode causar problemas de transparência indesejada em cores spot.",
        "action": "Defina OPM=1 nas configurações de exportação do PDF."
    },
    "E_BLACK_TEXT_DEVICEGRAY": {
        "title": "Texto Preto em DeviceGray",
        "message": "O texto está em tons de cinza puro, impedindo a sobreimpressão em CMYK.",
        "action": "Converta o texto preto para 100% K em DeviceCMYK."
    },
    "E_RGB_IMAGE_FORBIDDEN": {
        "title": "Imagem RGB Proibida",
        "message": "Este perfil (§4.24) não permite imagens RGB nesta variante.",
        "action": "Converta as imagens para CMYK usando o perfil do papel alvo."
    },
    "E_OC_CONFIGS_PRESENT": {
        "title": "Configurações Alternativas de Camada",
        "message": "O PDF contém múltiplas configurações de visualização (OCG Configs).",
        "action": "Remova configurações extras de camadas para garantir que o que verificamos é o que será impresso."
    },
    "E_BLACK_THIN_NO_OVERPRINT": {
        "title": "Traços Finos Sem Sobreposição",
        "message": "Linhas pretas muito finas não estão configuradas para sobrepor o fundo.",
        "action": "Ative o Overprint para traços e preenchimentos pretos 100%."
    },
    
    # Sprint 3
    "E_CROPBOX_NEQ_MEDIABOX": {
        "title": "CropBox Irregular",
        "message": "A CropBox difere da MediaBox ({found}). Isso pode mascarar áreas de sangria.",
        "action": "Remova a CropBox ou defina-a com o mesmo tamanho da MediaBox."
    },
    "E_TRIMBOX_INCONSISTENT": {
        "title": "Tamanho de Página Inconsistente",
        "message": "As páginas têm tamanhos de corte diferentes (TrimBox). Pág {found}.",
        "action": "Padronize o tamanho de todas as páginas no documento original."
    },
    "E_PAGE_ROTATED": {
        "title": "Página com Rotação Lógica",
        "message": "Uma ou mais páginas possuem o atributo 'Rotate' ({found}), o que atrapalha a imposição.",
        "action": "Remova a rotação lógica nas configurações de exportação/destilação."
    },
    "W_EMPTY_PAGE": {
        "title": "Página Vazia Detectada",
        "message": "A página {found} parece não conter nenhum elemento gráfico visível.",
        "action": "Verifique se a inclusão desta página em branco é intencional."
    },
    "E_PAGE_COUNT_INVALID": {
        "title": "Número de Páginas Inválido",
        "message": "Este perfil exige exatamente {expected} página(s), mas o arquivo tem {found}.",
        "action": "Separe as páginas em arquivos individuais para o envio de anúncios."
    },
    "E_SPOT_RESERVED_NAME": {
        "title": "Nome de Cor Especial Reservado",
        "message": "A cor spot '{found}' usa um nome proibido pela norma (§4.20).",
        "action": "Renomeie a cor especial no aplicativo original (ex: Illustrator/InDesign)."
    },
    "E_SPOT_NAME_NOT_UTF8": {
        "title": "Erro de Codificação no Nome da Cor",
        "message": "O nome da cor especial contém caracteres corrompidos ou não-UTF8.",
        "action": "Use apenas caracteres padrão e UTF-8 para nomear cores especiais."
    },
    "E_SPOT_AMBIGUOUS": {
        "title": "Cor Especial Ambígua",
        "message": "A cor '{found}' está definida com diferentes misturas de CMYK/Lab ao longo do arquivo.",
        "action": "Unifique a definição da cor especial em todas as páginas e elementos."
    },
    "E_SPOT_COUNT_EXCEEDED": {
        "title": "Limite de Cores Especiais Excedido",
        "message": "O perfil permite {expected} cor(es) especial(is), mas foram detectadas {found}.",
        "action": "Reduza o número de cores spot ou utilize o perfil de saída correto."
    },
    "E_IMAGE_OVERPRINT": {
        "title": "Sobreimpressão de Imagem Proibida",
        "message": "Uma imagem CMYK está configurada para sobrepor (overprint) o fundo.",
        "action": "Desative a sobreimpressão para imagens CMYK para evitar escurecimento inesperado."
    },
    "E_DEVICEN_WHITE_OVERPRINT": {
        "title": "Sobreimpressão de 'Branco' (Zera-Tint)",
        "message": "Um objeto de cor spot com 0% de tinta está em sobreimpressão.",
        "action": "Certifique-se de que tintas spot com 0% (branco) não estejam em overprint."
    }
}

def get_human_error(codigo: str, found: str = "", expected: str = "") -> dict:
    """Returns a dictionary with title, message, and action based on the error code."""
    info = ERROR_MAP.get(codigo, {
        "title": "Aviso Técnico",
        "message": f"Identificado problema técnico: {codigo}",
        "action": "Revise o arquivo original ou as configurações de exportação."
    })
    
    # Format strings with context
    msg = info["message"].format(found=found, expected=expected)
    action = info["action"].format(found=found, expected=expected)
    
    return {
        "title": info["title"],
        "message": msg,
        "action": action
    }
