from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key_for_aduu_project"

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Өгөгдлийн сангийн холболт
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///aduu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- ӨГӨГДЛИЙН САНГИЙН ХҮСНЭГТҮҮД ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # ШИНЭ: И-мэйл багана
    password = db.Column(db.String(80), nullable=False)

class Horse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(50), nullable=False) 
    color = db.Column(db.String(50), nullable=False)
    mark = db.Column(db.String(100), nullable=True)
    stallion = db.Column(db.String(100), nullable=False) 
    dam = db.Column(db.String(100), nullable=True, default="Тодорхойгүй") 
    herd_stallion = db.Column(db.String(100), nullable=True, default="Тодорхойгүй") 
    image_file = db.Column(db.String(200), nullable=True, default='default_horse.jpg')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login')
    
    username = session['username']
    all_horses = Horse.query.filter_by(username=username).all()
    
    stallions = sorted(list(set([h.stallion.strip() for h in all_horses if h.stallion and h.stallion.strip()])))
    selected_stallion = request.args.get('filter_stallion', '').strip()
    
    if selected_stallion:
        horses = Horse.query.filter_by(username=username, stallion=selected_stallion).all()
    else:
        horses = all_horses

    return render_template('index.html', horses=horses, stallions=stallions, selected_stallion=selected_stallion)

@app.route('/add', methods=['POST'])
def add_horse():
    if 'username' not in session:
        return redirect('/login')
    
    username = session['username']
    name = request.form.get('name')
    age = request.form.get('age') 
    color = request.form.get('color')
    mark = request.form.get('mark', '')
    stallion = request.form.get('stallion', '').strip() or "Тодорхойгүй"
    dam = request.form.get('dam', '').strip() or "Тодорхойгүй" 
    herd_stallion = request.form.get('herd_stallion', '').strip() or "Тодорхойгүй" 

    image_name = 'default_horse.jpg'
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{username}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            image_name = unique_filename

    new_horse = Horse(
        username=username, name=name, age=age, color=color, mark=mark,
        stallion=stallion, dam=dam, herd_stallion=herd_stallion, image_file=image_name
    )
    db.session.add(new_horse)
    db.session.commit()
    return redirect('/')

@app.route('/delete/<int:horse_id>')
def delete_horse(horse_id):
    if 'username' not in session:
        return redirect('/login')
    
    username = session['username']
    horse = Horse.query.filter_by(id=horse_id, username=username).first()
    if horse:
        if horse.image_file != 'default_horse.jpg':
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], horse.image_file))
            except:
                pass
        db.session.delete(horse)
        db.session.commit()
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Хэрэглэгч нэр эсвэл И-мэйлийн алинаар нь ч нэвтэрч болно
        login_input = request.form.get('username').strip()
        password = request.form.get('password')
        
        user = User.query.filter((User.username == login_input) | (User.email == login_input)).first()
        if user and user.password == password:
            session['username'] = user.username
            return redirect('/')
        return render_template('login.html', error="Нэвтрэх нэр эсвэл нууц үг буруу байна!")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Энэ хэрэглэгчийн нэр бүртгэлтэй байна!")
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error="Энэ и-мэйл хаяг аль хэдийн бүртгэгдсэн байна!")
            
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect('/')
    return render_template('register.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        new_password = request.form.get('new_password')
        
        # И-мэйл хаягаар нь хайж нууц үгийг солино
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = new_password
            db.session.commit()
            return render_template('login.html', success="Нууц үг амжилттай солигдлоо! Шинэ нууц үгээрээ нэвтэрнэ үү.")
        return render_template('reset_password.html', error="Энэ и-мэйл хаяг бүртгэлгүй байна!")
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)