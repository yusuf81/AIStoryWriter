
CHAPTER_COUNT_PROMPT = """
<OUTLINE>
{_Summary}
</OUTLINE>

Harap berikan respons berformat JSON yang berisi jumlah total bab dalam outline di atas.
Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.

Balas dengan format objek JSON berikut:
{{"TotalChapters": <jumlah total bab>}}

Harap jangan sertakan teks lain, hanya objek JSON karena respons Anda akan diparsing oleh komputer. Seluruh respons Anda harus hanya objek JSON.
"""

CHAPTER_GENERATION_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."

CHAPTER_GENERATION_PROMPT = """
Harap bantu saya mengekstrak bagian dari outline ini yang hanya untuk bab {_ChapterNum}.
Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.

<OUTLINE>
{_Outline}
</OUTLINE>

Jangan sertakan hal lain dalam respons Anda kecuali hanya konten untuk bab {_ChapterNum}.
"""

CHAPTER_HISTORY_INSERT = """
Harap bantu saya menulis novel saya.

Saya mendasarkan pekerjaan saya pada outline ini:

<OUTLINE>
{_Outline}
</OUTLINE>

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
"""

CHAPTER_SUMMARY_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."

CHAPTER_SUMMARY_PROMPT = """
Saya sedang menulis bab berikutnya dalam novel saya (bab {_ChapterNum}), dan saya telah menulis sejauh ini.

Outline saya:
<OUTLINE>
{_Outline}
</OUTLINE>

Dan apa yang telah saya tulis di bab terakhir:
<PREVIOUS_CHAPTER>
{_LastChapter}
</PREVIOUS_CHAPTER>

Harap buat daftar poin ringkasan penting dari bab terakhir sehingga saya tahu apa yang harus diingat saat menulis bab ini.
Pastikan juga untuk menambahkan ringkasan dari bab sebelumnya, dan fokus pada pencatatan poin plot penting, dan keadaan cerita saat bab berakhir.
Dengan begitu, ketika saya menulis, saya akan tahu di mana harus melanjutkannya.

Berikut beberapa panduan format:

```
Bab Sebelumnya:
    - Plot:
        - Ringkasan poin Anda di sini dengan detail sebanyak yang dibutuhkan
    - Latar:
        - beberapa hal di sini
    - Karakter:
        - karakter 1
            - info tentang mereka, dari bab itu
            - jika mereka berubah, bagaimana caranya

Hal yang Perlu Diingat:
    - sesuatu yang dilakukan bab sebelumnya untuk memajukan plot, jadi kita memasukkannya ke bab berikutnya
    - sesuatu yang lain yang penting untuk diingat saat menulis bab berikutnya
    - hal lain
    - dll.
```

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Terima kasih telah membantu saya menulis cerita saya! Harap hanya sertakan ringkasan Anda dan hal-hal yang perlu diingat, jangan menulis hal lain.
"""

GET_IMPORTANT_BASE_PROMPT_INFO = """
Harap ekstrak informasi penting apa pun dari prompt pengguna di bawah ini:

<USER_PROMPT>
{_Prompt}
</USER_PROMPT>

Cukup tuliskan informasi apa pun yang tidak akan tercakup dalam outline.
Harap gunakan templat di bawah ini untuk memformat respons Anda.
Ini akan menjadi hal-hal seperti instruksi untuk panjang bab, visi keseluruhan, instruksi untuk format, dll.
(Jangan gunakan tag xml - itu hanya contoh)

<EXAMPLE>
# Konteks Tambahan Penting
- Poin penting 1
- Poin penting 2
</EXAMPLE>

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
JANGAN tulis outline itu sendiri, hanya beberapa konteks tambahan. Buat respons Anda singkat.
"""

CHAPTER_GENERATION_STAGE1 = """
{ContextHistoryInsert}

{_BaseContext}

Harap tulis plot untuk bab {_ChapterNum} dari {_TotalChapters} berdasarkan outline bab berikut dan bab-bab sebelumnya.
Perhatikan bab-bab sebelumnya, dan pastikan Anda melanjutkannya dengan mulus, Sangat penting bahwa tulisan Anda terhubung dengan baik dengan bab sebelumnya, dan mengalir ke bab berikutnya (jadi cobalah untuk mengikuti outline)!

Berikut adalah outline saya untuk bab ini:
<CHAPTER_OUTLINE>
{ThisChapterOutline}
</CHAPTER_OUTLINE>

{FormattedLastChapterSummary}

Saat Anda menulis karya Anda, harap gunakan saran berikut untuk membantu Anda menulis bab {_ChapterNum} (pastikan Anda hanya menulis yang ini):
    - Laju:
    - Apakah Anda melewatkan hari sekaligus? Meringkas peristiwa? Jangan lakukan itu, tambahkan adegan untuk merincinya.
    - Apakah cerita terlalu cepat melewati poin plot tertentu dan terlalu fokus pada yang lain?
    - Alur: Apakah setiap bab mengalir ke bab berikutnya? Apakah plot masuk akal secara logis bagi pembaca? Apakah memiliki struktur naratif tertentu yang dimainkan? Apakah struktur naratif konsisten di seluruh cerita?
    - Genre: Apa genrenya? Bahasa apa yang sesuai untuk genre itu? Apakah adegan mendukung genre tersebut?

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
{Feedback}"""

