from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
import json
from .utils import qr_bytes_to_base64, add_user, check_user, load_users
from .utils import generate_qr_image_bytes, append_product_to_gsheet, save_qr_to_local, append_qr_record_to_gsheet, append_summary_to_gsheet, append_summary_to_excel
from . import db as _db
from datetime import datetime
import uuid
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
import csv
# (BaseModel/Depends not required in current simplified app)
from authlib.integrations.starlette_client import OAuth
import os

router = APIRouter()
#GATEWAY_URL = "http://localhost:9000/plc"
sessions = {}  # session_id: {"username":..., "role":...}

oauth = OAuth()
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID") or "244679551739-boqp42itaadufo2f3ma3ok4difn4tsi3.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET") or "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"
with open(os.path.join(os.path.dirname(__file__), "google_oauth_config.json"), encoding="utf-8") as f:
    google_conf = json.load(f)["web"]
oauth.register(
    name='google',
    client_id=google_conf["client_id"],
    client_secret=google_conf["client_secret"],
    access_token_url=google_conf["token_uri"],
    access_token_params=None,
    authorize_url=google_conf["auth_uri"],
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)

# Removed PLC/socket/order-specific endpoints to focus on product management.
## Đăng nhập và đăng ký người dùng
@router.get("/login")
def login_form():
    return HTMLResponse(open("webserver/templates/login.html", encoding="utf-8").read())

@router.post("/login")
def login(response: Response, username: str = Form(...), password: str = Form(...)):
    role = check_user(username, password)
    if role:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"username": username, "role": role}
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("session_id", session_id)
        return response
    return HTMLResponse("Sai tài khoản hoặc mật khẩu. <a href='/login'>Thử lại</a>")

@router.get("/register")
def register_form():
    return HTMLResponse(open("webserver/templates/register.html", encoding="utf-8").read())

@router.post("/register")
def register(username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    ok = add_user(username, password, role)
    if ok:
        return RedirectResponse("/login", status_code=302)
    return HTMLResponse("Tài khoản đã tồn tại. <a href='/register'>Thử lại</a>")

@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.parse_id_token(request, token)
    email = user_info.get("email")
    name = user_info.get("name")
    # Tạo user nếu chưa có
    users = load_users()
    if not any(u["username"] == email for u in users):
        add_user(email, "google_oauth", "user")
    # Đăng nhập
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"username": email, "role": "user", "name": name}
    response = RedirectResponse("/")
    response.set_cookie("session_id", session_id)
    return response

def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None

# Middleware kiểm tra đăng nhập
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # allow unauthenticated access only to login/register, static files, and the public product detail view
        path = request.url.path
        public_prefixes = ['/static', '/product/view']
        allowed = ["/login", "/register"] + public_prefixes
        # require login for all other routes (home, create, list, edit, etc.)
        if not any(path == a or path.startswith(a) for a in allowed):
            user = get_current_user(request)
            if not user:
                return RedirectResponse("/login")
            request.state.user = user
        return await call_next(request)

# Thêm middleware vào app FastAPI (ở main.py)
# app.add_middleware(AuthMiddleware)

# Đăng xuất
@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session_id")
    return response

@router.get("/")
def index(request: Request):
    user = get_current_user(request)
    username = user["username"] if user else ""
    # role 'control' means the user may edit/delete; 'view' is read-only
    is_control = (user.get('role') == 'control') if user else False
    templates = Jinja2Templates(directory="webserver/templates")
    return templates.TemplateResponse("index.html", {"request": request, "username": username, "is_control": is_control})


# --- Product management routes ---
@router.get("/product/new")
def product_form(request: Request):
    # simple form for creating product
    templates = Jinja2Templates(directory="webserver/templates")
    return templates.TemplateResponse("product_form.html", {"request": request})


