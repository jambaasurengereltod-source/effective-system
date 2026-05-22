from flask import Flask, render_template, request, redirect, session, url_parser
import json
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_for_aduu_project"
DATA_FILE = "users.json"

# Өгөгдөл хадгалах, унших функцууд
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "horses": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"users": {}, "horses": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login')
    
    username = session['username']
    data = load_data()
    
    # Зөвхөн тухайн нэвтэрсэн малчны адуунуудыг шүүж авна
    all_horses = data.get("horses", {}).get(username, [])
    
    # Бүртгэлтэй байгаа бүх азаргануудын нэрсийг давхардахгүйгээр жагсааж авах
    stallions = sorted(list(set([h['stallion'].strip() for h in all_horses if h.get('stallion') and h['stallion'].strip()])))
    
    # HTML-ээс ирж буй шүүлтүүрийн утга
    selected_stallion = request.args.get('filter_stallion', '').strip()
    
    # Хэрэв азарга сонгосон байвал адуугаа шүүнэ (Том жижиг үсэг харгалзахгүй)
    if selected_stallion:
        horses = [h for h in all_horses if h.get('stallion', '').strip().lower() == selected_stallion.lower()]
    else:
        horses = all_horses

    return render_template('index.html', horses=horses, stallions=stallions, selected_stallion=selected_stallion)

@app.route('/add', models=['POST'])
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

    data = load_data()
    if "horses" not in data:
        data["horses"] = {}
    if username not in data["horses"]:
        data["horses"][username] = []

    # Шинэ адууны ID үүсгэх
    horse_id = len(data["horses"][username]) + 1
    
    new_horse = {
        "id": horse_id,
        "name": name,
        "age": age,
        "color": color,
        "mark": mark,
        "stallion": stallion
    }
    
    data["horses"][username].append(new_horse)
    save_data(data)
    return redirect('/')

@app.route('/delete/<int:horse_id>')
def delete_horse(horse_id):
    if 'username' not in session:
        return redirect('/login')
    
    username = session['username']
    data = load_data()
    
    if username in data.get("horses", {}):
        data["horses"][username] = [h for h in data["horses"][username] if h['id'] != horse_id]
        save_data(data)
        
    return redirect('/')

@app.route('/login', models=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        data = load_data()
        if username in data['users'] and data['users'][username] == password:
            session['username'] = username
            return redirect('/')
        return render_template('login.html', error="Хэрэглэгчийн нэр эсвэл нууц үг буруу байна!")
        
    return render_template('login.html')

@app.route('/register', models=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        data = load_data()
        if username in data['users']:
            return render_template('register.html', error="Энэ хэрэглэгчийн нэр бүртгэлтэй байна!")
            
        data['users'][username] = password
        save_data(data)
        session['username'] = username
        return redirect('/')
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)