# Setup Google Gemini untuk AIStoryWriter

## Langkah 1: Dapatkan API Key

1. Kunjungi: https://makersuite.google.com/app/apikey
2. Login dengan akun Google
3. Klik "Create API Key" atau "Get API Key"
4. Copy API key yang dihasilkan

## Langkah 2: Setup File .env

Edit file `.env` di root folder project (`/var/www/AIStoryWriter/.env`):

```bash
# Google Gemini API Key
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Optional: API keys lainnya (jika tidak dipakai, bisa dikosongkan)
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=

# Ollama settings (jika masih pakai ollama lokal)
OLLAMA_API_BASE=http://localhost:11434
```

**Catatan:** Ganti `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` dengan API key asli Anda!

## Langkah 3: Konfigurasi Model di Config.py

Edit file `Writer/Config.py`, ubah baris `ollamasemua`:

```python
# Comment out model yang lama
# ollamasemua = "aisingapore/Qwen-SEA-LION-v4-32B-IT:latest"

# Uncomment dan pilih salah satu model Gemini:
ollamasemua = "google://gemini-flash-latest"  # Always newest (recommended)
# ollamasemua = "google://gemini-2.5-flash"    # Latest stable, best quality
# ollamasemua = "google://gemini-2.0-flash-exp"  # Experimental features
```

## Langkah 4: Test Story Generation

```bash
# Test dengan prompt sederhana
python Write.py -Prompt Prompts/kuntilanak.txt

# Atau buat prompt baru
echo "Cerita tentang petualangan anak di hutan" > Prompts/test.txt
python Write.py -Prompt Prompts/test.txt
```

## Model Gemini yang Tersedia (2025)

| Model | Kecepatan | Kualitas | Harga | Keterangan |
|-------|-----------|----------|-------|------------|
| `gemini-flash-latest` | ⚡⚡⚡ | ★★★★★ | $ | Always newest, auto-updates |
| `gemini-2.5-flash` | ⚡⚡⚡ | ★★★★★ | $ | Latest stable, 1M tokens |
| `gemini-2.5-pro` | ⚡⚡☆ | ★★★★★ | $$$ | Best quality, slower |
| `gemini-2.0-flash-exp` | ⚡⚡⚡ | ★★★★☆ | $ | Experimental features |

## Troubleshooting

### Error: "No module named 'google.genai'"

Install dependency yang kurang:

```bash
pip install google-genai
# atau
.venv/bin/pip install google-genai
```

### Error: "Invalid API key"

- Pastikan API key sudah benar di file `.env`
- Pastikan tidak ada spasi sebelum/sesudah API key
- Pastikan format: `GOOGLE_API_KEY=AIzaSy...` (tanpa quotes)

### Error: "Rate limit exceeded"

- Gemini free tier memiliki limit request
- Tunggu beberapa menit lalu coba lagi
- Atau upgrade ke paid tier

## Perbandingan dengan Ollama

**Kelebihan Gemini:**
- ✅ Tidak perlu setup server lokal
- ✅ Kualitas output sangat bagus
- ✅ Lebih cepat untuk task kompleks
- ✅ Gratis tier cukup generous

**Kekurangan Gemini:**
- ❌ Membutuhkan koneksi internet
- ❌ Ada rate limit
- ❌ Data dikirim ke Google

**Kelebihan Ollama:**
- ✅ Offline/lokal
- ✅ No rate limit
- ✅ Privacy terjaga
- ✅ Gratis unlimited

**Kekurangan Ollama:**
- ❌ Perlu GPU kuat
- ❌ Setup lebih kompleks
- ❌ Kualitas tergantung model lokal

## Rekomendasi Penggunaan

**Gunakan Gemini jika:**
- Testing/prototyping cepat
- Tidak punya GPU kuat
- Butuh kualitas output terbaik
- OK dengan cloud service

**Gunakan Ollama jika:**
- Punya GPU RTX/high-end
- Butuh privacy/offline
- Generate cerita banyak (no limit)
- Sudah familiar dengan setup Ollama
