from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, jsonify
import sqlite3
import random
import string
import qrcode
from io import BytesIO
from pyzbar.pyzbar import decode as pyzbar_decode
from PIL import Image
import base64
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pyzbar.pyzbar import decode
import os
import stripe

ticket_bp = Blueprint('ticket', __name__, template_folder='templates')
app = Flask(__name__)
app.secret_key = 'your_secret_key'

stripe.api_key = 'sk_test_51PUzFcP5lJfzmHx5DPkdO8IP3TSai3UGxU7olJTx2QLvlJxbTcu2dFAMbsT2d8X3H3v4JRtVtFvYjrJlSXZiRwut00D0420zYw'

EMAIL_ADDRESS = 'cybergottalent.se@gmail.com'
APP_PASSWORD = 'nanz wkos rloh mign'
# Database initialization

def init_db(tickets_db_path):
    with sqlite3.connect(tickets_db_path) as conn:
        c = conn.cursor()

        # Create tables if they do not exist
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password TEXT)''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS tickets
            (ticket_number TEXT PRIMARY KEY, 
            row INTEGER, 
            seat INTEGER, 
            status TEXT CHECK(status IN ('available', 'booked')) DEFAULT 'available', 
            name TEXT DEFAULT "", 
            email TEXT DEFAULT "", 
            scanned TEXT CHECK(scanned IN ('not_scanned', 'scanned')) DEFAULT 'not_scanned')
        ''')

        c.execute('''CREATE TABLE IF NOT EXISTS scans
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     ticket_number TEXT, 
                     scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS customer
                     (email TEXT PRIMARY KEY, 
                     name TEXT)''')

        # Check if tickets table is empty
        c.execute('SELECT COUNT(*) FROM tickets')
        count = c.fetchone()[0]

        if count == 0:
            # Populate tickets table with initial data
            for row in range(1, 6):
                for seat in range(1, 14):
                    ticket_number = generate_ticket_number()
                    c.execute('INSERT INTO tickets (ticket_number, row, seat) VALUES (?, ?, ?)',
                              (ticket_number, row, seat))

            conn.commit()

def insert_ticket(ticket_number, row, seat, name, email):
    with sqlite3.connect('tickets.db') as conn:
        cursor = conn.cursor()
        # Ensure only 'available' is inserted for status initially
        cursor.execute('''
        INSERT INTO tickets (ticket_number, row, seat, status, name, email, scanned)
        VALUES (?, ?, ?, 'available', ?, ?, 'not_scanned')
        ''', (ticket_number, row, seat, name, email))
        conn.commit()

def insert_ticket(ticket_number, row, seat, name, email):
    with sqlite3.connect('tickets.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO tickets (ticket_number, row, seat, status, name, email, scanned)
        VALUES (?, ?, ?, 'available', ?, ?, 'not_scanned')
        ''', (ticket_number, row, seat, name, email))
        conn.commit()

def update_status_to_booked(ticket_number):
    with sqlite3.connect('tickets.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE tickets
        SET status = 'booked'
        WHERE ticket_number = ?
        ''', (ticket_number,))
        conn.commit()

def update_scanned_status(ticket_number):
    with sqlite3.connect('tickets.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE tickets
        SET scanned = 'scanned'
        WHERE ticket_number = ?
        ''', (ticket_number,))
        conn.commit()

# Function to generate a random ticket number with 8 digits
def generate_ticket_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Function to generate QR code for a given ticket number and name
def generate_qr_code(ticket_number, name):
    data = f"Ticket Number: {ticket_number}\nName: {name}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = BytesIO()
    qr_img.save(img_buffer)
    img_buffer.seek(0)
    return img_buffer

# Function to save QR code image to file
def save_qr_code_to_file(ticket_number, qr_image):
    filename = f"qrcodes/{ticket_number}.png"  # Assuming qrcodes folder exists
    with open(filename, 'wb') as f:
        f.write(qr_image.getvalue())

# Generate QR codes for all tickets in the database
def generate_qr_codes_for_tickets():
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute('SELECT ticket_number, name FROM tickets')
    tickets = c.fetchall()
    for ticket in tickets:
        ticket_number, name = ticket
        qr_image = generate_qr_code(ticket_number, name)
        save_qr_code_to_file(ticket_number, qr_image)
    conn.close()

