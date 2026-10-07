import csv
import io
import json
import re
import secrets
from hmac import compare_digest

from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import ALLOWED_EXTENSIONS, EXPORT_FOLDER, SECRET_KEY, UPLOAD_FOLDER
from database import (
    fetch_all_questions,
    fetch_question_by_id,
    fetch_question_stats,
    create_user,
    fetch_user_by_username,
    initialize_database,
    insert_question,
    search_questions,
)
from services.duplicate_service import remove_duplicates
from services.nlp_service import extract_keywords
from services.pdf_service import process_pdf_upload
from services.question_service import generate_questions
from services.topic_service import classify_topic

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = SECRET_KEY

initialize_database()


@app.context_processor
def inject_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(32)
    return {'csrf_token': session['_csrf_token']}


@app.before_request
def require_login():
    endpoint = request.endpoint
    public_endpoints = {'login', 'register', 'static'}

    if endpoint in public_endpoints:
        if endpoint in {'login', 'register'} and session.get('user_id'):
            return redirect(url_for('index'))
        if endpoint in {'login', 'register'} and request.method == 'POST':
            submitted_token = request.form.get('csrf_token', '')
            expected_token = session.get('_csrf_token', '')
            if not expected_token or not compare_digest(submitted_token, expected_token):
                flash('Your session expired. Please try again.', 'error')
                return redirect(url_for(endpoint))
        return None

    if not session.get('user_id'):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Authentication required'}), 401
        flash('Please log in to access the question bank.', 'error')
        return redirect(url_for('login'))

    if endpoint == 'logout' and request.method == 'POST':
        submitted_token = request.form.get('csrf_token', '')
        expected_token = session.get('_csrf_token', '')
        if not expected_token or not compare_digest(submitted_token, expected_token):
            flash('Your session expired. Please try again.', 'error')
            return redirect(url_for('index'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not re.fullmatch(r'[A-Za-z0-9_.-]{3,32}', username):
        flash('Username must be 3–32 characters using letters, numbers, dots, dashes, or underscores.', 'error')
        return render_template('register.html')
    if len(password) < 8 or len(password) > 128:
        flash('Password must be between 8 and 128 characters.', 'error')
        return render_template('register.html')
    if password != confirm_password:
        flash('The passwords do not match.', 'error')
        return render_template('register.html')
    if create_user(username, generate_password_hash(password)) is None:
        flash('That username is already registered. Please log in or choose another.', 'error')
        return render_template('register.html')

    flash('Your account is ready. Log in to continue.', 'success')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    user = fetch_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        flash('Username or password is incorrect.', 'error')
        return render_template('login.html')

    session.clear()
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['_csrf_token'] = secrets.token_urlsafe(32)
    return redirect(url_for('index'))


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/')
def index():
    stats = fetch_question_stats()
    return render_template('index.html', stats=stats)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')

    file = request.files.get('pdf_file')
    if not file or file.filename == '':
        flash('Please select a PDF file before submitting.', 'error')
        return render_template('upload.html')

    if not allowed_file(file.filename):
        flash('Only PDF files are allowed.', 'error')
        return render_template('upload.html')

    question_types = request.form.getlist('question_types') or ['Short Answer']
    question_count = request.form.get('question_count', default=5, type=int)
    difficulty_mode = request.form.get('difficulty', 'Auto')

    pdf_result = process_pdf_upload(file, UPLOAD_FOLDER)
    if not pdf_result.get('success'):
        flash(pdf_result.get('message', 'The PDF could not be processed.'), 'error')
        return render_template('upload.html')

    text = pdf_result.get('text', '').strip()
    if not text:
        flash('The uploaded PDF does not contain readable text. Please upload a digital PDF or ensure OCR support is installed.', 'error')
        return render_template('upload.html')

    keywords = extract_keywords(text)
    topic = classify_topic(keywords, text)
    generated = generate_questions(
        text,
        topic,
        keywords,
        question_types=question_types,
        count=question_count,
        difficulty_mode=difficulty_mode,
        source_file=pdf_result['filename'],
    )

    deduped, removed = remove_duplicates(generated)
    stored_questions = []
    for item in deduped:
        item['source_file'] = pdf_result['filename']
        item['question_type'] = item.get('question_type', 'Short Answer')
        item['difficulty'] = item.get('difficulty', 'Auto')
        item['keywords'] = item.get('keywords', [])
        item['quality_score'] = int(item.get('quality_score', 0))
        item['topic'] = topic
        question_id = insert_question(item)
        item['id'] = question_id
        stored_questions.append(item)

    result = {
        'file_name': pdf_result['filename'],
        'pages': pdf_result.get('page_count', 0),
        'ocr_used': pdf_result.get('ocr_used', False),
        'ocr_status': pdf_result.get('ocr_status', 'Digital PDF'),
        'detected_topic': topic,
        'keywords': keywords[:12],
        'text_preview': pdf_result.get('preview', text[:1200]),
        'question_count': len(stored_questions),
        'duplicates_removed': removed,
        'questions': stored_questions,
    }
    session['last_result'] = result
    return redirect(url_for('results_page'))


@app.route('/results')
def results_page():
    result = session.get('last_result')
    if not result:
        flash('There is no previous processing result available.', 'error')
        return redirect(url_for('upload'))
    return render_template('results.html', result=result)


@app.route('/questions', methods=['GET'])
def questions_page():
    search_term = request.args.get('search', '').strip()
    topic_filter = request.args.get('topic', '').strip()
    difficulty_filter = request.args.get('difficulty', '').strip()
    question_type_filter = request.args.get('question_type', '').strip()
    keyword_filter = request.args.get('keyword', '').strip()

    items = search_questions(
        term=search_term or None,
        topic=topic_filter or None,
        difficulty=difficulty_filter or None,
        question_type=question_type_filter or None,
        keyword=keyword_filter or None,
    )

    topics = ['Database', 'Operating Systems', 'Computer Networks', 'Machine Learning', 'Data Structures', 'IoT', 'Programming', 'General']
    difficulties = ['Easy', 'Medium', 'Hard']
    types = ['MCQ', 'Short Answer', 'Numerical/Application', 'Case-based']
    return render_template('questions.html', questions=items, topics=topics, difficulties=difficulties, types=types,
                           search_term=search_term, topic_filter=topic_filter, difficulty_filter=difficulty_filter,
                           question_type_filter=question_type_filter, keyword_filter=keyword_filter)


@app.route('/export/csv')
def export_csv():
    questions = fetch_all_questions()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id', 'question', 'answer', 'question_type', 'topic', 'difficulty', 'keywords', 'source_file', 'quality_score', 'created_at'])
    writer.writeheader()
    for item in questions:
        writer.writerow(item)

    memory = output.getvalue().encode('utf-8')
    return send_file(io.BytesIO(memory), mimetype='text/csv', as_attachment=True, download_name='question_bank.csv')


@app.route('/export/json')
def export_json():
    questions = fetch_all_questions()
    payload = json.dumps(questions, indent=2, ensure_ascii=False)
    return send_file(io.BytesIO(payload.encode('utf-8')), mimetype='application/json', as_attachment=True, download_name='question_bank.json')


@app.route('/api/questions')
def api_questions():
    return jsonify(fetch_all_questions())


@app.route('/api/questions/<int:question_id>')
def api_question(question_id):
    question = fetch_question_by_id(question_id)
    if question is None:
        return jsonify({'error': 'Question not found'}), 404
    return jsonify(question)


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message='The page you requested could not be found.'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message='A server error occurred while processing your request. Please try again later.'), 500


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
