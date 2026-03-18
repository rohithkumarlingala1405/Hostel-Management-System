# 🏨 IIT Goa Hostel Management System

A full-stack web application built with Flask to streamline hostel operations at IIT Goa.

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | SQLite, SQLAlchemy |
| Frontend | HTML, CSS, Bootstrap 5, Jinja2 |
| Authentication | Flask-Login |
| Forms | WTForms |
| Data Upload | Pandas |

## ✨ Features

- **Role-based access control** — Admin (Hall Office) and Student roles
- **Student Management** — Add, Edit, Delete, Search students
- **Room Management** — Manage rooms by block (B1, B2, B3 for Boys / G1 for Girls)
- **Gender Restriction** — Male students can only be assigned to Boys blocks, Female to Girls block
- **Complaints System** — Submit, track and resolve complaints
- **Bulk CSV Upload** — Upload multiple students and rooms at once using CSV
- **Dashboard** — Live statistics for students, rooms, complaints
- **Responsive UI** — Works on desktop and mobile

## 🚀 Setup & Installation
```bash
# 1. Clone the repository
git clone https://github.com/rohithkumarlingala1405/Hostel-Management-System.git

# 2. Navigate to project folder
cd Hostel-Management-System

# 3. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 4. Install dependencies
pip install flask flask-sqlalchemy flask-login flask-wtf wtforms email-validator pandas

# 5. Run the app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## 🔐 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin (Hall Office) | admin | admin123 |
| Student | student | student123 |

## 📁 Project Structure
```
HostelManagement/
├── app.py                  # Main Flask application
├── forms.py                # WTForms form classes
├── static/
│   └── css/
│       └── style.css       # Custom CSS
└── templates/
    ├── base.html           # Sidebar layout
    ├── login.html          # Login page
    ├── dashboard.html      # Dashboard
    ├── students/
    │   ├── list.html
    │   ├── form.html
    │   └── bulk_upload.html
    ├── rooms/
    │   ├── list.html
    │   ├── form.html
    │   ├── available.html
    │   └── assign.html
    └── complaints/
        └── list.html
```

## 📊 Database Schema

| Table | Key Columns |
|-------|------------|
| users | id, username, password, role |
| rooms | id, block, room_number, floor, capacity |
| students | id, name, roll_no, email, gender, room_id |
| complaints | id, student_id, title, description, status, created_at |

## 📝 CSV Upload Format

### Rooms CSV
```
block,room_number,floor,capacity
B1,101,1,2
G1,101,1,2
```

### Students CSV
```
name,roll_no,email,gender,block,room_number
Ravi Kumar,20241001,ravi@iitgoa.ac.in,Male,B1,101
Priya Sharma,20241002,priya@iitgoa.ac.in,Female,G1,101
```