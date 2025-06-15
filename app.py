from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import re
from flask import request, flash, redirect, url_for


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Важливо для сесій

DB = 'reservations.db'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id_, username, is_admin):
        self.id = id_
        self.username = username
        self.is_admin = is_admin

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1], bool(row[2]))
    return None

def get_user_by_username(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, username, password, is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'password': row[2], 'is_admin': bool(row[3])}
    return None

def user_exists(username):
    return get_user_by_username(username) is not None

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

def init_db():
    db_exists = os.path.exists(DB)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if not db_exists:
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_from TEXT NOT NULL,
                date_to TEXT NOT NULL,
                rooms INTEGER NOT NULL,
                room_type TEXT NOT NULL,
                guests INTEGER NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        admin_password = generate_password_hash("123")
        c.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', ("admin", admin_password, 1))
    else:
        # Якщо таблиці reviews немає — створюємо
        try:
            c.execute('SELECT 1 FROM reviews LIMIT 1')
        except sqlite3.OperationalError:
            c.execute('''
                CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    message TEXT NOT NULL,
    approved BOOLEAN DEFAULT 0
);
            ''')

    try:
        c.execute("ALTER TABLE reservations ADD COLUMN user_id INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE reservations ADD COLUMN room_type TEXT NOT NULL DEFAULT 'Двомісна'")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE reviews ADD COLUMN approved INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

@app.route('/')git add app.py
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    return redirect(url_for('menu_category', category='hot'))

