# Akses shell hosting & linking Git hosting ↔ GitHub

Catatan teknis untuk shared hosting cPanel yang dipakai site kantor
(panel `https://panel.example.com:2222`, user cPanel `<proyek>660`).

## Dua port, dua protocol berbeda

| Port | Protocol | Guna |
|---|---|---|
| 2222 | HTTPS | panel cPanel (Evolution) — **bukan SSH**; `ssh -p 2222` selalu ditolak |
| 22 | SSH | shell hosting; `ssh-keyscan -p 22` mengembalikan banner `OpenSSH` |

Jadi: probe port 22 untuk memastikan shell tersedia, port 2222 untuk panel
web. Jangan tertukar mana yang SSH.

## Username shell = username cPanel

Untuk shared hosting, user shell biasanya sama dengan username cPanel
(`<proyek>660`). Login memakai password auth yang sama dengan entri vault
panel — jadi satu entri vault cukup untuk dua jalur.

## Menu panel yang sudah diverifikasi ada

- **Git** → path `/evo/git-version` (bukan `/evo/versioncontrol` → 404).
  Halaman menyediakan "CREATE REPOSITORY".
- **SSH Keys** → path `/evo/ssh-keys` (redirect ke `/evo/ssh-keys/public`),
  punya tab Public Keys / Authorized Keys + tombol CREATE KEY / PASTE KEY.
- **Terminal** → path `/evo/terminal` (xterm).
- Path URL lain bisa dicari dari DOM dashboard: filter anchor yang
  `href`/`text` mengandung kata kunci, daripada menebak path.

**Terminal panel berbasis xterm dengan canvas renderer** → output tidak
terbaca dari DOM (`.xterm-rows` kosong). Untuk perintah yang butuh output,
lebih andal lewat SSH langsung (port 22) daripada mengetik ke terminal panel.

## Menjalankan perintah remote tanpa mencetak password

Password diambil dari vault (profil aktif) lalu diserahkan ke `ssh` lewat
`SSH_ASKPASS`, jadi nilainya tidak pernah masuk output/chat:

```bash
SSH_ASKPASS=<script-helper> SSH_ASKPASS_REQUIRE=force DISPLAY=:0 \
  ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no \
      <user>@<host> '<perintah>'
```

Helper `askpass` cukup `printf '%s' "$ENV_PW"`; env var diberi nilainya dari
vault, bukan argumen baris perintah. Lihat `scripts/ssh_vault.py` — satu file
yang melakukan resolve-secret → jalankan ssh → cetak stdout/exit code saja.

## Petakan docroot sebelum deploy

Pada hosting berbasis CageFS:

```
~/public_html -> ./domains/<domain>/public_html
~/domains/<domain>/public_html/
```

Jadi `~/public_html` hanya symlink; path asli ada di `~/domains/<domain>/`.
Selalu `ls -la` symlink tersebut dan `ls -A` docroot asli untuk menghitung
isi sebelum menimpa.

## Git: arah private/public key untuk `git clone` dari hosting

Agar hosting bisa `git clone git@github.com:<owner>/<repo>.git`:

1. Generate keypair di mesin yang memegang akses, mis.
   `ssh-keygen -t ed25519 -f deploy_key -N ""`.
2. **Private key** → salin ke akun hosting (`.ssh/id_ed25519`, mode 600) —
   inilah yang dipakai saat clone.
3. **Public key** → daftarkan sebagai **deploy key read-only** pada repo
   GitHub yang dituju (`POST /repos/<owner>/<repo>/keys`).
4. `ssh-keyscan github.com >> ~/.ssh/known_hosts` di akun hosting — tanpa
   ini clone gagal dengan `Host key verification failed`.
5. Uji ke direktori scratch di luar docroot, lalu hapus.

### Key troubleshooting and per-repo scope

- **Arah key terbalik** → `Permission denied (publickey)` padahal key sudah
  "dipasang": kalau hanya public key yang ada di hosting, tidak ada yang bisa
  membuktikan kepemilikan saat GitHub meminta signature. Private key harus
  ada di sisi yang melakukan clone.
- **Satu deploy key hanya berlaku untuk satu repo.** GitHub menolak key yang
  sudah dipakai di repo lain (`key is already in use`). Bila mandatnya jelas,
  buat keypair baru untuk repo target; jangan pakai ulang key test.
- Simpan private key secara aman di host pull (mode `600`); public key
  ditambahkan sebagai deploy key read-only pada repo kanonis yang tepat.
  Verifikasi fingerprint tanpa mencetak private key, lalu lakukan clone
  scratch dari akun hosting, catat commit/file count, dan hapus scratch.
  Jangan menyebut jalur deploy terverifikasi hanya karena key tercatat di
  GitHub atau cPanel.

### Credential host lokal ≠ credential hosting

GitHub CLI di mesin koordinator (scope `repo`) ≠ akses git dari hosting.
Deploy key read-only di GitHub + private key di hosting adalah dua hal
terpisah; satu tidak menyiratkan yang lain.

## Bukti minimal sebelum mengklaim "Git terhubung"

- `ssh <user>@<host> 'git --version'` → nomor versi
- `ssh <user>@<host> 'curl -sI https://github.com'` → 200 (hosting bisa keluar)
- `ssh <user>@<host> 'git clone <repo> scratch && cat scratch/<file>'` → isi file
  benar (membuktikan private key + deploy key + known_hosts semua benar)
- `git -C scratch log --oneline -1` → commit yang diharapkan ter-pull

Empat bukti itu berbeda dengan "repo dibuat" atau "menu Git ada di panel".
