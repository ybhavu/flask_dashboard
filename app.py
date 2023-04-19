
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g
import os
from flask import flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_from_directory


# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Define the database path
DB_PATH = 'database.db'
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static\\css\\uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Create a function to get a new database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

# Define the schema for the table
create_table_query = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    pincode TEXT NOT NULL,
    user_type TEXT NOT NULL,
    profile_pic TEXT NOT NULL
);
'''

# Create the table
with sqlite3.connect('database.db') as conn:
    cursor = conn.cursor()
    cursor.execute(create_table_query)
    conn.commit()

# Create a function to close the database connection
@app.teardown_appcontext
def close_db(error):
    if 'db' in g:
        g.db.close()

# Define the routes for the application
@app.route('/')
def index():
    return render_template('welcome.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get the form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        pincode = request.form['pincode']
        user_type = request.form['user_type']

        # Get the profile picture file
        profile_pic = request.files['profile_pic']
        if profile_pic.filename == '':
            flash('No selected file.', 'error')
            return redirect(url_for('signup'))

        # Save the profile picture file to the server
        filename = secure_filename(profile_pic.filename)
        profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Add the user to the database with the filename
        db = get_db()
        db.execute('INSERT INTO users (first_name, last_name, username, email, password, address, city, state, pincode, user_type, profile_pic) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (first_name, last_name, username, email, generate_password_hash(password), address, city, state, pincode, user_type, filename))
        db.commit()

        flash('You were successfully registered and can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the form data
        email = request.form['email']
        password = request.form['password']

        # Check if the user exists in the database
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user is None:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

        # Check if the password is correct
        if not check_password_hash(user['password'], password):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

        # If the user exists and the password is correct, log the user in
        session.clear()
        session['user_id'] = user['id']
        session['user_type'] = user['user_type']
        flash('You were successfully logged in.', 'success')
        if user['user_type'] == 'patient':
                return redirect(url_for('patient_dashboard'))
        elif user['user_type'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the user's session and redirect to the login page
    session.clear()
    return redirect(url_for('login'))


@app.route('/doctor_dashboard')
def doctor_dashboard():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get the user's information from the database
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', [session['user_id']]).fetchone()
    
    # Check if the user is a doctor
    if user['user_type'] != 'doctor':
        return redirect(url_for('patient_dashboard'))
    print(user['profile_pic'])
    # Render the doctor dashboard template with the user's information
    return render_template('dashboard_doctor.html', user=user,profile_pic=url_for('static', filename='css/uploads/' + user['profile_pic']))


@app.route('/patient_dashboard')
def patient_dashboard():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get the user's information from the database
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', [session['user_id']]).fetchone()

    # Check if the user is a patient
    if user['user_type'] != 'patient':
        return redirect(url_for('doctor_dashboard'))

    # Render the patient dashboard template with the user's information
    return render_template('dashboard_patient.html', user=user,profile_pic=url_for('static', filename='css/uploads/' + user['profile_pic']))

@app.route('/profile/<filename>')
def profile_pic(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
