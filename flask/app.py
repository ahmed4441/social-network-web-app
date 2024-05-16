from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
#from flask_sqlalchemy import SQLAlchemy
from models import User
from flask_bcrypt import check_password_hash
from extensions import db
from flask_bcrypt import generate_password_hash
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
import secrets
from profileform import ProfileForm, LoginForm
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generate a 16-byte (32-character) secret key
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Define user loader function
@login_manager.user_loader
def load_user(user_id):
    # Load user from the database based on user ID
    return User.query.get(int(user_id))

migrate = Migrate(app, db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
# Initialize SQLAlchemy with the Flask application
db.init_app(app)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()  # Create a WTForms form for updating user profile
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        # Pre-populate form fields with current user data
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    return render_template('profile.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    if form.validate_on_submit():
        # Handle form submission
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # Login user
            login_user(user)
            # Login successful, redirect to home page
            return redirect(url_for('profile'))
        else:
            # Login failed, display error message
            error_message = 'Invalid username or password'
            #flash('Invalid username or password')
    return render_template('login.html', error=error_message,form=form)




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        
        # Check if passwords match
        if password != confirm_password:
            error_message = 'Passwords do not match'
            return render_template('signup.html', error=error_message)
        
        # Check if username is available
        if User.query.filter_by(username=username).first():
            error_message = 'Username is already taken'
            return render_template('signup.html', error=error_message)

         # Hash the password
        hashed_password = generate_password_hash(password).decode('utf-8')

        # Create new user and add to database
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()
        
        # Redirect to login page after successful signup
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
