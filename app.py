from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key_for_aduu_project"

# --- ЗУРАГ ХАДГАЛАХ ТОХИРГОО ---
# static/uploads хавтсыг зураг хадгалах үндсэн газар болгож заана
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Зургийн файлын дээд хэмжээг 16MB-аар хязгаарлана (Сервер гацахаас сэргийлнэ)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

# Зөвхөн дараах өргөтгөлтэй зургийн файлуудыг зөвшөөрнө
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ӨГӨГДЛИЙН САНГИЙН ТОХИРГОО ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///aduu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Хэрэглэгчийн хүснэгт
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Адууны хүснэгт
class Horse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    mark = db.Column(db.String(100), nullable=True)
    stallion = db.Column(db.String(100), nullable=False)
    # ШИНЭ: Зургийн файлын нэрийг хадгалах багана (Зураггүй үед default_horse.jpg-ийг харуулна)
    image_file = db.Column(db.String(200), nullable=True, default='default_horse.jpg') 

# Дээрх uploads хавтас байхгүй бол систем өөрөө автомат үүсгэнэ
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

with app.app_context():
    db.create_all()

# --- ВЭБ САЙТЫН МАРШРУТУУД ---

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
    stallion = request.form.get('stallion', '').strip()

    if not stallion:
        stallion = "Тодорхойгүй"

    # --- ЗУРАГ ХҮЛЭЭН АВАХ ШИНЭ ХЭСЭГ ---
    image_name = 'default_horse.jpg' # Хэрэглэгч зураг оруулахгүй бол ашиглах үндсэн нэр
    
    if 'image' in request.files:
        file = request.files['image']
        # Хэрэглэгч файл сонгосон бөгөөд зөвшөөрөгдсөн зураг мөн эсэхийг шалгана
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Өөр өөр малчид ижил нэртэй зураг оруулбал давхцахаас сэргийлж урд нь хэрэглэгчийн нэрийг залгана
            unique_filename = f"{username}_{filename}"
            # Файлыг static/uploads хавтсанд хадгална
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            image_name = unique_filename

    new_horse = Horse(
        username=username,
        name=name,
        age=age,
        color=color,
        mark=mark,
        stallion=stallion,
        image_file=image_name # Зургийн нэрийг өгөгдлийн санд хадгалах
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
        # Хэрэв устгах гэж буй адуу зурагтай байсан бол сервер дээрх зургийн файлыг нь давхар устгана
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
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            return redirect('/')
        return render_template('login.html', error="Хэрэглэгчийн нэр эсвэл нууц үг буруу байна!")
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Энэ хэрэглэгчийн нэр бүртгэлтэй байна!")
            
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        session['username'] = username
        return redirect('/')
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)