CHAPTER_GENERATION_STAGE2 = """
{ContextHistoryInsert}

{_BaseContext}

Harap tulis pengembangan karakter untuk bab berikut {_ChapterNum} dari {_TotalChapters} berdasarkan kriteria berikut dan bab-bab sebelumnya.
Perhatikan bab-bab sebelumnya, dan pastikan Anda melanjutkannya dengan mulus, Sangat penting bahwa tulisan Anda terhubung dengan baik dengan bab sebelumnya, dan mengalir ke bab berikutnya (jadi cobalah untuk mengikuti outline)!

Jangan mengambil konten, sebaliknya perluas untuk membuat output yang lebih panjang dan lebih detail.

Sebagai referensi Anda, berikut adalah outline saya untuk bab ini:
<CHAPTER_OUTLINE>
{ThisChapterOutline}
</CHAPTER_OUTLINE>

{FormattedLastChapterSummary}

Dan inilah yang saya miliki untuk plot bab saat ini:
<CHAPTER_PLOT>
{Stage1Chapter}
</CHAPTER_PLOT>

Sebagai pengingat untuk mengingat kriteria berikut saat Anda memperluas karya di atas:
    - Karakter: Siapa karakter dalam bab ini? Apa arti mereka satu sama lain? Bagaimana situasi di antara mereka? Apakah itu konflik? Apakah ada ketegangan? Apakah ada alasan karakter-karakter tersebut disatukan?
    - Pengembangan: Apa tujuan masing-masing karakter, dan apakah mereka mencapai tujuan tersebut? Apakah karakter berubah dan menunjukkan pertumbuhan? Apakah tujuan masing-masing karakter berubah sepanjang cerita?
    - Detail: Bagaimana hal-hal dijelaskan? Apakah berulang? Apakah pilihan kata sesuai untuk adegan tersebut? Apakah kita menjelaskan hal-hal terlalu banyak atau terlalu sedikit?

Jangan menjawab pertanyaan-pertanyaan ini secara langsung, sebaliknya buat tulisan Anda secara implisit menjawabnya. (Tunjukkan, jangan beri tahu)

Pastikan bab Anda mengalir ke bab berikutnya dan dari bab sebelumnya (jika berlaku).

Ingat, bersenang-senanglah, berkreasilah, dan tingkatkan pengembangan karakter bab {_ChapterNum} (pastikan Anda hanya menulis yang ini)!

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
{Feedback}"""

CHAPTER_GENERATION_STAGE3 = """
{ContextHistoryInsert}

{_BaseContext}

Harap tambahkan dialog pada bab berikut {_ChapterNum} dari {_TotalChapters} berdasarkan kriteria berikut dan bab-bab sebelumnya.
Perhatikan bab-bab sebelumnya, dan pastikan Anda melanjutkannya dengan mulus, Sangat penting bahwa tulisan Anda terhubung dengan baik dengan bab sebelumnya, dan mengalir ke bab berikutnya (jadi cobalah untuk mengikuti outline)!

Jangan mengambil konten, sebaliknya perluas untuk membuat output yang lebih panjang dan lebih detail.


{FormattedLastChapterSummary}

Inilah yang saya miliki sejauh ini untuk bab ini:
<CHAPTER_CONTENT>
{Stage2Chapter}
</CHAPTER_CONTENT>

Sebagai pengingat untuk mengingat kriteria berikut:
    - Dialog: Apakah dialog masuk akal? Apakah sesuai dengan situasi? Apakah laju masuk akal untuk adegan tersebut Misalnya: (Apakah lajunya cepat karena mereka berlari, atau lambat karena mereka makan malam romantis)?
    - Gangguan: Jika alur dialog terganggu, apa alasan gangguan tersebut? Apakah itu rasa urgensi? Apa yang menyebabkan gangguan tersebut? Bagaimana pengaruhnya terhadap dialog ke depan?
     - Laju:
       - Apakah Anda melewatkan hari sekaligus? Meringkas peristiwa? Jangan lakukan itu, tambahkan adegan untuk merincinya.
       - Apakah cerita terlalu cepat melewati poin plot tertentu dan terlalu fokus pada yang lain?

Jangan menjawab pertanyaan-pertanyaan ini secara langsung, sebaliknya buat tulisan Anda secara implisit menjawabnya. (Tunjukkan, jangan beri tahu)

Pastikan bab Anda mengalir ke bab berikutnya dan dari bab sebelumnya (jika berlaku).

Juga, harap hapus semua judul dari outline yang mungkin masih ada di bab tersebut.

Ingat, bersenang-senanglah, berkreasilah, dan tambahkan dialog ke bab {_ChapterNum} (pastikan Anda hanya menulis yang ini)!

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
{Feedback}"""

CHAPTER_REVISION = """
Harap revisi bab berikut:

<CHAPTER_CONTENT>
{_Chapter}
</CHAPTER_CONTENT>

Berdasarkan umpan balik berikut:
<FEEDBACK>
{_Feedback}
</FEEDBACK>
Jangan merefleksikan revisi, cukup tulis bab yang ditingkatkan yang membahas umpan balik dan kriteria prompt.
Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Ingatlah untuk tidak menyertakan catatan penulis apa pun."""

SUMMARY_CHECK_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."

SUMMARY_CHECK_PROMPT = """
Harap ringkas bab berikut:

<CHAPTER>
{_Work}
</CHAPTER>

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Jangan sertakan apa pun dalam respons Anda kecuali ringkasan."""

SUMMARY_OUTLINE_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."

SUMMARY_OUTLINE_PROMPT = """
Harap ringkas outline bab berikut:

<OUTLINE>
{_RefSummary}
</OUTLINE>

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Jangan sertakan apa pun dalam respons Anda kecuali ringkasan."""

