import os
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from functools import wraps
from forms import LoginForm, StudentForm, RoomForm, ComplaintForm

# ── App Setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = "hostel-secret-key-change-me"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True

db            = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view             = 'login'
login_manager.login_message          = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


# ── MODELS ────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer,     primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role     = db.Column(db.String(50),  nullable=False, default='student')

    def __repr__(self):
        return f'<User {self.username}>'


class Room(db.Model):
    __tablename__ = 'rooms'
    id          = db.Column(db.Integer,    primary_key=True)
    block       = db.Column(db.String(10), nullable=False, default='B1')
    room_number = db.Column(db.String(10), nullable=False)
    floor       = db.Column(db.Integer,    nullable=False, default=1)
    capacity    = db.Column(db.Integer,    nullable=False, default=2)
    students    = db.relationship('Student', backref='room', lazy=True)

    @property
    def occupied(self):
        return len(self.students)

    @property
    def available(self):
        return self.capacity - self.occupied

    @property
    def is_full(self):
        return self.occupied >= self.capacity

    @property
    def full_name(self):
        return f'{self.block}-{self.room_number}'

    def __repr__(self):
        return f'<Room {self.full_name}>'


class Student(db.Model):
    __tablename__ = 'students'
    id         = db.Column(db.Integer,     primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    roll_no    = db.Column(db.String(20),  nullable=False, unique=True)
    email      = db.Column(db.String(120), nullable=True)
    gender     = db.Column(db.String(10),  nullable=False, default='Male')
    room_id    = db.Column(db.Integer,     db.ForeignKey('rooms.id'), nullable=True)
    complaints = db.relationship('Complaint', backref='student',
                                 lazy=True, cascade='all, delete-orphan')

    @property
    def allowed_blocks(self):
        if self.gender == 'Male':
            return ['B1', 'B2', 'B3']
        else:
            return ['G1']

    def __repr__(self):
        return f'<Student {self.name}>'


class Complaint(db.Model):
    __tablename__ = 'complaints'
    id          = db.Column(db.Integer,     primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=False)
    status      = db.Column(db.String(20),  nullable=False, default='pending')
    created_at  = db.Column(db.DateTime,    nullable=False, default=db.func.now())
    student_id  = db.Column(db.Integer,     db.ForeignKey('students.id'), nullable=False)

    def __repr__(self):
        return f'<Complaint {self.title}>'


# ── FLASK-LOGIN USER LOADER ───────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ── DATABASE INIT ─────────────────────────────────────────────────────────────

def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password='admin123', role='admin'))
    if not User.query.filter_by(username='student').first():
        db.session.add(User(username='student', password='student123', role='student'))
    db.session.commit()


# ── DECORATORS ────────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ── AUTH ROUTES ───────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    total_students     = Student.query.count()
    total_rooms        = Room.query.count()
    total_complaints   = Complaint.query.count()
    pending_complaints = Complaint.query.filter_by(status='pending').count()
    available_rooms    = sum(1 for r in Room.query.all() if not r.is_full)

    return render_template(
        'dashboard.html',
        total_students     = total_students,
        total_rooms        = total_rooms,
        total_complaints   = total_complaints,
        available_rooms    = available_rooms,
        pending_complaints = pending_complaints,
    )


# ── STUDENTS ──────────────────────────────────────────────────────────────────

@app.route('/students')
@login_required
def list_students():
    search = request.args.get('search', '').strip()
    if search:
        students = Student.query.filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.roll_no.ilike(f'%{search}%')
            )
        ).order_by(Student.name).all()
    else:
        students = Student.query.order_by(Student.name).all()
    return render_template('students/list.html', students=students, search=search)


