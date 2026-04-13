import fitz
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

class AgenteGeradorPDF:
    """Gerador de relatórios PDF profissionais para validação de arquivos."""

    def __init__(self):
        # Cores do Design System (Industrial/Premium)
        self.COLORS = {
            "PRIMARY": (0.04, 0.04, 0.06),    # #0a0b10 (Deep Dark)
            "ACCENT": (0.23, 0.51, 0.96),     # #3b82f6 (Blue)
            "SUCCESS": (0.06, 0.73, 0.51),    # #10b981 (Green)
            "ERROR": (0.94, 0.27, 0.27),      # #ef4444 (Red)
            "WARNING": (0.96, 0.62, 0.04),    # #f59e0b (Orange)
            "TEXT_MAIN": (0.08, 0.09, 0.13),  # Dark for print
            "TEXT_MUTED": (0.39, 0.45, 0.55), # Greyish
            "BG_SOFT": (0.96, 0.97, 0.98),    # Soft white for readability
        }

    def gerar_relatorio(
        self, 
        job_data: dict, 
        validation_results: list,
        output_path: str
    ) -> str:
        """Gera um PDF formatado com os resultados da validação."""
        doc = fitz.open()
        page = doc.new_page()
        width, height = page.rect.width, page.rect.height

        # --- 1. CABEÇALHO ---
        # Fundo do cabeçalho
        page.draw_rect(fitz.Rect(0, 0, width, 100), color=None, fill=self.COLORS["PRIMARY"])
        
        # Título
        page.insert_text(
            (40, 45), 
            "RELATÓRIO DE PRÉ-IMPRESSÃO", 
            fontsize=22, 
            color=(1, 1, 1),
            fontname="Helvetica-Bold"
        )
        page.insert_text(
            (40, 75), 
            f"Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')}", 
            fontsize=10, 
            color=(0.7, 0.7, 0.7),
            fontname="Helvetica"
        )

        # --- 2. INFORMAÇÕES DO JOB ---
        curr_y = 140
        page.insert_text((40, curr_y), "INFORMAÇÕES DO ARQUIVO", fontsize=14, color=self.COLORS["PRIMARY"], fontname="Helvetica-Bold")
        curr_y += 25
        
        meta_info = [
            ("Arquivo:", job_data.get("original_filename", "N/A")),
            ("Job ID:", str(job_data.get("id", "N/A"))),
            ("Tamanho:", f"{job_data.get('file_size_bytes', 0) / 1024 / 1024:.2f} MB"),
            ("Produto:", job_data.get("detected_product", "Não detectado")),
            ("Agente:", job_data.get("processing_agent", "N/A")),
        ]

        for label, val in meta_info:
            page.insert_text((40, curr_y), label, fontsize=10, color=self.COLORS["TEXT_MUTED"], fontname="Helvetica-Bold")
            page.insert_text((120, curr_y), str(val), fontsize=10, color=self.COLORS["TEXT_MAIN"], fontname="Helvetica")
            curr_y += 18

        # --- 3. STATUS GERAL (BADGE) ---
        status = job_data.get("final_status", "PENDENTE")
        status_color = self.COLORS["SUCCESS"] if status == "APROVADO" else \
                       self.COLORS["WARNING"] if status == "APROVADO_COM_RESSALVAS" else \
                       self.COLORS["ERROR"]
        
        status_text = status.replace("_", " ")
        badge_rect = fitz.Rect(380, 130, 550, 170)
        page.draw_rect(badge_rect, color=status_color, fill=status_color, width=0, overlay=True)
        
        # Text centering in badge
        text_w = fitz.get_text_length(status_text, fontname="Helvetica-Bold", fontsize=12)
        page.insert_text(
            (badge_rect.x0 + (badge_rect.width - text_w)/2, badge_rect.y0 + 25),
            status_text,
            fontsize=12,
            color=(1, 1, 1),
            fontname="Helvetica-Bold"
        )

        # --- 4. LISTA DE VERIFICAÇÕES ---
        curr_y += 40
        page.insert_text((40, curr_y), "DETALHAMENTO TÉCNICO", fontsize=14, color=self.COLORS["PRIMARY"], fontname="Helvetica-Bold")
        curr_y += 10
        page.draw_line((40, curr_y), (width - 40, curr_y), color=self.COLORS["TEXT_MUTED"], width=0.5)
        curr_y += 25

        # Table header
        page.insert_text((55, curr_y), "Status", fontsize=10, color=self.COLORS["TEXT_MUTED"], fontname="Helvetica-Bold")
        page.insert_text((110, curr_y), "Teste", fontsize=10, color=self.COLORS["TEXT_MUTED"], fontname="Helvetica-Bold")
        page.insert_text((250, curr_y), "Encontrado", fontsize=10, color=self.COLORS["TEXT_MUTED"], fontname="Helvetica-Bold")
        page.insert_text((400, curr_y), "Esperado", fontsize=10, color=self.COLORS["TEXT_MUTED"], fontname="Helvetica-Bold")
        curr_y += 15

        for res in validation_results:
            if curr_y > height - 60:
                page = doc.new_page()
                curr_y = 50
            
            # Icon/Indicator
            res_status = res.get("status", "OK")
            res_color = self.COLORS["SUCCESS"] if res_status == "OK" else \
                        self.COLORS["WARNING"] if res_status == "AVISO" else \
                        self.COLORS["ERROR"]
            
            page.draw_circle((45, curr_y - 3), 4, color=res_color, fill=res_color)
            
            page.insert_text((55, curr_y), res_status, fontsize=9, color=res_color, fontname="Helvetica-Bold")
            page.insert_text((110, curr_y), res.get("check_name", res.get("check_code", "Desconhecido")), fontsize=9, color=self.COLORS["TEXT_MAIN"], fontname="Helvetica")
            
            val_found = res.get("value_found", "")
            if val_found and len(str(val_found)) > 40: val_found = str(val_found)[:37] + "..."
            page.insert_text((250, curr_y), str(val_found), fontsize=9, color=self.COLORS["TEXT_MAIN"], fontname="Helvetica")
            
            val_exp = res.get("value_expected", "")
            page.insert_text((400, curr_y), str(val_exp), fontsize=9, color=self.COLORS["TEXT_MUTED"], fontname="Helvetica")
            
            curr_y += 20
            page.draw_line((40, curr_y - 5), (width - 40, curr_y - 5), color=(0.9, 0.9, 0.9), width=0.3)

        # --- 5. RODAPÉ ---
        page.insert_text(
            (width/2 - 60, height - 20), 
            "Projeto Gráfica - Pre-Flight Digital", 
            fontsize=8, 
            color=self.COLORS["TEXT_MUTED"],
            fontname="Helvetica"
        )

        doc.save(output_path)
        doc.close()
        return output_path