@router.post("/product/create")
async def product_create(request: Request, name: str = Form(...), description: str = Form(None), product_code: str = Form(None), issue_date: str = Form(None), serial_no: str = Form(None), certificate_no: str = Form(None), organization: str = Form(None), check_count: str = Form(None), staff_name: str = Form(...), staff_id: str = Form(...), external_link: str = Form(None)):
    # Handle multipart form and file upload
    form = await request.form()
    upload = form.get('certificate')
    # Ensure name comes from the submitted form (trim whitespace).
    # Prefer the explicit form field 'name' if present (defensive in case caller bypassed parameter binding).
    submitted_name = (form.get('name') or name or '').strip()
    name = submitted_name
    # Determine upload handling: save a local copy under static/uploads for immediate preview
    try:
        upload_fname = upload.filename if hasattr(upload, 'filename') else None
    except Exception:
        upload_fname = None
    # prefer uploaded file; otherwise use external_link

    # Create product id
    product_id = str(uuid.uuid4())
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Determine the public target URL for this product: upload file to Drive or use external link
    target_url = ''
    cert_link = ''
    if upload and hasattr(upload, 'filename') and upload.filename:
        # read bytes once
        try:
            contents = await upload.read()
            filename = upload.filename
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            # Ensure uploads dir exists inside static
            uploads_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            # Create a safe local filename using product_id
            local_name = f"cert_{product_id}{ext if ext else '.bin'}"
            local_path = os.path.join(uploads_dir, local_name)

            # Try HEIC conversion where possible, otherwise write raw bytes
            if ext in ('.heic', '.heif'):
                try:
                    import io
                    try:
                        import pillow_heif
                        pillow_heif.register_heif_opener()
                        from PIL import Image
                        img = Image.open(io.BytesIO(contents))
                        # save as jpg for browser preview
                        local_path = os.path.join(uploads_dir, f"cert_{product_id}.jpg")
                        img.save(local_path, format='JPEG')
                    except Exception:
                        try:
                            import importlib
                            pyheif = importlib.import_module('pyheif')
                            from PIL import Image
                            heif = pyheif.read_heif(contents)
                            image = Image.frombytes(heif.mode, heif.size, heif.data, 'raw')
                            local_path = os.path.join(uploads_dir, f"cert_{product_id}.jpg")
                            image.save(local_path, format='JPEG')
                        except Exception:
                            # fallback: write raw bytes with original ext
                            with open(local_path, 'wb') as f:
                                f.write(contents)
                except Exception:
                    # fallback: write raw bytes with original ext
                    with open(local_path, 'wb') as f:
                        f.write(contents)
            else:
                with open(local_path, 'wb') as f:
                    f.write(contents)

            # Use local static URL for immediate preview in the UI
            cert_link = f"/static/uploads/{os.path.basename(local_path)}"
            target_url = cert_link

            # (No Drive upload) We keep only a local copy for preview under /static/uploads
        except Exception as e:
            print('File upload error:', e)
            cert_link = ''
    else:
        if external_link:
            target_url = external_link

    # If neither file nor link provided -> error
    if not target_url:
        return JSONResponse({"success": False, "error": "Bạn phải upload file hoặc cung cấp đường link"}, status_code=400)

    # Build public product detail URL and generate QR that links to the product page
    try:
        product_page_url = request.url_for('product_view_db', product_id=product_id)
    except Exception:
        # fallback to base_url + path
        product_page_url = str(request.base_url).rstrip('/') + f'/product/view/{product_id}'

    qr_bytes = generate_qr_image_bytes(product_page_url)
    # Save QR locally in static/QRmana (this returns /static/QRmana/qr_xxx.png)
    qr_local_path = save_qr_to_local(qr_bytes, filename=f"qr_{product_id}.png")
    qr_link = qr_local_path or ''
    # We do NOT upload QR to Drive. The QR image is saved locally under static/QRmana
    qr_drive_link = ''

    # Append to Google Sheet (include staff info and product fields)
    sheet_id = os.environ.get('GOOGLE_SHEET_ID', '13SAnCeHe0vgaFjFwrI9KfI0del8ImQMOrembLYbQr6M')
    ok = append_product_to_gsheet(sheet_id, 'Products', {
        'product_id': product_id,
        'name': name,
        'description': description,
        'product_code': product_code,
        'issue_date': issue_date,
        'serial_no': serial_no,
        'certificate_no': certificate_no,
        'organization': organization,
        'check_count': check_count,
        'staff_name': staff_name,
        'staff_id': staff_id,
        'cert_drive_link': cert_link,
        'external_link': external_link or '',
    'qr_drive_link': qr_link,
        'created_at': created_at
    })

    # Append minimal QR record to dedicated sheet (stt, staff_name, ma_qr, ghi_chu)
    try:
        append_qr_record_to_gsheet(sheet_id, 'QRrecords', {
            'stt': '',
            'staff_name': staff_name,
        'qr_code': product_page_url,
            'note': f"product:{product_id}"
        })
    except Exception as e:
        print('QR record append error:', e)

    # Also append concise summary row to ProductsSummary sheet and local Excel
    try:
        summary = {
            'id': product_id,
            'name': name,
            'product_code': product_code or '',
            'serial_no': serial_no or '',
            'created_at': created_at,
            'issue_date': issue_date or '',
            'staff_name': staff_name or '',
            'staff_id': staff_id or '',
            'detail_url': product_page_url
        }
        try:
            append_summary_to_gsheet(sheet_id, 'ProductsSummary', summary)
        except Exception as e:
            print('Append summary to gsheet error:', e)
        try:
            excel_path = os.path.join(os.path.dirname(__file__), 'products_summary.xlsx')
            append_summary_to_excel(excel_path, summary)
        except Exception as e:
            print('Append summary to excel error:', e)
    except Exception as e:
        print('Summary append error:', e)

    # Persist only product info (do not store staff_name/staff_id per requirement)
    product = {
        'product_id': product_id,
        'name': name,
        'description': description,
        'product_code': product_code,
        'issue_date': issue_date,
        'serial_no': serial_no,
        'certificate_no': certificate_no,
        'organization': organization,
        'check_count': check_count,
        'cert_link': cert_link,
        'external_link': external_link or '',
        'qr_link': qr_link,
        'created_at': created_at,
        'staff_name': staff_name,
        'staff_id': staff_id,
        'qr_base64': qr_bytes_to_base64(qr_bytes) if qr_bytes else None
    }

    try:
        _db.insert_product(product)
    except Exception as e:
        print('DB insert error:', e)

    templates = Jinja2Templates(directory="webserver/templates")
    # propagate admin flag to template
    user = get_current_user(request)
    is_control = (user.get('role') == 'control') if user else False
    return templates.TemplateResponse("product_detail.html", {"request": request, "product": product, "is_control": is_control})


