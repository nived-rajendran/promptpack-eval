from promptpack_eval.hashing import sha256_file, sha256_text

# Known SHA-256 of the ASCII string "abc".
ABC_SHA = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_sha256_text_known_value():
    assert sha256_text("abc") == ABC_SHA


def test_sha256_text_deterministic_and_sensitive():
    assert sha256_text("prompt") == sha256_text("prompt")
    assert sha256_text("prompt") != sha256_text("prompt ")


def test_sha256_file_matches_text(tmp_path):
    path = tmp_path / "f.txt"
    path.write_text("abc", encoding="utf-8")
    assert sha256_file(path) == ABC_SHA