# Function to decode QR code and extract ticket number
def decode_qr_code(image_data):
    try:
        # Convert base64 image data to bytes
        image_bytes = base64.b64decode(image_data)

        # Convert the bytes to a PIL image
        image = Image.open(BytesIO(image_bytes))

        # Decode the QR code from the image
        decoded_objects = pyzbar_decode(image)

        if decoded_objects:
            qr_code_data = decoded_objects[0].data.decode('utf-8')
            return qr_code_data
        else:
            return None
    except Exception as e:
        print(f"Fel vid avkodning av QR-kod: {e}")
        return None

# Function to parse datetime string with unwanted characters
def parse_datetime_string(date_string):
    truncated_string = date_string[:19]
    date_object = datetime.strptime(truncated_string, '%Y-%m-%d %H:%M:%S')
    return date_object

@ticket_bp.route('/generate_qr/<ticket_number>/<name>')
def generate_qr(ticket_number, name):
    qr_image = generate_qr_code(ticket_number, name)
    return send_file(qr_image, mimetype='image/png')

@ticket_bp.route('/login_ticket', methods=['GET', 'POST'])
def login_ticket():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_login(username, password):
            session['logged_in'] = True
            return redirect(url_for('check'))
        else:
            return 'Invalid login credentials'
    return render_template('ticket/ticket-login.html')

