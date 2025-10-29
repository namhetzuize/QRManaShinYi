import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')

CREATE_SQL = '''
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    product_code TEXT,
    issue_date TEXT,
    serial_no TEXT,
    certificate_no TEXT,
    organization TEXT,
    check_count TEXT,
    cert_link TEXT,
    external_link TEXT,
    qr_link TEXT,
    staff_name TEXT,
    staff_id TEXT,
    created_at TEXT
)
'''


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(CREATE_SQL)
    conn.commit()
    # Ensure any new columns exist (migration)
    try:
        c.execute('PRAGMA table_info(products)')
        existing = [row[1] for row in c.fetchall()]
        needed = ['product_code','issue_date','serial_no','certificate_no','organization','check_count','staff_name','staff_id']
        for col in needed:
            if col not in existing:
                try:
                    c.execute(f"ALTER TABLE products ADD COLUMN {col} TEXT")
                except Exception:
                    pass
        conn.commit()
    except Exception as e:
        print('DB migration check error:', e)
    conn.close()


def insert_product(prod):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO products (id, name, description, product_code, issue_date, serial_no, certificate_no, organization, check_count, cert_link, external_link, qr_link, staff_name, staff_id, created_at)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
        prod.get('product_id'), prod.get('name'), prod.get('description'), prod.get('product_code'), prod.get('issue_date'), prod.get('serial_no'), prod.get('certificate_no'), prod.get('organization'), prod.get('check_count'), prod.get('cert_link'), prod.get('external_link'), prod.get('qr_link'), prod.get('staff_name'), prod.get('staff_id'), prod.get('created_at')
    ))
    conn.commit()
    conn.close()


def list_products(limit=100):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id, name, description, product_code, issue_date, serial_no, certificate_no, organization, check_count, staff_name, staff_id, cert_link, external_link, qr_link, created_at FROM products ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            'product_id': r[0], 'name': r[1], 'description': r[2], 'product_code': r[3], 'issue_date': r[4], 'serial_no': r[5], 'certificate_no': r[6], 'organization': r[7], 'check_count': r[8], 'staff_name': r[9], 'staff_id': r[10], 'cert_link': r[11], 'external_link': r[12], 'qr_link': r[13], 'created_at': r[14]
        } for r in rows
    ]


def get_product(product_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id, name, description, product_code, issue_date, serial_no, certificate_no, organization, check_count, staff_name, staff_id, cert_link, external_link, qr_link, created_at FROM products WHERE id=?', (product_id,))
    r = c.fetchone()
    conn.close()
    if not r:
        return None
    return {'product_id': r[0], 'name': r[1], 'description': r[2], 'product_code': r[3], 'issue_date': r[4], 'serial_no': r[5], 'certificate_no': r[6], 'organization': r[7], 'check_count': r[8], 'staff_name': r[9], 'staff_id': r[10], 'cert_link': r[11], 'external_link': r[12], 'qr_link': r[13], 'created_at': r[14]}


def delete_product(product_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (product_id,))
    conn.commit()
    conn.close()


def update_product_name(product_id, name):
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE products SET name=? WHERE id=?', (name, product_id))
    conn.commit()
    conn.close()
