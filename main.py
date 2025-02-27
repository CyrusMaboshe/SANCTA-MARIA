from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import io
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sanctamariacollege2023'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student, parent
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    profile_pic = db.Column(db.String(200), default='default.jpg')
    
    # Relationship with student
    student = db.relationship('Student', backref='user', uselist=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admission_number = db.Column(db.String(50), unique=True)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    religion = db.Column(db.String(50))
    class_name = db.Column(db.String(50))
    section = db.Column(db.String(50))
    admission_date = db.Column(db.Date)
    father_occupation = db.Column(db.String(100))
    about = db.Column(db.Text)
    sponsorship_type = db.Column(db.String(50))  # Self, Government, Corporate, Other
    
    # Relationships
    attendance = db.relationship('Attendance', backref='student', lazy=True)
    exam_results = db.relationship('ExamResult', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    date = db.Column(db.Date, default=datetime.now().date())
    status = db.Column(db.String(20))  # Present, Half Day Present, Late Coming, Absent

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    exam_type = db.Column(db.String(50))  # Class Test, Quarterly Test, Oral Test, etc.
    subject = db.Column(db.String(50))
    date = db.Column(db.Date)
    
    # Relationships
    results = db.relationship('ExamResult', backref='exam', lazy=True)

class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    grade = db.Column(db.String(5))
    percentage = db.Column(db.Float)

class FinalExam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(50))
    academic_year = db.Column(db.String(20))
    publish_date = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    results = db.relationship('FinalResult', backref='final_exam', lazy=True)

class FinalResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    final_exam_id = db.Column(db.Integer, db.ForeignKey('final_exam.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    subject = db.Column(db.String(100))
    marks = db.Column(db.Float)
    grade = db.Column(db.String(5))
    remarks = db.Column(db.String(200))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    student = db.relationship('Student', backref='final_results')
    teacher = db.relationship('User', backref='results_given')
    
class BOWCorporationResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('final_exam.id'))
    subject_code = db.Column(db.String(20))
    subject_name = db.Column(db.String(100))
    credit_hours = db.Column(db.Integer)
    marks = db.Column(db.Float)
    grade = db.Column(db.String(5))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    student = db.relationship('Student', backref='bow_results')
    exam = db.relationship('FinalExam', backref='bow_results')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    time = db.Column(db.Time)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    credit_hours = db.Column(db.Integer)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy=True)
    teacher = db.relationship('User', backref='courses_taught')
    
class CourseEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    enrollment_date = db.Column(db.DateTime, default=datetime.now)
    grade = db.Column(db.String(5))
    
    # Relationships
    student = db.relationship('Student', backref='course_enrollments')

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Accommodation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))  # Hostel, Apartment, etc.
    address = db.Column(db.String(200))
    total_capacity = db.Column(db.Integer)
    monthly_fee = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now)

class StudentAccommodation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accommodation.id'))
    room_number = db.Column(db.String(20))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20))  # Active, Inactive, Pending
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    student = db.relationship('Student', backref='accommodations')
    accommodation = db.relationship('Accommodation', backref='students')

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    invoice_number = db.Column(db.String(50), unique=True)
    issue_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    total_amount = db.Column(db.Float)
    paid_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20))  # Paid, Unpaid, Partially Paid
    semester = db.Column(db.String(50))
    academic_year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    student = db.relationship('Student', backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan')

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=1)
    item_type = db.Column(db.String(50))  # Tuition, Accommodation, Books, etc.

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    payment_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))  # Bank Transfer, Cash, etc.
    transaction_id = db.Column(db.String(100))
    receipt_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    invoice = db.relationship('Invoice', backref='payments')
    recorder = db.relationship('User', backref='recorded_payments')

class Sponsorship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    sponsor_name = db.Column(db.String(100))
    sponsor_type = db.Column(db.String(50))  # Government, Corporate, Individual, Self
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    coverage_details = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    student = db.relationship('Student', backref='sponsorships')

class ExamSlip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    final_exam_id = db.Column(db.Integer, db.ForeignKey('final_exam.id'))
    generated_date = db.Column(db.DateTime, default=datetime.now)
    is_valid = db.Column(db.Boolean, default=True)
    financial_clearance = db.Column(db.Boolean, default=False)
    academic_clearance = db.Column(db.Boolean, default=False)
    
    # Relationships
    student = db.relationship('Student', backref='exam_slips')
    exam = db.relationship('FinalExam', backref='exam_slips')

class CourseAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    assessment_type = db.Column(db.String(50))  # Quiz, Assignment, Mid-term, etc.
    assessment_date = db.Column(db.Date)
    marks = db.Column(db.Float)
    total_marks = db.Column(db.Float)
    weight = db.Column(db.Float)  # Percentage weight in final grade
    comments = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    student = db.relationship('Student', backref='assessments')
    course = db.relationship('Course', backref='assessments')
    teacher = db.relationship('User', backref='given_assessments')

class LectureNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    attachment_path = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    course = db.relationship('Course', backref='notes')
    teacher = db.relationship('User', backref='uploaded_notes')

class LectureMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # PDF, DOC, PPT, etc.
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    course = db.relationship('Course', backref='materials')
    teacher = db.relationship('User', backref='uploaded_materials')

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=30)
    total_marks = db.Column(db.Float, default=100.0)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    course = db.relationship('Course', backref='quizzes')
    questions = db.relationship('QuizQuestion', backref='quiz', cascade='all, delete-orphan')
    teacher = db.relationship('User', backref='created_quizzes')
    attempts = db.relationship('QuizAttempt', backref='quiz', cascade='all, delete-orphan')

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # multiple_choice, true_false, short_answer
    marks = db.Column(db.Float, default=1.0)
    order = db.Column(db.Integer, default=0)
    
    # For short answer questions
    correct_answer = db.Column(db.Text)
    
    # Relationships
    options = db.relationship('QuizQuestionOption', backref='question', cascade='all, delete-orphan')

class QuizQuestionOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.now)
    submit_time = db.Column(db.DateTime)
    total_score = db.Column(db.Float)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    student = db.relationship('Student', backref='quiz_attempts')
    answers = db.relationship('QuizAnswer', backref='attempt', cascade='all, delete-orphan')

class QuizAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    
    # For multiple choice/true-false
    selected_option_id = db.Column(db.Integer, db.ForeignKey('quiz_question_option.id'))
    
    # For short answer
    answer_text = db.Column(db.Text)
    
    # Grading
    marks_awarded = db.Column(db.Float)
    is_correct = db.Column(db.Boolean)
    
    # Relationships
    question = db.relationship('QuizQuestion')
    selected_option = db.relationship('QuizQuestionOption')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Role-based access control decorators
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('admin')(f)

def ict_required(f):
    return role_required('admin', 'ict')(f)

def accounts_required(f):
    return role_required('admin', 'accounts')(f)

# Account Department Routes
@app.route('/accounts/dashboard')
@login_required
@accounts_required
def accounts_dashboard():
    invoice_count = Invoice.query.count()
    total_billed = db.session.query(db.func.sum(Invoice.total_amount)).scalar() or 0
    total_paid = db.session.query(db.func.sum(Invoice.paid_amount)).scalar() or 0
    total_outstanding = total_billed - total_paid
    
    # Get upcoming invoices due in the next 30 days
    today = datetime.now().date()
    upcoming_invoices = []
    invoices = Invoice.query.filter(
        Invoice.due_date >= today,
        Invoice.due_date <= today + timedelta(days=30),
        Invoice.status != 'Paid'
    ).order_by(Invoice.due_date).limit(10).all()
    
    for invoice in invoices:
        student = Student.query.get(invoice.student_id)
        user = User.query.get(student.user_id)
        upcoming_invoices.append({
            'invoice_number': invoice.invoice_number,
            'student_name': f"{user.first_name} {user.last_name}",
            'total_amount': invoice.total_amount,
            'due_date': invoice.due_date,
            'status': invoice.status
        })
    
    return render_template('accounts_dashboard.html',
                          invoice_count=invoice_count,
                          total_billed=total_billed,
                          total_paid=total_paid,
                          total_outstanding=total_outstanding,
                          upcoming_invoices=upcoming_invoices)

@app.route('/accounts/invoices')
@login_required
@accounts_required
def accounts_invoices():
    invoices = Invoice.query.order_by(Invoice.issue_date.desc()).all()
    return render_template('accounts_invoices.html', invoices=invoices)

@app.route('/accounts/create_invoice', methods=['GET', 'POST'])
@login_required
@accounts_required
def accounts_create_invoice():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        issue_date = datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d').date()
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
        semester = request.form.get('semester')
        academic_year = request.form.get('academic_year')
        
        # Generate invoice number
        latest_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        invoice_number = f"INV-{datetime.now().year}-{latest_invoice.id + 1 if latest_invoice else 1:04d}"
        
        # Create invoice
        new_invoice = Invoice(
            student_id=student_id,
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            total_amount=0,  # Will be updated after adding items
            status='Unpaid',
            semester=semester,
            academic_year=academic_year
        )
        
        db.session.add(new_invoice)
        db.session.flush()  # Get the invoice ID without committing
        
        # Add invoice items
        total_amount = 0
        item_count = int(request.form.get('item_count', 0))
        
        for i in range(1, item_count + 1):
            description = request.form.get(f'description_{i}')
            amount = float(request.form.get(f'amount_{i}', 0))
            quantity = int(request.form.get(f'quantity_{i}', 1))
            item_type = request.form.get(f'item_type_{i}')
            
            if description and amount > 0:
                item = InvoiceItem(
                    invoice_id=new_invoice.id,
                    description=description,
                    amount=amount,
                    quantity=quantity,
                    item_type=item_type
                )
                db.session.add(item)
                total_amount += amount * quantity
        
        # Update invoice total
        new_invoice.total_amount = total_amount
        
        db.session.commit()
        flash('Invoice created successfully', 'success')
        return redirect(url_for('accounts_invoices'))
    
    students = Student.query.all()
    return render_template('accounts_create_invoice.html', students=students)

