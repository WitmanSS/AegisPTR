from app.services.scope_engine import ScopeEngine


def test_ip_in_scope() -> None:
    assert ScopeEngine.validate_target("10.10.0.25", ["10.10.0.0/24"], []) is True


def test_ip_excluded() -> None:
    assert ScopeEngine.validate_target("10.10.0.50", ["10.10.0.0/24"], ["10.10.0.50"]) is False


def test_domain_allowed() -> None:
    assert ScopeEngine.validate_target("example.com", ["example.com"]) is True
