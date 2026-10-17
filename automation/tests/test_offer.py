import pytest

from jobsearch.offer import InvalidOfferError, parse_offer, safe_cv_filename

from .conftest import raw_offer


def parse(**overrides: object):
    return parse_offer(raw_offer(**overrides), bullet_count=3)


# ── Nombre de fichero del CV (el modelo decide su valor: debe ser inofensivo) ─────────────────


@pytest.mark.parametrize(
    "malicious",
    [
        "../../evil.docx",
        "..\\..\\evil.docx",
        "/etc/cron.d/evil.docx",
        "C:\\Windows\\evil.docx",
        "sub/dir/cv.docx",
        ".hidden.docx",
        "cv.docx.exe",
        "cv.exe",
        "cv.docx\x00.png",
        "con..cv.docx",
        "a" * 200 + ".docx",
        "",
    ],
)
def test_malicious_cv_filenames_are_replaced(malicious: str) -> None:
    offer = parse(cv_file=malicious)
    if offer.cv_file is not None:
        assert "/" not in offer.cv_file
        assert "\\" not in offer.cv_file
        assert ".." not in offer.cv_file
        assert offer.cv_file.endswith(".docx")
        assert not offer.cv_file.startswith(".")
        assert len(offer.cv_file) < 120


def test_valid_cv_filename_is_kept() -> None:
    assert parse().cv_file == "OF999_Acme_JuniorJava.docx"


def test_fallback_name_is_built_from_clean_parts() -> None:
    assert safe_cv_filename("../x", ("OF1", "Ac/me S.L.", "Dev <b>")) == "OF1_AcmeSL_Dev b.docx".replace(" ", "")
    assert safe_cv_filename(None, ("", "")) is None


# ── Validación general ───────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "data:text/html,x", "file:///etc/passwd", "ftp://x.com", "", "x"]
)
def test_non_http_urls_discard_the_offer(url: str) -> None:
    with pytest.raises(InvalidOfferError, match="URL"):
        parse(url=url)


@pytest.mark.parametrize("raw", [None, [], "texto", 5])
def test_non_object_is_invalid(raw: object) -> None:
    with pytest.raises(InvalidOfferError):
        parse_offer(raw, bullet_count=3)


def test_title_and_company_are_required() -> None:
    with pytest.raises(InvalidOfferError):
        parse(title="")
    with pytest.raises(InvalidOfferError):
        parse(company="   ")
    with pytest.raises(InvalidOfferError):
        parse(title="<b></b>")  # vacío tras sanear


@pytest.mark.parametrize(("raw", "expected"), [(150, 100), (-5, 0), ("82%", 82), ("x", 0), (None, 0), (77.9, 77)])
def test_compatibility_is_clamped(raw: object, expected: int) -> None:
    assert parse(compatibility=raw).compatibility == expected


def test_priority_is_derived_when_invalid() -> None:
    assert parse(priority="Urgente", compatibility=80).priority == "Alta"
    assert parse(priority="", compatibility=70).priority == "Secundaria"


def test_status_cannot_be_set_by_the_model() -> None:
    assert parse(status="Contratada").status == "Pendiente de revisión"


def test_html_and_control_chars_are_stripped() -> None:
    offer = parse(title="Dev <script>alert(1)</script>Java", notes="<img src=x onerror=alert(1)>Hola\x00")
    assert offer.title == "Dev Java"
    assert offer.notes == "Hola"


def test_formula_text_is_preserved_but_never_executable() -> None:
    # El saneado no altera el texto; el Excel lo escribe siempre como cadena (ver test_excel_store).
    assert parse(notes='=HYPERLINK("http://evil")').notes.startswith("=")


def test_bad_date_and_skills_order_fall_back() -> None:
    offer = parse(date="mañana", cv_skills_order="hacker_first")
    assert offer.date == ""
    assert offer.cv_skills_order == "fullstack"


def test_bullets_are_filtered_to_valid_unique_indexes() -> None:
    assert parse(cv_bullets=[2, 2, 9, -1, True, "1", 0]).cv_bullets == [2, 0]
    assert parse(cv_bullets="no es lista").cv_bullets == []


def test_sequence_number_renames_cv_file() -> None:
    renamed = parse().with_sequence_number(42)
    assert renamed.id == "OF042"
    assert renamed.cv_file == "OF042_Acme_JuniorJava.docx"


def test_cv_only_for_good_matches() -> None:
    assert parse(compatibility=80).wants_cv
    assert not parse(compatibility=64).wants_cv
    assert not parse(cv_file=None, compatibility=90).wants_cv
