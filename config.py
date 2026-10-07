import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
INSTANCE_FOLDER = os.path.join(BASE_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_FOLDER, 'question_bank.db')
ALLOWED_EXTENSIONS = {'pdf'}
SECRET_KEY = os.environ.get('QUESTION_BANK_SECRET_KEY') or secrets.token_hex(32)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)
os.makedirs(INSTANCE_FOLDER, exist_ok=True)