def verify_login(username, password):
    with sqlite3.connect('tickets.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        if user:
            return True
    return False

@ticket_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_ticket'))

@ticket_bp.route('/ticket')
def index():
    available_tickets = get_available_tickets()
    booked_seats = get_booked_seats()
    num_available_tickets = len(available_tickets)
    return render_template('ticket/tickets.html', available_tickets=available_tickets, booked_seats=booked_seats, num_available_tickets=num_available_tickets)

# Function to get booked seats
def get_booked_seats():
    with sqlite3.connect('tickets.db') as conn:
        c = conn.cursor()
        c.execute('SELECT row, seat FROM tickets WHERE status = "booked"')
        booked_seats = c.fetchall()
    return booked_seats

@ticket_bp.route('/check', methods=['GET'])
def check():
    if 'logged_in' not in session:
        return redirect(url_for('ticket.login_ticket'))
    return render_template('ticket/check.html')

# Function to query the database and retrieve ticket information
def check_ticket(search_by, value):
    conn = sqlite3.connect('tickets.db')  # Replace 'tickets.db' with your database file path
    c = conn.cursor()

    if search_by == 'row' and value.startswith('rad '):
        row_number = value[4:]  # Extract row number from "rad X"
        c.execute('SELECT ticket_number, row, seat, status, name, email, scanned FROM tickets WHERE row = ?', (row_number,))
    elif search_by == 'ticket_number':
        c.execute("SELECT * FROM tickets WHERE ticket_number = ?", (value,))
    elif search_by == 'name':
        c.execute("SELECT * FROM tickets WHERE name = ?", (value,))
    elif search_by == 'email':
        c.execute("SELECT * FROM tickets WHERE email = ?", (value,))

    tickets = c.fetchall()
    conn.close()

    return tickets

# Route to handle ticket checking
@ticket_bp.route('/check-ticket', methods=['GET', 'POST'])
def check_ticket_route():
    if request.method == 'POST':
        search_by = request.form['search_by']
        value = request.form['value']

        if not value:
            return render_template('ticket/check.html', result='Please enter a value.')

        tickets = check_ticket(search_by, value)

        if tickets:
            return render_template('ticket/check.html', tickets=tickets)
        else:
            return render_template('ticket/check.html', result='Biljetter hittades inte.')

    return render_template('ticket/ticket/check.html')  # Render the initial form

def send_email_with_qr(recipient_email, ticket_number, name, row, seat):
    # Generate QR code
    qr_image_buffer = generate_qr_code(ticket_number, name)

    # Create email message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg['Subject'] = 'Din biljett är här nu'

    # Attach QR code image to the email
    qr_image = MIMEImage(qr_image_buffer.getvalue())
    qr_image.add_header('Content-Disposition', 'attachment', filename=f'qr_code_{ticket_number}.png')
    msg.attach(qr_image)

    # Add thank you message and additional text in the body
    body = f"Hej på dig {name},\n\n"
    body += "Tack för att du köpte en biljett till vår talangshow! Vi är glada att du kommer att vara med oss för att uppleva"
    body += "alla talanger och kreativiteten som våra elever har att erbjuda.\n\n"
    body += "För att bekräfta din biljett och säkerställa en smidig ingång, bifogar vi den elektroniska biljetten nedan.\n\n"
    body += "Kom ihåg att dörrarna öppnas 20 minuter innan showen börjar och stänger 15:30, så se till att vara där i god tid för att hitta "
    body += "din plats och njuta av alla fantastiska talanger som våra elever har att erbjuda.\n\n"
    body += f"Din biljett med nummer {ticket_number} är bokad för {name} på rad {row}, plats {seat}.\n\n"
    body += "Tack för ditt stöd och vi ser fram emot att ha dig med oss på talangshowen!\n\n"
    body += "Med Vänliga Hälsningar,\nCyber Got Talent Team"
    msg.attach(MIMEText(body, 'plain'))

    # Connect to SMTP server and send email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, APP_PASSWORD)
        server.send_message(msg)

    print("E-postmeddelandet har skickats.")

@ticket_bp.route('/create_ticket', methods=['POST'])
def create_ticket():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    row = int(request.form['row'])
    seat = int(request.form['seat'])

    # Generate ticket_number
    ticket_number = generate_ticket_number()

    # Save ticket to database
    with sqlite3.connect('tickets.db') as conn:
        c = conn.cursor()

        # Check if a ticket already exists for the given row and seat
        c.execute('SELECT * FROM tickets WHERE row = ? AND seat = ?', (row, seat))
        existing_ticket = c.fetchone()

        if existing_ticket:
            # Check if the existing ticket is booked
            if existing_ticket[3] == 'booked':
                return 'Platsen är redan bokad, välj en annan plats eller kontakta supporten för assistans.'
            else:
                # Update existing ticket with customer info
                ticket_number = existing_ticket[0]
                c.execute('UPDATE tickets SET name = ?, email = ? WHERE ticket_number = ?',
                          (name, email, ticket_number))
        else:
            # Insert new ticket with customer info
            c.execute('INSERT INTO tickets (ticket_number, row, seat, status, name, email) VALUES (?, ?, ?, ?, ?, ?)',
                      (ticket_number, row, seat, 'available', name, email))

        conn.commit()

        # Insert/update customer details in the customer table
        if name and email:
            c.execute('INSERT OR REPLACE INTO customer (email, name) VALUES (?, ?)', (email, name))
            conn.commit()

    # Redirect to payment page with ticket details
    return redirect(url_for('ticket.payment', ticket_number=ticket_number, name=name, email=email, row=row, seat=seat))

@ticket_bp.route('/success-ticket')
def success_ticket():
    ticket_number = request.args.get('ticket_number')
    name = request.args.get('name')

    if not ticket_number or not name:
        return jsonify({'error': 'Missing ticket_number or name'})

    # Update ticket status in the database
    with sqlite3.connect('tickets.db') as conn:
        c = conn.cursor()
        c.execute('UPDATE tickets SET status = "booked" WHERE ticket_number = ?', (ticket_number,))
        conn.commit()

        # Retrieve ticket details from the database
        c.execute('SELECT ticket_number, row, seat, status, name, email FROM tickets WHERE ticket_number = ? AND name = ?', (ticket_number, name))
        ticket_details = c.fetchone()

    if ticket_details:
        ticket_number, row, seat, status, name, email = ticket_details
        send_email_with_qr(email, ticket_number, name, row, seat)

        # Insert customer details into the customer table if not already present
        c.execute('INSERT OR IGNORE INTO customer (email, name) VALUES (?, ?)', (email, name))
        conn.commit()

        return render_template('ticket/ticket-success.html', ticket_number=ticket_number, name=name, row=row, seat=seat)
    else:
        return jsonify({'error': 'Ticket not found'})

def mark_ticket_as_scanned(ticket_number):
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute('UPDATE tickets SET scanned = "scanned" WHERE ticket_number = ?', (ticket_number,))
    conn.commit()
    conn.close()

def get_available_tickets():
    with sqlite3.connect('tickets.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM tickets WHERE status = "available"')
        available_tickets = c.fetchall()
    return available_tickets

# Modify the get_ticket function to handle cases where the ticket is not found
def get_ticket(ticket_number, name):
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    # Adjust the column names based on the actual table schema
    c.execute('SELECT ticket_number, row, seat, status, name, email FROM tickets WHERE ticket_number = ? AND name = ?', (ticket_number, name))
    ticket_details = c.fetchone()
    conn.close()
    return ticket_details

# Modify the scan_qr route to handle cases where the ticket is None
@ticket_bp.route('/scan_qr', methods=['POST'])
def scan_qr():
    try:
        # Receive image data as data URL
        data = request.get_json()
        data_url = data['image_data']

        # Convert data URL to bytes
        image_data = base64.b64decode(data_url.split(',')[1])

        # Decode bytes to image
        image = Image.open(BytesIO(image_data))

        # Decode QR code
        decoded_objects = decode(image)
        print("Decoded objects:", decoded_objects)  # Debugging line

        if decoded_objects:
            # Extracting QR code data
            qr_code_data = decoded_objects[0].data.decode('utf-8')
            print("QR Code Data:", qr_code_data)  # Debugging line

            # Extracting ticket number and name from QR code data
            ticket_number = qr_code_data.split('Ticket Number: ')[1].split('\n')[0]
            name = qr_code_data.split('Name: ')[1].split('\n')[0]
            print("Extracted ticket number:", ticket_number)  # Debugging line
            print("Extracted name:", name)  # Debugging line

            # Get ticket information from the database
            ticket = get_ticket(ticket_number, name)

            if ticket:
                # Unpack ticket information if it exists
                ticket_number, row, seat, status, scanned_name, email = ticket

                # Check the last scan time
                last_scan_time = get_last_scan_time(ticket_number)

                if last_scan_time:
                    # Ticket has been scanned before, calculate time difference
                    time_difference = datetime.now() - parse_datetime_string(last_scan_time)
                    time_difference_str = str(time_difference).split('.')[0]  # Remove milliseconds
                    return f'Biljett {ticket_number} med {name} har redan skannats för {time_difference_str} sedan. Sittande vid rad: {row}, plats: {seat}.'
                else:
                    # Insert scan record into scans table
                    insert_scan_record(ticket_number)

                    # Call send_email_after_scan with correct email, name, and ticket number
                    send_email_after_scan(email, name, ticket_number)

                    return f'Välkommen {name}! Ditt biljettnummer är {ticket_number}. Ett ytterligare e-postmeddelande har skickats.'
            else:
                return 'Ogiltig biljett: Biljett hittades inte i databasen.'
        else:
            return 'Ingen QR-kod hittades i bilden'
    except Exception as e:
        return str(e)

# Function to send email after ticket scan
def send_email_after_scan(email, name, ticket_number):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = 'Din biljett har skannats'

    body = f"Hej {name},\n\n"
    body += "Vi vill informera dig om att din biljett till vår föreställning nu är skannad. Vi ser fram emot "
    body += "att välkomna dig till showen och hoppas att du kommer njuta av vad våra elever har att erbjuda. \n\n"
    body += "Om det inte var du som skannade biljetten, vänligen kontakta oss omedelbart. Vid sådana "
    body += "fall, se till att ta med dig en giltig ID-handling som bevisar att det är du.\n\n"
    body += "Du kan kontakta oss via mejl på cybergottalent@gmail.se eller ringa oss på 072 914 4755.\n\n"
    body += "Tack för din förståelse och ha det så trevlig i showen!\n\n"
    body += "Med Vänliga Halsningar,\nCyber Got Talent Team"
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, APP_PASSWORD)
        server.send_message(msg)

    # Update the scanned status after sending the email
    update_scanned_status(ticket_number)

