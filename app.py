from flask import Flask, render_template, request
import csv
import os
import qrcode
from datetime import datetime

app = Flask(__name__)

DATA_DIR = "data"
QR_DIR = "static/qrcodes"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

def load_guests():
    guests = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            path = os.path.join(DATA_DIR, file)
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["folder"] = file
                    guests.append(row)
    return guests

def update_guest_status(unique_id, folder):
    path = os.path.join(DATA_DIR, folder)
    rows = []
    found = False
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    for row in rows:
        if row['id'] == unique_id:
            if row['status'] == 'sudah':
                return False
            row['status'] = 'sudah'
            row['waktu'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            found = True
    if found:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'nama', 'status', 'waktu'])
            writer.writeheader()
            writer.writerows(rows)
    return found

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    nama = request.form['nama']
    folder = request.form['folder']
    filename = f"tamu_{nama.replace(' ', '_').lower()}"
    unique_id = f"{folder.split('.')[0]}_{filename}"
    qr_filename = f"{unique_id}.png"
    qr_path = os.path.join(QR_DIR, qr_filename)
    img = qrcode.make(unique_id)
    img.save(qr_path)
    filepath = os.path.join(DATA_DIR, folder)
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'nama', 'status', 'waktu'])
            writer.writeheader()
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'nama', 'status', 'waktu'])
        writer.writerow({'id': unique_id, 'nama': nama, 'status': 'belum', 'waktu': ''})
    qr_url = f"/static/qrcodes/{qr_filename}"
    return render_template('index.html', qr_url=qr_url)

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/validate', methods=['POST'])
def validate():
    code = request.form['code']
    guests = load_guests()
    for guest in guests:
        if guest['id'] == code:
            valid = update_guest_status(code, guest['folder'])
            if not valid:
                return render_template('result.html', status='duplicate', nama=guest['nama'])
            return render_template('result.html', status='success', nama=guest['nama'])
    return render_template('result.html', status='invalid', nama='')

if __name__ == '__main__':
    app.run(debug=True)
