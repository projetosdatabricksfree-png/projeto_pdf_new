"""
Client for OpenAI API interactions using GPT-4o-mini.
Provides specific prompts for routing (Gerente) and report generation (Validador).
"""
import os
import json
import logging
from typing import Any, Dict
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize client using environment variable OPENAI_API_KEY
# If missing, it will safely defer to returning None at runtime.
api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key) if api_key else None

MODEL_NAME = "gpt-4o-mini"

async def analisar_roteamento_llm(metadata: Dict[str, Any]) -> Dict[str, Any] | None:
    """Uses LLM to perform advanced routing based on extracted physical metadata."""
    if not os.getenv("OPENAI_API_KEY"):
        return None

    prompt = f"""
    Você é um experiente Gerente de Produção em uma gráfica de alta demanda.
    Seu papel é analisar os metadados extraídos de um arquivo enviado pelo cliente 
    e roteá-lo para o operador correto.

    Metadados extraídos:
    {json.dumps(metadata, indent=2)}

    Os fluxos (Operários) disponíveis são:
    - operario_projetos_cad: Grandes formatos CAD (A0, A1, A2) ou larguras maiores que 420mm.
    - operario_papelaria_plana: Pequenos formatos geométricos (< 6000 mm2 de área), até 2 páginas. (Ex: Cartão de visita).
    - operario_editoriais: Arquivos com muitas páginas (8 ou mais páginas). Foco em livros e revistas.
    - operario_dobraduras: Arquivos com 2 a 7 páginas, ou panfletos panorâmicos (largura desproporcional à altura, como folders sanfona).
    - operario_cortes_especiais: Pequenos formatos irregulares de até 4 páginas que podem conter nomes de camadas (ExifTool / PDF) indicando 'CutContour', 'Faca' ou similar.

    Responda ESTRITAMENTE em formato JSON com 3 chaves:
    {{
        "route_to": "nome_do_operario_decidido",
        "confidence": 0.0 a 1.0,
        "reason": "Explicação técnica curta do porquê dessa rota"
    }}
    """

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Você é uma IA especializada em analisar e rotear ordens de produção gráfica e responde apenas no formato JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            # Validate output keys
            if "route_to" in result and "confidence" in result and "reason" in result:
               return result
    except Exception as e:
        logger.error(f"[LLM Routing] Failed to parse LLM routing: {e}")
    
    return None


async def gerar_relatorio_humanizado_llm(
    status: str, 
    produto: str, 
    erros: list[dict], 
    avisos: list[dict]
) -> str | None:
    """Uses LLM to generate an empathetic DTP-style text report for the customer."""
    if not os.getenv("OPENAI_API_KEY"):
        return None

    erros_texto = json.dumps(erros, indent=2, ensure_ascii=False)
    avisos_texto = json.dumps(avisos, indent=2, ensure_ascii=False)

    prompt = f"""
    Você atua como Atendimento Técnico B2B (Bureau DTP) em uma gráfica profissional.
    O sistema automático de validação inspecionou um arquivo do cliente e produziu este resultado cru:
    Status: {status}
    Produto: {produto}
    Erros Críticos: {erros_texto}
    Avisos: {avisos_texto}

    Sua tarefa é explicar esses resultados para o cliente final. 
    Se o status for REPROVADO, seja empático, mas explique claramente por que o arquivo não pode ser impresso e direcione como ele no (Illustrator/InDesign/Corel) pode consertar os erros mencionados.
    Se o status for APROVADO_COM_RESSALVAS, parabenize pela aprovação, mas recomende atenção aos avisos listados.
    Se o status for APROVADO, parabenize pela conformidade.

    Formato: markdown limpo. Seja amigável, utilize listas ou passos fáceis de seguir. Não inclua os códigos técnicos crus (tipo "E002_MISSING_BLEED") no texto lido pelo cliente se puder usar termos humanos ("Falta de Sangria"). Não invente erros que não foram listados.
    """

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Você é um técnico DTP amigável explicando artefinal gráfica a um cliente."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"[LLM Report] Failed to fetch LLM report: {e}")
        return None
