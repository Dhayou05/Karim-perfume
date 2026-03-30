from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pandas as pd
import os
import json
from datetime import timedelta
from pymongo import MongoClient
import re
from dotenv import load_dotenv
import certifi
import dns.resolver

# Fix SRV resolution timeouts by forcing Google DNS
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'perfume_secret_key_123')
app.permanent_session_lifetime = timedelta(hours=1)

UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# setup mongodb client
MONGO_URI_FALLBACK = "mongodb+srv://karimperfum_db_user:karim-perfm05@cluster0.0n7io2u.mongodb.net/?retryWrites=true&w=majority&readPreference=secondaryPreferred&serverSelectionTimeoutMS=5000&appName=Cluster0"
MONGO_URI = os.getenv("MONGO_URI", MONGO_URI_FALLBACK)
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.perfume_store
perfumes_collection = db.perfumes

questions = [
    {'id': 0, 'question': "ما هو الانطباع الأول الذي ترغب في تركه عند دخولك لمكان ما؟", 'answers': ["أناقة وفخامة هادئة", "قوة، ثقة، وحضور طاغٍ", "حيوية، نظافة، وانتعاش"]},
    {'id': 1, 'question': "ما هي عائلة النوتات العطرية التي تميل إليها بطبيعتك؟", 'answers': ["الأخشاب، العود، والتوابل الشرقية الدافئة", "الزهور الناعمة والفواكه الحلوة", "الليمون، البرغموت، والنسيم البحري"]},
    {'id': 2, 'question': "في أي بيئة تقضي معظم وقتك طوال اليوم؟", 'answers': ["مكتب العمل أو اجتماعات مغلقة", "حركة مستمرة وأماكن مفتوحة", "سهرات ليلية ومناسبات خاصة"]},
    {'id': 3, 'question': "كيف تفضل أن يكون مدى فوحان (انتشار) عطرك؟", 'answers': ["هادئ ومقتصر على من يقترب مني", "معتدل يترك أثراً أنيقاً عند المرور", "قوي يملأ المكان بمجرد الدخول"]},
    {'id': 4, 'question': "لو اخترت رائحة لرحلة إجازة، أي الوجهات التالية تشبه ذوقك؟", 'answers': ["مدينة أوروبية شتوية وأجواء باردة", "جزيرة مشمسة وشواطئ استوائية", "منتجع طبيعي مليء بالأعشاب والهدوء"]},
    {'id': 5, 'question': "أي التركيبات التالية تثير مشاعرك وتشعرك بالراحة الفورية؟", 'answers': ["الورد الجوري الممزوج بلمسة فانيليا كريمية", "أخشاب الصندل والعنبر مع لمحة من الدخان أو البخور", "الشاي الأخضر، اللافندر، أو الحمضيات اللاذعة"]},
    {'id': 6, 'question': "ما هي الخاصية الأهم بالنسبة لك عند شراء عطر باهظ الثمن؟", 'answers': ["ثبات الرائحة (أكثر من 12 ساعة متواصلة)", "التميز والندرة (ألا يكون مكرراً بين الناس)", "نعومة الرائحة وسهولة تقبلها في جميع الأوقات"]},
    {'id': 7, 'question': "كيف تعبر عن أسلوب ملابسك الشخصي (الذي يعكس شخصيتك)؟", 'answers': ["الألوان الداكنة والبدلات الرسمية أو الفخمة", "ملابس كاجوال خفيفة ومريحة وألوان فاتحة", "أزياء عصرية وألوان جريئة لافتة للأنظار"]},
    {'id': 8, 'question': "مرحلة تطور العطر على الجلد: ما الذي تفضله؟", 'answers': ["أحب أن يتغير العطر مع الوقت وتظهر نوتات جديدة معقدة", "أفضل أن تلفتني الفتحة (الرشة الأولى) وأن تبقى الرائحة كما هي", "أهتم فقط لما تبقى من الرائحة بعد ساعات طويلة على ملابسي"]},
    {'id': 9, 'question': "متى تشعر أنك في أمسّ الحاجة لارتداء عطرك المميز؟", 'answers': ["عندما أستعد لمقابلة عمل أو صفقة مهمة", "كل صباح كروتين يومي لتجديد النشاط والثقة", "في الأمسيات الليلة الرومانسية أو الأعراس"]}
]

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password123')

def get_all_perfumes():
    return list(perfumes_collection.find({}, {'_id': 0}).sort('like_percent', -1))

import random

def generate_recommendations(user_answers, target_gender=None):
    score = 0
    for answer in user_answers.values():
        try:
            score += int(answer)
        except:
            pass
    query = {'hidden': {'$ne': True}}
    if target_gender in ['male', 'female']:
        query['$or'] = [
            {'gender_target': {'$in': [target_gender, 'unisex']}},
            {'gender_target': {'$exists': False}}
        ]
        
    visible_perfumes = list(perfumes_collection.find(query, {'_id': 0}).sort('like_percent', -1))
    if not visible_perfumes:
        return []
    
    num_to_select = min(3, len(visible_perfumes))
    rng = random.Random(score)
    selected_perfumes = rng.sample(visible_perfumes, num_to_select)
    
    selected_perfumes.sort(key=lambda x: x.get('like_percent', 0), reverse=True)
    return selected_perfumes