@router.get('/products')
def products_list(request: Request):
    templates = Jinja2Templates(directory='webserver/templates')
    prods = _db.list_products(200)
    user = get_current_user(request)
    is_control = (user.get('role') == 'control') if user else False
    return templates.TemplateResponse('products_list.html', {'request': request, 'products': prods, 'is_control': is_control})


@router.post('/product/delete')
def product_delete(product_id: str = Form(...), request: Request = None):
    # server-side enforcement: only control role can delete
    user = get_current_user(request) if request is not None else None
    if not user or user.get('role') != 'control':
        return RedirectResponse('/login')
    try:
        _db.delete_product(product_id)
    except Exception as e:
        print('Delete product error:', e)
    return RedirectResponse('/products', status_code=302)


@router.get('/product/edit/{product_id}')
def product_edit(request: Request, product_id: str):
    # only control users can access edit page
    user = get_current_user(request)
    if not user or user.get('role') != 'control':
        return RedirectResponse('/login')
    prod = _db.get_product(product_id)
    if not prod:
        return HTMLResponse('Not found', status_code=404)
    templates = Jinja2Templates(directory='webserver/templates')
    is_control = True
    return templates.TemplateResponse('product_edit.html', {'request': request, 'product': prod, 'is_control': is_control})


@router.post('/product/update')
def product_update(product_id: str = Form(...), name: str = Form(...), request: Request = None):
    # enforce control role
    user = get_current_user(request) if request is not None else None
    if not user or user.get('role') != 'control':
        return RedirectResponse('/login')
    try:
        _db.update_product_name(product_id, name.strip())
    except Exception as e:
        print('Update product name error:', e)
    return RedirectResponse(f'/product/view/{product_id}', status_code=302)


@router.get('/products/export.csv')
def export_products_csv():
    prods = _db.list_products(1000)
    def iter_csv():
        w = csv.writer(__import__('io').StringIO())
        # write header
        header = ['product_id','name','description','product_code','issue_date','serial_no','certificate_no','organization','check_count','staff_name','staff_id','cert_link','external_link','qr_link','created_at']
        buf = __import__('io').StringIO()
        writer = csv.writer(buf)
        writer.writerow(header)
        yield buf.getvalue()
        buf.seek(0); buf.truncate(0)
        for p in prods:
            writer.writerow([p.get(k,'') for k in header])
            yield buf.getvalue()
            buf.seek(0); buf.truncate(0)
    return StreamingResponse(iter_csv(), media_type='text/csv')


@router.get('/product/view/{product_id}')
def product_view_db(request: Request, product_id: str):
    prod = _db.get_product(product_id)
    if not prod:
        return HTMLResponse('Not found', status_code=404)
    templates = Jinja2Templates(directory='webserver/templates')
    # ensure qr_base64 is available for display if needed
    qr_bytes = None
    try:
        # try to generate qr bytes from stored link (prefer cert_link then external_link)
        target = prod.get('cert_link') or prod.get('external_link') or ''
        if target:
            qr_bytes = generate_qr_image_bytes(target)
    except Exception:
        qr_bytes = None
    prod['qr_base64'] = qr_bytes_to_base64(qr_bytes) if qr_bytes else None
    user = get_current_user(request)
    is_control = (user.get('role') == 'control') if user else False
    return templates.TemplateResponse('product_detail.html', {'request': request, 'product': prod, 'is_control': is_control})


@router.get("/product/{product_id}")
def product_view(request: Request, product_id: str):
    # This demo implementation does not persist products locally; in a real app you should store them in DB.
    return HTMLResponse(f"Product page for {product_id}. Use the listing in Google Sheets to find details.")