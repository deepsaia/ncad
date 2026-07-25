"""Static drift guard for the Docker config (no daemon needed).

Asserts the Dockerfile + .dockerignore stay honest against the NCAD_ contract + the repo hygiene
rules. The image build/run itself is verified manually (see deploy/run.sh); this only checks the
invariants that can be read from the files.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DOCKERFILE = _ROOT / "Dockerfile"
_DOCKERIGNORE = _ROOT / ".dockerignore"


def test_dockerfile_exists():
    assert _DOCKERFILE.is_file()


def test_dockerignore_excludes_scratch_and_artifacts():
    patterns = {line.strip() for line in _DOCKERIGNORE.read_text().splitlines()
                if line.strip() and not line.startswith("#")}
    for needed in ("out/", ".venv/", ".git/", "docs/superpowers/", "__pycache__/",
                   ".pytest_cache/", "tests/", "other_docs/", ".env"):
        assert needed in patterns, f".dockerignore must exclude {needed!r}"


def test_dockerfile_serves_on_the_ncad_env_contract():
    text = _DOCKERFILE.read_text()
    # The server must bind 0.0.0.0 in-container (so the mapped port is reachable) + expose 8000.
    assert "NCAD_HOST=0.0.0.0" in text
    assert "NCAD_PORT=8000" in text
    assert "EXPOSE 8000" in text
    # The entrypoint runs the serve command (JSON form).
    assert '["ncad", "serve"]' in text or "ncad serve" in text
    # out/ is a volume so artifacts CAN persist (optional at run time).
    assert "VOLUME" in text and "/app/out" in text
    # Runs as a non-root user, and pins the linux/amd64-only stack via a slim py3.13 base.
    assert "python:3.13-slim" in text
    assert "USER ncad" in text


def test_dockerfile_documents_stateless_roadmap():
    # The Stage B migration seams are recorded for posterity (task #73).
    text = _DOCKERFILE.read_text().lower()
    assert "jobstore" in text and "artifactstore" in text
    assert "stateless" in text