SUMMARY_COMPARE_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."

SUMMARY_COMPARE_PROMPT = """
Harap bandingkan ringkasan bab yang disediakan dan outline terkait, dan tunjukkan apakah konten yang disediakan secara kasar mengikuti outline.

Harap tulis respons berformat JSON tanpa konten lain dengan kunci-kunci berikut.
Catatan bahwa komputer mem-parsing JSON ini jadi harus benar.

<CHAPTER_SUMMARY>
{WorkSummary}
</CHAPTER_SUMMARY>

<OUTLINE>
{OutlineSummary}
</OUTLINE>

Pastikan semua nilai teks dalam JSON (khususnya 'Suggestions') ditulis dalam Bahasa Indonesia. Kunci JSON harus tetap dalam Bahasa Inggris.
Harap balas dengan field JSON berikut:

{{
    "Suggestions": str,
    "DidFollowOutline": true/false
}}

"Suggestions" harus berisi string berisi umpan balik terperinci berformat markdown yang akan digunakan untuk memandu penulis pada iterasi generasi berikutnya.
Sebutkan hal-hal umum yang akan membantu penulis mengingat apa yang harus dilakukan pada iterasi berikutnya.
Penulis tidak akan melihat bab saat ini, jadi umpan balik khusus untuk bab ini tidak membantu, sebaliknya sebutkan area di mana ia perlu memperhatikan prompt atau outline.
Penulis juga tidak mengetahui setiap iterasi - jadi berikan informasi terperinci dalam prompt yang akan membantunya.
Mulai saran Anda dengan 'Hal-hal penting yang perlu diingat saat Anda menulis: \n'.

Tidak apa-apa jika ringkasannya bukan pasangan yang sempurna, tetapi harus memiliki plot dan laju yang kurang lebih sama.

Sekali lagi, ingatlah untuk membuat respons Anda *hanya* objek JSON tanpa kata atau format tambahan. Ini akan langsung dimasukkan ke parser JSON.
"""

CRITIC_OUTLINE_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."

CRITIC_OUTLINE_PROMPT = """
Harap kritik outline berikut - pastikan untuk memberikan kritik konstruktif tentang bagaimana outline tersebut dapat ditingkatkan dan tunjukkan masalah apa pun dengannya.

<OUTLINE>
{_Outline}
</OUTLINE>

Saat Anda merevisi, pertimbangkan kriteria berikut:
    - Laju: Apakah cerita terlalu cepat melewati poin plot tertentu dan terlalu fokus pada yang lain?
    - Detail: Bagaimana hal-hal dijelaskan? Apakah berulang? Apakah pilihan kata sesuai untuk adegan tersebut? Apakah kita menjelaskan hal-hal terlalu banyak atau terlalu sedikit?
    - Alur: Apakah setiap bab mengalir ke bab berikutnya? Apakah plot masuk akal secara logis bagi pembaca? Apakah memiliki struktur naratif tertentu yang dimainkan? Apakah struktur naratif konsisten di seluruh cerita?
    - Genre: Apa genrenya? Bahasa apa yang sesuai untuk genre itu? Apakah adegan mendukung genre tersebut?

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Juga, harap periksa apakah outline ditulis bab demi bab, bukan dalam bagian yang mencakup beberapa bab atau subbagian.
Harus sangat jelas bab mana yang mana, dan konten di setiap bab."""

OUTLINE_COMPLETE_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."
OUTLINE_COMPLETE_PROMPT = """
<OUTLINE>
{_Outline}
</OUTLINE>

Outline ini memenuhi semua kriteria berikut (benar atau salah):
    - Laju: Apakah cerita terlalu cepat melewati poin plot tertentu dan terlalu fokus pada yang lain?
    - Detail: Bagaimana hal-hal dijelaskan? Apakah berulang? Apakah pilihan kata sesuai untuk adegan tersebut? Apakah kita menjelaskan hal-hal terlalu banyak atau terlalu sedikit?
    - Alur: Apakah setiap bab mengalir ke bab berikutnya? Apakah plot masuk akal secara logis bagi pembaca? Apakah memiliki struktur naratif tertentu yang dimainkan? Apakah struktur naratif konsisten di seluruh cerita?
    - Genre: Apa genrenya? Bahasa apa yang sesuai untuk genre itu? Apakah adegan mendukung genre tersebut?

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Berikan respons berformat JSON dengan struktur berikut:
{{"IsComplete": true/false}}

Harap jangan sertakan teks lain, hanya objek JSON karena respons Anda akan diparsing oleh komputer. Seluruh respons Anda harus hanya objek JSON.
"""