# Function to insert scan record into scans table
def insert_scan_record(ticket_number):
    try:
        # Connect to the database
        with sqlite3.connect('tickets.db') as conn:
            # Create a cursor object
            c = conn.cursor()

            # Insert the scan record into the scans table
            c.execute('INSERT INTO scans (ticket_number, scanned_at) VALUES (?, ?)',
                      (ticket_number, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            # Commit the transaction
            conn.commit()
            print("Skanningsposten har infogats.")
    except sqlite3.Error as e:
        print("Det gick inte att infoga skanningsposten:", e)

# Function to get last scan time for a ticket
def get_last_scan_time(ticket_number):
    with sqlite3.connect('tickets.db') as conn:
        c = conn.cursor()
        c.execute('SELECT MAX(scanned_at) FROM scans WHERE ticket_number = ?', (ticket_number,))
        last_scan_time = c.fetchone()[0]
        return last_scan_time

def decode_qr_code(image_data):
    try:
        # Convert the raw image data to a PIL image
        image = Image.frombytes('RGB', (640, 480), bytes(image_data))

        # Decode the QR code from the image
        decoded_objects = pyzbar_decode(image)

        if decoded_objects:
            qr_code_data = decoded_objects[0].data.decode('utf-8')
            return qr_code_data
        else:
            return None
    except Exception as e:
        print(f"Fel vid avkodning av QR-kod: {e}")
        return None

@ticket_bp.route('/camera')
def camera():
    # Retrieve the ticket number from the query parameters
    ticket_number = request.args.get('ticket_number')

    if ticket_number:
        # Retrieve the last scan time for the specified ticket number from the database
        last_scan_time = get_last_scan_time(ticket_number)
        if last_scan_time:
            last_scan_time = parse_datetime_string(last_scan_time)
    else:
        # Handle the case where no ticket number is provided
        last_scan_time = None

    # Render the template with the last_scan_time variable in the context
    return render_template('ticket/camera.html', last_scan_time=last_scan_time)

@ticket_bp.route('/search_ticket', methods=['POST'])
def search_ticket():
    if 'logged_in' not in session:
        return redirect(url_for('login_ticket'))

    qr_image = request.files['qr_image']
    ticket_number = decode_qr_code(qr_image)

    if ticket_number:
        with sqlite3.connect('tickets.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM tickets WHERE ticket_number = ?', (ticket_number,))
            ticket = c.fetchone()

        if ticket:
            ticket_number, row, seat, status, name = ticket
            if name:
                return f'Biljetten  {ticket_number} är bokad av {name}. med Rad: {row} , plats: {seat}'
            else:
                return f'Biljetten {ticket_number} är tillgänglig. Rad: {row} , plats: {seat}'
        else:
            return f'Ingen biljett hittades med biljettnummer {ticket_number}'
    else:
        return 'Det gick inte att avkoda QR-koden'

@ticket_bp.route('/payment')
def payment():
    ticket_number = request.args.get('ticket_number')
    name = request.args.get('name')
    email = request.args.get('email')
    row = request.args.get('row')
    seat = request.args.get('seat')
    return render_template('ticket/ticket-payment.html', ticket_number=ticket_number, name=name, email=email, row=row, seat=seat)

@ticket_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    ticket_id = request.form['ticket_id']
    name = request.form['name']
    row = request.form['row']
    seat = request.form['seat']

    # Retrieve ticket details from the database
    ticket_details = get_ticket(ticket_id, name)  # Pass both ticket_id and name

    if ticket_details:
        # Debugging: print ticket_details to check its contents
        print('Ticket details:', ticket_details)

        if len(ticket_details) == 6:
            ticket_number, row, seat, status, name, email = ticket_details
        else:
            return jsonify({'error': 'Unexpected number of ticket details'}), 500

        # Create a Stripe Checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'sek',
                    'product_data': {
                        'name': f'Biljett {ticket_number} för {name}, Rad {row}, Plats {seat}',
                    },
                    'unit_amount': 2000,  # Amount in cents (e.g., SEK 20.00)
                },
                'quantity': 1,
            }],
            mode='payment',
            success_ticket_url=url_for('success_ticket', ticket_number=ticket_number, name=name, _external=True),
            cancel_ticket_url=url_for('cancel_ticket', _external=True),
        )

        return jsonify({'sessionId': session['id']})
    else:
        return jsonify({'error': 'Ticket not found'})

@ticket_bp.route('/cancel_ticket')
def cancel_ticket():
    return render_template('ticket/ticket-cancel.html')

# Webhook endpoint for Stripe
@ticket_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = 'your_endpoint_secret'  # Replace with your endpoint secret

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        return jsonify(success_ticeket=False), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify(success_ticket=False), 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        ticket_number = session['client_reference_id']

        # Update ticket status to booked
        with sqlite3.connect('tickets.db') as conn:
            c = conn.cursor()
            c.execute('UPDATE tickets SET status = "booked" WHERE ticket_number = ?', (ticket_number,))
            conn.commit()

        # Retrieve the ticket details
        ticket_details = get_ticket(ticket_number)
        if ticket_details:
            ticket_number, row, seat, status, name, email = ticket_details
            send_email_with_qr(email, ticket_number, name, row, seat)

    return jsonify(success_ticket=True)

if __name__ == '__main__':
    init_db()  # Call the function to initialize the database
    app.run(debug=True)
