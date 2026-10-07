import io
import json
import sqlite3
from pathlib import Path

import requests
from reportlab.pdfgen import canvas

from services.difficulty_service import estimate_difficulty
from services.duplicate_service import remove_duplicates
from services.nlp_service import extract_keywords
from services.quality_service import compute_quality
from services.question_service import generate_questions
from services.topic_service import classify_topic

BASE = 'http://127.0.0.1:5000'

print('=== QA CHECKS ===')

home = requests.get(BASE + '/', timeout=20)
print('1. Flask startup:', home.status_code)

print('2. Database creation:', Path('instance/question_bank.db').exists())
conn = sqlite3.connect('instance/question_bank.db')
print('Table questions exists:', conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'").fetchone())
conn.close()

# PDF sample generation
pdf_buf = io.BytesIO()
c = canvas.Canvas(pdf_buf)
text = 'Operating Systems: Process scheduling is the method used by the operating system to decide which process gets CPU time. The kernel manages memory and deadlock prevention. A process may have multiple threads.'
c.drawString(60, 760, text[:110])
c.save()
file_bytes = pdf_buf.getvalue()

files = {'pdf_file': ('sample_os.pdf', file_bytes, 'application/pdf')}
form = {'question_count': '10', 'difficulty': 'Auto', 'question_types': ['MCQ', 'Short Answer', 'Numerical/Application', 'Case-based']}
upload = requests.post(BASE + '/upload', files=files, data=form, timeout=90, allow_redirects=True)
print('4. PDF upload:', upload.status_code)
print('5. PDF text extraction preview present:', 'Operating Systems' in upload.text or 'process' in upload.text.lower())

kw = extract_keywords(text)
print('7. NLP keyword extraction:', kw[:10])
print('8. Topic classification:', classify_topic(kw, text))

qs = generate_questions(text, classify_topic(kw, text), kw, question_types=['MCQ', 'Short Answer', 'Numerical/Application', 'Case-based'], count=4, difficulty_mode='Auto', source_file='sample_os.pdf')
print('9. MCQ generation:', any(q['question_type'] == 'MCQ' for q in qs))
print('10. Short-answer generation:', any(q['question_type'] == 'Short Answer' for q in qs))
print('11. Numerical generation:', any(q['question_type'] == 'Numerical/Application' for q in qs))
print('12. Case-based generation:', any(q['question_type'] == 'Case-based' for q in qs))
print('13. Difficulty estimation:', [estimate_difficulty(q['question'], q['answer'], q['question_type']) for q in qs])
print('14. Quality score:', [compute_quality(q['question'], q['answer'], q['topic'], q['keywords']) for q in qs])
print('15. Duplicate detection:', remove_duplicates(qs)[1])

# validate stored DB insertion
conn = sqlite3.connect('instance/question_bank.db')
count = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
print('16. SQLite insertion count:', count)
conn.close()

# Search and filters
search = requests.get(BASE + '/questions?search=process', timeout=20)
print('17. Search page:', search.status_code)
filter_topic = requests.get(BASE + '/questions?topic=Operating%20Systems', timeout=20)
print('18. Topic filter page:', filter_topic.status_code)
filter_diff = requests.get(BASE + '/questions?difficulty=Easy', timeout=20)
print('19. Difficulty filter page:', filter_diff.status_code)
filter_type = requests.get(BASE + '/questions?question_type=MCQ', timeout=20)
print('20. Question-type filter page:', filter_type.status_code)

csv_resp = requests.get(BASE + '/export/csv', timeout=20)
print('21. CSV export:', csv_resp.status_code, 'rows=', len(csv_resp.text.splitlines()) if csv_resp.text else 0)
json_resp = requests.get(BASE + '/export/json', timeout=20)
print('22. JSON export:', json_resp.status_code, 'bytes=', len(json_resp.content))

api_resp = requests.get(BASE + '/api/questions', timeout=20)
questions = api_resp.json()
print('23. GET /api/questions:', api_resp.status_code, 'count=', len(questions))
if questions:
    first_id = questions[0]['id']
    single = requests.get(f'{BASE}/api/questions/{first_id}', timeout=20)
    print('24. GET /api/questions/<id>:', single.status_code)
    missing = requests.get(BASE + '/api/questions/999999', timeout=20)
    print('Missing id status:', missing.status_code)

bad = requests.post(BASE + '/upload', files={'pdf_file': ('bad.txt', b'not a pdf', 'text/plain')}, timeout=20)
print('25. Invalid file handling:', bad.status_code, 'Only PDF files are allowed' in bad.text)

print('=== END QA CHECKS ===')
