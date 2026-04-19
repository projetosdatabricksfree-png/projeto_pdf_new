-- Table: validation_findings
CREATE TABLE IF NOT EXISTS validation_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL, -- INFO, WARNING, ERROR
    message TEXT NOT NULL,
    page_number INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_validation_findings_job_id ON validation_findings(job_id);
