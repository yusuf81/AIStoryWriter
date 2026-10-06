# Known Issues

Bug dan temuan yang sudah diverifikasi tetapi belum dikerjakan. Kerjakan lewat alur superpowers
(brainstorming → writing-plans → TDD). Hapus entri setelah selesai; riwayatnya ada di git.

Dicatat: 2026-10-06 (saat audit CLAUDE.md).

## 1. `-Seed` hardcoded, `Config.SEED` diabaikan

- **Lokasi:** `Write.py:184`, `Write.py:317`
- **Bukti:** `Parser.add_argument("-Seed", default=12, ...)` lalu `Writer.Config.SEED = Args.Seed`
  pada setiap run baru. Argumen lain memakai `default=Writer.Config.<X>`.
- **Dampak:** Mengubah `SEED` di `Writer/Config.py:194` tidak berpengaruh pada run baru. Saat ini
  tidak terlihat karena keduanya bernilai 12. `SEED` dipakai di `Writer/Interface/Wrapper.py:1697`
  dan `Writer/Chapter/ChapterGenerator.py:331,402,513`.
- **Arah perbaikan:** `default=Writer.Config.SEED`.

## 2. Teks bantuan `-ExpandOutline` terbalik

- **Lokasi:** `Write.py:217-221`
- **Bukti:** help berbunyi "Disables the system from expanding the outline...", padahal flag ini
  menyetel `EXPAND_OUTLINE = True` (`Write.py:342-343`).
- **Dampak:** `python Write.py -h` menyesatkan.
- **Arah perbaikan:** ganti teks menjadi "Enables ...".

## 3. `MAX_PYDANTIC_RETRIES` didefinisikan dua kali

- **Lokasi:** `Writer/Config.py:264` dan `Writer/Config.py:571`
- **Bukti:** keduanya `= 5`; definisi kedua menimpa yang pertama.
- **Dampak:** Mengubah baris 264 tidak berpengaruh apa pun.
- **Arah perbaikan:** hapus salah satu definisi.

## 4. Fixture `mock_interface` mengembalikan objek yang mustahil ada

- **Lokasi:** `tests/conftest.py:50-53`
- **Bukti:** `SafeGeneratePydantic` mengembalikan `Mock` dengan `.text = "mock"` dan `.word_count = 5`.
  Model asli `ChapterOutput` (`Writer/Models.py:34-38`) mewajibkan `text` ≥ 100 karakter dan
  `chapter_number`, dan tidak punya field `word_count`.
- **Dampak:** Kode yang membaca field lain mendapat `Mock` secara diam-diam, sehingga test lulus
  walau integrasi rusak. Fixture dipakai di 60 file test, jadi perubahannya berdampak luas.
- **Arah perbaikan:** kembalikan instance asli dari `Writer/Models.py`. Setelah selesai, hapus
  catatan terkait di bagian Testing CLAUDE.md.

## 5. Change-detector test

- **Lokasi:** `tests/test_config_quality_updates.py` (mis. baris 13:
  `assert Config.OUTLINE_QUALITY == 92`), `tests/test_prompt_word_count_targets.py` (mis. baris 14:
  `assert "600-800 words" in Prompts.CHAPTER_GENERATION_STAGE1`)
- **Dampak:** Test gagal setiap kali nilai/teks sengaja diubah, tetapi tidak menangkap bug.
- **Arah perbaikan:** ganti dengan test perilaku yang bergantung pada nilai tersebut, atau hapus.

## 6. Konfigurasi tooling yang tidak berfungsi

- **`Makefile:53`:** `lint-report: flake8 mypy pyright vulture-report`, padahal target `flake8`,
  `mypy`, dan `pyright` tidak ada, sehingga `make lint-report` gagal.
- **`vulture.toml`:** tidak dibaca vulture (vulture hanya membaca `[tool.vulture]` di
  `pyproject.toml` atau file yang diberikan lewat `--config`). Selain itu `whitelist_files` merujuk
  `Writer/Interface/__init__.py` dan `Writer/Interface/Ollama.py` yang tidak ada.
- **Arah perbaikan:** arahkan `lint-report` ke target `lint`; hapus `vulture.toml` atau pindahkan
  isinya ke `[tool.vulture]` di `pyproject.toml`.

## 7. File test di root repo tidak pernah dijalankan pytest

- **Lokasi:** `test_enhanced_revision.py`, `test_integration_improvements.py`, `test_layout_fix.py`,
  `test_ollama_runpod.py`, `test_paragraph_issue.py`, `test_red_review.py`,
  `test_runpod_endpoints.py`, `test_validation_fixes.py`
- **Bukti:** `pyproject.toml:65` → `testpaths = ["tests"]`.
- **Arah perbaikan:** periksa satu per satu: pindahkan ke `tests/` bila masih relevan, jadikan
  skrip manual di `scripts/` bila memang bukan test, atau hapus.
