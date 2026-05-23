import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = "aduu_secret_key_123"

# Cloudinary Тохиргоо
cloudinary.config(
    cloud_name="dnaspppgk",
    api_key="188174488349258",
    api_secret="986z60OAsv0j05ZHehCHLzBvGhk"
)

# --- POSTGRESQL ӨГӨГДЛИЙН САНГИЙН ТОХИРГОО ---
if os.environ.get('RENDER'):
    # Таны өгсөн жинхэнэ PostgreSQL URL-ийг шууд энд холбов
    db_url = "postgresql://aduu_db_crhp_user:80mljWGsg7L5oKOrUIFaRR1rx3Mv4vTQ@dpg-d88igkdckfvc73fn088g-a/aduu_db_crhp"
    
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # Компьютер дээр чинь ажиллахдаа хуучин шигээ SQLite-аа ашиглана
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'aduu_local.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- ӨГӨГДЛИЙН САНГИЙН МОДЕЛУУД ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Horse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    mark = db.Column(db.String(100), nullable=True)
    stallion = db.Column(db.String(100), nullable=False)
    dam = db.Column(db.String(100), nullable=True)
    herd_stallion = db.Column(db.String(100), nullable=True)
    image_file = db.Column(db.String(200), nullable=False, default='default')

# --- СҮЛЖЭЭНИЙ СУВАГ (ROUTES) ---

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sw.js', mimetype='application/javascript')

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    selected_stallion = request.args.get('filter_stallion', '')
    
    all_horses = Horse.query.filter_by(user_id=session['user_id']).all()
    stallions = sorted(list(set([h.stallion for h in all_horses if h.stallion])))
    
    query = Horse.query.filter_by(user_id=session['user_id'])
    if selected_stallion:
        query = query.filter_by(stallion=selected_stallion)
        
    horses = query.all()
    return render_template('index.html', horses=horses, stallions=stallions, selected_stallion=selected_stallion)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Хэрэглэгчийн нэр эсвэл нууц үг буруу байна.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template('register.html', error="Хэрэглэгчийн нэр эсвэл и-мэйл аль хэдийн бүртгэгдсэн байна.")
            
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return render_template('login.html', success="Бүртгэл амжилттай! Та нэвтэрч орно уу.")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add_horse():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    name = request.form['name']
    age = request.form['age']
    color = request.form['color']
    mark = request.form.get('mark', '')
    stallion = request.form['stallion']
    dam = request.form.get('dam', '')
    herd_stallion = request.form.get('herd_stallion', '')
    
    image_url = 'default'
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            try:
                upload_result = cloudinary.uploader.upload(file)
                image_url = upload_result['secure_url']
            except Exception as e:
                print("Зураг хуулахад алдаа гарлаа:", e)

    new_horse = Horse(
        user_id=session['user_id'],
        name=name, age=age, color=color, mark=mark,
        stallion=stallion, dam=dam, herd_stallion=herd_stallion,
        image_file=image_url
    )
    db.session.add(new_horse)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/horse/<int:horse_id>')
def horse_detail(horse_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    horse = Horse.query.get_or_404(horse_id)
    if horse.user_id != session['user_id']:
        return "Хандах эрхгүй байна!", 403
    return f"<h3>🐴 {horse.name}</h3><p>Нас: {horse.age}</p><p>Зүс: {horse.color}</p><p>Эцэг: {horse.stallion}</p><br><a href='/'>Буцах</a>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)