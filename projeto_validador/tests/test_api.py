"""
Tests for the validation API endpoints.
"""
from __future__ import annotations

import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    def test_health_returns_200(self):
        """Health endpoint should return 200 with service info."""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "preflight-validator"
            assert data["version"] == "1.0.0"


class TestValidateEndpoint:
    """Tests for POST /api/v1/validate."""

    def test_unsupported_media_type(self, tmp_path):
        """Should reject non-PDF/TIFF/JPEG files."""
        from fastapi.testclient import TestClient
        from app.main import app

        # Create a dummy text file
        test_file = tmp_path / "test.txt"
        test_file.write_text("not a pdf")

        with TestClient(app) as client:
            with open(test_file, "rb") as f:
                response = client.post(
                    "/api/v1/validate",
                    files={"file": ("test.txt", f, "text/plain")},
                )
            assert response.status_code == 415

    def test_valid_pdf_upload(self, tmp_path):
        """Should accept a valid PDF upload and return 202."""
        from fastapi.testclient import TestClient
        from app.main import app

        # Create a minimal PDF
        try:
            import fitz
            doc = fitz.open()
            page = doc.new_page(width=242, height=153)  # ~85.6x53.98mm
            pdf_path = tmp_path / "test_card.pdf"
            doc.save(str(pdf_path))
            doc.close()

            os.environ["VOLUME_PATH"] = str(tmp_path / "uploads")

            with TestClient(app) as client:
                with open(pdf_path, "rb") as f:
                    response = client.post(
                        "/api/v1/validate",
                        files={"file": ("test_card.pdf", f, "application/pdf")},
                    )
                assert response.status_code == 202
                data = response.json()
                assert "job_id" in data
                assert data["status"] == "QUEUED"
                assert "polling_url" in data
        except ImportError:
            pytest.skip("PyMuPDF not installed")


class TestJobStatusEndpoint:
    """Tests for GET /api/v1/jobs/{job_id}/status."""

    def test_nonexistent_job(self):
        """Should return 404 for unknown job ID."""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/v1/jobs/nonexistent-id/status")
            assert response.status_code == 404


class TestJobReportEndpoint:
    """Tests for GET /api/v1/jobs/{job_id}/report."""

    def test_nonexistent_job(self):
        """Should return 404 for unknown job ID."""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/v1/jobs/nonexistent-id/report")
            assert response.status_code == 404