CRITIC_CHAPTER_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."
CRITIC_CHAPTER_PROMPT = """<CHAPTER>
{_Chapter}
</CHAPTER>

Harap berikan umpan balik pada bab di atas berdasarkan kriteria berikut:
    - Laju: Apakah cerita terlalu cepat melewati poin plot tertentu dan terlalu fokus pada yang lain?
    - Detail: Bagaimana hal-hal dijelaskan? Apakah berulang? Apakah pilihan kata sesuai untuk adegan tersebut? Apakah kita menjelaskan hal-hal terlalu banyak atau terlalu sedikit?
    - Alur: Apakah setiap bab mengalir ke bab berikutnya? Apakah plot masuk akal secara logis bagi pembaca? Apakah memiliki struktur naratif tertentu yang dimainkan? Apakah struktur naratif konsisten di seluruh cerita?
    - Genre: Apa genrenya? Bahasa apa yang sesuai untuk genre itu? Apakah adegan mendukung genre tersebut?

    - Karakter: Siapa karakter dalam bab ini? Apa arti mereka satu sama lain? Bagaimana situasi di antara mereka? Apakah itu konflik? Apakah ada ketegangan? Apakah ada alasan karakter-karakter tersebut disatukan?
    - Pengembangan: Apa tujuan masing-masing karakter, dan apakah mereka mencapai tujuan tersebut? Apakah karakter berubah dan menunjukkan pertumbuhan? Apakah tujuan masing-masing karakter berubah sepanjang cerita?

    - Dialog: Apakah dialog masuk akal? Apakah sesuai dengan situasi? Apakah laju masuk akal untuk adegan tersebut Misalnya: (Apakah lajunya cepat karena mereka berlari, atau lambat karena mereka makan malam romantis)?
    - Gangguan: Jika alur dialog terganggu, apa alasan gangguan tersebut? Apakah itu rasa urgensi? Apa yang menyebabkan gangguan tersebut? Bagaimana pengaruhnya terhadap dialog ke depan?
Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
"""

CHAPTER_COMPLETE_INTRO = "Anda adalah Asisten AI yang membantu. Jawab prompt pengguna sebaik mungkin. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."
CHAPTER_COMPLETE_PROMPT = """

<CHAPTER>
{_Chapter}
</CHAPTER>

Bab ini memenuhi semua kriteria berikut (benar atau salah):
    - Laju: Apakah cerita terlalu cepat melewati poin plot tertentu dan terlalu fokus pada yang lain?
    - Detail: Bagaimana hal-hal dijelaskan? Apakah berulang? Apakah pilihan kata sesuai untuk adegan tersebut? Apakah kita menjelaskan hal-hal terlalu banyak atau terlalu sedikit?
    - Alur: Apakah setiap bab mengalir ke bab berikutnya? Apakah plot masuk akal secara logis bagi pembaca? Apakah memiliki struktur naratif tertentu yang dimainkan? Apakah struktur naratif konsisten di seluruh cerita?
    - Genre: Apa genrenya? Bahasa apa yang sesuai untuk genre itu? Apakah adegan mendukung genre tersebut?

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Berikan respons berformat JSON dengan struktur berikut:
{{"IsComplete": true/false}}

Harap jangan sertakan teks lain, hanya objek JSON karena respons Anda akan diparsing oleh komputer. Seluruh respons Anda harus hanya objek JSON.
"""

CHAPTER_EDIT_PROMPT = """
<OUTLINE>
{_Outline}
</OUTLINE>

<ADJACENT_CHAPTERS_CONTEXT>
{NovelText}
</ADJACENT_CHAPTERS_CONTEXT>

# Tugas: Edit Bab {i} untuk Koherensi Lokal

Anda diberikan outline cerita keseluruhan dan cuplikan konteks yang berisi bab tepat sebelum bab {i} (jika ada), bab {i} itu sendiri (sebelum diedit), dan bab tepat setelah bab {i} (jika ada).

Tujuan Anda adalah mengedit konten bab {i} (ditemukan dalam <ADJACENT_CHAPTERS_CONTEXT>) untuk memastikan alurnya lancar dari bab sebelumnya, mengarah secara efektif ke bab berikutnya, dan selaras dengan <OUTLINE> cerita yang disediakan.

Fokus pada:
- Menjaga konsistensi dalam plot, karakterisasi, dan nada dengan bab-bab yang berdekatan.
- Memastikan peristiwa dalam bab {i} secara logis menghubungkan bab sebelumnya dan berikutnya.
- Menyempurnakan prosa untuk kejelasan dan dampak dalam konteks lokal ini.
- Memperbaiki referensi yang salah ke nomor bab dalam teks bab {i} itu sendiri (pastikan secara konsisten merujuk sebagai bab {i}).

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Kembalikan hanya teks lengkap yang telah diedit untuk bab {i}.
"""

INITIAL_OUTLINE_PROMPT = """
Harap tulis outline berformat markdown berdasarkan prompt berikut:

<PROMPT>
{_OutlinePrompt}
</PROMPT>

<ELEMENTS>
{StoryElements}
</ELEMENTS>

Saat Anda menulis, ingatlah untuk bertanya pada diri sendiri pertanyaan berikut:
    - Apa konfliknya?
    - Siapa karakternya (setidaknya dua karakter)?
    - Apa arti karakter satu sama lain?
    - Di mana kita berada?
    - Apa taruhannya (apakah tinggi, apakah rendah, apa yang dipertaruhkan di sini)?
    - Apa tujuan atau solusi dari konflik tersebut?

Jangan menjawab pertanyaan-pertanyaan ini secara langsung, sebaliknya buat outline Anda secara implisit menjawabnya. (Tunjukkan, jangan beri tahu)

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Harap jaga agar outline Anda jelas mengenai konten apa yang ada di bab mana.
Pastikan untuk menambahkan banyak detail saat Anda menulis.

Juga, sertakan informasi tentang karakter yang berbeda, dan bagaimana mereka berubah selama cerita.
Kami ingin memiliki pengembangan karakter yang kaya dan kompleks!"""

