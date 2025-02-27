from datetime import datetime, timedelta
from main import app, db, User, Student, Attendance, Exam, ExamResult, Event, Course, CourseEnrollment

# Sample data for initialization
def init_db():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        print("Creating sample users...")

        # Create admin user
        admin = User(
            username="admin",
            password="admin123",  # In production, use proper password hashing
            email="admin@sanctamaria.edu",
            role="admin",
            first_name="Admin",
            last_name="User",
            phone="555-123-4567"
        )

        # Create ICT department user
        ict = User(
            username="ict",
            password="ict123",  # In production, use proper password hashing
            email="ict@sanctamaria.edu",
            role="ict",
            first_name="ICT",
            last_name="Admin",
            phone="555-987-6543"
        )

        # Create Accounts department user
        accounts = User(
            username="accounts",
            password="accounts123",  # In production, use proper password hashing
            email="accounts@sanctamaria.edu",
            role="accounts",
            first_name="Accounts",
            last_name="Admin",
            phone="555-567-8901"
        )

        # Create teacher users
        teacher1 = User(
            username="jsmith",
            password="teacher123",
            email="jsmith@sanctamaria.edu",
            role="teacher",
            first_name="John",
            last_name="Smith",
            phone="555-234-5678"
        )

        teacher2 = User(
            username="mlee",
            password="teacher123",
            email="mlee@sanctamaria.edu",
            role="teacher",
            first_name="Maria",
            last_name="Lee",
            phone="555-345-6789"
        )

        # Create student users
        student1 = User(
            username="jpatel",
            password="student123",
            email="jpatel@student.sanctamaria.edu",
            role="student",
            first_name="Jay",
            last_name="Patel",
            phone="555-456-7890"
        )

        student2 = User(
            username="sjohnson",
            password="student123",
            email="sjohnson@student.sanctamaria.edu",
            role="student",
            first_name="Sarah",
            last_name="Johnson",
            phone="555-567-8901"
        )

        student3 = User(
            username="dkim",
            password="student123",
            email="dkim@student.sanctamaria.edu",
            role="student",
            first_name="David",
            last_name="Kim",
            phone="555-678-9012"
        )

        # Create parent users
        parent1 = User(
            username="apatel",
            password="parent123",
            email="apatel@parent.sanctamaria.edu",
            role="parent",
            first_name="Anita",
            last_name="Patel",
            phone="555-789-0123"
        )

        parent2 = User(
            username="djohnson",
            password="parent123",
            email="djohnson@parent.sanctamaria.edu",
            role="parent",
            first_name="Daniel",
            last_name="Johnson",
            phone="555-890-1234"
        )

        # Add users to database
        db.session.add_all([admin, ict, accounts, teacher1, teacher2, student1, student2, student3, parent1, parent2])
        db.session.commit()

        print("Creating student records...")

        # Create student records
        student1_record = Student(
            user_id=student1.id,
            admission_number="SMC2023001",
            date_of_birth=datetime(2006, 5, 12),
            gender="Male",
            father_name="Raj Patel",
            mother_name="Anita Patel",
            address="123 Main St, Cityville",
            religion="Hindu",
            class_name="Grade 11",
            section="A",
            admission_date=datetime(2018, 8, 15),
            father_occupation="Software Engineer",
            about="Jay is an enthusiastic student who enjoys science and mathematics. He participates in the debate club and robotics team."
        )

        student2_record = Student(
            user_id=student2.id,
            admission_number="SMC2023002",
            date_of_birth=datetime(2005, 9, 23),
            gender="Female",
            father_name="Daniel Johnson",
            mother_name="Elizabeth Johnson",
            address="456 Oak Ave, Townsburg",
            religion="Christian",
            class_name="Grade 12",
            section="B",
            admission_date=datetime(2017, 8, 10),
            father_occupation="Business Manager",
            about="Sarah is a dedicated student with interests in literature and history. She is the editor of the school newspaper and plays on the volleyball team."
        )

        student3_record = Student(
            user_id=student3.id,
            admission_number="SMC2023003",
            date_of_birth=datetime(2006, 3, 15),
            gender="Male",
            father_name="Sung Kim",
            mother_name="Min-Ji Kim",
            address="789 Pine Lane, Villageton",
            religion="Buddhist",
            class_name="Grade 11",
            section="A",
            admission_date=datetime(2018, 8, 15),
            father_occupation="Medical Doctor",
            about="David excels in mathematics and science. He is part of the chess club and has won several regional competitions."
        )

        # Add student records to database
        db.session.add_all([student1_record, student2_record, student3_record])
        db.session.commit()

        print("Creating attendance records...")

        # Create attendance records for the past month
        today = datetime.now().date()
        month_start = today.replace(day=1)

        attendance_types = ["Present", "Absent", "Late Coming", "Half Day Present"]

        # For each student, create attendance records
        for student_record in [student1_record, student2_record, student3_record]:
            current_date = month_start
            while current_date <= today:
                # Skip weekends
                if current_date.weekday() < 5:  # Monday to Friday
                    # Mostly present, with some variations
                    if current_date.day % 10 == 0:
                        status = "Absent"
                    elif current_date.day % 7 == 0:
                        status = "Late Coming"
                    elif current_date.day % 15 == 0:
                        status = "Half Day Present"
                    else:
                        status = "Present"

                    attendance = Attendance(
                        student_id=student_record.id,
                        date=current_date,
                        status=status
                    )
                    db.session.add(attendance)

                current_date += timedelta(days=1)

        db.session.commit()

        print("Creating exams and results...")

        # Create exams
        math_exam = Exam(
            name="Mid-Term Mathematics",
            exam_type="Mid-Term Test",
            subject="Mathematics",
            date=today - timedelta(days=15)
        )

        science_exam = Exam(
            name="Science Quarterly Assessment",
            exam_type="Quarterly Test",
            subject="Science",
            date=today - timedelta(days=10)
        )

        english_exam = Exam(
            name="English Literature Review",
            exam_type="Class Test",
            subject="English",
            date=today - timedelta(days=5)
        )

        history_exam = Exam(
            name="History Oral Presentation",
            exam_type="Oral Test",
            subject="History",
            date=today - timedelta(days=8)
        )

        db.session.add_all([math_exam, science_exam, english_exam, history_exam])
        db.session.commit()

        # Create exam results
        results = [
            # Student 1 results
            ExamResult(exam_id=math_exam.id, student_id=student1_record.id, grade="A", percentage=92.5),
            ExamResult(exam_id=science_exam.id, student_id=student1_record.id, grade="A-", percentage=88.0),
            ExamResult(exam_id=english_exam.id, student_id=student1_record.id, grade="B+", percentage=85.5),
            ExamResult(exam_id=history_exam.id, student_id=student1_record.id, grade="B", percentage=82.0),

            # Student 2 results
            ExamResult(exam_id=math_exam.id, student_id=student2_record.id, grade="B+", percentage=86.0),
            ExamResult(exam_id=science_exam.id, student_id=student2_record.id, grade="B", percentage=83.5),
            ExamResult(exam_id=english_exam.id, student_id=student2_record.id, grade="A", percentage=94.0),
            ExamResult(exam_id=history_exam.id, student_id=student2_record.id, grade="A-", percentage=89.5),

            # Student 3 results
            ExamResult(exam_id=math_exam.id, student_id=student3_record.id, grade="A+", percentage=96.0),
            ExamResult(exam_id=science_exam.id, student_id=student3_record.id, grade="A", percentage=93.5),
            ExamResult(exam_id=english_exam.id, student_id=student3_record.id, grade="B", percentage=84.0),
            ExamResult(exam_id=history_exam.id, student_id=student3_record.id, grade="B+", percentage=87.5)
        ]

        db.session.add_all(results)
        db.session.commit()

        print("Creating events...")

        # Create events
        events = [
            Event(
                title="Parent-Teacher Meeting",
                description="Annual parent-teacher meeting to discuss student progress",
                date=today + timedelta(days=10),
                time=datetime.strptime("16:00", "%H:%M").time()
            ),
            Event(
                title="Science Fair",
                description="Students showcase their science projects",
                date=today + timedelta(days=15),
                time=datetime.strptime("10:00", "%H:%M").time()
            ),
            Event(
                title="Sports Day",
                description="Annual sports competition and activities",
                date=today + timedelta(days=20),
                time=datetime.strptime("09:00", "%H:%M").time()
            ),
            Event(
                title="Career Guidance Workshop",
                description="Guest speakers from various industries",
                date=today + timedelta(days=25),
                time=datetime.strptime("14:00", "%H:%M").time()
            ),
            Event(
                title="Arts Exhibition",
                description="Showcase of student artwork and performances",
                date=today + timedelta(days=30),
                time=datetime.strptime("15:30", "%H:%M").time()
            ),
            Event(
                title="Final Exam Week",
                description="End of term examinations",
                date=today + timedelta(days=45),
                time=datetime.strptime("08:00", "%H:%M").time()
            )
        ]

        db.session.add_all(events)
        db.session.commit()

        print("Creating courses...")

        # Create courses
        courses = [
            Course(
                course_code="MATH101",
                course_name="Fundamentals of Mathematics",
                description="An introduction to basic mathematical concepts and principles.",
                credit_hours=3,
                teacher_id=teacher1.id
            ),
            Course(
                course_code="SCI201",
                course_name="General Science",
                description="A comprehensive overview of scientific principles and discoveries.",
                credit_hours=4,
                teacher_id=teacher2.id
            ),
            Course(
                course_code="ENG102",
                course_name="English Literature",
                description="Analysis of classical and contemporary literary works.",
                credit_hours=3,
                teacher_id=teacher1.id
            ),
            Course(
                course_code="HIST101",
                course_name="World History",
                description="Exploring major historical events and their impacts on modern society.",
                credit_hours=3,
                teacher_id=teacher2.id
            )
        ]

        db.session.add_all(courses)
        db.session.commit()

        # Enroll students in courses
        enrollments = [
            CourseEnrollment(student_id=student1_record.id, course_id=courses[0].id, grade="A-"),
            CourseEnrollment(student_id=student1_record.id, course_id=courses[1].id, grade="B+"),
            CourseEnrollment(student_id=student2_record.id, course_id=courses[0].id, grade="B"),
            CourseEnrollment(student_id=student2_record.id, course_id=courses[2].id, grade="A"),
            CourseEnrollment(student_id=student3_record.id, course_id=courses[1].id, grade="A+"),
            CourseEnrollment(student_id=student3_record.id, course_id=courses[3].id, grade="A-")
        ]

        db.session.add_all(enrollments)
        db.session.commit()

        print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()