"""
OC Filter — GWG §3.16 Optional Content visibility helper.

Builds the set of OCG xrefs that are visible under the default configuration
(`OCProperties.D`) so that every downstream checker can skip content marked
for layers that ship invisible by default.

Advanced (OC-03): Supports RBGroups (Radio Button Groups) and OCMD
(Optional Content Membership Dictionaries) with AND/OR/NOT logic
as seen in Ghent Patches 15.0-15.2.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

import fitz

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class VisibilityFilter:
    """Set of OCG xrefs visible under the default config.

    `all_visible=True` means the document has no OCProperties or a permissive
    default config; every object is considered visible.

    NOTE: `doc` is excluded from pickling — fitz.Document is a C extension
    with file descriptors and cannot be serialized across processes.
    OCMD resolution (OC-03 advanced logic) is unavailable in subprocess
    contexts; the filter falls back to xref-based visibility (OC-02).
    """
    visible_ocgs: frozenset[int] = field(default_factory=frozenset)
    all_visible: bool = True
    doc: Optional[fitz.Document] = field(default=None, compare=False, hash=False)

    def __getstate__(self) -> dict:
        # Exclude fitz.Document — not picklable (C extension with FDs/threads).
        return {"visible_ocgs": self.visible_ocgs, "all_visible": self.all_visible}

    def __setstate__(self, state: dict) -> None:
        object.__setattr__(self, "visible_ocgs", state["visible_ocgs"])
        object.__setattr__(self, "all_visible", state["all_visible"])
        object.__setattr__(self, "doc", None)  # unavailable in child processes

    def is_visible(self, ocg_xrefs: Iterable[int]) -> bool:
        """Determines if the given OCGs (or OCMDs) allow visibility."""
        if self.all_visible:
            return True

        xrefs = list(ocg_xrefs)
        if not xrefs:
            return True

        # OC-03: Membership Dictionary (OCMD) Logic
        for xref in xrefs:
            if self._is_ocmd(xref):
                if self._resolve_ocmd(xref):
                    return True
            elif xref in self.visible_ocgs:
                return True

        return False

    def _is_ocmd(self, xref: int) -> bool:
        """Heuristic check if a xref is an OCMD."""
        if not self.doc:
            return False
        try:
            obj = self.doc.xref_object(xref)
            return "/OCMD" in obj
        except Exception:
            return False

    def _resolve_ocmd(self, xref: int) -> bool:
        """Resolves /P (Policy) and /VE (Visibility Expression) for an OCMD."""
        if not self.doc:
            return True
        try:
            obj = self.doc.xref_object(xref)

            # Policy (/P): AllOn, AnyOn, AnyOff, AllOff
            policy_m = re.search(r"/P\s+/(\w+)", obj)
            policy = policy_m.group(1) if policy_m else "AnyOn"

            # OCGs involved in this OCMD
            ocgs_m = re.search(r"/OCGs\s*\[([^\]]*)\]", obj)
            if not ocgs_m:
                # Might be single OCG ref instead of array
                ocgs_m = re.search(r"/OCGs\s+(\d+)\s+0\s+R", obj)
                ocg_list = [int(ocgs_m.group(1))] if ocgs_m else []
            else:
                ocg_list = [int(m) for m in re.findall(r"(\d+)\s+0\s+R", ocgs_m.group(1))]

            if not ocg_list:
                return True

            states = [ocg in self.visible_ocgs for ocg in ocg_list]

            if policy == "AllOn":
                return all(states)
            if policy == "AnyOn":
                return any(states)
            if policy == "AnyOff":
                return not all(states)
            if policy == "AllOff":
                return not any(states)

            return True
        except Exception:
            return True

def _extract_refs(section: str) -> list[int]:
    return [int(m) for m in re.findall(r"(\d+)\s+0\s+R", section)]

def build_visibility_filter(file_path: str) -> VisibilityFilter:
    """Compute the visible OCG set from the default config (D)."""
    doc = fitz.open(file_path)
    try:
        try:
            catalog_xref = doc.pdf_catalog()
        except Exception:
            return VisibilityFilter(all_visible=True, doc=doc)
        if not catalog_xref:
            return VisibilityFilter(all_visible=True, doc=doc)

        catalog = doc.xref_object(catalog_xref, compressed=False)
        m = re.search(r"/OCProperties\s+(\d+)\s+0\s+R", catalog)
        if m:
            ocprops = doc.xref_object(int(m.group(1)), compressed=False)
        else:
            m = re.search(r"/OCProperties\s*(<<.*?>>)", catalog, re.DOTALL)
            if not m:
                return VisibilityFilter(all_visible=True, doc=doc)
            ocprops = m.group(1)

        all_ocgs_m = re.search(r"/OCGs\s*\[([^\]]*)\]", ocprops)
        all_ocgs = set(_extract_refs(all_ocgs_m.group(1))) if all_ocgs_m else set()

        d_m = re.search(r"/D\s+(\d+)\s+0\s+R", ocprops)
        if d_m:
            d_dict = doc.xref_object(int(d_m.group(1)), compressed=False)
        else:
            d_m = re.search(r"/D\s*(<<.*?>>)", ocprops, re.DOTALL)
            if not d_m:
                return VisibilityFilter(all_visible=True, doc=doc)
            d_dict = d_m.group(1)

        on_m = re.search(r"/ON\s*\[([^\]]*)\]", d_dict)
        off_m = re.search(r"/OFF\s*\[([^\]]*)\]", d_dict)
        on_set = set(_extract_refs(on_m.group(1))) if on_m else set()
        off_set = set(_extract_refs(off_m.group(1))) if off_m else set()

        base_visible = all_ocgs - off_set if all_ocgs else on_set
        visible = (base_visible | on_set) - off_set

        return VisibilityFilter(
            visible_ocgs=frozenset(visible),
            all_visible=False,
            doc=doc
        )
    finally:
        doc.close()

NULL_FILTER = VisibilityFilter(all_visible=True)
