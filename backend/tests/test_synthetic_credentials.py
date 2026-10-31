import sys
from pathlib import Path

import pytest

# Ensure dev/keycloak is in sys.path to import generate_synthetic_credentials
REPO_ROOT = Path(__file__).resolve().parents[2]
DEV_KEYCLOAK = REPO_ROOT / "dev" / "keycloak"
if str(DEV_KEYCLOAK) not in sys.path:
    sys.path.insert(0, str(DEV_KEYCLOAK))

import generate_synthetic_credentials as gen  # noqa: E402


@pytest.fixture(autouse=True)
def _bind_repo_root_to_tmp(tmp_path, monkeypatch):
    if hasattr(gen, "REPO_ROOT"):
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)


def test_generate_synthetic_credentials_creates_new_env(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    assert not env_file.exists()

    exit_code = gen.main([])
    assert exit_code == 0
    assert env_file.is_file()

    content = env_file.read_text(encoding="utf-8")
    for var in gen.SECRET_VARS:
        assert f"{var}=" in content
        # Ensure value is non-empty
        val = next(
            line.split("=", 1)[1] for line in content.splitlines() if line.startswith(f"{var}=")
        )
        assert len(val.strip()) >= 20

    captured = capsys.readouterr()
    assert "SUCCESS: Generated per-run synthetic credentials" in captured.out
    for var in gen.SECRET_VARS:
        assert f"- {var}: [SET_REDACTED]" in captured.out


def test_generate_synthetic_credentials_updates_existing_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "PRESERVED_VAR=kept_value\n# KC_BOOTSTRAP_ADMIN_PASSWORD=placeholder\n",
        encoding="utf-8",
    )

    exit_code = gen.main([])
    assert exit_code == 0

    content = env_file.read_text(encoding="utf-8")
    assert "PRESERVED_VAR=kept_value" in content
    assert "# KC_BOOTSTRAP_ADMIN_PASSWORD" not in content
    for var in gen.SECRET_VARS:
        assert f"{var}=" in content


