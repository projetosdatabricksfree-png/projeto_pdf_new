# Post-MVP Backlog

Items intentionally deferred from the 4-sprint MVP. Each entry: ID, title, reason deferred, estimated effort, recommended version.

| ID | Title | Reason Deferred | Effort | Target Version |
|---|---|---|---|---|
| FO-05 | Rich Black ratio per variant (§4.15) | Already partial; per-variant ratio table intersects FO-04. Bundle into atomic per-variant text-quality release. | M | v1.1 |
| SP-05 | DeviceN with >1 non-process colorant (Ghent 14.x) | Niche; affects packaging only, which is outside the 14 GWG2015 variants in MVP scope. | M | v1.1 |
| GE-01 (full hardening) | UserUnit absent on **all** page dicts including inherited resources | Currently partial; full inheritance traversal across PageTree is rare and edge-case. | S | v1.1 |
| CO-04 (full hardening) | Transparency Blend CS edge cases (Form XObject Groups within Patterns) | Captured by TR-01/TR-02 at the page level; nested Form XObject scanning deferred. | M | v1.1 |
| OV-09 (mask variant) | CMYK ImageMask overprint with chroma-keyed alternates | Deep mask-graph traversal; rare in real-world ad PDFs. | M | v1.2 |
| Multi-language colorant naming normalization | NFKC normalization for non-ASCII spot color names | Multilingual print shops are post-MVP; current SP-02 already enforces UTF-8 validity. | M | v1.2 |
| Streaming TAC for posters > A2 | Tile-based TAC for very large pages at 300dpi | MVP target is up to A2 @300dpi; covers >95% of customer jobs. | L | v1.2 |
| OPI / DeviceN+NChannel image data | Real OPI references and image-as-NChannel detection | Outside GWG2015 press-job scope. | L | v2.0 |
| FO-03 (CFF table parser) | Validate CFF charstring program correctness inside embedded OpenType | Beyond pure presence/embedded check; needs `fontTools` integration. | XL | v2.0 |
| Per-page TAC heatmap export | Export 15mm² mean heatmap as overlay PNG for QA review | UX feature, not a compliance gate. | M | v1.1 |
| Custom user-defined variants | Allow shop-specific variant definitions through admin UI | Requires UI work and persistence layer; not in compliance MVP. | L | v1.2 |
| Audit log of every threshold lookup | Per-job structured JSON of which variant rule matched and why | Observability nice-to-have; current `progress_bus` events suffice for MVP. | M | v1.1 |
| Smart `W_VARIANT_AMBIGUOUS` recovery flow | Frontend prompts user to confirm variant when detection is ambiguous | Backend emits warning today; frontend interaction post-MVP. | M | v1.1 |
