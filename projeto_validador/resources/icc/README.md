# ICC Profiles (Hermetic Build Assets)

These profiles are **committed to the repo** so `docker build` is reproducible
and survives network outages / upstream throttling.

## Required file

- `ISOcoated_v2_300_eci.icc` — Coated FOGRA39 (ISO 12647-2:2004), 300% TAC.
  Used by `ColorSpaceRemediator` for CMYK separation of coated-paper jobs.

## Where to get it (one-time setup)

Download from the ECI registry and drop it here:

- https://www.eci.org/en/downloads (section "ICC Profiles from ECI")
- Or the color.org mirror: https://www.color.org/registry/

Expected SHA-256: verify with `sha256sum ISOcoated_v2_300_eci.icc` after
download and record the hash alongside the file in version control.

## Licensing

The ECI profiles are distributed free of charge under the ECI license
(redistribution permitted, no modification). Keep the accompanying license
text alongside the `.icc` file if committing.
