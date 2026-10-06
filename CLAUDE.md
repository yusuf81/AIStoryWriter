# CLAUDE.md

AIStoryWriter: generator novel multi-tahap berbasis LLM. Entry point `Write.py` → `Writer/Pipeline.py`.

## Perintah

```bash
python Write.py -Prompt Docs/examples/ShortDebuggingStory/Prompt.txt   # contoh lain: Docs/examples/*/Prompt.txt
python Write.py -Resume Logs/Generation_<timestamp>/run.state.json     # + -ForceResume jika status bukan in_progress
python Evaluate.py -Story1 a.json -Story2 b.json -Model "ollama://<model>"

pytest tests/<path>/test_x.py::test_name   # saat iterasi
pytest                                     # sebelum menyatakan selesai
flake8 --ignore=E501,W504,W503 <file>      # setiap file yang diubah
pyright <file>
make vulture                               # dead code; laporan: make vulture-report → reports/
```

## Konfigurasi & gotcha

- `Writer/Config.py` adalah sumber semua default: model, ambang kualitas, feature flag.
- Flag boolean CLI hanya bisa **mengaktifkan**. `EXPAND_OUTLINE`, `SCENE_GENERATION_PIPELINE`,
  `ENABLE_FINAL_EDIT_PASS`, `ENABLE_PDF_GENERATION` sudah `True`, jadi mematikannya hanya lewat Config.py.
  Yang bisa mematikan dari CLI: `-NoChapterRevision`, `-NoScrubChapters`.
- Saat `-Resume`, flag CLI diabaikan dan semua konstanta Config dipulihkan dari `run.state.json`;
  mengubah Config.py tidak memengaruhi run yang di-resume.
- Format model: `provider://model@host?param=value`. Provider: `ollama` (default bila tanpa prefix),
  `google`, `openrouter`, `grok`, `synthetic`, `vllm`. API key di `.env` (lihat `.env.example`).
- IMPORTANT: tahap bertanda `[STRUCTURED]` di Config.py memakai `SafeGeneratePydantic`;
  modelnya wajib mendukung output JSON terstruktur, jika tidak akan crash.
- Jangan ubah `ollamasemua` atau pilihan model lain kecuali diminta.
- Bahasa prompt default `NATIVE_LANGUAGE = "id"` → `Writer/Prompts_id.py`; `Writer/Prompts.py` untuk Inggris.

## Checklist dampak

Sebelum mengubah, telusuri semua titik yang ikut terdampak:
- Teks prompt → `Prompts.py` **dan** `Prompts_id.py`, placeholder identik.
- Model Pydantic (`Writer/Models.py`) → contoh output di `_LANGUAGE_STRINGS`
  (`Writer/Interface/Wrapper.py`, bagian `en` dan `id`).
- Konstanta Config baru → argumen CLI di `Write.py` bila perlu; konstanta otomatis ikut tersimpan di state.
- Langkah pipeline baru → `last_completed_step` dan percabangan resume di `Writer/Pipeline.py`.

## Pakai ulang (DRY)

- Cari helper yang ada sebelum menulis baru: `PromptsHelper` (modul prompt sesuai bahasa, validasi
  placeholder), `StateManager` (simpan/muat state berisi objek Pydantic), `FieldConstants`
  (klasifikasi field/section/error), `ContentValidator` (deteksi penyusutan konten), fixture di `tests/conftest.py`.
- DRY berlaku untuk pengetahuan, bukan kemiripan teks: `Prompts.py` dan `Prompts_id.py` sengaja paralel; jangan digabung.

## Testing (pelengkap skill TDD superpowers)

- Mock hanya batas eksternal: panggilan LLM (`Interface.SafeGenerate*`), Lorebook/ChromaDB/embedding,
  klien API, `time.sleep`.
- Mock LLM mengembalikan instance asli dari `Writer/Models.py`, bukan `Mock`. Fixture `mock_interface`
  masih mengembalikan `Mock`; timpa `return_value`-nya.
- Pakai versi asli: model Pydantic, Config (atur nilai dengan `monkeypatch.setattr`), filesystem (`tmp_path`),
  `StateManager`, `MarkdownProcessor`.
- Jangan uji nilai konstanta Config atau keberadaan teks di prompt. Uji perilaku dan kontrak:
  placeholder ter-render, kunci `Prompts.py` = `Prompts_id.py`.
- Test baru di `tests/`; file `test_*.py` di root repo tidak dikoleksi pytest.

## Cara kerja

- Grounded: baca kode atau sumber library sebelum memakai API-nya; dukung setiap klaim dengan
  `file:line` atau output perintah.
- Sederhana ≠ diff terkecil: selesaikan akar masalah di semua tempat terdampak, pakai ulang kode yang ada,
  jangan tambah fitur yang tidak diminta (YAGNI).
- Sebelum mengubah sebuah file, perbaiki error flake8/pyright yang sudah ada di file itu dalam commit
  terpisah (`chore: ...`), lalu jalankan `pytest`. Perbaikan yang mengubah perilaku runtime tetap lewat TDD.
- Laporan: ringkasan perubahan + bukti (perintah test/lint dan hasilnya).
- Pesan commit dalam bahasa Indonesia, deskriptif.
- Dead code: false positive vulture yang umum adalah field/validator Pydantic (`Writer/Models.py`,
  `Evaluate.py`) dan kode di balik flag Config. Verifikasi manual sebelum menghapus.
- Bug/temuan yang belum dikerjakan dicatat di `docs/known-issues.md`.