def test_generate_synthetic_credentials_stdout_redaction_safety(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"

    exit_code = gen.main([])
    assert exit_code == 0

    content = env_file.read_text(encoding="utf-8")
    secrets_generated = []
    for line in content.splitlines():
        if "=" in line:
            var, val = line.split("=", 1)
            if var in gen.SECRET_VARS:
                secrets_generated.append(val)

    captured = capsys.readouterr()
    # Confirm secret values NEVER appear in stdout or stderr
    for secret in secrets_generated:
        assert secret not in captured.out
        assert secret not in captured.err


def test_generate_synthetic_credentials_accepts_conventional_env_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exit_code = gen.main(["--env-file", ".env"])
    assert exit_code == 0
    assert (tmp_path / ".env").is_file()


def test_generate_synthetic_credentials_rejects_env_example(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    example_file = tmp_path / ".env.example"
    original_content = "KC_BOOTSTRAP_ADMIN_PASSWORD=CHANGE_ME\n"
    example_file.write_text(original_content, encoding="utf-8")

    exit_code = gen.main(["--env-file", ".env.example"])
    # Must fail safely with non-zero exit code
    assert exit_code != 0

    # .env.example must remain untouched
    assert example_file.read_text(encoding="utf-8") == original_content

    # Output must not print secrets
    captured = capsys.readouterr()
    for var in gen.SECRET_VARS:
        assert f"{var}=" not in captured.out
        assert f"{var}=" not in captured.err


def test_generate_synthetic_credentials_rejects_arbitrary_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    bad_target = tmp_path / "arbitrary_output.env"

    exit_code = gen.main(["--env-file", str(bad_target)])
    assert exit_code != 0
    assert not bad_target.exists()

    captured = capsys.readouterr()
    assert "ERROR" in captured.err or "ERROR" in captured.out

    # Even if named .env, paths outside cwd must be rejected
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()
    sub_env = sub_dir / ".env"
    exit_code_sub = gen.main(["--env-file", str(sub_env)])
    assert exit_code_sub != 0
    assert not sub_env.exists()


def test_generate_synthetic_credentials_safe_failure_on_write_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    env_dir = tmp_path / ".env"
    # Create .env as a directory so writing to it as a file raises OSError / PermissionError
    env_dir.mkdir()

    exit_code = gen.main([])
    assert exit_code != 0

    captured = capsys.readouterr()
    # Confirmation of safe failure without echoing secrets
    for var in gen.SECRET_VARS:
        assert f"{var}=" not in captured.out
        assert f"{var}=" not in captured.err


def test_repo_env_example_untouched():
    repo_example = REPO_ROOT / ".env.example"
    assert repo_example.is_file()
    content = repo_example.read_text(encoding="utf-8")
    assert "CHANGE_ME" in content
    # Ensure no generated random tokens landed in .env.example
    for var in gen.SECRET_VARS:
        for line in content.splitlines():
            if line.startswith(f"{var}="):
                val = line.split("=", 1)[1]
                assert "CHANGE_ME" in val or val == ""


def test_generate_synthetic_credentials_anchors_to_repo_root_from_external_cwd(
    tmp_path, monkeypatch
):
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    external_cwd = tmp_path / "outside"
    external_cwd.mkdir()

    # Explicit seam: anchor repository root to fake_repo
    monkeypatch.setattr(gen, "REPO_ROOT", fake_repo, raising=False)
    monkeypatch.chdir(external_cwd)

    exit_code = gen.main([])
    assert exit_code == 0

    # The repo root .env must be created
    assert (fake_repo / ".env").is_file()
    # The external cwd must receive NO .env
    assert not (external_cwd / ".env").exists()


def test_generate_synthetic_credentials_rejects_external_cwd_env_target(
    tmp_path, monkeypatch, capsys
):
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    external_cwd = tmp_path / "outside"
    external_cwd.mkdir()

    monkeypatch.setattr(gen, "REPO_ROOT", fake_repo, raising=False)
    monkeypatch.chdir(external_cwd)

    # Attempt to target .env in external directory explicitly
    external_env = external_cwd / ".env"
    exit_code = gen.main(["--env-file", str(external_env)])
    assert exit_code != 0
    assert not external_env.exists()

    captured = capsys.readouterr()
    assert "ERROR" in captured.err or "ERROR" in captured.out


def test_generate_synthetic_credentials_accepts_relative_env_from_external_cwd(
    tmp_path, monkeypatch
):
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    external_cwd = tmp_path / "outside"
    external_cwd.mkdir()

    monkeypatch.setattr(gen, "REPO_ROOT", fake_repo, raising=False)
    monkeypatch.chdir(external_cwd)

    exit_code = gen.main(["--env-file", ".env"])
    assert exit_code == 0
    assert (fake_repo / ".env").is_file()
    assert not (external_cwd / ".env").exists()


def test_generate_synthetic_credentials_accepts_absolute_repo_env_from_external_cwd(
    tmp_path, monkeypatch
):
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    external_cwd = tmp_path / "outside"
    external_cwd.mkdir()

    monkeypatch.setattr(gen, "REPO_ROOT", fake_repo, raising=False)
    monkeypatch.chdir(external_cwd)

    exit_code = gen.main(["--env-file", str(fake_repo / ".env")])
    assert exit_code == 0
    assert (fake_repo / ".env").is_file()
    assert not (external_cwd / ".env").exists()


def test_generate_synthetic_credentials_rejects_path_traversal(tmp_path, monkeypatch, capsys):
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    external_cwd = tmp_path / "outside"
    external_cwd.mkdir()

    monkeypatch.setattr(gen, "REPO_ROOT", fake_repo, raising=False)
    monkeypatch.chdir(external_cwd)

    exit_code = gen.main(["--env-file", "../outside/.env"])
    assert exit_code != 0
    assert not (external_cwd / ".env").exists()

    captured = capsys.readouterr()
    assert "ERROR" in captured.err or "ERROR" in captured.out


def test_generate_synthetic_credentials_rejects_symlinked_repo_env(tmp_path, monkeypatch, capsys):
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    external_target = outside_dir / "target.env"
    original_content = "EXTERNAL_KEY=preserved_value\n"
    external_target.write_text(original_content, encoding="utf-8")

    repo_env = fake_repo / ".env"
    symlink_created = False
    try:
        repo_env.symlink_to(external_target)
        symlink_created = True
    except (OSError, NotImplementedError):
        # Platform limitation: Windows non-elevated user may lack SeCreateSymbolicLinkPrivilege
        pass

    monkeypatch.setattr(gen, "REPO_ROOT", fake_repo, raising=False)

    if symlink_created:
        exit_code = gen.main([])
        assert exit_code != 0
        assert external_target.read_text(encoding="utf-8") == original_content

        captured = capsys.readouterr()
        for var in gen.SECRET_VARS:
            assert f"{var}=" not in captured.out
            assert f"{var}=" not in captured.err
    else:
        # Fallback to deterministic unit test around the is_symlink() rejection seam
        assert hasattr(gen, "is_symlink"), "gen must provide an is_symlink rejection seam"
        monkeypatch.setattr(gen, "is_symlink", lambda p: Path(p) == repo_env)
        exit_code = gen.main([])
        assert exit_code != 0
        assert external_target.read_text(encoding="utf-8") == original_content

        captured = capsys.readouterr()
        assert "ERROR" in captured.err or "ERROR" in captured.out
        for var in gen.SECRET_VARS:
            assert f"{var}=" not in captured.out
            assert f"{var}=" not in captured.err


def test_generate_synthetic_credentials_rejects_symlink_alias_target(tmp_path, monkeypatch, capsys):
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    repo_env = fake_repo / ".env"
    alias_path = fake_repo / "symlink_alias.env"

    symlink_created = False
    try:
        alias_path.symlink_to(repo_env)
        symlink_created = True
    except (OSError, NotImplementedError):
        pass

    monkeypatch.setattr(gen, "REPO_ROOT", fake_repo, raising=False)

    if symlink_created:
        exit_code = gen.main(["--env-file", str(alias_path)])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "ERROR" in captured.err or "ERROR" in captured.out
    else:
        assert hasattr(gen, "is_symlink"), "gen must provide an is_symlink rejection seam"
        monkeypatch.setattr(gen, "is_symlink", lambda p: Path(p) == alias_path)
        exit_code = gen.main(["--env-file", str(alias_path)])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "ERROR" in captured.err or "ERROR" in captured.out


def test_resolve_target_env_and_update_reject_symlinks(tmp_path, monkeypatch):
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    repo_env = fake_repo / ".env"
    repo_env.write_text("DUMMY=1\n", encoding="utf-8")

    monkeypatch.setattr(gen, "REPO_ROOT", fake_repo, raising=False)
    assert hasattr(gen, "is_symlink"), "gen must provide an is_symlink rejection seam"
    monkeypatch.setattr(gen, "is_symlink", lambda p: True)

    with pytest.raises(ValueError, match="[Ss]ymlink"):
        gen.resolve_target_env(".env")

    with pytest.raises(ValueError, match="[Ss]ymlink"):
        gen.update_env_file(repo_env)