@app.route('/accounts/record_payment', methods=['GET', 'POST'])
@login_required
@accounts_required
def accounts_record_payment():
    if request.method == 'POST':
        invoice_id = request.form.get('invoice_id')
        payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
        amount = float(request.form.get('amount'))
        payment_method = request.form.get('payment_method')
        transaction_id = request.form.get('transaction_id', '')
        notes = request.form.get('notes', '')
        
        # Generate receipt number
        latest_payment = Payment.query.order_by(Payment.id.desc()).first()
        receipt_number = f"RCPT-{datetime.now().year}-{latest_payment.id + 1 if latest_payment else 1:04d}"
        
        # Record payment
        new_payment = Payment(
            invoice_id=invoice_id,
            payment_date=payment_date,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            receipt_number=receipt_number,
            notes=notes,
            recorded_by=current_user.id
        )
        
        db.session.add(new_payment)
        
        # Update invoice paid amount and status
        invoice = Invoice.query.get(invoice_id)
        invoice.paid_amount += amount
        
        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = 'Paid'
        elif invoice.paid_amount > 0:
            invoice.status = 'Partially Paid'
        
        db.session.commit()
        flash('Payment recorded successfully', 'success')
        return redirect(url_for('accounts_payments'))
    
    # Get unpaid or partially paid invoices
    invoices = Invoice.query.filter(Invoice.status != 'Paid').all()
    return render_template('accounts_record_payment.html', invoices=invoices)

@app.route('/accounts/payments')
@login_required
@accounts_required
def accounts_payments():
    payments = Payment.query.order_by(Payment.payment_date.desc()).all()
    return render_template('accounts_payments.html', payments=payments)

@app.route('/accounts/financial_summary')
@login_required
@accounts_required
def accounts_financial_summary():
    # Overall summary
    total_billed = db.session.query(db.func.sum(Invoice.total_amount)).scalar() or 0
    total_paid = db.session.query(db.func.sum(Invoice.paid_amount)).scalar() or 0
    total_outstanding = total_billed - total_paid
    
    # Get payment methods breakdown
    payment_methods = db.session.query(
        Payment.payment_method,
        db.func.sum(Payment.amount).label('total')
    ).group_by(Payment.payment_method).all()
    
    # Get item type breakdown
    item_types = db.session.query(
        InvoiceItem.item_type,
        db.func.sum(InvoiceItem.amount * InvoiceItem.quantity).label('total')
    ).group_by(InvoiceItem.item_type).all()
    
    return render_template('accounts_financial_summary.html',
                          total_billed=total_billed,
                          total_paid=total_paid,
                          total_outstanding=total_outstanding,
                          payment_methods=payment_methods,
                          item_types=item_types)

@app.route('/accounts/outstanding')
@login_required
@accounts_required
def accounts_outstanding():
    # Get students with outstanding balances
    outstanding_data = []
    
    students = Student.query.all()
    for student in students:
        # Calculate student's total billing and payment
        total_billed = db.session.query(db.func.sum(Invoice.total_amount)).filter_by(student_id=student.id).scalar() or 0
        total_paid = db.session.query(db.func.sum(Invoice.paid_amount)).filter_by(student_id=student.id).scalar() or 0
        
        if total_billed > total_paid:
            user = User.query.get(student.user_id)
            outstanding_data.append({
                'student_id': student.id,
                'name': f"{user.first_name} {user.last_name}",
                'admission_number': student.admission_number,
                'total_billed': total_billed,
                'total_paid': total_paid,
                'balance': total_billed - total_paid
            })
    
    return render_template('accounts_outstanding.html', outstanding_data=outstanding_data)

@app.route('/accounts/financial_reports')
@login_required
@accounts_required
def accounts_financial_reports():
    return render_template('accounts_financial_reports.html')

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # In production, use proper password hashing
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/student/courses')
@login_required
def student_courses():
    if current_user.role != 'student':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all courses the student is enrolled in
    enrollments = CourseEnrollment.query.filter_by(student_id=student.id).all()
    
    courses_data = []
    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        teacher = User.query.get(course.teacher_id) if course.teacher_id else None
        
        # Get continuous assessments for this course
        assessments = CourseAssessment.query.filter_by(
            student_id=student.id,
            course_id=course.id
        ).all()
        
        courses_data.append({
            'course': course,
            'enrollment': enrollment,
            'teacher': teacher,
            'assessments': assessments
        })
    
    # Get sponsorship information
    sponsorships = Sponsorship.query.filter_by(student_id=student.id).all()
    
    return render_template('student_courses.html', 
                          courses_data=courses_data,
                          sponsorships=sponsorships,
                          student=student)

@app.route('/student/accommodation')
@login_required
def student_accommodation():
    if current_user.role != 'student':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get current accommodation if any
    current_accommodation = StudentAccommodation.query.filter_by(
        student_id=student.id,
        status='Active'
    ).first()
    
    # Get accommodation history
    accommodation_history = StudentAccommodation.query.filter_by(
        student_id=student.id
    ).order_by(StudentAccommodation.start_date.desc()).all()
    
    return render_template('student_accommodation.html', 
                          current_accommodation=current_accommodation,
                          accommodation_history=accommodation_history,
                          student=student)

@app.route('/student/invoices')
@login_required
def student_invoices():
    if current_user.role != 'student':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all invoices
    invoices = Invoice.query.filter_by(student_id=student.id).order_by(Invoice.issue_date.desc()).all()
    
    return render_template('student_invoices.html', 
                          invoices=invoices,
                          student=student)

@app.route('/student/invoice/<int:invoice_id>')
@login_required
def student_invoice_detail(invoice_id):
    if current_user.role != 'student':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get the invoice
    invoice = Invoice.query.filter_by(id=invoice_id, student_id=student.id).first_or_404()
    
    # Get payments for this invoice
    payments = Payment.query.filter_by(invoice_id=invoice.id).all()
    
    return render_template('student_invoice_detail.html', 
                          invoice=invoice,
                          payments=payments,
                          student=student)

@app.route('/student/financial')
@login_required
def student_financial():
    if current_user.role != 'student':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get financial summary
    total_billed = db.session.query(db.func.sum(Invoice.total_amount)).filter_by(student_id=student.id).scalar() or 0
    total_paid = db.session.query(db.func.sum(Invoice.paid_amount)).filter_by(student_id=student.id).scalar() or 0
    balance = total_billed - total_paid
    
    # Get recent payments
    recent_payments = db.session.query(Payment, Invoice).join(
        Invoice, Payment.invoice_id == Invoice.id
    ).filter(
        Invoice.student_id == student.id
    ).order_by(Payment.payment_date.desc()).limit(5).all()
    
    # Get sponsorship information
    sponsorships = Sponsorship.query.filter_by(student_id=student.id).all()
    
    return render_template('student_financial.html', 
                          total_billed=total_billed,
                          total_paid=total_paid,
                          balance=balance,
                          recent_payments=recent_payments,
                          sponsorships=sponsorships,
                          student=student)

@app.route('/print-exam-slip')
@login_required
def print_exam_slip():
    if current_user.role != 'student':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get active final exams
    active_exams = FinalExam.query.filter(
        FinalExam.publish_date > datetime.now()
    ).order_by(FinalExam.publish_date).all()
    
    # Check if student has any valid exam slips
    exam_slips = ExamSlip.query.filter_by(
        student_id=student.id,
        is_valid=True
    ).all()
    
    # Check financial clearance
    unpaid_invoices = Invoice.query.filter_by(
        student_id=student.id,
        status='Unpaid'
    ).count()
    
    financial_clearance = unpaid_invoices == 0
    
    return render_template('print_exam_slip.html', 
                          active_exams=active_exams,
                          exam_slips=exam_slips,
                          financial_clearance=financial_clearance,
                          student=student)

@app.route('/generate-exam-slip/<int:exam_id>', methods=['POST'])
@login_required
def generate_exam_slip(exam_id):
    if current_user.role != 'student':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if student already has an exam slip for this exam
    existing_slip = ExamSlip.query.filter_by(
        student_id=student.id,
        final_exam_id=exam_id
    ).first()
    
    if existing_slip:
        if existing_slip.is_valid:
            flash('You already have a valid exam slip for this exam', 'warning')
        else:
            # Reactivate the slip
            existing_slip.is_valid = True
            db.session.commit()
            flash('Your exam slip has been regenerated', 'success')
        
        return redirect(url_for('print_exam_slip'))
    
    # Check financial clearance
    unpaid_invoices = Invoice.query.filter_by(
        student_id=student.id,
        status='Unpaid'
    ).count()
    
    financial_clearance = unpaid_invoices == 0
    
    # Check academic clearance (e.g., attendance requirements)
    # For now, we'll assume academic clearance is granted
    academic_clearance = True
    
    # Create the exam slip
    new_slip = ExamSlip(
        student_id=student.id,
        final_exam_id=exam_id,
        financial_clearance=financial_clearance,
        academic_clearance=academic_clearance,
        is_valid=True
    )
    
    db.session.add(new_slip)
    db.session.commit()
    
    flash('Exam slip generated successfully', 'success')
    return redirect(url_for('view_exam_slip', slip_id=new_slip.id))