@app.route('/menu/<category>')
def menu_category(category):
    categories = {
        'hot': {
            'title': 'Гарячі страви',
            'dishes': [
                ('🥣 Борщ український зі сметаною', 120, 'images/1.jpg'),
                ('🥟 Вареники з картоплею та грибами', 110, 'images/2.jpg'),
                ('🍲 Котлета по-київськи', 180, 'images/3.jpg'),
                ('🍛 Галушки з м’ясом', 130, 'images/4.jpg'),
                ('🍖 Запечена свинина з овочами', 220, 'images/5.jpg'),
                ('🥗 Овочевий борщ із домашнім хлібом', 115, 'images/6.jpg'),
                ('🍗 Курячі крильця барбекю', 190, 'images/7.jpg'),
                ('🥘 Рагу з яловичини та овочів', 250, 'images/8.jpg'),
            ]
        },
        'japanese': {
            'title': 'Японська кухня',
            'dishes': [
                ('🍣 Суші-сет "Срібний лев"', 300, 'images/11.jpg'),
                ('🍜 Рамен з куркою', 200, 'images/12.jpg'),
                ('🍡 Мочі з полуницею', 80, 'images/13.jpg'),
                ('🍵 Зелений чай матча', 90, 'images/14.jpg'),
                ('🥢 Темпура з овочами', 180, 'images/15.jpg'),
                ('🍤 Ебі-фрай (смажені креветки)', 220,'images/16.jpg'),
                ('🍙 Онігірі з лососем', 130, 'images/17.jpg'),
                ('🍥 Такоякі (кульки з восьминога)', 170, 'images/18.jpg'),
            ]
        },
        'drinks': {
            'title': 'Напої',
            'dishes': [
                ('🍹 Свіжовижатий сік', 70, 'images/41.jpg'),
                ('🍶 Традиційне саке', 150, 'images/42.jpg'),
                ('☕ Кава американо', 60, 'images/43.jpg'),
                ('🍵 Зелений чай матча', 90, 'images/14.jpg'),
                ('🥤 Домашній лимонад', 80, 'images/45.jpg'),
                ('🍺 Пиво (світле/темне)', 90, 'images/46.jpg'),
                ('🍷 Червоне вино', 180, 'images/47.jpg'),
                ('🍸 Коктейль "Мохіто"', 220, 'images/48.jpg'),
            ]
        },
        'salads': {
            'title': 'Салати',
            'dishes': [
                ('🥗 Салат "Цезар" з куркою', 130, 'images/21.jpg'),
                ('🥬 Грецький салат', 110, 'images/22.jpg'),
                ('🌽 Олів’є', 100, 'images/23.jpg'),
                ('🥒 Овочевий салат із оливковою олією', 90, 'images/24.jpg'),
                ('🥑 Авокадо з томатами', 140, 'images/25.jpg'),
                ('🍅 Капрезе з моцарелою', 150, 'images/26.jpg'),
                ('🌿 Салат з руколою та горіхами', 160, 'images/27.jpg'),
                ('🥕 Морквяний салат з родзинками', 95, 'images/28.jpg'),
            ]
        },
        'desserts': {
            'title': 'Десерти',
            'dishes': [
                ('🍰 Тірамісу', 120, 'images/31.jpg'),
                ('🍮 Десерт "Наполеон"', 100, 'images/32.jpg'),
                ('🍓 Полуниця зі збитими вершками', 90, 'images/33.jpg'),
                ('🍫 Шоколадний мус', 130, 'images/34.jpg'),
                ('🍪 Печиво "Орео"', 80, 'images/35.jpg'),
                ('🍧 Мохіто сорбет', 110, 'images/36.jpg'),
                ('🍨 Ванільне морозиво', 95, 'images/37.jpg'),
                ('🥧 Чізкейк з ягодами', 140, 'images/38.jpg'),
            ]
        }
        
    }

    if category not in categories:
        return render_template('404.html'), 404

    data = categories[category]
    return render_template('menu_category.html', title=data['title'], dishes=data['dishes'])

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        if 'review' in request.form:
            # Додавання відгуку
            name = request.form['name']
            text = request.form['review']
            c.execute("INSERT INTO reviews (name, text, approved) VALUES (?, ?, 0)", (name, text))
            conn.commit()
            flash("Відгук надіслано на модерацію.", "info")
            conn.close()
            return redirect(url_for('contacts'))

        elif 'review_id' in request.form:
            action = request.form.get('action')

            if action == 'approve':
                c.execute("UPDATE reviews SET approved = 1 WHERE id = ?", (request.form['review_id'],))
                conn.commit()
                flash("Відгук схвалено.", "success")

            elif action == 'delete':
                c.execute("DELETE FROM reviews WHERE id = ?", (request.form['review_id'],))
                conn.commit()
                flash("Відгук видалено.", "success")

            conn.close()
            return redirect(url_for('contacts'))

    # GET - вивід відгуків
    c.execute("SELECT name, text FROM reviews WHERE approved = 1")
    approved_reviews = c.fetchall()

    unapproved_reviews = []
    if current_user.is_authenticated and current_user.is_admin:
        c.execute("SELECT id, name, text FROM reviews WHERE approved = 0")
        unapproved_reviews = c.fetchall()

    conn.close()

    return render_template('contacts.html', reviews=approved_reviews, pending_reviews=unapproved_reviews)

@app.route('/moderate_reviews', methods=['GET', 'POST'])
@login_required
def moderate_reviews():
    if not current_user.is_admin:
        flash("Доступ заборонено!", "danger")
        return redirect(url_for('index'))

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        review_id = request.form['review_id']
        c.execute("UPDATE reviews SET approved = 1 WHERE id = ?", (review_id,))
        conn.commit()
        flash("Відгук схвалено.", "success")

    c.execute("SELECT id, name, text FROM reviews WHERE approved = 0")
    reviews = c.fetchall()
    conn.close()

    return render_template("moderate_reviews.html", reviews=reviews)