OUTLINE_REVISION_PROMPT = """
Harap revisi outline berikut:
<OUTLINE>
{_Outline}
</OUTLINE>

Berdasarkan umpan balik berikut:
<FEEDBACK>
{_Feedback}
</FEEDBACK>

Ingatlah untuk memperluas outline Anda dan menambahkan konten untuk menjadikannya sebaik mungkin!


Saat Anda menulis, ingatlah hal berikut:
    - Apa konfliknya?
    - Siapa karakternya (setidaknya dua karakter)?
    - Apa arti karakter satu sama lain?
    - Di mana kita berada?
    - Apa taruhannya (apakah tinggi, apakah rendah, apa yang dipertaruhkan di sini)?
    - Apa tujuan atau solusi dari konflik tersebut?


Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Harap jaga agar outline Anda jelas mengenai konten apa yang ada di bab mana.
Pastikan untuk menambahkan banyak detail saat Anda menulis.

Jangan menjawab pertanyaan-pertanyaan ini secara langsung, sebaliknya buat tulisan Anda secara implisit menjawabnya. (Tunjukkan, jangan beri tahu)
"""

CHAPTER_OUTLINE_PROMPT = """
Harap hasilkan outline untuk bab {_Chapter} berdasarkan outline yang disediakan.

<OUTLINE>
{_Outline}
</OUTLINE>

Saat Anda menulis, ingatlah hal berikut:
    - Apa konfliknya?
    - Siapa karakternya (setidaknya dua karakter)?
    - Apa arti karakter satu sama lain?
    - Di mana kita berada?
    - Apa taruhannya (apakah tinggi, apakah rendah, apa yang dipertaruhkan di sini)?
    - Apa tujuan atau solusi dari konflik tersebut?

Ingatlah untuk mengikuti outline yang disediakan saat membuat outline bab Anda.

Jangan menjawab pertanyaan-pertanyaan ini secara langsung, sebaliknya buat outline Anda secara implisit menjawabnya. (Tunjukkan, jangan beri tahu)

Harap bagi respons Anda menjadi adegan-adegan, yang masing-masing memiliki format berikut (harap ulangi format adegan untuk setiap adegan dalam bab (minimal 3):

# Bab {_Chapter}

## Adegan: [Judul Adegan Singkat]

- **Karakter & Latar:**
  - Karakter: [Nama Karakter] - [Deskripsi Singkat]
  - Lokasi: [Lokasi Adegan]
  - Waktu: [Kapan adegan berlangsung]

- **Konflik & Nada:**
  - Konflik: [Jenis & Deskripsi]
  - Nada: [Nada emosional]

- **Peristiwa & Dialog Kunci:**
  - [Jelaskan secara singkat peristiwa, tindakan, atau dialog penting]

- **Perangkat Sastra:**
  - [Firasat, simbolisme, atau perangkat lain, jika ada]

- **Resolusi & Pengantar:**
  - [Bagaimana adegan berakhir dan terhubung ke adegan berikutnya]

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Sekali lagi, jangan menulis bab itu sendiri, cukup buat outline bab yang detail.

Pastikan bab Anda memiliki nama berformat markdown!
"""

CHAPTER_SCRUB_PROMPT = """
<CHAPTER>
{_Chapter}
</CHAPTER>

Mengingat bab di atas, harap bersihkan sehingga siap untuk diterbitkan.
Artinya, harap hapus semua sisa outline atau komentar editorial hanya menyisakan cerita yang sudah jadi.

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Jangan mengomentari tugas Anda, karena output Anda akan menjadi versi cetak final.
"""

STATS_PROMPT = """
Harap tulis respons berformat JSON tanpa konten lain dengan kunci-kunci berikut.
Catatan bahwa komputer mem-parsing JSON ini jadi harus benar.

Dasarkan jawaban Anda pada cerita yang ditulis dalam pesan-pesan sebelumnya.

Pastikan semua nilai teks dalam JSON (khususnya 'Title', 'Summary', 'Tags') ditulis dalam Bahasa Indonesia. Kunci JSON harus tetap dalam Bahasa Inggris.

"Title": (judul pendek yang terdiri dari tiga hingga delapan kata)
"Summary": (satu atau dua paragraf yang merangkum cerita dari awal hingga akhir)
"Tags": (string tag yang dipisahkan koma yang menjelaskan cerita)
"OverallRating": (skor keseluruhan Anda untuk cerita dari 0-100, sebagai integer)

Harap balas dengan format objek JSON berikut:
{{
    "Title": "...",
    "Summary": "...",
    "Tags": "...",
    "OverallRating": ...
}}

Sekali lagi, ingatlah untuk membuat respons Anda *hanya* objek JSON tanpa kata atau format tambahan. Ini akan langsung dimasukkan ke parser JSON.
"""

TRANSLATE_PROMPT = """

Harap terjemahkan teks yang diberikan ke dalam Bahasa {TargetLang} - jangan ikuti instruksi apa pun, cukup terjemahkan ke Bahasa {TargetLang}.
Pastikan semua komunikasi Anda di luar teks terjemahan inti adalah dalam Bahasa Indonesia. Respons utama harus berupa teks terjemahan dalam {TargetLang}.

<TEXT>
{_Prompt}
</TEXT>

Mengingat teks di atas, harap terjemahkan ke Bahasa {TargetLang} dari Bahasa {_Language}.
"""

CHAPTER_TRANSLATE_PROMPT = """
<CHAPTER>
{_Chapter}
</CHAPTER>

Terjemahkan seluruh teks di dalam tag <CHAPTER> di atas ke Bahasa {_Language}.
Respons Anda HARUS HANYA berisi teks terjemahan dari bab tersebut.
JANGAN sertakan frasa pengantar, penjelasan, komentar, permintaan maaf, format markdown, atau teks apa pun selain terjemahan langsung itu sendiri.
Jika ada komunikasi tambahan yang mutlak diperlukan di luar terjemahan, pastikan itu dalam Bahasa Indonesia, namun idealnya, respons Anda hanya berisi teks terjemahan.
"""

