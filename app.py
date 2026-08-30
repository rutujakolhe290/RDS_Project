from flask import Flask, render_template, request, jsonify, session, redirect
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'rds_project_secret_2025'

# --- DATABASE (Tujha data) ---
USERS_DB = {
    '111122223333': {'mobile': '9876543210', 'role': 'shopkeeper', 'shop_id': 'SHOP001', 'name': 'Shopkeeper A'},
    '222233334444': {'mobile': '9876543211', 'role': 'shopkeeper', 'shop_id': 'SHOP002', 'name': 'Shopkeeper B'},
    '333344445555': {'mobile': '9876543212', 'role': 'shopkeeper', 'shop_id': 'SHOP003', 'name': 'Shopkeeper C'},
    '999988887777': {'mobile': '9371274004', 'role': 'admin', 'shop_id': None, 'name': 'Admin'},
    '444455556666': {'mobile': '9699519897', 'role': 'citizen', 'shop_id': 'SHOP001', 'name': 'Navin'},
}

# --- PERMANENT LIVE DATA - KADHICH DELETE HONAR NAHI ---
live_data = {
    "stock": [
        {"id": "SHOP001", "name": "Fair Price Shop - A", "wheat": 120, "rice": 85, "sugar": 45},
        {"id": "SHOP002", "name": "Fair Price Shop - B", "wheat": 90, "rice": 60, "sugar": 30},
        {"id": "SHOP003", "name": "Fair Price Shop - C", "wheat": 15, "rice": 40, "sugar": 10},
    ],
    "complaints": [],
    "transactions": [],
    "citizen_receipts": [], # NEW - Permanent
    "distribution_reports": [], # NEW - Permanent
    "admin_logs": [] # NEW - Permanent
}

otp_storage = {}

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('verification.html')

@app.route('/dashboard')
def dashboard():
    if session.get('role')!= 'shopkeeper':
        return redirect('/')
    return render_template('dashboard.html')

@app.route('/admin')
def admin_page():
    if session.get('role')!= 'admin':
        return redirect('/')
    return render_template('admin.html') # Tujha new wala

@app.route('/status')
def status_page():
    if 'aadhar' not in session:
        return redirect('/')
    return render_template('status.html')

# --- AUTH APIs (Tujhe junech) ---
@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    aadhar = data.get('aadhar','').replace(' ','').replace('-','')
    mobile = data.get('mobile','').strip()
    if aadhar not in USERS_DB:
        return jsonify({'success': False, 'msg': 'Aadhar not registered in RDS'})
    if USERS_DB[aadhar]['mobile']!= mobile:
        return jsonify({'success': False, 'msg': 'Mobile number mismatch'})
    otp = str(random.randint(100000, 999999))
    otp_storage[aadhar] = otp
    print(f"\n--- OTP for {aadhar} is: {otp} ---\n")
    return jsonify({'success': True, 'otp': otp, 'msg': 'OTP sent'})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    aadhar = data.get('aadhar','').replace(' ','')
    otp = data.get('otp','').strip()
    if otp_storage.get(aadhar) == otp:
        user = USERS_DB[aadhar]
        session['aadhar'] = aadhar
        session['role'] = user['role']
        session['shop_id'] = user['shop_id']
        session['name'] = user['name']
        if user['role'] == 'shopkeeper':
            return jsonify({'success': True, 'redirect': '/dashboard'})
        elif user['role'] == 'admin':
            return jsonify({'success': True, 'redirect': '/admin'})
        else:
            return jsonify({'success': True, 'redirect': '/status'})
    return jsonify({'success': False, 'msg': 'Invalid OTP'})

@app.route('/api/my-data')
def my_data():
    aadhar = session.get('aadhar')
    if not aadhar: return jsonify({"error": "Not logged in"})
    user = USERS_DB.get(aadhar)
    shop = next((s for s in live_data["stock"] if s["id"] == user['shop_id']), None)
    return jsonify({"user": user, "shop": shop, "all_shops": live_data["stock"]})

@app.route('/api/get-stock')
def get_stock():
    return jsonify(live_data["stock"])

@app.route('/api/update-stock', methods=['POST'])
def update_stock():
    data = request.json
    shop_id = data.get('shop_id')
    for shop in live_data["stock"]:
        if shop['id'] == shop_id:
            shop['wheat'] = int(data.get('wheat', shop['wheat']))
            shop['rice'] = int(data.get('rice', shop['rice']))
            shop['sugar'] = int(data.get('sugar', shop['sugar']))
            # Admin log save
            live_data["admin_logs"].append({
                "date": datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p"),
                "isoDate": datetime.now().isoformat(),
                "shop": shop_id,
                "item": data.get('last_item', 'stock'),
                "qty": data.get('last_qty', 0),
                "byAadhar": session.get('aadhar', 'ADMIN')
            })
            return jsonify({'success': True})
    return jsonify({'success': False})

# --- NEW APIS - 100% COMPLETE SATHI ---

# 1. Citizen Receipts
@app.route('/api/save-receipt', methods=['POST'])
def save_receipt():
    data = request.json
    data['id'] = len(live_data["citizen_receipts"]) + 1
    if 'fullDate' not in data:
        data['fullDate'] = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")
    if 'isoDate' not in data:
        data['isoDate'] = datetime.now().isoformat()
    live_data["citizen_receipts"].append(data)
    print(f"Receipt Saved: {data}")
    return jsonify({'success': True})

@app.route('/api/get-receipts')
def get_receipts():
    return jsonify(live_data["citizen_receipts"])

# 2. Distribution Reports
@app.route('/api/save-report', methods=['POST'])
def save_report():
    data = request.json
    data['id'] = len(live_data["distribution_reports"]) + 1
    data['date'] = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")
    data['isoDate'] = datetime.now().isoformat()
    live_data["distribution_reports"].append(data)
    return jsonify({'success': True})

@app.route('/api/get-reports')
def get_reports():
    return jsonify(live_data["distribution_reports"])

# 3. Complaints
@app.route('/api/save-complaint', methods=['POST'])
def save_complaint():
    data = request.json
    data['id'] = len(live_data["complaints"]) + 1
    data['date'] = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")
    data['isoDate'] = datetime.now().isoformat()
    if 'status' not in data: data['status'] = 'Pending'
    live_data["complaints"].append(data)
    return jsonify({'success': True})

@app.route('/api/get-complaints')
def get_complaints():
    return jsonify(live_data["complaints"])

@app.route('/api/resolve-complaint', methods=['POST'])
def resolve_complaint():
    data = request.json
    cid = data.get('id')
    for c in live_data["complaints"]:
        if c['id'] == cid:
            c['status'] = 'Resolved'
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/get-admin-logs')
def get_admin_logs():
    return jsonify(live_data["admin_logs"])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    print("✅ RDS FINAL Project running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)