@app.route('/view-exam-slip/<int:slip_id>')
@login_required
def view_exam_slip(slip_id):
    if current_user.role != 'student' and current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get the exam slip
    exam_slip = ExamSlip.query.get_or_404(slip_id)
    
    # Check if current user is authorized to view this slip
    student = Student.query.get(exam_slip.student_id)
    if current_user.role == 'student' and student.user_id != current_user.id:
        flash('You do not have permission to view this exam slip', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get exam details
    exam = FinalExam.query.get(exam_slip.final_exam_id)
    
    # Get student details
    user = User.query.get(student.user_id)
    
    # Get enrolled courses for this student
    enrolled_courses = db.session.query(Course).join(
        CourseEnrollment, CourseEnrollment.course_id == Course.id
    ).filter(
        CourseEnrollment.student_id == student.id
    ).all()
    
    return render_template('view_exam_slip.html',
                          exam_slip=exam_slip,
                          exam=exam,
                          student=student,
                          user=user,
                          enrolled_courses=enrolled_courses)

@app.route('/dashboard')
@login_required
def dashboard():
    # Redirect to role-specific dashboards
    if current_user.role == 'ict':
        return redirect(url_for('ict_dashboard'))
    elif current_user.role == 'accounts':
        return redirect(url_for('accounts_dashboard'))
    elif current_user.role == 'teacher':
        return redirect(url_for('lecturer_dashboard'))
    
    events = Event.query.limit(6).all()
    
    # Calculate attendance stats if the user is a student
    attendance_stats = {}
    if current_user.role == 'student':
        # Check if Student table has sponsorship_type column
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('student')]
        if 'sponsorship_type' not in columns:
            with app.app_context():
                db.engine.execute('ALTER TABLE student ADD COLUMN sponsorship_type VARCHAR(50)')
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        if student:
            # Get current month attendance
            current_month = datetime.now().month
            current_year = datetime.now().year
            monthly_attendance = Attendance.query.filter(
                Attendance.student_id == student.id,
                db.extract('month', Attendance.date) == current_month,
                db.extract('year', Attendance.date) == current_year
            ).all()
            
            # Calculate statistics
            total = len(monthly_attendance)
            present = sum(1 for a in monthly_attendance if a.status == 'Present')
            half_day = sum(1 for a in monthly_attendance if a.status == 'Half Day Present')
            late = sum(1 for a in monthly_attendance if a.status == 'Late Coming')
            absent = sum(1 for a in monthly_attendance if a.status == 'Absent')
            
            attendance_stats = {
                'present': present,
                'half_day': half_day,
                'late': late,
                'absent': absent,
                'total': total,
                'present_percent': (present / total * 100) if total > 0 else 0,
                'half_day_percent': (half_day / total * 100) if total > 0 else 0,
                'late_percent': (late / total * 100) if total > 0 else 0,
                'absent_percent': (absent / total * 100) if total > 0 else 0
            }
            
            # Get exam results
            exam_results = ExamResult.query.filter_by(student_id=student.id).all()
            
            # Get sponsorship information for student home page
            sponsorships = Sponsorship.query.filter_by(student_id=student.id).all()
            
            # Get course enrollment information
            course_enrollments = CourseEnrollment.query.filter_by(student_id=student.id).all()
            course_count = len(course_enrollments)
            
            # Get financial info for quick display
            total_billed = db.session.query(db.func.sum(Invoice.total_amount)).filter_by(student_id=student.id).scalar() or 0
            total_paid = db.session.query(db.func.sum(Invoice.paid_amount)).filter_by(student_id=student.id).scalar() or 0
            balance = total_billed - total_paid
            
            return render_template('dashboard.html', 
                                  events=events,
                                  attendance_stats=attendance_stats,
                                  student=student,
                                  sponsorships=sponsorships,
                                  course_count=course_count,
                                  total_billed=total_billed,
                                  total_paid=total_paid,
                                  balance=balance)
            
    # For ICT staff, show system statistics
    elif current_user.role == 'ict':
        user_count = User.query.count()
        student_count = Student.query.count()
        return render_template('dashboard.html', 
                              events=events,
                              user_count=user_count,
                              student_count=student_count)
                              
    # For Accounts staff, show financial statistics
    elif current_user.role == 'accounts':
        invoice_count = Invoice.query.count()
        total_billed = db.session.query(db.func.sum(Invoice.total_amount)).scalar() or 0
        total_paid = db.session.query(db.func.sum(Invoice.paid_amount)).scalar() or 0
        total_outstanding = total_billed - total_paid
        return render_template('dashboard.html', 
                              events=events,
                              invoice_count=invoice_count,
                              total_billed=total_billed,
                              total_paid=total_paid,
                              total_outstanding=total_outstanding)
    
    return render_template('dashboard.html', 
                          events=events,
                          attendance_stats=attendance_stats)

