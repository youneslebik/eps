from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///video_montage_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== Models ====================

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    video_type = db.Column(db.String(20), nullable=False)
    video_url = db.Column(db.String(500))
    minutes = db.Column(db.Integer, default=0)
    seconds = db.Column(db.Integer, default=0)
    price_per_minute = db.Column(db.Float, default=3.5)
    reel_price = db.Column(db.Float, default=2.5)
    standalone_price = db.Column(db.Float, default=5.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    split_reels = db.relationship('SplitReel', backref='video', lazy=True, cascade='all, delete-orphan')

class SplitReel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    video_url = db.Column(db.String(500))

# ==================== Helper Functions ====================

def custom_round(value):
    """دالة التقريب المخصصة"""
    if not isinstance(value, (int, float)) or value != value:
        return 0
    
    absolute_value = abs(value)
    integer_part = int(absolute_value)
    fractional_part = absolute_value - integer_part
    
    if fractional_part < 0.25:
        rounded_value = integer_part
    elif fractional_part < 0.75:
        rounded_value = integer_part + 0.5
    else:
        rounded_value = integer_part + 1
    
    return rounded_value

def calculate_video_total(video):
    """حساب السعر الإجمالي للفيديو"""
    precise_total = 0
    
    if video.video_type == 'yt_reels':
        time_in_minutes = video.minutes + (video.seconds / 60)
        yt_price = time_in_minutes * video.price_per_minute
        reels_count = len(video.split_reels)
        reels_price = reels_count * video.reel_price
        precise_total = yt_price + reels_price
    
    elif video.video_type == 'yt_only':
        time_in_minutes = video.minutes + (video.seconds / 60)
        precise_total = time_in_minutes * video.price_per_minute
    
    elif video.video_type == 'reel_only':
        precise_total = video.standalone_price
    
    return custom_round(precise_total)

def init_database():
    """تهيئة قاعدة البيانات مع بيانات افتراضية"""
    with app.app_context():
        db.create_all()
        
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            print("✅ تم إنشاء حساب المسؤول الافتراضي (admin/admin123)")
        
        if not Video.query.first():
            videos_data = [
                {
                    'name': 'فيديو ريلز ميلان',
                    'video_type': 'reel_only',
                    'video_url': 'https://www.youtube.com/shorts/Z8GEh4KLMgc',
                    'standalone_price': 5.0
                },
                {
                    'name': 'غرائب الاسبوع 6',
                    'video_type': 'yt_reels',
                    'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'minutes': 4,
                    'seconds': 31,
                    'price_per_minute': 3.5,
                    'reel_price': 2.5,
                    'reels': [
                        {'name': 'ريل غرائب 6 - 1', 'url': 'https://www.youtube.com/shorts/jNQXAC9IVRw'},
                        {'name': 'ريل غرائب 6 - 2', 'url': 'https://www.youtube.com/shorts/Z8GEh4KLMgc'},
                        {'name': 'ريل غرائب 6 - 3', 'url': 'https://www.youtube.com/shorts/L_jWHffIx5E'}
                    ]
                },
                {
                    'name': 'دوري الابطال 2',
                    'video_type': 'yt_reels',
                    'video_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
                    'minutes': 3,
                    'seconds': 45,
                    'price_per_minute': 3.5,
                    'reel_price': 2.5,
                    'reels': [
                        {'name': 'ريل أبطال 2 - 1', 'url': 'https://www.youtube.com/shorts/kJQP7kiw5Fk'},
                        {'name': 'ريل أبطال 2 - 2', 'url': 'https://www.youtube.com/shorts/gCNeDWCI0vo'}
                    ]
                },
                {
                    'name': 'غرائب دوري الاسبوع 7',
                    'video_type': 'yt_only',
                    'video_url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
                    'minutes': 4,
                    'seconds': 17,
                    'price_per_minute': 3.5
                },
                {
                    'name': 'فيديو ريلز لاعبون أكبر من مدربيهم',
                    'video_type': 'reel_only',
                    'video_url': 'https://www.youtube.com/shorts/kJQP7kiw5Fk',
                    'standalone_price': 5.0
                },
                {
                    'name': 'قصة اندريس اوسكوبار',
                    'video_type': 'yt_only',
                    'video_url': 'https://www.youtube.com/watch?v=M7lc1UVf-VE',
                    'minutes': 5,
                    'seconds': 42,
                    'price_per_minute': 3.5
                },
                {
                    'name': 'ريلز مختصر لقصة اندريس اوسكوبار',
                    'video_type': 'reel_only',
                    'video_url': 'https://www.youtube.com/shorts/gCNeDWCI0vo',
                    'standalone_price': 5.0
                },
                {
                    'name': 'غرائب دوري الأسبوع 8',
                    'video_type': 'yt_reels',
                    'video_url': 'https://www.youtube.com/watch?v=ZZ5LpwO-An4',
                    'minutes': 5,
                    'seconds': 34,
                    'price_per_minute': 3.5,
                    'reel_price': 2.5,
                    'reels': [
                        {'name': 'ريل غرائب 8 - 1', 'url': 'https://www.youtube.com/shorts/L_jWHffIx5E'},
                        {'name': 'ريل غرائب 8 - 2', 'url': 'https://www.youtube.com/shorts/Z8GEh4KLMgc'},
                        {'name': 'ريل غرائب 8 - 3', 'url': 'https://www.youtube.com/shorts/jNQXAC9IVRw'},
                        {'name': 'ريل غرائب 8 - 4', 'url': 'https://www.youtube.com/shorts/kJQP7kiw5Fk'}
                    ]
                },
                {
                    'name': 'دوري الابطال 3',
                    'video_type': 'yt_only',
                    'video_url': 'https://www.youtube.com/watch?v=OPf0YbXqDm0',
                    'minutes': 4,
                    'seconds': 6,
                    'price_per_minute': 3.5
                }
            ]
            
            for video_data in videos_data:
                reels = video_data.pop('reels', [])
                video = Video(**video_data)
                db.session.add(video)
                db.session.flush()
                
                for reel_data in reels:
                    reel = SplitReel(
                        video_id=video.id,
                        name=reel_data['name'],
                        video_url=reel_data['url']
                    )
                    db.session.add(reel)
            
            print("✅ تم إضافة الفيديوهات الافتراضية")
        
        db.session.commit()
        print("✅ تم تهيئة قاعدة البيانات بنجاح!")

# ==================== Routes ====================

@app.route('/')
def index():
    """الصفحة الرئيسية - إعادة توجيه إلى صفحة العرض"""
    return redirect(url_for('display'))

@app.route('/display')
def display():
    """صفحة العرض العامة - للقراءة فقط"""
    videos = Video.query.order_by(Video.created_at).all()
    
    grand_total = 0
    videos_data = []
    
    for video in videos:
        total = calculate_video_total(video)
        grand_total += total
        
        video_dict = {
            'id': video.id,
            'name': video.name,
            'video_type': video.video_type,
            'video_url': video.video_url,
            'minutes': video.minutes,
            'seconds': video.seconds,
            'price_per_minute': video.price_per_minute,
            'reel_price': video.reel_price,
            'standalone_price': video.standalone_price,
            'split_reels': [{'id': r.id, 'name': r.name, 'video_url': r.video_url} for r in video.split_reels],
            'calculated_total': total
        }
        videos_data.append(video_dict)
    
    return render_template('display.html', videos=videos_data, grand_total=grand_total)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """صفحة تسجيل دخول المسؤول"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            flash('✅ تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """تسجيل خروج المسؤول"""
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """لوحة تحكم المسؤول"""
    if not session.get('admin_logged_in'):
        flash('⚠️ يجب تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    videos = Video.query.order_by(Video.created_at).all()
    grand_total = sum(calculate_video_total(v) for v in videos)
    return render_template('admin_dashboard.html', videos=videos, grand_total=grand_total, calculate_total=calculate_video_total)

@app.route('/admin/video/get/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """الحصول على بيانات فيديو محدد"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    video = Video.query.get_or_404(video_id)
    return jsonify({
        'success': True,
        'video': {
            'id': video.id,
            'name': video.name,
            'video_type': video.video_type,
            'video_url': video.video_url,
            'minutes': video.minutes,
            'seconds': video.seconds,
            'price_per_minute': video.price_per_minute,
            'reel_price': video.reel_price,
            'standalone_price': video.standalone_price
        }
    })

@app.route('/admin/video/add', methods=['POST'])
def add_video():
    """إضافة فيديو جديد"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    data = request.json
    
    video = Video(
        name=data['name'],
        video_type=data['video_type'],
        video_url=data.get('video_url', ''),
        minutes=data.get('minutes', 0),
        seconds=data.get('seconds', 0),
        price_per_minute=data.get('price_per_minute', 3.5),
        reel_price=data.get('reel_price', 2.5),
        standalone_price=data.get('standalone_price', 5.0)
    )
    
    db.session.add(video)
    db.session.commit()
    
    return jsonify({'success': True, 'video_id': video.id, 'message': '✅ تم إضافة الفيديو بنجاح'})

@app.route('/admin/video/update/<int:video_id>', methods=['POST'])
def update_video(video_id):
    """تحديث فيديو موجود"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    video = Video.query.get_or_404(video_id)
    data = request.json
    
    video.name = data['name']
    video.video_type = data['video_type']
    video.video_url = data.get('video_url', '')
    video.minutes = data.get('minutes', 0)
    video.seconds = data.get('seconds', 0)
    video.price_per_minute = data.get('price_per_minute', 3.5)
    video.reel_price = data.get('reel_price', 2.5)
    video.standalone_price = data.get('standalone_price', 5.0)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '✅ تم تحديث الفيديو بنجاح'})