@app.route('/leave_review', methods=['GET', 'POST'])
@login_required
def leave_review():
    if request.method == 'POST':
        review_text = request.form.get('review_text')
        reservation_id = request.form.get('reservation_id')

        if review_text:
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("INSERT INTO reviews (username, text, approved) VALUES (?, ?, ?)",
                      (current_user.username, review_text, 0))
            conn.commit()
            conn.close()
            flash("Ваш відгук надіслано на модерацію", "success")
            return redirect(url_for('my_bookings'))
        else:
            flash("Відгук не може бути порожнім", "danger")
    
    reservation_id = request.args.get('reservation_id')
    return render_template("leave_review.html", reservation_id=reservation_id)

@app.route('/reservation', methods=['GET', 'POST'])
@login_required
def reservation():
    if request.method == 'POST':
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        rooms = request.form.get('rooms')
        room_type = request.form.get('room_type')
        guests = request.form.get('guests')

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('''
            INSERT INTO reservations (date_from, date_to, rooms, room_type, guests, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date_from, date_to, rooms, room_type, guests, current_user.id))
        conn.commit()
        conn.close()

        flash('Бронювання успішно створено!', 'success')
        return redirect(url_for('index'))

    return render_template('reservation.html')
@app.route('/reservations_list')
@login_required
def reservations_list():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        SELECT r.id, r.date_from, r.date_to, r.rooms, r.room_type, r.guests,
               u.username, u.phone, u.email
        FROM reservations r
        LEFT JOIN users u ON r.user_id = u.id
    ''')
    reservations = c.fetchall()
    conn.close()
    return render_template('reservations_list.html', reservations=reservations)

@app.route('/bookings')
@login_required
def bookings():
    if not current_user.is_admin:
        flash("Доступ заборонено!", "danger")
        return redirect(url_for('index'))

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        SELECT r.id, r.date_from, r.date_to, r.rooms, r.room_type, r.guests,
               u.username, u.phone, u.email
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.date_from DESC
    ''')
    reservations = c.fetchall()
    conn.close()
    return render_template('bookings.html', reservations=reservations)

@app.route('/my_bookings', methods=['GET', 'POST'])
@login_required
def my_bookings():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if request.method == 'POST':
        # Оновлюємо телефон і email користувача
        phone = request.form.get('phone')
        email = request.form.get('email')

        c.execute('UPDATE users SET phone = ?, email = ? WHERE id = ?', (phone, email, current_user.id))
        conn.commit()
        flash("Контактні дані оновлено", "success")

    # Виводимо бронювання та контактні дані
    c.execute('''
        SELECT id, date_from, date_to, rooms, room_type, guests
        FROM reservations
        WHERE user_id = ?
        ORDER BY id DESC
    ''', (current_user.id,))
    reservations = c.fetchall()

    c.execute('SELECT phone, email FROM users WHERE id = ?', (current_user.id,))
    user_data = c.fetchone()
    conn.close()

    return render_template('my_bookings.html', reservations=reservations)
    

    phone = user_data[0] if user_data else None
    email = user_data[1] if user_data else None

    return render_template('my_bookings.html', reservations=reservations, phone=phone, email=email)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form['password']

        print(f"DEBUG: username={username}, phone={phone}, email={email}, password={password}")

        if user_exists(username):
            flash("Користувач з таким логіном вже існує", "error")
            return redirect(url_for('register'))

        if not username or not password:
            flash("Будь ласка, заповніть усі поля.", "warning")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, phone, email) VALUES (?, ?, ?, ?)", 
                  (username, hashed_pw, phone, email))
        conn.commit()
        conn.close()

        flash("Реєстрація пройшла успішно. Ви можете увійти.", "success")
        return redirect(url_for('login'))

    return render_template('auth.html', active_form='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['is_admin'])
            login_user(user_obj)
            flash("Вхід виконано успішно", "success")
            return redirect(url_for('index'))
        else:
            flash("Неправильний логін або пароль", "danger")
            return redirect(url_for('login'))

    return render_template('auth.html', active_form='login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з системи", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
@app.route('/check_users_table')
def check_users_table():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users);")
    columns = c.fetchall()
    conn.close()
    return f"<pre>{columns}</pre>"