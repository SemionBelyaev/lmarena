from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, User, Booking, ChatMessage, BookingNote, Guide, Transport, Supplier, Inventory
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'city-sightseeing-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ==========================================
# 1. СТРАНИЦЫ (NAVIGATION ROUTES)
# ==========================================

# Главная (Дашборд)
@app.route('/')
def index():
    # Загружаем заявки
    all_bookings = Booking.query.order_by(Booking.priority == 'high', Booking.tour_date).all()
    
    # Сортируем по колонкам
    bookings_new = [b for b in all_bookings if b.status == 'new']
    bookings_conf = [b for b in all_bookings if b.status in ['confirmed', 'in_progress']]
    bookings_paid = [b for b in all_bookings if b.status == 'paid']
    bookings_done = [b for b in all_bookings if b.status == 'completed']

    # KPI
    total_price = sum(b.price for b in all_bookings)
    total_cost = sum(b.cost for b in all_bookings)
    stats = {'income': total_price, 'margin': total_price - total_cost - (total_price * 0.15)}
    
    # Чат
    last_messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(20).all()
    chat_history = last_messages[::-1]
    
    # Список менеджеров для модального окна
    managers = User.query.all()

    return render_template('dashboard.html', 
                           bookings_new=bookings_new, bookings_conf=bookings_conf, 
                           bookings_paid=bookings_paid, bookings_done=bookings_done, 
                           stats=stats, chat_history=chat_history, managers=managers)

# Страница "Все заявки"
@app.route('/bookings')
def bookings_page():
    all_bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template('bookings.html', bookings=all_bookings)

# Страница "Финансы"
@app.route('/finance')
def finance_page():
    all_bookings = Booking.query.all()
    income = sum(b.price for b in all_bookings)
    expenses = sum(b.cost for b in all_bookings)
    return render_template('finance.html', income=income, expenses=expenses)

# Страница "Настройки"
@app.route('/settings')
def settings_page():
    user = {'name': 'Семён Admin', 'role': 'Operational Director', 'email': 'admin@city-sightseeing.ru'}
    return render_template('settings.html', user=user)


# ==========================================
# 2. API МЕТОДЫ (LOGIC ROUTES)
# ==========================================

# Получить детали заявки (для окна редактирования)
@app.route('/api/booking/<int:id>/details')
def get_booking_details(id):
    b = db.session.get(Booking, id)
    if not b: return jsonify({'error': 'Not found'}), 404
    
    notes = [{'author': n.author, 'text': n.text, 'date': n.created_at.strftime('%d.%m %H:%M')} for n in b.notes]
    
    return jsonify({
        'id': b.id,
        'client': b.client_name,
        'phone': b.client_phone,
        'tour': b.tour_type,
        'price': b.price,
        'priority': b.priority,
        'manager_id': b.manager_id,
        'date': b.tour_date.strftime('%Y-%m-%d'),
        'notes': notes
    })

# Сохранить изменения заявки
@app.route('/api/booking/update', methods=['POST'])
def update_booking():
    data = request.json
    b = db.session.get(Booking, int(data['id']))
    if b:
        b.client_name = data.get('client')
        b.tour_type = data.get('tour')
        b.priority = data.get('priority')
        try:
            b.price = float(data.get('price'))
        except:
            pass
            
        b.manager_id = int(data.get('manager_id')) if data.get('manager_id') else None
        
        if data.get('date'):
            try:
                b.tour_date = datetime.strptime(data.get('date'), '%Y-%m-%d')
            except:
                pass
            
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

# Добавить комментарий
@app.route('/api/booking/add_note', methods=['POST'])
def add_note():
    data = request.json
    if not data.get('text'): return jsonify({'success': False})
    
    note = BookingNote(
        text=data['text'],
        booking_id=data['booking_id'],
        author='Вы' 
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({
        'success': True, 
        'date': note.created_at.strftime('%d.%m %H:%M'),
        'author': note.author
    })

# Обновление статуса (Drag & Drop)
@app.route('/api/booking/status', methods=['POST'])
def update_status():
    data = request.json
    booking = db.session.get(Booking, int(data['id']))
    if booking:
        booking.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

# Создание быстрой заявки
@app.route('/create_quick_booking', methods=['POST'])
def create_quick_booking():
    b = Booking(
        client_name=f'New Client {random.randint(100,999)}', client_phone='+7999...',
        tour_type='Hop-On Hop-Off', status='new', priority='medium',
        price=15000, cost=5000, tour_date=datetime.now() + timedelta(days=2),
        manager_id=1
    )
    db.session.add(b)
    db.session.commit()
    return redirect(url_for('index'))

# Чат
@app.route('/api/chat/send', methods=['POST'])
def send_message():
    data = request.json
    if not data.get('text'): return jsonify({'success': False})
    msg = ChatMessage(sender='Вы', text=data['text'], channel='general')
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True})


# ==========================================
# 3. ИНИЦИАЛИЗАЦИЯ
# ==========================================
def create_initial_data():
    with app.app_context():
        db.create_all()
        if not User.query.first():
            print("🚀 База пуста. Генерация демо-данных...")
            m1 = User(username='Manager Anna', role='manager')
            m2 = User(username='Manager Ivan', role='manager')
            db.session.add_all([m1, m2])
            
            # Заявка с комментарием
            b = Booking(client_name='Test Client', tour_type='Red Bus', status='new', priority='high', price=5000, tour_date=datetime.now(), manager_id=1)
            db.session.add(b)
            db.session.commit()
            
            n = BookingNote(text="Клиент просил место у окна", booking_id=b.id, author="Manager Anna")
            db.session.add(n)
            
            # Чат
            db.session.add(ChatMessage(sender='System', text='CRM запущена', channel='general'))
            
            db.session.commit()
            print("✅ Готово!")

if __name__ == '__main__':
    create_initial_data()
    app.run(debug=True)