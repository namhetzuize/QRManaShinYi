# Product Management Webapp (cleaned)

Mục tiêu: ứng dụng web nhỏ để quản lý thông tin sản phẩm, upload giấy chứng nhận, tự động tạo QR cho mỗi sản phẩm và lưu thông tin vào Google Sheets hoặc file Excel.

Quick start:

1. Cài dependencies (ví dụ):

```powershell
python -m pip install fastapi uvicorn jinja2 authlib qrcode pillow google-api-python-client google-auth google-auth-oauthlib gspread oauth2client openpyxl pandas
```

2. Đảm bảo các file credential hiện có trong `webserver/` (ví dụ: `festive-post-464106-p3-d250f2280eae.json`, `google_oauth_config.json`).

3. Chạy server:

```powershell
uvicorn webserver.main:app --reload --host 0.0.0.0 --port 8000
```

4. Mở: `http://localhost:8000`

Notes:
- Product lưu vào Google Sheets (sheet name `Products`) bằng service account. Nếu Sheets không khả dụng, bạn có thể config để ghi file Excel cục bộ bằng hàm `append_product_to_excel`.

## Portability and moving the project to another machine

Short answer: you can copy the project folder to another machine, but you must also bring the runtime environment, credentials, and the data files (SQLite DB and Excel) or configure them on the target machine. Below are the main things to check and recommended options to make the app portable.

What can break when you copy the folder
- Absolute paths in code: ensure no hard-coded absolute paths remain (e.g. `D:\Visualstudiocode\...`). Prefer relative paths via `os.path.join(os.path.dirname(__file__), ...)`.
- Python environment & dependencies: the target machine needs Python (same major version) and installed packages.
- Service account / OAuth JSON files and environment variables: copy `festive-post-...json` or set `GOOGLE_SERVICE_ACCOUNT_FILE` and `GOOGLE_SHEET_ID` appropriately.
- OAuth redirect URIs: if using Google OAuth web flow, update redirect URIs in Google Cloud Console to match the new host (localhost vs domain).
- SQLite DB and Excel files: copy `webserver/products.db` and `webserver/products_summary.xlsx` if you want existing data; ensure Excel isn't open (file lock on Windows).

Recommended portable options

1) Docker (best for reproducible portability)
- Packages OS, Python, dependencies and app. I added a `Dockerfile` and `docker-compose.yml` to this repo.
- Put the service account JSON into a local `secrets/` folder and set up `.env` (see `.env.example`). Compose mounts `webserver/products.db`, `webserver/products_summary.xlsx` and `webserver/static/` as volumes so data remains on the host.
- Quick run on target machine (after copying project and placing secrets):

```powershell
cp .env.example .env
# edit .env and put your service account filename under GOOGLE_SERVICE_ACCOUNT_FILENAME
docker compose up --build -d
```

2) Virtualenv + pip (simple)
- On the target machine create a venv, install `requirements.txt` and run `uvicorn`. I added `requirements.txt` to the repo.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn webserver.main:app --reload --host 0.0.0.0 --port 8000
```

3) Freezing into an executable (not recommended for web apps)
- PyInstaller can produce an EXE, but bundling templates/static and writable DB files is tricky. Prefer Docker or venv.

Extra tips
- Use environment variables for secrets (`GOOGLE_SERVICE_ACCOUNT_FILE`, `GOOGLE_SHEET_ID`).
- Keep persistent data (DB, Excel) outside any immutable image/container when possible.
- If you want I can produce a PowerShell "install-and-run" script, or build and run a Docker image here to validate (tell me which you prefer).
