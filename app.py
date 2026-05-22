from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'aduu_nuuts_tulhuur_2026'

# Файлуудын нэр (Компьютер дээр файл болж хадгалагдана)
USERS_FILE = 'users.json'
HORSES_FILE = 'horses.json'

# --- ФАЙЛААС МЭДЭЭЛЭЛ УНШИХ ФУНКЦУУД ---
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"admin": "1234"} # Файл байхгүй бол анхны хэрэглэгч

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def load_horses():
    if os.path.exists(HORSES_FILE):
        with open(HORSES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Файл байхгүй бол анхны хэдэн адууг оруулж өгөх
    return [
        {"id": 1, "name": "Хонгор үрээ", "age": "Шүдлэн", "color": "Хонгор", "brand": "Сартай", "stallion": "Хөх Төмөр"},
        {"id": 2, "name": "Хээр гүү", "age": "Их нас", "color": "Хээр", "brand": "Галтай", "stallion": "Хөх Төмөр"},
        {"id": 3, "name": "Цагаан охин даага", "age": "Даага", "color": "Цагаан", "brand": "Сартай", "stallion": "Хурдан Цагаан"}
    ]

def save_horses(horses):
    with open(HORSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(horses, f, ensure_ascii=False, indent=4)


# --- НҮҮР ХҮҮДАС (ЖАГСААЛТ БОЛОН ШҮҮЛТҮҮР) ---
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    horses_db = load_horses() # Файлаас адуунуудаа унших
    selected_stallion = request.args.get('stallion_filter')
    all_stallions = sorted(list(set([h['stallion'] for h in horses_db if h.get('stallion')])))

    if selected_stallion:
        filtered_horses = [h for h in horses_db if h.get('stallion') == selected_stallion]
    else:
        filtered_horses = horses_db

    return render_template('index.html', 
                           horses=filtered_horses, 
                           stallions=all_stallions, 
                           selected_stallion=selected_stallion, 
                           current_user=session.get('user'))

# --- НЭВТРЭХ ХҮҮДАС ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        users_db = load_users() # Файлаас хэрэглэгчдийг унших
        
        if username in users_db and users_db[username] == password:
            session['logged_in'] = True
            session['user'] = username
            return redirect(url_for('index'))
        else:
            error = 'Нэвтрэх нэр эсвэл нууц үг буруу байна!'
            
    return render_template('login.html', error=error)

# --- БҮРТГҮҮЛЭХ ХҮҮДАС ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        users_db = load_users() # Файлаас одоо байгаа хэрэглэгчдийг унших
        
        if not username or not password:
            error = 'Бүх талбарыг бөглөнө үү!'
        elif username in users_db:
            error = 'Энэ хэрэглэгчийн нэр аль хэдийн бүртгэгдсэн байна!'
        elif password != confirm_password:
            error = 'Нууц үгнүүд хоорондоо таарахгүй байна!'
        else:
            users_db[username] = password
            save_users(users_db) # Шинэ малчныг ФАЙЛ РУУ ХАДГАЛАХ
            success = 'Амжилттай бүртгүүллээ! Одоо нэвтрэх хэсэг рүү очиж нэвтэрнэ үү.'
            
    return render_template('register.html', error=error, success=success)

# --- СИСТЕМЭЭС ГАРАХ ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user', None)
    return redirect(url_for('login'))

# --- ШИНЭ АДУУ НЭМЭХ ---
@app.route('/add', methods=['POST'])
def add_horse():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        horses_db = load_horses() # Файлаас унших
        
        name = request.form.get('name')
        age = request.form.get('age')
        color = request.form.get('color')
        brand = request.form.get('brand')
        stallion = request.form.get('stallion')
        
        new_id = max([h['id'] for h in horses_db]) + 1 if horses_db else 1
        
        new_horse = {
            "id": new_id,
            "name": name,
            "age": age,
            "color": color,
            "brand": brand,
            "stallion": stallion
        }
        horses_db.append(new_horse)
        save_horses(horses_db) # Шинэ адууг ФАЙЛ РУУ ХАДГАЛАХ
        return redirect(url_for('index'))

# --- АДУУ УСТГАХ ---
@app.route('/delete/<int:horse_id>')
def delete_horse(horse_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    horses_db = load_horses() # Файлаас унших
    horses_db = [horse for horse in horses_db if horse['id'] != horse_id]
    save_horses(horses_db) # Хассан жагсаалтыг ФАЙЛ РУУ БУЦААЖ ХАДГАЛАХ
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)