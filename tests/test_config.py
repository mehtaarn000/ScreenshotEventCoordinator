from app.config import Settings


def test_allowed_origins_accept_comma_separated_environment_value(monkeypatch) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000, https://gatherly.example.com",
    )

    settings = Settings(_env_file=None)

    assert settings.allowed_origins == [
        "http://localhost:3000",
        "https://gatherly.example.com",
    ]
