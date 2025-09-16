from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pandas as pd
import os
import json
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'perfume_secret_key_123'  # Change this in production
app.permanent_session_lifetime = timedelta(hours=1)

UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_FILE = 'perfumes.json'

questions = [
    {'id': 0, 'question': "ما هي شخصية العطر التي تعتقد أنها تناسبك؟", 'answers': ["رومانسي وحالم", "جريء وواثق", "منعش وطبيعي"]},
    {'id': 1, 'question': "أي فصل يمثل أسلوبك بشكل أفضل؟", 'answers': ["زهور الربيع", "شمس الصيف", "دفء الشتاء"]},
    {'id': 2, 'question': "أين ترتدي العطر عادةً؟", 'answers': ["نهاراً بشكل عادي", "في الأماكن المهنية", "في المناسبات المسائية"]},
    {'id': 3, 'question': "كيف تريد أن يشعرك العطر؟", 'answers': ["أنيق ومتطور", "نشيط وحيوي", "هادئ ومرتاح"]},
    {'id': 4, 'question': "أي عائلة عطرية تجذبك أكثر؟", 'answers': ["باقات زهرية", "نوتات خشبية", "تركيبات حمضيات"]},
    {'id': 5, 'question': "ما مستوى الشدة الذي تفضله؟", 'answers': ["خفيف وخاص", "معتدل الحضور", "قوي ودائم"]},
    {'id': 6, 'question': "أي مناسبة هي الأهم لعطرك؟", 'answers': ["الارتداء اليومي", "مناسبات خاصة", "أمسيات رومانسية"]},
    {'id': 7, 'question': "ما المزاج الذي تريد إثارة؟", 'answers': ["غامض وجذاب", "مرح ومبهج", "هادئ وسلمي"]},
    {'id': 8, 'question': "أي تركيبة نوتات تبدو أكثر جاذبية؟", 'answers': ["الورد والفانيليا", "الصندل والكهرمان", "البرغموت والخزامى"]},
    {'id': 9, 'question': "كم يجب أن يدوم عطرك المثالي؟", 'answers': ["4-6 ساعات", "6-8 ساعات", "8+ ساعات"]}
]

perfume_database = []

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'  # Change this in production

def load_perfumes():
    global perfume_database
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            perfume_database = json.load(f)
    else:
        perfume_database = []

def save_perfumes():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(perfume_database, f, ensure_ascii=False, indent=4)

load_perfumes()

def generate_recommendations(user_answers):
    score = 0
    for answer in user_answers.values():
        try:
            score += int(answer)
        except:
            pass
    
    selected_indices = set()
    visible_perfumes = [p for p in perfume_database if not p.get('hidden', False)]
    if not visible_perfumes:
        return []
    
    while len(selected_indices) < 3 and len(selected_indices) < len(visible_perfumes):
        index = (score + len(selected_indices) * 2) % len(visible_perfumes)
        selected_indices.add(index)
    
    return [visible_perfumes[i] for i in selected_indices]

def get_next_perfume_id():
    if not perfume_database:
        return 1
    return max((p['id'] for p in perfume_database)) + 1

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def question(question_id):
    if question_id >= len(questions):
        return redirect(url_for('result'))
    
    if request.method == 'POST':
        if 'answers' not in session:
            session['answers'] = {}
        session['answers'][str(question_id)] = request.form.get('answer')
        session.modified = True
        
        next_question = question_id + 1
        if next_question < len(questions):
            return redirect(url_for('question', question_id=next_question))
        else:
            return redirect(url_for('result'))
    
    current_question = questions[question_id]
    progress_percent = ((question_id + 1) / len(questions)) * 100
    
    return render_template('question.html', question=current_question, question_id=question_id,
                           total_questions=len(questions), progress_percent=progress_percent)

@app.route('/result')
def result():
    if 'answers' not in session or len(session['answers']) < len(questions):
        return redirect(url_for('index'))
    
    recommendations = generate_recommendations(session['answers'])
    return render_template('result.html', perfumes=recommendations)

