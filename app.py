from flask import Flask, render_template, redirect, url_for, request, session
import random

app = Flask(__name__)
app.secret_key = 'dev'

SUPPORT_PHONE = '+7-999-123-45-67'

MENU = {
    'Супы': [
        {'id': 'soup1', 'name': 'Борщ', 'desc': 'Традиционный свекольный суп', 'price': 250, 'image': 'https://via.placeholder.com/150', 'available': True},
        {'id': 'soup2', 'name': 'Солянка', 'desc': 'Сборная мясная', 'price': 300, 'image': 'https://via.placeholder.com/150', 'available': False},
    ],
    'Десерты': [
        {'id': 'des1', 'name': 'Чизкейк', 'desc': 'Сырный десерт', 'price': 200, 'image': 'https://via.placeholder.com/150', 'available': True},
    ],
}


def get_cart():
    return session.setdefault('cart', {})


def cart_total():
    total = 0
    for item_id, qty in get_cart().items():
        for items in MENU.values():
            for item in items:
                if item['id'] == item_id:
                    total += item['price'] * qty
    return total


@app.context_processor
def inject_support():
    return {'support_phone': SUPPORT_PHONE, 'cart_total': cart_total()}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu')
def menu():
    category = request.args.get('category') or next(iter(MENU))
    items = MENU.get(category, [])
    return render_template('menu.html', categories=MENU.keys(), current=category, items=items)


@app.route('/add/<item_id>', methods=['POST'])
def add_to_cart(item_id):
    cart = get_cart()
    cart[item_id] = cart.get(item_id, 0) + 1
    session.modified = True
    return redirect(request.referrer or url_for('menu'))


@app.route('/cart')
def cart_view():
    cart = get_cart()
    items = []
    for item_id, qty in cart.items():
        for items_list in MENU.values():
            for item in items_list:
                if item['id'] == item_id:
                    items.append({'item': item, 'qty': qty, 'subtotal': item['price'] * qty})
    return render_template('cart.html', items=items, total=cart_total())


@app.route('/cart/add/<item_id>')
def cart_add(item_id):
    cart = get_cart()
    cart[item_id] = cart.get(item_id, 0) + 1
    session.modified = True
    return redirect(url_for('cart_view'))


@app.route('/cart/remove/<item_id>')
def cart_remove(item_id):
    cart = get_cart()
    if item_id in cart:
        cart[item_id] -= 1
        if cart[item_id] <= 0:
            cart.pop(item_id)
        session.modified = True
    return redirect(url_for('cart_view'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        table = request.form.get('table')
        comment = request.form.get('comment')
        session['order'] = {'table': table, 'comment': comment, 'items': get_cart().copy()}
        return redirect(url_for('payment'))
    if not get_cart():
        return redirect(url_for('menu'))
    summary = []
    for item_id, qty in get_cart().items():
        for items_list in MENU.values():
            for item in items_list:
                if item['id'] == item_id:
                    summary.append({'item': item, 'qty': qty, 'subtotal': item['price'] * qty})
    return render_template('checkout.html', items=summary, total=cart_total())


@app.route('/payment')
def payment():
    if 'order' not in session:
        return redirect(url_for('menu'))
    return render_template('payment.html')


@app.route('/pay', methods=['POST'])
def pay():
    if random.choice([True, False]):
        order_id = random.randint(1000, 9999)
        session.pop('cart', None)
        session.pop('order', None)
        return redirect(url_for('payment_success', order_id=order_id))
    else:
        return redirect(url_for('payment_error'))


@app.route('/payment/success')
def payment_success():
    order_id = request.args.get('order_id')
    return render_template('payment_success.html', order_id=order_id)


@app.route('/payment/error')
def payment_error():
    return render_template('payment_error.html')


if __name__ == '__main__':
    app.run(debug=True)