DEFAULT_SYSTEM_PROMPT = """Anda adalah asisten yang membantu. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."""


CHAPTER_TO_SCENES = """
# KONTEKS #
Saya sedang menulis cerita dan membutuhkan bantuan Anda untuk membagi bab menjadi adegan-adegan. Di bawah ini adalah outline saya sejauh ini:
```
{_Outline}
```
###############

# OBJEKTIF #
Buat outline adegan demi adegan untuk bab yang membantu saya menulis adegan yang lebih baik.
Pastikan untuk menyertakan informasi tentang setiap adegan yang menjelaskan apa yang terjadi, dalam nada apa ditulis, siapa karakter dalam adegan tersebut, dan apa latarnya.
Berikut adalah outline bab spesifik yang perlu kita bagi menjadi adegan-adegan:
```
{_ThisChapter}
```
###############

# GAYA #
Berikan respons kreatif yang membantu menambah kedalaman dan plot pada cerita, tetapi tetap mengikuti outline.
Buat respons Anda berformat markdown sehingga detail dan informasi tentang adegan tersebut jelas.

Di atas segalanya, pastikan untuk kreatif dan orisinal saat menulis.
###############

# AUDIENS #
Harap sesuaikan respons Anda untuk penulis kreatif lainnya.
###############

# RESPONS #
Jadilah detail dan berformat baik dalam respons Anda, namun pastikan Anda memiliki output yang dipikirkan dengan matang dan kreatif.
Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
###############
"""


# Prompts moved from Write.py
EXPAND_OUTLINE_CHAPTER_BY_CHAPTER = """
# Objektif
Tinjau outline cerita lengkap yang disediakan di bawah ini. Tugas Anda adalah menyempurnakan dan menyusunnya dengan jelas berdasarkan bab per bab, memastikan tujuan inti setiap bab jelas sebelum kita melanjutkan ke perincian adegan yang detail.

# Outline Input
<OUTLINE>
{_Outline}
</OUTLINE>

# Tugas
1.  **Verifikasi Struktur Bab:** Pastikan outline dibagi dengan jelas menjadi bab-bab yang berbeda. Jika ada bagian yang tampak ambigu atau mencakup beberapa bab, susun ulang secara logis.
2.  **Identifikasi Tujuan Bab:** Untuk setiap bab, tambahkan komentar atau judul singkat (1 kalimat) yang menunjukkan fungsi naratif utamanya (misalnya, "Memperkenalkan Konflik", "Fokus Pengembangan Karakter", "Aksi Meningkat", "Pengaturan Klimaks", "Resolusi Subplot").
3.  **Pastikan Detail Cukup (Tingkat Tinggi):** Periksa apakah setiap deskripsi bab memberikan detail tingkat tinggi yang cukup tentang peristiwa kunci atau perkembangan karakter dalam bab tersebut. Jika deskripsi bab terlalu samar, tambahkan 1-2 kalimat detail klarifikasi (JANGAN pecah menjadi adegan dulu).

# Format Output
Hasilkan outline yang disempurnakan dan terstruktur berdasarkan bab dalam format Markdown. Gunakan judul yang jelas untuk setiap bab (misalnya, `## Bab 1: Pendahuluan dan Insiden Pemicu`).

# Contoh Cuplikan Output:
```markdown
## Bab 1: Pendahuluan dan Insiden Pemicu
- Perkenalkan protagonis Alice dalam kehidupan biasanya.
- Tetapkan latar awal: Neo-Veridia futuristik.
- Rincian penemuan artefak misterius (insiden pemicu).
- Isyaratkan taruhan awal dan keengganan Alice.

## Bab 2: Aksi Meningkat dan Rintangan Pertama
- *Tujuan: Mengembangkan konflik awal dan memperkenalkan pengaruh antagonis.*
- Alice mencari informasi tentang artefak, menghadapi rintangan kecil.
- Pertemuan pertama (tidak langsung) dengan agen antagonis.
- Alice memutuskan untuk melindungi artefak, mengatasi ketakutan awal.
- Berakhir dengan Alice merencanakan langkah berikutnya.

... (lanjutkan untuk semua bab)
```

# Instruksi
- Fokus pada pemisahan bab yang jelas dan tujuan/peristiwa tingkat tinggi.
- **Jangan** pecah bab menjadi adegan-adegan individual dalam langkah ini.
- Pertahankan poin plot inti dari outline asli.
- Seluruh respons Anda harus berupa outline yang disempurnakan dan terstruktur berdasarkan bab.
Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
"""

