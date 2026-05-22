from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_for_aduu_project"

# Найдвартай линк (Хэрэв Render дээр тохируулаагүй бол шууд эндээс уншина)
MONGO_URI = os.environ.get(
    "MONGO_URI", 
    "mongodb+srv://aduuuser:aduu1234@cluster0.p0vqq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

# Өгөгдлийн сантай шууд холбох
client = MongoClient(MONGO_URI)
db = client['aduu_database']
users_col = db['users']
horses_col = db['horses']

@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login')
    
    username = session['username']
    all_horses = list(horses_col.find({"username": username}))
    
    stallions = sorted(list(set([h['stallion'].strip() for h in all_horses if h.get('stallion') and h['stallion'].strip()])))
    selected_stallion = request.args.get('filter_stallion', '').strip()
    
    if selected_stallion:
        horses = [h for h in all_horses if h.get('stallion', '').strip().lower() == selected_stallion.lower()]
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

    new_horse = {
        "username": username,
        "name": name,
        "age": age,
        "color": color,
        "mark": mark,
        "stallion": stallion
    }
    
    horses_col.insert_one(new_horse)
    return redirect('/')

@app.route('/delete/<string:horse_name>')
def delete_horse(horse_name):
    if 'username' not in session:
        return redirect('/login')
    
    username = session['username']
    horses_col.delete_one({"username": username, "name": horse_name})
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        user = users_col.find_one({"username": username})
        if user and user['password'] == password:
            session['username'] = username
            return redirect('/')
        return render_template('login.html', error="Хэрэглэгчийн нэр эсвэл нууц үг буруу байна!")
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        if users_col.find_one({"username": username}):
            return render_template('register.html', error="Энэ хэрэглэгчийн нэр бүртгэлтэй байна!")
            
        users_col.insert_one({"username": username, "password": password})
        session['username'] = username
        return redirect('/')
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)