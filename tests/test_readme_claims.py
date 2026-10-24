"""Guard the README against reintroduced false claims.

An earlier revision of the README documented integrations and modules that
did not exist (RestAdapter, profile_engine, twelve transform modules,
mistral/llamaindex/ollama extras), a PyPI install that was never published,
and performance numbers no benchmark could reproduce. These checks keep the
README anchored to the shipped implementation.
"""

from pathlib import Path

import pytest

from neurobridge.core.profile import Profile, get_profile_config
from neurobridge.core.transform import TransformPipeline

README = Path(__file__).resolve().parents[1] / "README.md"


@pytest.fixture(scope="module")
def readme_text() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_documented_modules_exist(readme_text: str) -> None:
    pipeline = TransformPipeline(profile=get_profile_config(Profile.ADHD))
    for module in pipeline.modules:
        class_name = type(module).__name__
        assert class_name in readme_text, (
            f"Transform module {class_name} is registered in the pipeline but "
            "not documented in the README"
        )


def test_readme_does_not_claim_nonexistent_integrations(readme_text: str) -> None:
    for fabricated in (
        "RestAdapter",
        "profile_engine",
        "neurobridge[mistral]",
        "neurobridge[llamaindex]",
        "neurobridge[ollama]",
        "neurobridgeuggingface",
    ):
        assert (
            fabricated not in readme_text
        ), f"README mentions {fabricated!r}, which does not exist in the package"


def test_readme_does_not_claim_twelve_modules(readme_text: str) -> None:
    assert "12 transformation" not in readme_text
    assert "AmbiguityResolver" not in readme_text
    assert "ReadingLevelAdapter" not in readme_text


def test_readme_does_not_claim_unpublished_pypi_install(readme_text: str) -> None:
    # The package is not on PyPI; the install line must point at the repository.
    assert "pip install neurobridge\n" not in readme_text
    assert "pypi.org/project/neurobridge" not in readme_text


def test_readme_links_point_at_the_real_repository(readme_text: str) -> None:
    assert "yourusername" not in readme_text


def test_readme_python_version_matches_package(readme_text: str) -> None:
    assert "3.10" in readme_text
    assert "Python-3.9" not in readme_text