@app.route('/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    form = StudentForm()

    available_rooms = [r for r in Room.query.all() if not r.is_full]
    form.room_id.choices = [(0, '— No room assigned —')] + [
        (r.id, f'{r.full_name} ({r.occupied}/{r.capacity} beds taken)')
        for r in available_rooms
    ]

    if form.validate_on_submit():
        if Student.query.filter_by(roll_no=form.roll_no.data).first():
            flash('A student with that roll number already exists.', 'danger')
            return render_template('students/form.html', form=form, action='Add')

        room_id = form.room_id.data if form.room_id.data != 0 else None

        if room_id:
            room = db.session.get(Room, room_id)
            if room and room.is_full:
                flash('That room is already full.', 'danger')
                return render_template('students/form.html', form=form, action='Add')

        # ✅ gender is now saved correctly
        student = Student(
            name    = form.name.data,
            roll_no = form.roll_no.data,
            email   = form.email.data or None,
            gender  = form.gender.data,
            room_id = room_id
        )
        db.session.add(student)
        db.session.commit()
        flash(f"Student '{form.name.data}' added successfully.", 'success')
        return redirect(url_for('list_students'))

    return render_template('students/form.html', form=form, action='Add')


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form    = StudentForm(obj=student)

    all_rooms = Room.query.all()
    form.room_id.choices = [(0, '— No room assigned —')] + [
        (r.id, f'{r.full_name} ({r.occupied}/{r.capacity} beds taken)')
        for r in all_rooms
        if not r.is_full or r.id == student.room_id
    ]

    if form.validate_on_submit():
        dup = Student.query.filter(
            Student.roll_no == form.roll_no.data,
            Student.id != student_id
        ).first()
        if dup:
            flash('Another student already uses that roll number.', 'danger')
            return render_template('students/form.html', form=form, action='Edit')

        student.name    = form.name.data
        student.roll_no = form.roll_no.data
        student.email   = form.email.data or None
        student.gender  = form.gender.data
        student.room_id = form.room_id.data if form.room_id.data != 0 else None
        db.session.commit()
        flash(f"Student '{student.name}' updated.", 'success')
        return redirect(url_for('list_students'))

    if request.method == 'GET':
        form.room_id.data = student.room_id or 0

    return render_template('students/form.html',
                           form=form, action='Edit', student=student)


@app.route('/students/delete/<int:student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    # ✅ This route was missing — now added back
    student = Student.query.get_or_404(student_id)
    name = student.name
    db.session.delete(student)
    db.session.commit()
    flash(f"Student '{name}' deleted.", 'info')
    return redirect(url_for('list_students'))


@app.route('/rooms/<int:room_id>/assign', methods=['GET', 'POST'])
@admin_required
def assign_student(room_id):
    room = Room.query.get_or_404(room_id)

    if room.is_full:
        flash(f'Room {room.full_name} is already full.', 'danger')
        return redirect(url_for('available_rooms'))

    boys_blocks = ['B1', 'B2', 'B3']

    if room.block in boys_blocks:
        allowed_gender = 'Male'
        block_label    = 'Boys Block'
    else:
        allowed_gender = 'Female'
        block_label    = 'Girls Block'

    eligible_students = Student.query.filter_by(
        gender  = allowed_gender,
        room_id = None
    ).order_by(Student.name).all()

    if request.method == 'POST':
        student_id = request.form.get('student_id')

        if not student_id:
            flash('Please select a student.', 'danger')
            return render_template('rooms/assign.html',
                                   room=room,
                                   students=eligible_students,
                                   block_label=block_label,
                                   allowed_gender=allowed_gender)

        student = Student.query.get_or_404(int(student_id))

        if student.gender != allowed_gender:
            flash(f'Cannot assign {student.gender} student to a {block_label}.', 'danger')
            return render_template('rooms/assign.html',
                                   room=room,
                                   students=eligible_students,
                                   block_label=block_label,
                                   allowed_gender=allowed_gender)

        if room.is_full:
            flash(f'Room {room.full_name} is already full.', 'danger')
            return redirect(url_for('available_rooms'))

        student.room_id = room.id
        db.session.commit()
        flash(f"'{student.name}' assigned to Room {room.full_name} successfully.", 'success')
        return redirect(url_for('available_rooms'))

    return render_template('rooms/assign.html',
                           room=room,
                           students=eligible_students,
                           block_label=block_label,
                           allowed_gender=allowed_gender)


# ── BULK UPLOAD STUDENTS ──────────────────────────────────────────────────────

@app.route('/students/bulk_upload', methods=['GET', 'POST'])
@admin_required
def bulk_upload_students():
    if request.method == 'POST':
        file = request.files.get('csv_file')

        if not file or file.filename == '':
            flash('Please select a CSV file.', 'danger')
            return redirect(request.url)

        if not file.filename.endswith('.csv'):
            flash('Only CSV files are allowed.', 'danger')
            return redirect(request.url)

        try:
            import pandas as pd
            from io import StringIO

            stream     = StringIO(file.stream.read().decode('utf-8'))
            df         = pd.read_csv(stream)
            df.columns = df.columns.str.strip().str.lower()

            required = {'name', 'roll_no'}
            if not required.issubset(df.columns):
                flash('CSV is missing required columns. Required: name, roll_no.', 'danger')
                return redirect(request.url)

            success_count = 0
            skip_count    = 0
            errors        = []

            for index, row in df.iterrows():
                row_num = index + 2
                try:
                    name        = str(row.get('name',    '')).strip()
                    roll_no     = str(row.get('roll_no', '')).strip()
                    email       = str(row.get('email',   '')).strip()
                    gender      = str(row.get('gender',  'Male')).strip()
                    block       = str(row.get('block',   '')).strip()
                    room_number = str(row.get('room_number', '')).strip()

                    if not name or not roll_no or name == 'nan' or roll_no == 'nan':
                        errors.append(f'Row {row_num}: Missing name or roll number — skipped.')
                        skip_count += 1
                        continue

                    if Student.query.filter_by(roll_no=roll_no).first():
                        errors.append(f'Row {row_num}: Roll No {roll_no} already exists — skipped.')
                        skip_count += 1
                        continue

                    # Validate gender
                    if gender not in ['Male', 'Female']:
                        gender = 'Male'

                    room_id = None
                    if block and room_number and block != 'nan' and room_number != 'nan':
                        room = Room.query.filter_by(block=block, room_number=room_number).first()
                        if not room:
                            errors.append(f'Row {row_num}: Room {block}-{room_number} not found — added without room.')
                        elif room.is_full:
                            errors.append(f'Row {row_num}: Room {block}-{room_number} is full — added without room.')
                        else:
                            room_id = room.id
                    elif room_number and room_number != 'nan':
                        errors.append(f'Row {row_num}: Block missing for room {room_number} — added without room.')

                    student = Student(
                        name    = name,
                        roll_no = roll_no,
                        email   = email if email and email != 'nan' else None,
                        gender  = gender,
                        room_id = room_id
                    )
                    db.session.add(student)
                    success_count += 1

                except Exception as e:
                    errors.append(f'Row {row_num}: Unexpected error — {str(e)}')
                    skip_count += 1
                    continue

            db.session.commit()

            if success_count:
                flash(f'Successfully added {success_count} student(s).', 'success')
            if skip_count:
                flash(f'Skipped {skip_count} row(s) due to errors.', 'warning')
            for error in errors:
                flash(error, 'warning')

            return redirect(url_for('list_students'))

        except Exception as e:
            flash(f'Error reading CSV file: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('students/bulk_upload.html')


# ── ROOMS ─────────────────────────────────────────────────────────────────────

@app.route('/rooms')
@login_required
def list_rooms():
    rooms = Room.query.order_by(Room.block, Room.room_number).all()
    return render_template('rooms/list.html', rooms=rooms)


@app.route('/rooms/add', methods=['GET', 'POST'])
@admin_required
def add_room():
    form = RoomForm()

    if form.validate_on_submit():
        existing = Room.query.filter_by(
            block=form.block.data,
            room_number=form.room_number.data
        ).first()
        if existing:
            flash(f'Room {form.block.data}-{form.room_number.data} already exists.', 'danger')
            return render_template('rooms/form.html', form=form, action='Add')

        room = Room(
            block       = form.block.data,
            room_number = form.room_number.data,
            floor       = form.floor.data,
            capacity    = form.capacity.data
        )
        db.session.add(room)
        db.session.commit()
        flash(f'Room {room.full_name} added.', 'success')
        return redirect(url_for('list_rooms'))

    return render_template('rooms/form.html', form=form, action='Add')


@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
@admin_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.occupied > 0:
        flash('Cannot delete: students are still assigned to this room.', 'danger')
        return redirect(url_for('list_rooms'))
    db.session.delete(room)
    db.session.commit()
    flash(f'Room {room.full_name} deleted.', 'info')
    return redirect(url_for('list_rooms'))


@app.route('/rooms/available')
@login_required
def available_rooms():
    rooms = [r for r in Room.query.order_by(Room.block, Room.room_number).all()
             if not r.is_full]
    return render_template('rooms/available.html', rooms=rooms)


# ── BULK UPLOAD ROOMS ─────────────────────────────────────────────────────────

@app.route('/rooms/bulk_upload', methods=['GET', 'POST'])
@admin_required
def bulk_upload_rooms():
    if request.method == 'POST':
        file = request.files.get('csv_file')

        if not file or file.filename == '':
            flash('Please select a CSV file.', 'danger')
            return redirect(request.url)

        if not file.filename.endswith('.csv'):
            flash('Only CSV files are allowed.', 'danger')
            return redirect(request.url)

        try:
            import pandas as pd
            from io import StringIO

            stream     = StringIO(file.stream.read().decode('utf-8'))
            df         = pd.read_csv(stream)
            df.columns = df.columns.str.strip().str.lower()

            required = {'block', 'room_number', 'floor', 'capacity'}
            if not required.issubset(df.columns):
                flash('CSV is missing required columns. Required: block, room_number, floor, capacity', 'danger')
                return redirect(request.url)

            success_count = 0
            skip_count    = 0
            errors        = []

            for index, row in df.iterrows():
                row_num = index + 2
                try:
                    block       = str(row.get('block',       '')).strip()
                    room_number = str(row.get('room_number', '')).strip()
                    floor       = row.get('floor',    1)
                    capacity    = row.get('capacity', 2)

                    if not room_number or room_number == 'nan':
                        errors.append(f'Row {row_num}: Missing room number — skipped.')
                        skip_count += 1
                        continue

                    valid_blocks = ['B1', 'B2', 'B3', 'G1']
                    if block not in valid_blocks:
                        errors.append(f'Row {row_num}: Invalid block "{block}". Must be B1/B2/B3/G1 — skipped.')
                        skip_count += 1
                        continue

                    if Room.query.filter_by(block=block, room_number=room_number).first():
                        errors.append(f'Row {row_num}: Room {block}-{room_number} already exists — skipped.')
                        skip_count += 1
                        continue

                    try:
                        floor    = int(floor)
                        capacity = int(capacity)
                    except (ValueError, TypeError):
                        errors.append(f'Row {row_num}: Floor and capacity must be numbers — skipped.')
                        skip_count += 1
                        continue

                    if floor < 0 or floor > 50:
                        errors.append(f'Row {row_num}: Floor must be between 0-50 — skipped.')
                        skip_count += 1
                        continue

                    if capacity < 1 or capacity > 20:
                        errors.append(f'Row {row_num}: Capacity must be between 1-20 — skipped.')
                        skip_count += 1
                        continue

                    room = Room(
                        block       = block,
                        room_number = room_number,
                        floor       = floor,
                        capacity    = capacity
                    )
                    db.session.add(room)
                    success_count += 1

                except Exception as e:
                    errors.append(f'Row {row_num}: Unexpected error — {str(e)}')
                    skip_count += 1
                    continue

            db.session.commit()

            if success_count:
                flash(f'Successfully added {success_count} room(s).', 'success')
            if skip_count:
                flash(f'Skipped {skip_count} row(s) due to errors.', 'warning')
            for error in errors:
                flash(error, 'warning')

            return redirect(url_for('list_rooms'))

        except Exception as e:
            flash(f'Error reading CSV file: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('rooms/bulk_upload.html')


# ── COMPLAINTS ────────────────────────────────────────────────────────────────

@app.route('/complaints')
@login_required
def list_complaints():
    status = request.args.get('status', 'all')
    if status != 'all':
        complaints = Complaint.query.filter_by(status=status)\
                              .order_by(Complaint.created_at.desc()).all()
    else:
        complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('complaints/list.html',
                           complaints=complaints, status=status)


@app.route('/complaints/add', methods=['GET', 'POST'])
@login_required
def add_complaint():
    form       = ComplaintForm()
    students   = Student.query.order_by(Student.name).all()
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()

    form.student_id.choices = [
        (s.id, f'{s.name} ({s.roll_no})') for s in students
    ]

    if form.validate_on_submit():
        complaint = Complaint(
            student_id  = form.student_id.data,
            title       = form.title.data,
            description = form.description.data
        )
        db.session.add(complaint)
        db.session.commit()
        flash('Complaint submitted successfully.', 'success')
        return redirect(url_for('list_complaints'))

    return render_template('complaints/list.html',
                           form=form, students=students,
                           show_form=True, complaints=complaints,
                           status='all')


@app.route('/complaints/update/<int:complaint_id>', methods=['POST'])
@admin_required
def update_complaint_status(complaint_id):
    complaint        = Complaint.query.get_or_404(complaint_id)
    complaint.status = request.form.get('status', 'pending')
    db.session.commit()
    flash('Complaint status updated.', 'success')
    return redirect(url_for('list_complaints'))


@app.route('/complaints/delete/<int:complaint_id>', methods=['POST'])
@admin_required
def delete_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    db.session.delete(complaint)
    db.session.commit()
    flash('Complaint removed.', 'info')
    return redirect(url_for('list_complaints'))


# ── BOOTSTRAP ─────────────────────────────────────────────────────────────────

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)