# Prompts moved from Writer/Outline/StoryElements.py
GENERATE_STORY_ELEMENTS = """
Saya sedang mengerjakan penulisan cerita fiksi, dan saya ingin bantuan Anda menulis elemen-elemen cerita.

Berikut adalah prompt untuk cerita saya.
<PROMPT>
{_OutlinePrompt}
</PROMPT>

Harap buat respons Anda memiliki format berikut:

<RESPONSE_TEMPLATE>
# Judul Cerita

## Genre
- **Kategori**: (misalnya, romansa, misteri, fiksi ilmiah, fantasi, horor)

## Tema
- **Ide atau Pesan Sentral**:

## Laju
- **Kecepatan**: (misalnya, lambat, cepat)

## Gaya
- **Penggunaan Bahasa**: (misalnya, struktur kalimat, kosakata, nada, bahasa kiasan)

## Plot
- **Eksposisi**:
- **Aksi Meningkat**:
- **Klimaks**:
- **Aksi Menurun**:
- **Resolusi**:

## Latar
### Latar 1
- **Waktu**: (misalnya, sekarang, masa depan, masa lalu)
- **Lokasi**: (misalnya, kota, pedesaan, planet lain)
- **Budaya**: (misalnya, modern, abad pertengahan, alien)
- **Suasana Hati**: (misalnya, suram, teknologi tinggi, distopia)

(Ulangi struktur di atas untuk latar tambahan)

## Konflik
- **Jenis**: (misalnya, internal, eksternal)
- **Deskripsi**:

## Simbolisme
### Simbol 1
- **Simbol**:
- **Makna**:

(Ulangi struktur di atas untuk simbol tambahan)

## Karakter
### Karakter Utama
#### Karakter Utama 1
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Motivasi**:

(Ulangi struktur di atas untuk karakter utama tambahan)


### Karakter Pendukung
#### Karakter 1
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Peran dalam cerita**:

#### Karakter 2
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Peran dalam cerita**:

#### Karakter 3
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Peran dalam cerita**:

#### Karakter 4
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Peran dalam cerita**:

#### Karakter 5
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Peran dalam cerita**:

#### Karakter 6
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Peran dalam cerita**:

#### Karakter 7
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Peran dalam cerita**:

#### Karakter 8
- **Nama**:
- **Deskripsi Fisik**:
- **Kepribadian**:
- **Latar Belakang**:
- **Peran dalam cerita**:

(Ulangi struktur di atas untuk karakter pendukung tambahan)

</RESPONSE_TEMPLATE>

Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
Tentu saja, jangan sertakan tag XML - itu hanya untuk menunjukkan contoh.
Juga, item dalam tanda kurung hanya untuk memberi Anda gambaran yang lebih baik tentang apa yang harus ditulis, dan juga harus dihilangkan dari respons Anda.
"""

# Prompts moved from Evaluate.py
EVALUATE_SYSTEM_PROMPT = "Anda adalah model bahasa AI yang membantu. Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia."

EVALUATE_OUTLINES = """
Harap evaluasi outline mana yang lebih baik dari dua outline berikut:

Berikut adalah outline pertama:
<OutlineA>
{_Outline1}
</OutlineA>

Dan berikut adalah outline kedua:
<OutlineB>
{_Outline2}
</OutlineB>

Gunakan kriteria berikut untuk mengevaluasi (CATATAN: Anda akan memilih outline A atau outline B nanti untuk kriteria ini):
- Plot: Apakah cerita memiliki plot yang koheren? Apakah kreatif?
- Bab: Apakah bab-bab mengalir satu sama lain (hati-hati saat memeriksa ini)? Apakah terasa terhubung? Apakah terasa homogen atau unik dan segar?
- Gaya: Apakah gaya penulisan membantu memajukan plot atau mengganggu sisa cerita? Apakah terlalu berbunga-bunga?
- Dialog: Apakah dialog spesifik untuk setiap karakter? Apakah terasa sesuai karakter? Apakah cukup atau terlalu sedikit?
- Trope: Apakah trope masuk akal untuk genre tersebut? Apakah menarik dan terintegrasi dengan baik?
- Genre: Apakah genre jelas?
- Struktur Naratif: Apakah jelas apa strukturnya? Apakah sesuai dengan genre/trope/konten?

Pastikan semua nilai teks dalam JSON (khususnya 'Thoughts', 'Reasoning', dan semua '*Explanation') ditulis dalam Bahasa Indonesia. Kunci JSON harus tetap dalam Bahasa Inggris.
Harap berikan respons Anda dalam format JSON, yang menunjukkan peringkat untuk setiap cerita:

{{
    "Thoughts": "Catatan dan alasan Anda tentang mana dari keduanya yang lebih baik dan mengapa.",
    "Reasoning": "Jelaskan secara spesifik apa yang dilakukan oleh yang lebih baik yang tidak dilakukan oleh yang lebih rendah, dengan contoh dari keduanya.",
    "Plot": "<A, B, atau Tie>",
    "PlotExplanation": "Jelaskan alasan Anda.",
    "Style": "<A, B, atau Tie>",
    "StyleExplanation": "Jelaskan alasan Anda.",
    "Chapters": "<A, B, atau Tie>",
    "ChaptersExplanation": "Jelaskan alasan Anda.",
    "Tropes": "<A, B, atau Tie>",
    "TropesExplanation": "Jelaskan alasan Anda.",
    "Genre": "<A, B, atau Tie>",
    "GenreExplanation": "Jelaskan alasan Anda.",
    "Narrative": "<A, B, atau Tie>",
    "NarrativeExplanation": "Jelaskan alasan Anda.",
    "OverallWinner": "<A, B, atau Tie>"
}}

Jangan merespons dengan apa pun kecuali JSON. Jangan sertakan field lain kecuali yang ditunjukkan di atas. Seluruh respons Anda harus hanya objek JSON.
"""