@app.route('/student/<int:student_id>')
@login_required
def student_profile(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    
    # Get attendance data
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_attendance = Attendance.query.filter(
        Attendance.student_id == student.id,
        db.extract('month', Attendance.date) == current_month,
        db.extract('year', Attendance.date) == current_year
    ).all()
    
    # Calculate attendance statistics
    total = len(monthly_attendance)
    present = sum(1 for a in monthly_attendance if a.status == 'Present')
    half_day = sum(1 for a in monthly_attendance if a.status == 'Half Day Present')
    late = sum(1 for a in monthly_attendance if a.status == 'Late Coming')
    absent = sum(1 for a in monthly_attendance if a.status == 'Absent')
    
    attendance_stats = {
        'present': present,
        'half_day': half_day,
        'late': late,
        'absent': absent,
        'total': total,
        'present_percent': (present / total * 100) if total > 0 else 0,
        'half_day_percent': (half_day / total * 100) if total > 0 else 0,
        'late_percent': (late / total * 100) if total > 0 else 0,
        'absent_percent': (absent / total * 100) if total > 0 else 0
    }
    
    # Get exam results
    exam_results = ExamResult.query.filter_by(student_id=student.id).all()
    exam_data = []
    
    for result in exam_results:
        exam = Exam.query.get(result.exam_id)
        exam_data.append({
            'id': f"#mar{result.id}",
            'type': exam.exam_type,
            'subject': exam.subject,
            'grade': result.grade,
            'percentage': result.percentage,
            'date': exam.date.strftime('%d %b %Y')
        })
    
    return render_template('student_profile.html', 
                          student=student,
                          user=user,
                          attendance_stats=attendance_stats,
                          exam_results=exam_data)

@app.route('/students')
@login_required
def students():
    all_students = Student.query.all()
    return render_template('students.html', students=all_students)

@app.route('/teachers')
@login_required
def teachers():
    all_teachers = User.query.filter_by(role='teacher').all()
    return render_template('teachers.html', teachers=all_teachers)

# Lecturer Routes
@app.route('/lecturer/dashboard')
@login_required
def lecturer_dashboard():
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get courses taught by the lecturer
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # Get recent activities
    recent_notes = LectureNote.query.filter_by(created_by=current_user.id).order_by(LectureNote.created_at.desc()).limit(5).all()
    recent_materials = LectureMaterial.query.filter_by(created_by=current_user.id).order_by(LectureMaterial.created_at.desc()).limit(5).all()
    recent_quizzes = Quiz.query.filter_by(created_by=current_user.id).order_by(Quiz.created_at.desc()).limit(5).all()
    
    return render_template('lecturer_dashboard.html', 
                           courses=courses,
                           recent_notes=recent_notes,
                           recent_materials=recent_materials,
                           recent_quizzes=recent_quizzes)

@app.route('/lecturer/courses')
@login_required
def lecturer_courses():
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get courses taught by the lecturer
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # For each course, get enrollment count
    for course in courses:
        course.enrollment_count = CourseEnrollment.query.filter_by(course_id=course.id).count()
    
    return render_template('lecturer_courses.html', courses=courses)

@app.route('/lecturer/course/<int:course_id>')
@login_required
def lecturer_course_detail(course_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the course
    course = Course.query.get_or_404(course_id)
    
    # Check if lecturer is assigned to this course
    if course.teacher_id != current_user.id:
        flash('You are not assigned to this course', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Get enrolled students
    enrollments = CourseEnrollment.query.filter_by(course_id=course.id).all()
    students_data = []
    
    for enrollment in enrollments:
        student = Student.query.get(enrollment.student_id)
        user = User.query.get(student.user_id)
        students_data.append({
            'id': student.id,
            'name': f"{user.first_name} {user.last_name}",
            'admission_number': student.admission_number,
            'grade': enrollment.grade
        })
    
    # Get course materials
    notes = LectureNote.query.filter_by(course_id=course.id).order_by(LectureNote.created_at.desc()).all()
    materials = LectureMaterial.query.filter_by(course_id=course.id).order_by(LectureMaterial.created_at.desc()).all()
    quizzes = Quiz.query.filter_by(course_id=course.id).order_by(Quiz.created_at.desc()).all()
    
    return render_template('lecturer_course_detail.html', 
                           course=course,
                           students=students_data,
                           notes=notes,
                           materials=materials,
                           quizzes=quizzes)

# Notes Management
@app.route('/lecturer/notes/<int:course_id>', methods=['GET', 'POST'])
@login_required
def manage_notes(course_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the course
    course = Course.query.get_or_404(course_id)
    
    # Check if lecturer is assigned to this course
    if course.teacher_id != current_user.id:
        flash('You are not assigned to this course', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Handle file upload if any
        attachment = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                # Create directory if it doesn't exist
                upload_folder = os.path.join(app.static_folder, 'uploads', 'notes')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save the file
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                attachment = f"uploads/notes/{filename}"
        
        new_note = LectureNote(
            course_id=course_id,
            title=title,
            content=content,
            attachment_path=attachment,
            created_by=current_user.id
        )
        
        db.session.add(new_note)
        db.session.commit()
        
        flash('Note added successfully', 'success')
        return redirect(url_for('manage_notes', course_id=course_id))
    
    # Get all notes for this course
    notes = LectureNote.query.filter_by(course_id=course_id).order_by(LectureNote.created_at.desc()).all()
    
    return render_template('lecturer_notes.html', course=course, notes=notes)

@app.route('/lecturer/notes/edit/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the note
    note = LectureNote.query.get_or_404(note_id)
    
    # Check if lecturer created this note
    if note.created_by != current_user.id:
        flash('You did not create this note', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        
        # Handle file upload if any
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                # Create directory if it doesn't exist
                upload_folder = os.path.join(app.static_folder, 'uploads', 'notes')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save the file
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                note.attachment_path = f"uploads/notes/{filename}"
        
        db.session.commit()
        
        flash('Note updated successfully', 'success')
        return redirect(url_for('manage_notes', course_id=note.course_id))
    
    return render_template('lecturer_edit_note.html', note=note)

@app.route('/lecturer/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the note
    note = LectureNote.query.get_or_404(note_id)
    
    # Check if lecturer created this note
    if note.created_by != current_user.id:
        flash('You did not create this note', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    course_id = note.course_id
    
    # Delete the note
    db.session.delete(note)
    db.session.commit()
    
    flash('Note deleted successfully', 'success')
    return redirect(url_for('manage_notes', course_id=course_id))

# Materials Management
@app.route('/lecturer/materials/<int:course_id>', methods=['GET', 'POST'])
@login_required
def manage_materials(course_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the course
    course = Course.query.get_or_404(course_id)
    
    # Check if lecturer is assigned to this course
    if course.teacher_id != current_user.id:
        flash('You are not assigned to this course', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '':
                # Create directory if it doesn't exist
                upload_folder = os.path.join(app.static_folder, 'uploads', 'materials')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save the file
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Get file type
                file_extension = os.path.splitext(filename)[1].lower()
                file_type = 'unknown'
                
                if file_extension in ['.pdf']:
                    file_type = 'PDF'
                elif file_extension in ['.doc', '.docx']:
                    file_type = 'DOC'
                elif file_extension in ['.ppt', '.pptx']:
                    file_type = 'PPT'
                elif file_extension in ['.xls', '.xlsx']:
                    file_type = 'XLS'
                elif file_extension in ['.txt']:
                    file_type = 'TXT'
                elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                    file_type = 'Image'
                elif file_extension in ['.mp4', '.avi', '.mov']:
                    file_type = 'Video'
                
                new_material = LectureMaterial(
                    course_id=course_id,
                    title=title,
                    description=description,
                    file_path=f"uploads/materials/{filename}",
                    file_type=file_type,
                    created_by=current_user.id
                )
                
                db.session.add(new_material)
                db.session.commit()
                
                flash('Material added successfully', 'success')
                return redirect(url_for('manage_materials', course_id=course_id))
            else:
                flash('No file selected', 'danger')
        else:
            flash('No file selected', 'danger')
    
    # Get all materials for this course
    materials = LectureMaterial.query.filter_by(course_id=course_id).order_by(LectureMaterial.created_at.desc()).all()
    
    return render_template('lecturer_materials.html', course=course, materials=materials)

@app.route('/lecturer/materials/delete/<int:material_id>', methods=['POST'])
@login_required
def delete_material(material_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the material
    material = LectureMaterial.query.get_or_404(material_id)
    
    # Check if lecturer created this material
    if material.created_by != current_user.id:
        flash('You did not upload this material', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    course_id = material.course_id
    
    # Delete the material
    db.session.delete(material)
    db.session.commit()
    
    flash('Material deleted successfully', 'success')
    return redirect(url_for('manage_materials', course_id=course_id))

# Quiz Management
@app.route('/lecturer/quizzes/<int:course_id>', methods=['GET'])
@login_required
def manage_quizzes(course_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the course
    course = Course.query.get_or_404(course_id)
    
    # Check if lecturer is assigned to this course
    if course.teacher_id != current_user.id:
        flash('You are not assigned to this course', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Get all quizzes for this course
    quizzes = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.created_at.desc()).all()
    
    return render_template('lecturer_quizzes.html', course=course, quizzes=quizzes)

@app.route('/lecturer/quizzes/create/<int:course_id>', methods=['GET', 'POST'])
@login_required
def create_quiz(course_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the course
    course = Course.query.get_or_404(course_id)
    
    # Check if lecturer is assigned to this course
    if course.teacher_id != current_user.id:
        flash('You are not assigned to this course', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        duration = request.form.get('duration')
        total_marks = request.form.get('total_marks')
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time')
        
        try:
            # Parse start and end dates/times
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
            
            new_quiz = Quiz(
                course_id=course_id,
                title=title,
                description=description,
                duration_minutes=int(duration),
                total_marks=float(total_marks),
                start_time=start_datetime,
                end_time=end_datetime,
                created_by=current_user.id
            )
            
            db.session.add(new_quiz)
            db.session.commit()
            
            flash('Quiz created successfully. Now add questions to your quiz.', 'success')
            return redirect(url_for('edit_quiz', quiz_id=new_quiz.id))
        except Exception as e:
            flash(f'Error creating quiz: {str(e)}', 'danger')
    
    return render_template('lecturer_create_quiz.html', course=course)

@app.route('/lecturer/quizzes/edit/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Get the course
    course = Course.query.get(quiz.course_id)
    
    if request.method == 'POST':
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        quiz.duration_minutes = int(request.form.get('duration'))
        quiz.total_marks = float(request.form.get('total_marks'))
        
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time')
        
        quiz.start_time = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        quiz.end_time = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
        
        db.session.commit()
        
        flash('Quiz updated successfully', 'success')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))
    
    # Get all questions for this quiz
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestion.order).all()
    
    return render_template('lecturer_edit_quiz.html', quiz=quiz, course=course, questions=questions)

@app.route('/lecturer/quizzes/publish/<int:quiz_id>', methods=['POST'])
@login_required
def publish_quiz(quiz_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Check if quiz has questions
    question_count = QuizQuestion.query.filter_by(quiz_id=quiz_id).count()
    
    if question_count == 0:
        flash('Cannot publish quiz with no questions', 'danger')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))
    
    # Publish the quiz
    quiz.is_published = True
    db.session.commit()
    
    flash('Quiz published successfully. Students can now take the quiz.', 'success')
    return redirect(url_for('manage_quizzes', course_id=quiz.course_id))

@app.route('/lecturer/quizzes/unpublish/<int:quiz_id>', methods=['POST'])
@login_required
def unpublish_quiz(quiz_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Unpublish the quiz
    quiz.is_published = False
    db.session.commit()
    
    flash('Quiz unpublished successfully', 'success')
    return redirect(url_for('manage_quizzes', course_id=quiz.course_id))

@app.route('/lecturer/quizzes/delete/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    course_id = quiz.course_id
    
    # Delete the quiz (will cascade to questions and options)
    db.session.delete(quiz)
    db.session.commit()
    
    flash('Quiz deleted successfully', 'success')
    return redirect(url_for('manage_quizzes', course_id=course_id))

# Quiz Question Management
@app.route('/lecturer/quizzes/add-question/<int:quiz_id>', methods=['POST'])
@login_required
def add_question(quiz_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Get form data
    question_type = request.form.get('question_type')
    question_text = request.form.get('question_text')
    marks = request.form.get('marks')
    
    # Get the highest order value for existing questions
    max_order = db.session.query(db.func.max(QuizQuestion.order)).filter_by(quiz_id=quiz_id).scalar() or 0
    
    # Create new question
    new_question = QuizQuestion(
        quiz_id=quiz_id,
        question_text=question_text,
        question_type=question_type,
        marks=float(marks),
        order=max_order + 1
    )
    
    # For short answer questions, get the correct answer
    if question_type == 'short_answer':
        new_question.correct_answer = request.form.get('correct_answer')
    
    db.session.add(new_question)
    db.session.flush()  # Get the question ID without committing
    
    # For multiple choice questions, add options
    if question_type == 'multiple_choice' or question_type == 'true_false':
        option_count = int(request.form.get('option_count', 0))
        
        for i in range(1, option_count + 1):
            option_text = request.form.get(f'option_{i}')
            is_correct = request.form.get(f'correct_option') == str(i)
            
            option = QuizQuestionOption(
                question_id=new_question.id,
                option_text=option_text,
                is_correct=is_correct,
                order=i
            )
            
            db.session.add(option)
    
    db.session.commit()
    
    flash('Question added successfully', 'success')
    return redirect(url_for('edit_quiz', quiz_id=quiz_id))

@app.route('/lecturer/quizzes/edit-question/<int:question_id>', methods=['POST'])
@login_required
def edit_question(question_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the question
    question = QuizQuestion.query.get_or_404(question_id)
    
    # Get the quiz
    quiz = Quiz.query.get(question.quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Update question data
    question.question_text = request.form.get('question_text')
    question.marks = float(request.form.get('marks'))
    
    # For short answer questions, update the correct answer
    if question.question_type == 'short_answer':
        question.correct_answer = request.form.get('correct_answer')
    
    # For multiple choice questions, update options
    if question.question_type == 'multiple_choice' or question.question_type == 'true_false':
        # Delete existing options
        QuizQuestionOption.query.filter_by(question_id=question.id).delete()
        
        option_count = int(request.form.get('option_count', 0))
        
        for i in range(1, option_count + 1):
            option_text = request.form.get(f'option_{i}')
            is_correct = request.form.get(f'correct_option') == str(i)
            
            option = QuizQuestionOption(
                question_id=question.id,
                option_text=option_text,
                is_correct=is_correct,
                order=i
            )
            
            db.session.add(option)
    
    db.session.commit()
    
    flash('Question updated successfully', 'success')
    return redirect(url_for('edit_quiz', quiz_id=quiz.id))

@app.route('/lecturer/quizzes/delete-question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the question
    question = QuizQuestion.query.get_or_404(question_id)
    
    # Get the quiz
    quiz = Quiz.query.get(question.quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Delete the question (will cascade to options)
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully', 'success')
    return redirect(url_for('edit_quiz', quiz_id=quiz.id))

# Quiz Results
@app.route('/lecturer/quizzes/results/<int:quiz_id>')
@login_required
def quiz_results(quiz_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Get all attempts for this quiz
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id, is_completed=True).all()
    
    students_data = []
    for attempt in attempts:
        student = Student.query.get(attempt.student_id)
        user = User.query.get(student.user_id)
        
        students_data.append({
            'id': student.id,
            'name': f"{user.first_name} {user.last_name}",
            'admission_number': student.admission_number,
            'attempt_id': attempt.id,
            'score': attempt.total_score,
            'submit_time': attempt.submit_time,
            'percentage': (attempt.total_score / quiz.total_marks) * 100 if quiz.total_marks > 0 else 0
        })
    
    return render_template('lecturer_quiz_results.html', quiz=quiz, students_data=students_data)

@app.route('/lecturer/quizzes/student-attempt/<int:attempt_id>')
@login_required
def view_student_attempt(attempt_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the attempt
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Get the quiz
    quiz = Quiz.query.get(attempt.quiz_id)
    
    # Check if lecturer created this quiz
    if quiz.created_by != current_user.id:
        flash('You did not create this quiz', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    # Get student information
    student = Student.query.get(attempt.student_id)
    user = User.query.get(student.user_id)
    
    # Get all answers for this attempt
    answers = QuizAnswer.query.filter_by(attempt_id=attempt.id).all()
    
    answers_data = []
    for answer in answers:
        question = QuizQuestion.query.get(answer.question_id)
        
        answer_data = {
            'question_text': question.question_text,
            'question_type': question.question_type,
            'marks': question.marks,
            'marks_awarded': answer.marks_awarded,
            'is_correct': answer.is_correct
        }
        
        if question.question_type == 'multiple_choice' or question.question_type == 'true_false':
            selected_option = QuizQuestionOption.query.get(answer.selected_option_id) if answer.selected_option_id else None
            answer_data['answer'] = selected_option.option_text if selected_option else 'No answer'
            
            # Get the correct option
            correct_option = QuizQuestionOption.query.filter_by(question_id=question.id, is_correct=True).first()
            answer_data['correct_answer'] = correct_option.option_text if correct_option else 'No correct answer'
        else:
            answer_data['answer'] = answer.answer_text
            answer_data['correct_answer'] = question.correct_answer
        
        answers_data.append(answer_data)
    
    return render_template('lecturer_view_attempt.html', 
                          quiz=quiz,
                          attempt=attempt,
                          student=student,
                          user=user,
                          answers=answers_data)

@app.route('/events')
@login_required
def events():
    all_events = Event.query.all()
    return render_template('events.html', events=all_events)

@app.route('/event/<int:event_id>')
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event_detail.html', event=event)

@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to add events', 'danger')
        return redirect(url_for('events'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            event_time = datetime.strptime(time_str, '%H:%M').time()
            
            new_event = Event(
                title=title,
                description=description,
                date=event_date,
                time=event_time
            )
            
            db.session.add(new_event)
            db.session.commit()
            
            flash('Event added successfully', 'success')
            return redirect(url_for('events'))
        except Exception as e:
            flash(f'Error adding event: {str(e)}', 'danger')
    
    return render_template('add_event.html')

@app.route('/attendance')
@login_required
def attendance():
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        attendances = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).all()
        return render_template('attendance.html', attendances=attendances, student=student)
    
    elif current_user.role == 'teacher' or current_user.role == 'admin':
        students = Student.query.all()
        return render_template('manage_attendance.html', students=students)
    
    else:
        flash('You do not have permission to view this page', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if current_user.role != 'teacher' and current_user.role != 'admin':
        flash('You do not have permission to mark attendance', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        for key, value in request.form.items():
            if key.startswith('status_'):
                student_id = int(key.replace('status_', ''))
                
                # Check if attendance record already exists
                existing = Attendance.query.filter_by(
                    student_id=student_id,
                    date=attendance_date
                ).first()
                
                if existing:
                    existing.status = value
                else:
                    new_attendance = Attendance(
                        student_id=student_id,
                        date=attendance_date,
                        status=value
                    )
                    db.session.add(new_attendance)
        
        db.session.commit()
        flash('Attendance marked successfully', 'success')
        return redirect(url_for('attendance'))
    
    students = Student.query.all()
    return render_template('mark_attendance.html', students=students, today=datetime.now().date())

@app.route('/exams')
@login_required
def exams():
    all_exams = Exam.query.all()
    return render_template('exams.html', exams=all_exams)

@app.route('/add_exam', methods=['GET', 'POST'])
@login_required
def add_exam():
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to add exams', 'danger')
        return redirect(url_for('exams'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        exam_type = request.form.get('exam_type')
        subject = request.form.get('subject')
        date_str = request.form.get('date')
        
        try:
            exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            new_exam = Exam(
                name=name,
                exam_type=exam_type,
                subject=subject,
                date=exam_date
            )
            
            db.session.add(new_exam)
            db.session.commit()
            
            flash('Exam added successfully', 'success')
            return redirect(url_for('exams'))
        except Exception as e:
            flash(f'Error adding exam: {str(e)}', 'danger')
    
    return render_template('add_exam.html')

@app.route('/exam_results/<int:exam_id>')
@login_required
def exam_results(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    results = ExamResult.query.filter_by(exam_id=exam_id).all()
    
    students_data = []
    for result in results:
        student = Student.query.get(result.student_id)
        user = User.query.get(student.user_id)
        students_data.append({
            'id': student.id,
            'name': f"{user.first_name} {user.last_name}",
            'admission_number': student.admission_number,
            'grade': result.grade,
            'percentage': result.percentage
        })
    
    return render_template('exam_results.html', exam=exam, results=students_data)

@app.route('/final-exams')
@login_required
def final_exams():
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    final_exams = FinalExam.query.order_by(FinalExam.created_at.desc()).all()
    
    # Count bow results for each exam
    for exam in final_exams:
        exam.bow_result_count = BOWCorporationResult.query.filter_by(exam_id=exam.id).count()
    
    return render_template('final_exams.html', final_exams=final_exams)

@app.route('/add-final-exam', methods=['GET', 'POST'])
@login_required
def add_final_exam():
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        semester = request.form.get('semester')
        academic_year = request.form.get('academic_year')
        publish_date_str = request.form.get('publish_date')
        publish_time_str = request.form.get('publish_time')
        
        try:
            # Combine date and time
            publish_datetime = datetime.strptime(f"{publish_date_str} {publish_time_str}", "%Y-%m-%d %H:%M")
            
            new_final_exam = FinalExam(
                name=name,
                semester=semester,
                academic_year=academic_year,
                publish_date=publish_datetime,
                is_published=False
            )
            
            db.session.add(new_final_exam)
            db.session.commit()
            
            flash('Final exam added successfully', 'success')
            return redirect(url_for('final_exams'))
        except Exception as e:
            flash(f'Error adding final exam: {str(e)}', 'danger')
    
    return render_template('add_final_exam.html')

@app.route('/manage-final-results/<int:final_exam_id>')
@login_required
def manage_final_results(final_exam_id):
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    final_exam = FinalExam.query.get_or_404(final_exam_id)
    final_results = FinalResult.query.filter_by(final_exam_id=final_exam_id).all()
    
    students_data = []
    for result in final_results:
        student = Student.query.get(result.student_id)
        user = User.query.get(student.user_id)
        students_data.append({
            'id': student.id,
            'name': f"{user.first_name} {user.last_name}",
            'admission_number': student.admission_number,
            'subject': result.subject,
            'marks': result.marks,
            'grade': result.grade,
            'remarks': result.remarks
        })
    
    return render_template('manage_final_results.html', 
                          final_exam=final_exam, 
                          results=students_data)

@app.route('/add-final-result/<int:final_exam_id>', methods=['GET', 'POST'])
@login_required
def add_final_result(final_exam_id):
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    final_exam = FinalExam.query.get_or_404(final_exam_id)
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject = request.form.get('subject')
        marks = request.form.get('marks')
        grade = request.form.get('grade')
        remarks = request.form.get('remarks')
        
        try:
            # Check if a result already exists for this student and subject
            existing_result = FinalResult.query.filter_by(
                final_exam_id=final_exam_id,
                student_id=student_id,
                subject=subject
            ).first()
            
            if existing_result:
                existing_result.marks = marks
                existing_result.grade = grade
                existing_result.remarks = remarks
                existing_result.teacher_id = current_user.id
            else:
                new_result = FinalResult(
                    final_exam_id=final_exam_id,
                    student_id=student_id,
                    subject=subject,
                    marks=marks,
                    grade=grade,
                    remarks=remarks,
                    teacher_id=current_user.id
                )
                db.session.add(new_result)
            
            db.session.commit()
            flash('Result added successfully', 'success')
            return redirect(url_for('manage_final_results', final_exam_id=final_exam_id))
        except Exception as e:
            flash(f'Error adding result: {str(e)}', 'danger')
    
    students = Student.query.all()
    return render_template('add_final_result.html', 
                          final_exam=final_exam, 
                          students=students)

@app.route('/publish-final-exam/<int:final_exam_id>', methods=['POST'])
@login_required
def publish_final_exam(final_exam_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized access'})
        
    final_exam = FinalExam.query.get_or_404(final_exam_id)
    
    # Toggle publish status
    final_exam.is_published = True if not final_exam.is_published else False
    db.session.commit()
    
    status = 'published' if final_exam.is_published else 'unpublished'
    return jsonify({
        'success': True, 
        'message': f'Final exam {status} successfully',
        'status': final_exam.is_published
    })

@app.route('/student-results')
@login_required
def student_results():
    if current_user.role != 'student':
        flash('This page is only for students', 'danger')
        return redirect(url_for('dashboard'))
        
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get published final exams and their results
    final_exams = FinalExam.query.filter(
        FinalExam.is_published == True,
        FinalExam.publish_date <= datetime.now()
    ).all()
    
    results_data = []
    for exam in final_exams:
        results = FinalResult.query.filter_by(
            final_exam_id=exam.id,
            student_id=student.id
        ).all()
        
        if results:
            results_data.append({
                'exam': exam,
                'results': results
            })
    
    # Get BOW Corporation results
    bow_results = db.session.query(FinalExam, BOWCorporationResult).\
        join(BOWCorporationResult, BOWCorporationResult.exam_id == FinalExam.id).\
        filter(
            BOWCorporationResult.student_id == student.id,
            FinalExam.is_published == True,
            FinalExam.publish_date <= datetime.now()
        ).all()
    
    bow_results_data = {}
    for exam, result in bow_results:
        if exam.id not in bow_results_data:
            bow_results_data[exam.id] = {
                'exam': exam,
                'results': []
            }
        bow_results_data[exam.id]['results'].append(result)
    
    return render_template('student_results.html', 
                          results_data=results_data,
                          bow_results_data=list(bow_results_data.values()))

@app.route('/bow-corporation-results/<int:final_exam_id>')
@login_required
def bow_corporation_results(final_exam_id):
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    final_exam = FinalExam.query.get_or_404(final_exam_id)
    
    # Get all BOW results for this exam
    results = db.session.query(BOWCorporationResult, Student, User).\
        join(Student, BOWCorporationResult.student_id == Student.id).\
        join(User, Student.user_id == User.id).\
        filter(BOWCorporationResult.exam_id == final_exam_id).\
        all()
    
    # Group results by student
    students_data = {}
    for result, student, user in results:
        if student.id not in students_data:
            students_data[student.id] = {
                'student_id': student.id,
                'name': f"{user.first_name} {user.last_name}",
                'admission_number': student.admission_number,
                'results': []
            }
        students_data[student.id]['results'].append({
            'subject_code': result.subject_code,
            'subject_name': result.subject_name,
            'credit_hours': result.credit_hours,
            'marks': result.marks,
            'grade': result.grade
        })
    
    return render_template('bow_corporation_results.html', 
                          final_exam=final_exam, 
                          students_data=list(students_data.values()))

@app.route('/add-bow-results/<int:final_exam_id>', methods=['GET', 'POST'])
@login_required
def add_bow_results(final_exam_id):
    if current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    final_exam = FinalExam.query.get_or_404(final_exam_id)
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        student = Student.query.get_or_404(student_id)
        
        # Get all subject data
        subject_count = 0
        results_to_add = []
        
        # Process form data for multiple subjects
        index = 0
        while f'subject_code_{index}' in request.form:
            subject_code = request.form.get(f'subject_code_{index}')
            subject_name = request.form.get(f'subject_name_{index}')
            credit_hours = request.form.get(f'credit_hours_{index}')
            marks = request.form.get(f'marks_{index}')
            
            # Calculate grade based on marks
            grade = 'F'
            marks_float = float(marks)
            if marks_float >= 97: grade = 'A+'
            elif marks_float >= 93: grade = 'A'
            elif marks_float >= 90: grade = 'A-'
            elif marks_float >= 87: grade = 'B+'
            elif marks_float >= 83: grade = 'B'
            elif marks_float >= 80: grade = 'B-'
            elif marks_float >= 77: grade = 'C+'
            elif marks_float >= 73: grade = 'C'
            elif marks_float >= 70: grade = 'C-'
            elif marks_float >= 67: grade = 'D+'
            elif marks_float >= 60: grade = 'D'
            
            if subject_code and subject_name and credit_hours and marks:
                subject_count += 1
                results_to_add.append({
                    'student_id': student_id,
                    'exam_id': final_exam_id,
                    'subject_code': subject_code,
                    'subject_name': subject_name,
                    'credit_hours': credit_hours,
                    'marks': marks,
                    'grade': grade
                })
            
            index += 1
        
        # Validate subject count (4-9 courses required)
        if subject_count < 4:
            flash('Error: Students must have at least 4 courses', 'danger')
            return redirect(url_for('add_bow_results', final_exam_id=final_exam_id))
        
        if subject_count > 9:
            flash('Error: Students cannot have more than 9 courses', 'danger')
            return redirect(url_for('add_bow_results', final_exam_id=final_exam_id))
        
        try:
            # First delete any existing results for this student and exam
            BOWCorporationResult.query.filter_by(
                student_id=student_id,
                exam_id=final_exam_id
            ).delete()
            
            # Add all new results
            for result_data in results_to_add:
                new_result = BOWCorporationResult(
                    student_id=result_data['student_id'],
                    exam_id=result_data['exam_id'],
                    subject_code=result_data['subject_code'],
                    subject_name=result_data['subject_name'],
                    credit_hours=result_data['credit_hours'],
                    marks=result_data['marks'],
                    grade=result_data['grade']
                )
                db.session.add(new_result)
            
            db.session.commit()
            flash(f'Successfully added {subject_count} results for {student.user.first_name} {student.user.last_name}', 'success')
            return redirect(url_for('bow_corporation_results', final_exam_id=final_exam_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding results: {str(e)}', 'danger')
    
    students = Student.query.all()
    return render_template('add_bow_results.html', 
                          final_exam=final_exam, 
                          students=students)

@app.route('/import-bow-results/<int:final_exam_id>', methods=['GET', 'POST'])
@login_required
def import_bow_results(final_exam_id):
    if current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    final_exam = FinalExam.query.get_or_404(final_exam_id)
    
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['excel_file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file:
            try:
                # Read Excel file
                df = pd.read_excel(file)
                
                # Validate Excel structure
                required_columns = ['admission_number', 'subject_code', 'subject_name', 'credit_hours', 'marks']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    flash(f'Missing columns in Excel file: {", ".join(missing_columns)}', 'danger')
                    return redirect(request.url)
                
                # Process data
                results_added = 0
                errors = []
                
                # Group by admission number
                student_groups = df.groupby('admission_number')
                
                for admission_number, group in student_groups:
                    # Find student
                    student = Student.query.filter_by(admission_number=admission_number).first()
                    if not student:
                        errors.append(f'Student with admission number {admission_number} not found')
                        continue
                    
                    # Validate course count (4-9)
                    course_count = len(group)
                    if course_count < 4:
                        errors.append(f'Student {admission_number} has less than 4 courses ({course_count})')
                        continue
                        
                    if course_count > 9:
                        errors.append(f'Student {admission_number} has more than 9 courses ({course_count})')
                        continue
                    
                    # Delete existing results for this student
                    BOWCorporationResult.query.filter_by(
                        student_id=student.id,
                        exam_id=final_exam_id
                    ).delete()
                    
                    # Add new results
                    for _, row in group.iterrows():
                        marks = float(row['marks'])
                        
                        # Calculate grade based on marks
                        grade = 'F'
                        if marks >= 97: grade = 'A+'
                        elif marks >= 93: grade = 'A'
                        elif marks >= 90: grade = 'A-'
                        elif marks >= 87: grade = 'B+'
                        elif marks >= 83: grade = 'B'
                        elif marks >= 80: grade = 'B-'
                        elif marks >= 77: grade = 'C+'
                        elif marks >= 73: grade = 'C'
                        elif marks >= 70: grade = 'C-'
                        elif marks >= 67: grade = 'D+'
                        elif marks >= 60: grade = 'D'
                        
                        new_result = BOWCorporationResult(
                            student_id=student.id,
                            exam_id=final_exam_id,
                            subject_code=row['subject_code'],
                            subject_name=row['subject_name'],
                            credit_hours=int(row['credit_hours']),
                            marks=marks,
                            grade=grade
                        )
                        db.session.add(new_result)
                    
                    results_added += 1
                
                if results_added > 0:
                    db.session.commit()
                    flash(f'Successfully imported results for {results_added} students', 'success')
                
                if errors:
                    error_message = '<br>'.join(errors)
                    flash(f'There were some errors during import:<br>{error_message}', 'warning')
                
                return redirect(url_for('bow_corporation_results', final_exam_id=final_exam_id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error importing from Excel: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('import_bow_results.html', final_exam=final_exam)

@app.route('/add_result/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def add_result(exam_id):
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to add exam results', 'danger')
        return redirect(url_for('exams'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('grade_'):
                student_id = int(key.replace('grade_', ''))
                grade = value
                percentage = request.form.get(f'percentage_{student_id}')
                
                # Check if result already exists
                existing = ExamResult.query.filter_by(
                    exam_id=exam_id,
                    student_id=student_id
                ).first()
                
                try:
                    percentage_float = float(percentage)
                    if existing:
                        existing.grade = grade
                        existing.percentage = percentage_float
                    else:
                        new_result = ExamResult(
                            exam_id=exam_id,
                            student_id=student_id,
                            grade=grade,
                            percentage=percentage_float
                        )
                        db.session.add(new_result)
                except ValueError:
                    flash(f'Invalid percentage value for student ID {student_id}', 'danger')
                    return redirect(url_for('add_result', exam_id=exam_id))
        
        db.session.commit()
        flash('Exam results added successfully', 'success')
        return redirect(url_for('exam_results', exam_id=exam_id))
    
    students = Student.query.all()
    return render_template('add_result.html', exam=exam, students=students)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.email = request.form.get('email')
        current_user.phone = request.form.get('phone')
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                # Create directory if it doesn't exist
                os.makedirs('static/img/profiles', exist_ok=True)
                
                # Save the file
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/img/profiles', filename)
                file.save(file_path)
                current_user.profile_pic = filename
        
        # Update password if provided
        password = request.form.get('password')
        if password and password.strip():
            current_user.password = password
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html')

@app.route('/admin/manage-passwords', methods=['GET', 'POST'])
@login_required
@ict_required
def admin_manage_passwords():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_password = request.form.get('new_password')
        
        if not user_id or not new_password:
            flash('User ID and new password are required', 'danger')
            return redirect(url_for('admin_manage_passwords'))
        
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('admin_manage_passwords'))
        
        # Update the password
        user.password = new_password  # In production, use proper password hashing
        db.session.commit()
        
        flash(f'Password updated successfully for {user.username}', 'success')
        
    # Get all students for admin to manage
    students = db.session.query(User, Student).join(
        Student, User.id == Student.user_id
    ).filter(
        User.role == 'student'
    ).all()
    
    return render_template('admin_manage_passwords.html', students=students)

@app.route('/admin/staff', methods=['GET'])
@login_required
@admin_required
def admin_staff():
    # Get staff members by role
    teachers = User.query.filter_by(role='teacher').all()
    ict_staff = User.query.filter_by(role='ict').all()
    accounts_staff = User.query.filter_by(role='accounts').all()
    
    return render_template('admin_staff.html', 
                           teachers=teachers,
                           ict_staff=ict_staff,
                           accounts_staff=accounts_staff)

@app.route('/admin/get_user/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Return user data without sensitive info like password
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'role': user.role
        }
    })

@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    try:
        # Update user fields
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone', '')
        
        # Update password if provided
        new_password = request.form.get('password')
        if new_password and new_password.strip():
            user.password = new_password
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'User updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating user: {str(e)}'})

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    try:
        # Check if this is a student user
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            return jsonify({'success': False, 'message': 'Cannot delete student users from this interface'})
        
        # For teachers, check if they are assigned to any courses
        if user.role == 'teacher' and Course.query.filter_by(teacher_id=user.id).count() > 0:
            return jsonify({'success': False, 'message': 'Cannot delete teacher who is assigned to courses'})
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting user: {str(e)}'})

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search_results.html', results={})
    
    # Search in students
    students = Student.query.join(User).filter(
        db.or_(
            User.first_name.contains(query),
            User.last_name.contains(query),
            Student.admission_number.contains(query)
        )
    ).all()
    
    # Search in teachers
    teachers = User.query.filter(
        db.and_(
            User.role == 'teacher',
            db.or_(
                User.first_name.contains(query),
                User.last_name.contains(query),
                User.email.contains(query)
            )
        )
    ).all()
    
    # Search in events
    events = Event.query.filter(
        db.or_(
            Event.title.contains(query),
            Event.description.contains(query)
        )
    ).all()
    
    results = {
        'students': students,
        'teachers': teachers,
        'events': events
    }
    
    return render_template('search_results.html', results=results, query=query)

# Admin, ICT and Accounts Routes
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if current_user.role != 'admin' and current_user.role != 'ict':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            # Get form data
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            role = request.form.get('role')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone', '')
            
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                return jsonify({'success': False, 'message': 'Username already exists'})
            
            if User.query.filter_by(email=email).first():
                return jsonify({'success': False, 'message': 'Email already exists'})
            
            # Create new user
            new_user = User(
                username=username,
                password=password,  # In production, use proper password hashing
                email=email,
                role=role,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'User created successfully'})
        
        elif action == 'edit':
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'success': False, 'message': 'User not found'})
            
            # Update user data
            user.first_name = request.form.get('first_name')
            user.last_name = request.form.get('last_name')
            user.email = request.form.get('email')
            user.phone = request.form.get('phone', '')
            
            # Update password if provided
            new_password = request.form.get('password')
            if new_password and new_password.strip():
                user.password = new_password
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'User updated successfully'})
        
        elif action == 'delete':
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'success': False, 'message': 'User not found'})
            
            # Check if user is a student and delete related records
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                # Delete attendance records
                Attendance.query.filter_by(student_id=student.id).delete()
                # Delete exam results
                ExamResult.query.filter_by(student_id=student.id).delete()
                # Delete student record
                db.session.delete(student)
            
            # Delete user
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'User deleted successfully'})
    
    # GET request - return all users
    users = User.query.all()
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone
        } for user in users]
    })

@app.route('/admin/system-config', methods=['POST'])
@login_required
def admin_system_config():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
    
    config_type = request.form.get('config_type')
    
    if config_type == 'calendar':
        # Process calendar configuration
        # In a real app, this would save to a configuration table in the database
        return jsonify({'success': True, 'message': 'Calendar configuration updated'})
    
    elif config_type == 'branding':
        # Process branding configuration
        # In a real app, this would save to a configuration table in the database
        return jsonify({'success': True, 'message': 'Branding configuration updated'})
    
    elif config_type == 'grading':
        # Process grading system configuration
        # In a real app, this would save to a configuration table in the database
        return jsonify({'success': True, 'message': 'Grading system configuration updated'})
    
    return jsonify({'success': False, 'message': 'Invalid configuration type'})

@app.route('/admin/generate-report', methods=['POST'])
@login_required
def admin_generate_report():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
    
    report_type = request.form.get('report_type')
    report_period = request.form.get('report_period')
    report_format = request.form.get('report_format')
    
    # In a real application, this would generate and return the appropriate report
    # For now, just return a success message
    return jsonify({
        'success': True, 
        'message': f'{report_type.capitalize()} report for {report_period} period generated successfully in {report_format.upper()} format'
    })

# Course Management Routes
@app.route('/admin/courses', methods=['GET'])
@login_required
def admin_courses():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    courses = Course.query.all()
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin_courses.html', courses=courses, teachers=teachers)

@app.route('/admin/courses/add', methods=['POST'])
@login_required
def add_course():
    if current_user.role != 'admin':
        flash('You do not have permission to add courses', 'danger')
        return redirect(url_for('dashboard'))
    
    course_code = request.form.get('course_code')
    course_name = request.form.get('course_name')
    description = request.form.get('description')
    credit_hours = request.form.get('credit_hours')
    teacher_id = request.form.get('teacher_id')
    
    # Check if course code already exists
    if Course.query.filter_by(course_code=course_code).first():
        return jsonify({'success': False, 'message': 'Course code already exists'})
    
    new_course = Course(
        course_code=course_code,
        course_name=course_name,
        description=description,
        credit_hours=credit_hours,
        teacher_id=teacher_id
    )
    
    db.session.add(new_course)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Course added successfully'})

@app.route('/admin/courses/edit/<int:course_id>', methods=['POST'])
@login_required
def edit_course(course_id):
    if current_user.role != 'admin':
        flash('You do not have permission to edit courses', 'danger')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    
    course.course_code = request.form.get('course_code')
    course.course_name = request.form.get('course_name')
    course.description = request.form.get('description')
    course.credit_hours = request.form.get('credit_hours')
    course.teacher_id = request.form.get('teacher_id')
    

@app.route('/admin/add_student', methods=['POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized access'})
    
    try:
        # Create user account first
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone', '')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already exists'})
        
        # Create new user with role 'student'
        new_user = User(
            username=username,
            password=password,
            email=email,
            role='student',
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        
        db.session.add(new_user)
        db.session.flush()  # Flush to get the user.id without committing
        
        # Now create the student record
        admission_number = request.form.get('admission_number')
        date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
        gender = request.form.get('gender')
        father_name = request.form.get('father_name', '')
        mother_name = request.form.get('mother_name', '')
        address = request.form.get('address', '')
        religion = request.form.get('religion', '')
        class_name = request.form.get('class_name')
        section = request.form.get('section')
        admission_date = datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d').date()
        father_occupation = request.form.get('father_occupation', '')
        about = request.form.get('about', '')
        
        # Check if admission number already exists
        if Student.query.filter_by(admission_number=admission_number).first():
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Admission number already exists'})
        
        # Create student record
        new_student = Student(
            user_id=new_user.id,
            admission_number=admission_number,
            date_of_birth=date_of_birth,
            gender=gender,
            father_name=father_name,
            mother_name=mother_name,
            address=address,
            religion=religion,
            class_name=class_name,
            section=section,
            admission_date=admission_date,
            father_occupation=father_occupation,
            about=about
        )
        
        db.session.add(new_student)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Student added successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error adding student: {str(e)}'})

@app.route('/admin/add_staff', methods=['POST'])
@login_required
@admin_required
def add_staff():
    try:
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role')  # 'ict', 'accounts', 'teacher'
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone', '')
        
        # Validate role
        if role not in ['ict', 'accounts', 'teacher']:
            return jsonify({'success': False, 'message': 'Invalid role selected'})
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already exists'})
        
        # Create new staff user
        new_staff = User(
            username=username,
            password=password,
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        
        db.session.add(new_staff)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{role.capitalize()} staff member added successfully',
            'staff_id': new_staff.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error adding staff: {str(e)}'})

@app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized access'})
    
    try:
        # Get the student record
        student = Student.query.get_or_404(student_id)
        user_id = student.user_id
        
        # Delete attendance records
        Attendance.query.filter_by(student_id=student.id).delete()
        
        # Delete exam results
        ExamResult.query.filter_by(student_id=student.id).delete()
        
        # Delete course enrollments
        CourseEnrollment.query.filter_by(student_id=student.id).delete()
        
        # Delete student record
        db.session.delete(student)
        
        # Delete user account
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Student deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting student: {str(e)}'})

    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Course updated successfully'})

@app.route('/admin/courses/delete/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    if current_user.role != 'admin':
        flash('You do not have permission to delete courses', 'danger')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    
    # Delete enrollments first
    CourseEnrollment.query.filter_by(course_id=course.id).delete()
    
    # Then delete the course
    db.session.delete(course)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Course deleted successfully'})

@app.route('/admin/courses/enroll', methods=['POST'])
@login_required
def enroll_student():
    if current_user.role != 'admin':
        flash('You do not have permission to enroll students', 'danger')
        return redirect(url_for('dashboard'))
    
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    
    # Check if student is already enrolled
    if CourseEnrollment.query.filter_by(student_id=student_id, course_id=course_id).first():
        return jsonify({'success': False, 'message': 'Student already enrolled in this course'})
    
    enrollment = CourseEnrollment(
        student_id=student_id,
        course_id=course_id
    )
    
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Student enrolled successfully'})

@app.route('/admin/courses/grade', methods=['POST'])
@login_required
def update_grade():
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('You do not have permission to update grades', 'danger')
        return redirect(url_for('dashboard'))
    
    enrollment_id = request.form.get('enrollment_id')
    grade = request.form.get('grade')
    
    enrollment = CourseEnrollment.query.get_or_404(enrollment_id)
    
    # Check if teacher is assigned to this course
    if current_user.role == 'teacher' and Course.query.get(enrollment.course_id).teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'You are not assigned to this course'})
    
    enrollment.grade = grade
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Grade updated successfully'})

@app.route('/admin/home-page', methods=['GET', 'POST'])
@login_required
def admin_home_page():
    if current_user.role != 'admin':
        flash('You do not have permission to edit the home page', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_content':
            try:
                # Get the path to the home.html template
                home_template_path = os.path.join(app.root_path, 'templates', 'home.html')
                
                # Get the edited content
                content = request.form.get('content')
                
                # Write the content to the file
                with open(home_template_path, 'w') as file:
                    file.write(content)
                
                flash('Home page updated successfully!', 'success')
                return jsonify({'success': True, 'message': 'Home page updated successfully'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error updating home page: {str(e)}'})
        
        elif action == 'upload_file':
            if 'file' not in request.files:
                return jsonify({'success': False, 'message': 'No file part'})
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No selected file'})
            
            try:
                # Create directories if they don't exist
                upload_folder = os.path.join(app.static_folder, 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save the file
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Return the URL to the uploaded file
                file_url = url_for('static', filename=f'uploads/{filename}')
                return jsonify({'success': True, 'message': 'File uploaded successfully', 'file_url': file_url})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error uploading file: {str(e)}'})
    
    # GET request - display the home page editor
    try:
        home_template_path = os.path.join(app.root_path, 'templates', 'home.html')
        with open(home_template_path, 'r') as file:
            content = file.read()
        return render_template('admin_home_editor.html', content=content)
    except Exception as e:
        flash(f'Error loading home page: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

def check_and_publish_results():
    """Background thread that checks and publishes results at the specified time"""
    with app.app_context():
        while True:
            try:
                # Find exams that should be published now
                now = datetime.now()
                exams_to_publish = FinalExam.query.filter(
                    FinalExam.is_published == False,
                    FinalExam.publish_date <= now
                ).all()
                
                for exam in exams_to_publish:
                    exam.is_published = True
                    db.session.commit()
                    print(f"Auto-published exam: {exam.name} at {now}")
            except Exception as e:
                print(f"Error in publishing scheduler: {str(e)}")
            
            # Check every 60 seconds
            time.sleep(60)

# ICT Department Routes
@app.route('/ict/dashboard')
@login_required
@ict_required
def ict_dashboard():
    user_count = User.query.count()
    student_count = Student.query.count()
    return render_template('ict_dashboard.html', 
                           user_count=user_count,
                           student_count=student_count)

@app.route('/ict/manage_users')
@login_required
@ict_required
def ict_manage_users():
    users = User.query.all()
    return render_template('ict_manage_users.html', users=users)

@app.route('/ict/manage_students')
@login_required
@ict_required
def ict_manage_students():
    students = db.session.query(User, Student).join(
        Student, User.id == Student.user_id
    ).filter(
        User.role == 'student'
    ).all()
    return render_template('ict_manage_students.html', students=students)

@app.route('/ict/system_backup')
@login_required
@ict_required
def ict_system_backup():
    return render_template('ict_system_backup.html')

# Lecturer Attendance Routes
@app.route('/lecturer/course/<int:course_id>/mark_attendance', methods=['GET', 'POST'])
@login_required
def lecturer_mark_attendance(course_id):
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('dashboard'))
        
    # Get the course
    course = Course.query.get_or_404(course_id)
    
    # Check if lecturer is assigned to this course
    if course.teacher_id != current_user.id:
        flash('You are not assigned to this course', 'danger')
        return redirect(url_for('lecturer_courses'))
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all enrollments for this course
        enrollments = CourseEnrollment.query.filter_by(course_id=course.id).all()
        
        for enrollment in enrollments:
            status_key = f'status_{enrollment.student_id}'
            if status_key in request.form:
                status = request.form.get(status_key)
                
                # Check if attendance record already exists
                existing = Attendance.query.filter_by(
                    student_id=enrollment.student_id,
                    date=attendance_date
                ).first()
                
                if existing:
                    existing.status = status
                else:
                    new_attendance = Attendance(
                        student_id=enrollment.student_id,
                        date=attendance_date,
                        status=status
                    )
                    db.session.add(new_attendance)
        
        db.session.commit()
        flash('Attendance marked successfully', 'success')
        return redirect(url_for('lecturer_course_detail', course_id=course_id))
    
    # Get students enrolled in this course
    enrollments = CourseEnrollment.query.filter_by(course_id=course.id).all()
    students_data = []
    
    for enrollment in enrollments:
        student = Student.query.get(enrollment.student_id)
        user = User.query.get(student.user_id)
        students_data.append({
            'id': student.id,
            'name': f"{user.first_name} {user.last_name}",
            'admission_number': student.admission_number
        })
    
    return render_template('lecturer_mark_attendance.html', 
                           course=course,
                           students=students_data,
                           today=datetime.now())

# Admin Report Routes
@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    return render_template('admin_reports.html')

@app.route('/admin/generate_report', methods=['POST'])
@login_required
@admin_required
def admin_generate_report_file():
    report_type = request.form.get('report_type')
    report_period = request.form.get('report_period')
    report_format = request.form.get('report_format')
    
    try:
        # Import required libraries for report generation
        import pandas as pd
        from io import BytesIO
        from datetime import datetime
        
        # Generate different reports based on the type
        if report_type == 'student':
            # Create student report
            students = db.session.query(User, Student).join(
                Student, User.id == Student.user_id
            ).filter(
                User.role == 'student'
            ).all()
            
            data = []
            for user, student in students:
                data.append({
                    'Admission Number': student.admission_number,
                    'First Name': user.first_name,
                    'Last Name': user.last_name,
                    'Gender': student.gender,
                    'Class': student.class_name,
                    'Section': student.section,
                    'Date of Birth': student.date_of_birth,
                    'Email': user.email,
                    'Phone': user.phone,
                    'Address': student.address
                })
            
            df = pd.DataFrame(data)
            
        elif report_type == 'financial':
            # Create financial report
            invoices = Invoice.query.all()
            
            data = []
            for invoice in invoices:
                student = Student.query.get(invoice.student_id)
                user = User.query.get(student.user_id)
                
                data.append({
                    'Invoice Number': invoice.invoice_number,
                    'Student': f"{user.first_name} {user.last_name}",
                    'Admission Number': student.admission_number,
                    'Issue Date': invoice.issue_date,
                    'Due Date': invoice.due_date,
                    'Total Amount': invoice.total_amount,
                    'Paid Amount': invoice.paid_amount,
                    'Balance': invoice.total_amount - invoice.paid_amount,
                    'Status': invoice.status,
                    'Semester': invoice.semester,
                    'Academic Year': invoice.academic_year
                })
            
            df = pd.DataFrame(data)
        
        else:
            # Placeholder for other report types
            data = [{'Message': f'Sample {report_type} report for {report_period} period'}]
            df = pd.DataFrame(data)
        
        # Generate the report in the requested format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_report_{timestamp}"
        
        # Return a success message (in production, would return the actual file)
        return jsonify({
            'success': True, 
            'message': f'{report_type.capitalize()} report for {report_period} period generated successfully in {report_format.upper()} format',
            'filename': f"{filename}.{report_format}"
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# Connect to Supabase
@app.route('/admin/connect_supabase')
@login_required
@admin_required
def connect_supabase():
    try:
        from supabase_config import get_supabase_client
        
        # Test the connection
        supabase = get_supabase_client()
        response = supabase.table('users').select('*').limit(1).execute()
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to Supabase'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error connecting to Supabase: {str(e)}'
        })

if __name__ == '__main__':
    # Start the background thread for checking and publishing results
    scheduler_thread = threading.Thread(target=check_and_publish_results)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    app.run(host='0.0.0.0', port=8080, debug=True)