@app.route('/restart')
def restart():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/rate/<int:perfume_id>', methods=['POST'])
def rate_perfume(perfume_id):
    data = request.get_json()
    action = data.get('action')
    perfume = next((p for p in perfume_database if p['id'] == perfume_id), None)
    if not perfume:
        return jsonify({'success': False, 'message': 'العطر غير موجود'}), 404

    if 'like_count' not in perfume or not isinstance(perfume['like_count'], int):
        perfume['like_count'] = 0
    if 'dislike_count' not in perfume or not isinstance(perfume['dislike_count'], int):
        perfume['dislike_count'] = 0

    if action == 'like':
        perfume['like_count'] += 1
    elif action == 'dislike':
        perfume['dislike_count'] += 1
    else:
        return jsonify({'success': False, 'message': 'إجراء غير صالح'}), 400

    total = perfume['like_count'] + perfume['dislike_count']
    if total > 0:
        perfume['like_percent'] = round((perfume['like_count'] / total) * 100)
        perfume['dislike_percent'] = round((perfume['dislike_count'] / total) * 100)
    else:
        perfume['like_percent'] = 0
        perfume['dislike_percent'] = 0

    save_perfumes()
    return jsonify({
        'success': True,
        'like_percent': perfume['like_percent'],
        'dislike_percent': perfume['dislike_percent']
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        # If already logged in, redirect to admin page
        return redirect(url_for('admin'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('admin'))
        else:
            flash('بيانات الاعتماد غير صحيحة. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول للوصول إلى لوحة التحكم.', 'warning')
        return redirect(url_for('login'))
    
    search_query = request.args.get('q', '').strip()
    filtered_perfumes = perfume_database
    suggestions = []

    if search_query:
        # Filter perfumes by name containing search query (case-insensitive)
        filtered_perfumes = [p for p in perfume_database if search_query in p['name']]
        
        # If no exact matches, provide suggestions based on partial matches or similar names
        if not filtered_perfumes:
            # Simple suggestion: perfumes whose name contains any word from search query
            query_words = search_query.split()
            suggestions = []
            for p in perfume_database:
                if any(word.lower() in p['name'].lower() for word in query_words):
                    suggestions.append(p)
            # Limit suggestions to 5
            suggestions = suggestions[:5]
  


    return render_template('admin.html', perfumes=filtered_perfumes, search_query=search_query, suggestions=suggestions)
@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
   
    return response

@app.route('/admin/add', methods=['GET', 'POST'])
def add_perfume():
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول لإضافة العطور.', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        notes = [note.strip() for note in request.form['notes'].split(',') if note.strip()]
        
        if 'image' not in request.files:
            flash('لم يتم توفير ملف صورة.', 'danger')
            return redirect(url_for('add_perfume'))
        
        image_file = request.files['image']
        if image_file.filename == '':
            flash('لم يتم اختيار ملف.', 'danger')
            return redirect(url_for('add_perfume'))
        
        image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
        image_file.save(image_path)
        image_url = f"/{image_path}"
        
        new_perfume = {
            'id': get_next_perfume_id(),
            'name': request.form['name'],
            'description': request.form['description'],
            'notes': notes,
            'profile': request.form['profile'],
            'image_url': image_url,
            'hidden': False,
            'like_percent': 0,
            'dislike_percent': 0,
            'like_count': 0,
            'dislike_count': 0
        }
        perfume_database.append(new_perfume)
        save_perfumes()
        flash('تم إضافة العطر بنجاح!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_perfume.html')

@app.route('/admin/edit/<int:perfume_id>', methods=['GET', 'POST'])
def edit_perfume(perfume_id):
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول لتعديل العطور.', 'warning')
        return redirect(url_for('login'))
    
    perfume = next((p for p in perfume_database if p['id'] == perfume_id), None)
    if not perfume:
        flash('لم يتم العثور على العطر.', 'danger')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        notes = [note.strip() for note in request.form['notes'].split(',') if note.strip()]
        perfume['name'] = request.form['name']
        perfume['description'] = request.form['description']
        perfume['notes'] = notes
        perfume['profile'] = request.form['profile']
        
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                image_file.save(image_path)
                perfume['image_url'] = f"/{image_path}"
        
        save_perfumes()
        flash('تم تحديث العطر بنجاح!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('edit_perfume.html', perfume=perfume)

@app.route('/admin/delete/<int:perfume_id>')
def delete_perfume(perfume_id):
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول لحذف العطور.', 'warning')
        return redirect(url_for('login'))
    
    global perfume_database
    perfume_database = [p for p in perfume_database if p['id'] != perfume_id]
    save_perfumes()
    flash('تم حذف العطر بنجاح!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/toggle_hide/<int:perfume_id>')
def toggle_hide_perfume(perfume_id):
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول لتعديل العطور.', 'warning')
        return redirect(url_for('login'))
    
    perfume = next((p for p in perfume_database if p['id'] == perfume_id), None)
    if perfume:
        perfume['hidden'] = not perfume.get('hidden', False)
        save_perfumes()
        status = 'مخفي' if perfume['hidden'] else 'ظاهر'
        flash(f'تم تحديث حالة العطر إلى: {status}', 'success')
    else:
        flash('لم يتم العثور على العطر.', 'danger')
    return redirect(url_for('admin'))

@app.route('/admin/upload', methods=['GET', 'POST'])
def upload_data():
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول لرفع البيانات.', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)
                required_columns = ['Name', 'Description', 'Notes', 'Profile', 'Image URL']
                for col in required_columns:
                    if col not in df.columns:
                        flash(f'عمود مطلوب مفقود: {col}', 'danger')
                        return redirect(url_for('upload_data'))
                
                for _, row in df.iterrows():
                    new_perfume = {
                        'id': get_next_perfume_id(),
                        'name': row['Name'],
                        'description': row['Description'],
                        'notes': row['Notes'].split(',') if 'Notes' in row and isinstance(row['Notes'], str) else [],
                        'profile': row['Profile'] if 'Profile' in row else '',
                        'image_url': row['Image URL'] if 'Image URL' in row else '',
                        'hidden': False,
                        'like_percent': 0,
                        'dislike_percent': 0,
                        'like_count': 0,
                        'dislike_count': 0
                    }
                    perfume_database.append(new_perfume)
                
                save_perfumes()
                flash('تم رفع البيانات بنجاح!', 'success')
                return redirect(url_for('admin'))
            except Exception as e:
                flash(f'خطأ في معالجة الملف: {str(e)}', 'danger')
        else:
            flash('تنسيق الملف غير صالح. يرجى رفع ملف Excel.', 'danger')
    
    return render_template('upload_data.html')

if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=5000, debug=True)