import json

def _parse_verapdf_json(raw: str):
    try:
        data = json.loads(raw)
        jobs = data.get("report", {}).get("jobs", [])
        if not jobs:
            return "No jobs"
        
        # O log mostra que validationResult está dentro de jobs[0]
        vr = jobs[0].get("validationResult", {})
        passed = bool(vr.get("compliant", False))
        details = vr.get("details", {})
        
        print(f"Passed: {passed}")
        
        # O log mostra ruleSummaries dentro de details
        for summary in details.get("ruleSummaries", []):
            print(f"Processing summary: {summary}")
            # Aqui pode estar o erro se summary for uma lista (improvável)
            # Ou se ruleId for uma lista?
            rule_id_obj = summary.get("ruleId", {})
            print(f"RuleId found: {rule_id_obj}")
            
    except Exception as exc:
        print(f"Error: {exc}")

# JSON extraído do log (simplificado)
raw_json = """
{
  "report": {
    "jobs": [
      {
        "validationResult": {
          "details": {
            "ruleSummaries": [
              {
                "ruleStatus": "FAILED",
                "clause": "6.2.10.4.1",
                "testNumber": 1
              }
            ]
          }
        }
      }
    ]
  }
}
"""

_parse_verapdf_json(raw_json)