EVALUATE_CHAPTERS = """
Harap evaluasi mana dari dua bab yang tidak terkait dan terpisah yang lebih baik berdasarkan kriteria berikut: Plot, Bab, Gaya, Dialog, Trope, Genre, dan Narasi.


Gunakan kriteria berikut untuk mengevaluasi (CATATAN: Anda akan memilih bab A atau bab B nanti untuk kriteria ini):
- Plot: Apakah cerita memiliki plot yang koheren? Apakah kreatif?
- Bab: Apakah bab-bab mengalir satu sama lain (hati-hati saat memeriksa ini)? Apakah terasa terhubung? Apakah terasa homogen atau unik dan segar?
- Gaya: Apakah gaya penulisan membantu memajukan plot atau mengganggu sisa cerita? Apakah terlalu berbunga-bunga?
- Dialog: Apakah dialog spesifik untuk setiap karakter? Apakah terasa sesuai karakter? Apakah cukup atau terlalu sedikit?
- Trope: Apakah trope masuk akal untuk genre tersebut? Apakah menarik dan terintegrasi dengan baik?
- Genre: Apakah genre jelas?
- Struktur Naratif: Apakah jelas apa strukturnya? Apakah sesuai dengan genre/trope/konten?


Berikut adalah bab A:
<CHAPTER_A>
{_ChapterA}

!AKHIR BAB!
</CHAPTER_A>

Dan berikut adalah bab B:
<CHAPTER_B>
{_ChapterB}
!AKHIR BAB!
</CHAPTER_B>


Pastikan semua nilai teks dalam JSON (khususnya semua '*Explanation') ditulis dalam Bahasa Indonesia. Kunci JSON harus tetap dalam Bahasa Inggris.
Harap berikan respons Anda dalam format JSON, yang menunjukkan peringkat untuk setiap cerita:

{{
    "Plot": "<A, B, atau Tie>",
    "PlotExplanation": "Jelaskan alasan Anda.",
    "Style": "<A, B, atau Tie>",
    "StyleExplanation": "Jelaskan alasan Anda.",
    "Dialogue": "<A, B, atau Tie>",
    "DialogueExplanation": "Jelaskan alasan Anda.",
    "Tropes": "<A, B, atau Tie>",
    "TropesExplanation": "Jelaskan alasan Anda.",
    "Genre": "<A, B, atau Tie>",
    "GenreExplanation": "Jelaskan alasan Anda.",
    "Narrative": "<A, B, atau Tie>",
    "NarrativeExplanation": "Jelaskan alasan Anda.",
    "OverallWinner": "<A, B, atau Tie>"
}}

Jangan merespons dengan apa pun kecuali JSON.

Ingat, bab A dan B adalah dua versi terpisah dari cerita serupa. Keduanya tidak melanjutkan maupun melengkapi satu sama lain dan harus dievaluasi secara terpisah.

Tekankan Bab A dan B saat Anda menilai hasilnya. Seluruh respons Anda harus hanya objek JSON.
"""


SCENES_TO_JSON = """
# KONTEKS #
Saya perlu mengubah outline adegan demi adegan berikut menjadi daftar berformat JSON.
```
{_Scenes}
```
###############

# OBJEKTIF #
Buat daftar JSON dari setiap adegan dari outline yang disediakan di mana setiap elemen dalam daftar berisi konten untuk adegan tersebut.
Contoh:
{{
    "scenes": [
        "konten adegan 1...",
        "konten adegan 2...",
        "dll."
    ]
}}

+ Balas dengan objek JSON yang valid yang berisi satu kunci bernama "scenes". Nilai yang terkait dengan kunci ini harus berupa array JSON (daftar) string, di mana setiap string adalah konten dari sebuah adegan.
+ Jangan sertakan teks, komentar, atau format markdown apa pun di luar objek JSON itu sendiri. Seluruh respons Anda harus hanya objek JSON.
###############

# GAYA #
Balas dalam JSON murni.
###############

# AUDIENS #
Harap sesuaikan respons Anda sehingga murni berformat JSON.
###############

# RESPONS #
Jangan kehilangan informasi apa pun dari outline asli, cukup format agar sesuai dalam daftar.
+ Pastikan output adalah objek JSON tunggal yang valid seperti yang dijelaskan dalam objektif.
Pastikan semua respons Anda ditulis dalam Bahasa Indonesia (konten adegan dalam daftar JSON juga harus dalam Bahasa Indonesia). Kunci JSON harus tetap dalam Bahasa Inggris.
###############
"""

SCENE_OUTLINE_TO_SCENE = """
# KONTEKS #
Saya membutuhkan bantuan Anda untuk menulis adegan lengkap berdasarkan outline adegan berikut.
```
{_SceneOutline}
```

Sebagai konteks, berikut adalah outline lengkap dari cerita tersebut.
```
{_Outline}
```
###############

# OBJEKTIF #
Buat adegan lengkap berdasarkan outline adegan yang diberikan, yang ditulis dengan nada yang sesuai untuk adegan tersebut.
Pastikan untuk menyertakan dialog dan elemen penulisan lainnya sesuai kebutuhan.
###############

# GAYA #
Buat gaya Anda kreatif dan sesuai untuk adegan yang diberikan. Outline adegan harus menunjukkan gaya yang tepat, tetapi jika tidak, gunakan penilaian Anda sendiri.
###############

# AUDIENS #
Harap sesuaikan respons Anda untuk ditulis untuk hiburan masyarakat umum sebagai karya tulis kreatif.
###############

# RESPONS #
Pastikan respons Anda dipikirkan dengan matang dan kreatif. Luangkan waktu sejenak untuk memastikan respons tersebut mengikuti outline adegan yang disediakan, dan pastikan juga sesuai dengan outline cerita utama.
Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia.
###############
"""

# Harap terjemahkan semua prompt lainnya di file ini dengan cara yang sama.
# Pastikan untuk menjaga semua kunci JSON dalam Bahasa Inggris.
# Anda mungkin perlu menyesuaikan beberapa prompt agar lebih alami dalam Bahasa Indonesia
# sambil tetap mempertahankan fungsionalitasnya.