@app.route('/admin/video/delete/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    """حذف فيديو"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '✅ تم حذف الفيديو بنجاح'})

@app.route('/admin/video/<int:video_id>/reels', methods=['GET'])
def get_video_reels(video_id):
    """الحصول على ريلات فيديو محدد"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    video = Video.query.get_or_404(video_id)
    reels = [{'id': r.id, 'name': r.name, 'video_url': r.video_url} for r in video.split_reels]
    
    return jsonify({'success': True, 'reels': reels, 'video_name': video.name})

@app.route('/admin/reel/add/<int:video_id>', methods=['POST'])
def add_reel(video_id):
    """إضافة ريل مقسم"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    video = Video.query.get_or_404(video_id)
    data = request.json
    
    reel = SplitReel(
        video_id=video_id,
        name=data['name'],
        video_url=data.get('video_url', '')
    )
    
    db.session.add(reel)
    db.session.commit()
    
    return jsonify({'success': True, 'reel_id': reel.id, 'message': '✅ تم إضافة الريل بنجاح'})

@app.route('/admin/reel/update/<int:reel_id>', methods=['POST'])
def update_reel(reel_id):
    """تحديث ريل مقسم"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    reel = SplitReel.query.get_or_404(reel_id)
    data = request.json
    
    reel.name = data['name']
    reel.video_url = data.get('video_url', '')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '✅ تم تحديث الريل بنجاح'})

@app.route('/admin/reel/delete/<int:reel_id>', methods=['POST'])
def delete_reel(reel_id):
    """حذف ريل مقسم"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    reel = SplitReel.query.get_or_404(reel_id)
    db.session.delete(reel)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '✅ تم حذف الريل بنجاح'})

# ==================== Run ====================

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