def get_next_perfume_id():
    last_perfume = perfumes_collection.find_one(sort=[('id', -1)])
    if not last_perfume or 'id' not in last_perfume:
        return 1
    return last_perfume['id'] + 1

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/start/<gender>')
def start_quiz(gender):
    session.clear()
    session['target_gender'] = gender
    return redirect(url_for('question', question_id=0))

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
    
    recommendations = generate_recommendations(session['answers'], session.get('target_gender'))
    return render_template('result.html', perfumes=recommendations)

@app.route('/restart')
def restart():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/rate/<int:perfume_id>', methods=['POST'])
def rate_perfume(perfume_id):
    data = request.get_json()
    action = data.get('action')
    perfume = perfumes_collection.find_one({'id': perfume_id})
    if not perfume:
        return jsonify({'success': False, 'message': 'العطر غير موجود'}), 404

    like_count = perfume.get('like_count', 0)
    dislike_count = perfume.get('dislike_count', 0)

    if action == 'like':
        like_count += 1
    elif action == 'dislike':
        dislike_count += 1
    else:
        return jsonify({'success': False, 'message': 'إجراء غير صالح'}), 400

    total = like_count + dislike_count
    if total > 0:
        like_percent = round((like_count / total) * 100)
        dislike_percent = round((dislike_count / total) * 100)
    else:
        like_percent = 0
        dislike_percent = 0

    perfumes_collection.update_one(
        {'id': perfume_id},
        {'$set': {
            'like_count': like_count,
            'dislike_count': dislike_count,
            'like_percent': like_percent,
            'dislike_percent': dislike_percent
        }}
    )

    return jsonify({
        'success': True,
        'like_percent': like_percent,
        'dislike_percent': dislike_percent
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
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
    suggestions = []

    if search_query:
        regex_query = re.compile(f".*{re.escape(search_query)}.*", re.IGNORECASE)
        filtered_perfumes = list(perfumes_collection.find({'name': regex_query}, {'_id': 0}).sort('like_percent', -1))
        
        if not filtered_perfumes:
            query_words = search_query.split()
            regex_words = [re.compile(f".*{re.escape(w)}.*", re.IGNORECASE) for w in query_words]
            suggestions = list(perfumes_collection.find({'name': {'$in': regex_words}}, {'_id': 0}).limit(5))
    else:
        filtered_perfumes = get_all_perfumes()

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
            'gender_target': request.form.get('gender_target', 'unisex'),
            'image_url': image_url,
            'hidden': False,
            'like_percent': 0,
            'dislike_percent': 0,
            'like_count': 0,
            'dislike_count': 0
        }
        perfumes_collection.insert_one(new_perfume)
        flash('تم إضافة العطر بنجاح!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_perfume.html')

@app.route('/admin/edit/<int:perfume_id>', methods=['GET', 'POST'])
def edit_perfume(perfume_id):
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول لتعديل العطور.', 'warning')
        return redirect(url_for('login'))
    
    perfume = perfumes_collection.find_one({'id': perfume_id}, {'_id': 0})
    if not perfume:
        flash('لم يتم العثور على العطر.', 'danger')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        notes = [note.strip() for note in request.form['notes'].split(',') if note.strip()]
        update_data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'notes': notes,
            'profile': request.form['profile'],
            'gender_target': request.form.get('gender_target', 'unisex')
        }
        
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                image_file.save(image_path)
                update_data['image_url'] = f"/{image_path}"
        
        perfumes_collection.update_one({'id': perfume_id}, {'$set': update_data})
        flash('تم تحديث العطر بنجاح!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('edit_perfume.html', perfume=perfume)

@app.route('/admin/delete/<int:perfume_id>')
def delete_perfume(perfume_id):
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول لحذف العطور.', 'warning')
        return redirect(url_for('login'))
    
    perfumes_collection.delete_one({'id': perfume_id})
    flash('تم حذف العطر بنجاح!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/toggle_hide/<int:perfume_id>')
def toggle_hide_perfume(perfume_id):
    if not session.get('admin_logged_in'):
        flash('يرجى تسجيل الدخول لتعديل العطور.', 'warning')
        return redirect(url_for('login'))
    
    perfume = perfumes_collection.find_one({'id': perfume_id})
    if perfume:
        new_status = not perfume.get('hidden', False)
        perfumes_collection.update_one({'id': perfume_id}, {'$set': {'hidden': new_status}})
        status = 'مخفي' if new_status else 'ظاهر'
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
                
                new_perfumes = []
                current_id = get_next_perfume_id()
                for _, row in df.iterrows():
                    new_perfume = {
                        'id': current_id,
                        'name': row['Name'],
                        'description': row['Description'],
                        'notes': row['Notes'].split(',') if 'Notes' in row and isinstance(row['Notes'], str) else [],
                        'profile': row['Profile'] if 'Profile' in row else '',
                        'gender_target': 'unisex',
                        'image_url': row['Image URL'] if 'Image URL' in row else '',
                        'hidden': False,
                        'like_percent': 0,
                        'dislike_percent': 0,
                        'like_count': 0,
                        'dislike_count': 0
                    }
                    new_perfumes.append(new_perfume)
                    current_id += 1
                
                if new_perfumes:
                    perfumes_collection.insert_many(new_perfumes)
                flash('تم رفع البيانات بنجاح!', 'success')
                return redirect(url_for('admin'))
            except Exception as e:
                flash(f'خطأ في معالجة الملف: {str(e)}', 'danger')
        else:
            flash('تنسيق الملف غير صالح. يرجى رفع ملف Excel.', 'danger')
    
    return render_template('upload_data.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)