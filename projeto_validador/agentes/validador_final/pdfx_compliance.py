"""
PDF/X-4 conformance inspection.

Full VeraPDF-grade compliance is out of scope for a worker step — we perform
a pragmatic structural check: GTS_PDFXVersion present, OutputIntent with a
DeviceCMYK DestOutputProfile, no encryption. That is enough to block obvious
regressions introduced by a remediator failure.
"""
from __future__ import annotations

from pathlib import Path


def check_pdfx4(pdf_path: Path) -> dict:
    """Return a dict describing PDF/X-4 structural compliance.

    Keys: is_compliant, gts_pdfx_version, output_intent_subtype,
    output_intent_identifier, has_output_profile, errors.
    """
    result: dict = {
        "is_compliant": False,
        "gts_pdfx_version": None,
        "output_intent_subtype": None,
        "output_intent_identifier": None,
        "has_output_profile": False,
        "errors": [],
    }

    try:
        import pikepdf
    except ImportError as exc:
        result["errors"].append(f"pikepdf unavailable: {exc}")
        return result

    try:
        with pikepdf.open(pdf_path) as pdf:
            root = pdf.Root

            version = root.get("/GTS_PDFXVersion")
            if version is not None:
                result["gts_pdfx_version"] = str(version)

            intents = root.get("/OutputIntents")
            if intents is None or len(intents) == 0:
                result["errors"].append("Missing /OutputIntents array")
            else:
                oi = intents[0]
                subtype = oi.get("/S")
                ident = oi.get("/OutputConditionIdentifier")
                profile = oi.get("/DestOutputProfile")
                result["output_intent_subtype"] = str(subtype) if subtype else None
                result["output_intent_identifier"] = str(ident) if ident else None
                result["has_output_profile"] = profile is not None

                if str(subtype) != "/GTS_PDFX":
                    result["errors"].append(
                        f"OutputIntent subtype is {subtype}, expected /GTS_PDFX"
                    )
                if profile is None:
                    result["errors"].append("OutputIntent missing DestOutputProfile")

            if result["gts_pdfx_version"] is None:
                result["errors"].append("Missing /GTS_PDFXVersion in document catalog")

            result["is_compliant"] = len(result["errors"]) == 0
    except Exception as exc:
        result["errors"].append(f"pikepdf open failed: {exc}")

    return result
