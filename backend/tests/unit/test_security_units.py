import pytest
from pydantic import ValidationError

from job_tracker.api.security.rate_limit import SlidingWindowLimiter, client_ip
from job_tracker.config import Settings
from job_tracker.infrastructure.files.cv_locator import DirectoryCvLocator
from job_tracker.shared.sanitize import clean_bounded, clean_text, validate_http_url

# ── sanitize ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  hola  ", "hola"),
        ("<b>negrita</b>", "negrita"),
        ("<script>alert(1)</script>texto", "texto"),
        ("R&D y I+D", "R&D y I+D"),
        ("a\x00b\x07c", "abc"),
        ("sin\u200bespacio", "sinespacio"),
        ("\u202etxt.exe", "txt.exe"),
        ("Atención: año", "Atención: año"),
        ("é", "é"),  # normaliza a NFC
    ],
)
def test_clean_text(raw: str, expected: str) -> None:
    assert clean_text(raw) == expected


def test_clean_text_never_returns_markup_even_from_encoded_input() -> None:
    assert "<" not in clean_text("&lt;script&gt;alert(1)&lt;/script&gt;")


def test_clean_bounded_truncates() -> None:
    assert clean_bounded("a" * 500, 10) == "a" * 10


@pytest.mark.parametrize("url", ["http://a.com", "https://a.com/x?y=1&z=2"])
def test_valid_urls(url: str) -> None:
    assert validate_http_url(url) == url


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "JaVaScRiPt:alert(1)", "data:x", "file:///x", "ftp://a.com", "http://", "a.com"]
)
def test_invalid_urls(url: str) -> None:
    with pytest.raises(ValueError, match="http"):
        validate_http_url(url)


# ── CvLocator ────────────────────────────────────────────────────────────────────


def test_locator_finds_files_inside_base(tmp_path) -> None:
    (tmp_path / "cv.docx").write_bytes(b"x")
    assert DirectoryCvLocator(tmp_path).locate("cv.docx") == (tmp_path / "cv.docx").resolve()


@pytest.mark.parametrize("name", ["", "../x.txt", "sub/../../x.txt", "/etc/passwd", "ausente.docx", "a\x00b"])
def test_locator_never_escapes_or_invents_paths(tmp_path, name: str) -> None:
    base = tmp_path / "base"
    base.mkdir()
    (tmp_path / "x.txt").write_text("fuera")
    located = DirectoryCvLocator(base).locate(name)
    assert located is None or located.is_relative_to(base.resolve())


def test_locator_rejects_symlinks_pointing_outside(tmp_path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    secret = tmp_path / "secreto.txt"
    secret.write_text("fuera")
    try:
        (base / "enlace.docx").symlink_to(secret)
    except OSError:
        pytest.skip("symlinks no disponibles sin privilegios en este sistema")
    assert DirectoryCvLocator(base).locate("enlace.docx") is None


def test_locator_rejects_directories(tmp_path) -> None:
    (tmp_path / "carpeta").mkdir()
    assert DirectoryCvLocator(tmp_path).locate("carpeta") is None


# ── limitador ────────────────────────────────────────────────────────────────────


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_limiter_blocks_then_recovers_after_window() -> None:
    clock = FakeClock()
    limiter = SlidingWindowLimiter(clock=clock)
    assert [limiter.hit("ip", 2, 60) for _ in range(2)] == [0.0, 0.0]
    assert limiter.hit("ip", 2, 60) == pytest.approx(60)
    clock.now += 30
    assert limiter.hit("ip", 2, 60) == pytest.approx(30)
    clock.now += 31
    assert limiter.hit("ip", 2, 60) == 0.0


def test_limiter_keeps_keys_independent() -> None:
    limiter = SlidingWindowLimiter(clock=FakeClock())
    limiter.hit("a", 1, 60)
    assert limiter.hit("a", 1, 60) > 0
    assert limiter.hit("b", 1, 60) == 0.0


def test_limiter_memory_is_bounded() -> None:
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_keys=100, clock=clock)
    for i in range(100):
        limiter.hit(f"ip{i}", 5, 60)
    clock.now += 120  # todas las entradas caducan
    limiter.hit("nueva", 5, 60)
    assert len(limiter._hits) <= 2


def test_client_ip_ignores_forwarded_header_unless_proxy_is_trusted() -> None:
    scope = {"client": ("10.0.0.5", 1234), "headers": [(b"x-forwarded-for", b"1.2.3.4, 203.0.113.9")]}
    assert client_ip(scope, trust_proxy=False) == "10.0.0.5"
    # Con proxy de confianza se toma el último valor (el añadido por nuestro proxy), no el que envía el cliente.
    assert client_ip(scope, trust_proxy=True) == "203.0.113.9"


# ── configuración ────────────────────────────────────────────────────────────────


def _settings(**kwargs: object) -> Settings:
    return Settings(_env_file=None, **kwargs)  # type: ignore[arg-type]


def test_production_requires_a_strong_token() -> None:
    with pytest.raises(ValidationError, match="API_TOKEN"):
        _settings(app_env="production")
    with pytest.raises(ValidationError, match="API_TOKEN"):
        _settings(app_env="production", api_token="corto")
    assert _settings(app_env="production", api_token="x" * 32).docs_enabled is False


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="CORS"):
        _settings(app_env="production", api_token="x" * 32, cors_origins="*")


def test_secrets_are_not_printed() -> None:
    settings = _settings(api_token="s3cr3t-" + "x" * 30, anthropic_api_key="sk-ant-123")
    assert "s3cr3t" not in repr(settings) and "sk-ant-123" not in repr(settings)


def test_blank_token_is_treated_as_no_token() -> None:
    assert _settings(api_token="").api_token is None
    assert _settings(api_token="   ").api_token is None
    with pytest.raises(ValidationError, match="API_TOKEN"):
        _settings(app_env="production", api_token="")
