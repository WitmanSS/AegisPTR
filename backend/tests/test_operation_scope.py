from types import SimpleNamespace

from app.services.operation_scope import is_target_authorized


def test_operation_target_must_be_authorized_and_in_scope() -> None:
    assessment = SimpleNamespace(
        is_authorized=True,
        scope_text="example.com; 192.0.2.0/24; https://portal.example.net",
        exclusions="192.0.2.9; blocked.example.com",
    )

    assert is_target_authorized(assessment, "example.com")
    assert is_target_authorized(assessment, "https://portal.example.net/")
    assert is_target_authorized(assessment, "192.0.2.10")
    assert not is_target_authorized(assessment, "192.0.2.9")
    assert not is_target_authorized(assessment, "198.51.100.10")
    assert not is_target_authorized(assessment, "blocked.example.com")


def test_operation_target_requires_explicit_assessment_authorization() -> None:
    assessment = SimpleNamespace(is_authorized=False, scope_text="example.com", exclusions="")

    assert not is_target_authorized(assessment, "example.com")
