import datetime
import time
from flask import Flask, render_template, redirect, request, abort

from data import db_session
from data.group_class import Group, GroupForm
from data.login_form import LoginForm
from data.question_class import Question, QuestionForm
from data.student_class import Student, StudentForm
from data.quiz_class import Quiz, QuizForm, CheckQuizForm
from data.register_form import RegisterForm
from data.test_class import Test
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from generate_quiz import generate_full

db_session.global_init("db/digital_footprint.db")

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    app.run(host='127.0.0.1', port=8080, debug=True, use_reloader=False)


def check_admin(func):
    def wrapper(*args, **kwargs):
        if current_user.is_admin:
            return func(*args, **kwargs)
        else:
            return redirect("/")

    wrapper.__name__ = func.__name__
    return wrapper


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@login_manager.user_loader
def load_user(student_id):
    db_sess = db_session.create_session()
    return db_sess.query(Student).get(student_id)


@app.route("/questions", methods=['GET', 'POST'])
@check_admin
def questions():
    query_questions = db_sess.query(Question).all()
    query_groups = db_sess.query(Group)
    return render_template('questions.html', query_questions=query_questions, query_groups=query_groups,
                           title="Вопросы")


@app.route('/questions/add/<int:id>', methods=['GET', 'POST'])
@check_admin
def add_questions(id):
    query_questions = db_sess.query(Question).all()
    query_groups = db_sess.query(Group)
    form = QuestionForm()
    theme = query_groups.filter_by(id_group=id).first().label
    if form.validate_on_submit():
        question = Question()
        question.texts = form.content.data
        question.id_group = id
        db_sess.add(question)
        db_sess.commit()
        return redirect('/questions')
    return render_template('questions_add.html', query_questions=query_questions, query_groups=query_groups,
                           title="Вопросы", form=form, theme=theme)


@app.route('/questions/<int:id>', methods=['GET', 'POST'])
@check_admin
def edit_questions(id):
    form = QuestionForm()
    theme = 0
    if request.method == "GET":
        db_sess = db_session.create_session()
        question = db_sess.query(Question).filter(Question.id_question == id).first()
        group = db_sess.query(Group)
        theme = group.filter_by(id_group=question.id_group).first().label
        if question:
            form.content.data = question.texts
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        question = db_sess.query(Question).filter(Question.id_question == id).first()
        group = db_sess.query(Group)
        if question:
            question.texts = form.content.data
            db_sess.commit()
            return redirect('/questions')
        else:
            abort(404)

    return render_template('questions_edit.html', title="ниЧиво?", form=form, id=id, theme=theme)


@app.route('/questions_delete/<int:id>', methods=['GET', 'POST'])
@check_admin
def questions_delete(id):
    db_sess = db_session.create_session()
    question = db_sess.query(Question).filter(Question.id_question == id).first()
    if question:
        db_sess.delete(question)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/questions')


@app.route('/waiting/<int:id>')
def waiting(id):
    time = datetime.datetime.now()
    dl = datetime.timedelta(minutes=5, seconds=30)
    db_sess = db_session.create_session()
    current_quizzes = db_sess.query(Quiz).filter_by(id_student=id).all()
    return render_template('waiting.html', current_quizzes=current_quizzes,
                           time=time, dl=dl)


@app.route("/students", methods=['GET', 'POST'])
@check_admin
def students():
    query_students = db_sess.query(Student).all()
    return render_template('students.html', query_students=query_students,
                           title="Студенты")


@app.route("/choice_student&groups", methods=['GET', 'POST'])
@check_admin
def choice_student_groups():
    query_students = db_sess.query(Student).all()
    query_groops = db_sess.query(Group).all()
    if request.method == "POST":
        groups = [i.id_group for i in query_groops if request.form.get(str(i.label))]
        if groups:
            students = [i.id_student for i in query_students if request.form.get(str(i.name) + str(i.birthday))]
            generate_full(students, groups)
            return redirect('/')

    return render_template('MDmd.html', query_students=query_students, query_groops=query_groops,
                           title="Выбрать студентов")


@app.route('/students/<int:id>', methods=['GET', 'POST'])
@check_admin
def students_edit(id):
    form = StudentForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        student = db_sess.query(Student).filter(Student.id_student == id).first()
        if student:
            form.name.data = student.name
            form.date.data = student.birthday
            form.id_stepik.data = student.id_stepik
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        student = db_sess.query(Student).filter(Student.id_student == id).first()
        if student:
            student.name = form.name.data
            student.birthday = form.date.data
            student.id_stepik = form.id_stepik.data
            db_sess.commit()
            return redirect('/students')
        else:
            abort(404)
    return render_template('students_edit.html', title="ниЧиво?", form=form, id=student.id_student)


@app.route('/students_delete/<int:id>', methods=['GET', 'POST'])
@check_admin
def students_delete(id):
    db_sess = db_session.create_session()
    student = db_sess.query(Student).filter(Student.id_student == id).first()
    if student:
        db_sess.delete(student)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/students')


@app.route('/groups', methods=['GET', 'POST'])
@check_admin
def groups():
    query_groups = db_sess.query(Group).all()
    form = GroupForm()
    if form.validate_on_submit():
        group = Group()
        group.label = form.label.data
        db_sess.add(group)
        db_sess.commit()
        return redirect('/groups')
    return render_template('groups.html', query_groups=query_groups,
                           title="Группы", form=form)


@app.route('/groups/<int:id>', methods=['GET', 'POST'])
@check_admin
def edit_groups(id):
    form = GroupForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        group = db_sess.query(Group).filter(Group.id_group == id).first()
        if group:
            form.label.data = group.label
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        group = db_sess.query(Group).filter(Group.id_group == id).first()
        if group:
            group.label = form.label.data
            db_sess.commit()
            return redirect('/groups')
        else:
            abort(404)
    return render_template('groups_edit.html', title="ниЧиво?", form=form, id=group.id_group)


@app.route('/groups_delete/<int:id>', methods=['GET', 'POST'])
@check_admin
def groups_delete(id):
    db_sess = db_session.create_session()
    group = db_sess.query(Group).filter(Group.id_group == id).first()
    if group:
        db_sess.delete(group)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/groups')


@app.route('/quiz/<int:id>', methods=['GET', 'POST'])
def quiz(id):
    db_sess = db_session.create_session()
    query_quiz = db_sess.query(Quiz).filter(Quiz.id_quiz == id).first()
    pytime = query_quiz.date
    js_time = int(time.mktime(pytime.timetuple())) * 1000
    tests = db_sess.query(Test).filter(Test.id_quiz == id).all()
    quests = []
    for i in tests:
        quests.append(db_sess.query(Question).filter(Question.id_question == i.id_question).first())
    form = QuizForm()
    if form.validate_on_submit():
        for i in range(5):
            tests[i].stud_answers = form.answers.data[i]
        db_sess.commit()
        return redirect("/")

    return render_template('quiz_page.html', id=id, questions_num=5,
                           query_questions=quests, title="Тестирование",
                           form=form, timer=330, time=js_time)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(Student).filter(
            (Student.name == form.name.data) & (Student.birthday == form.birthday.data)).first()
        if user:
            login_user(user, remember=form.remember_me.data)
            if current_user.is_admin:
                return redirect("/profile_admin")
            else:
                return redirect("/profile_students")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Student).filter(Student.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        student = Student(
            name=form.name.data,
            birthday=form.birthday.data,
            id_stepik=form.stepik_id.data
        )
        db_sess.add(student)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/", methods=['GET', 'POST'])
@app.route("/index")
def index():
    return render_template('index.html')


@app.route('/add_student', methods=['GET', 'POST'])
@check_admin
def add_student():
    form = StudentForm()
    if form.validate_on_submit() and login_user():
        student = Student()
        student.name = form.name.data
        student.birthday = form.date.data
        student.id_stepik = form.id_stepik.data
        db_sess.add(student)
        db_sess.commit()

        return redirect('/students')
    return render_template('add_student.html',
                           title="Студенты", form=form)


@app.route('/dsu')
def dsu():
    query_questions = db_sess.query(Question).all()
    query_groups = db_sess.query(Group).all()
    form = GroupForm()
    if form.validate_on_submit():
        group = Group()
        group.label = form.label.data
        db_sess.add(group)
        db_sess.commit()
        return redirect('/dsu')
    return render_template('dsu.html', query_questions=query_questions, query_groups=query_groups,
                           title="Список тем и вопросов", form=form)


@app.route('/check_quiz/<id>', methods=['POST', 'GET'])
@check_admin
def check_quiz(id):
    db_sess = db_session.create_session()
    quiz = db_sess.query(Quiz).filter(Quiz.id_quiz == id).first()
    student = db_sess.query(Student).filter(Student.id_student == quiz.id_student).first()
    tests = db_sess.query(Test).filter(Test.id_quiz == id).all()
    form = CheckQuizForm()
    quests = []
    answers = []
    for i in tests:
        quests.append(db_sess.query(Question).filter(Question.id_question == i.id_question).first())
        answers.append(i.stud_answers)
    if form.validate_on_submit():
        for i in range(5):
            tests[i].mark = form.marks.data[i]
            tests[i].comment = form.comments.data[i]
        db_sess.commit()
        return redirect("/")
    return render_template("check_quiz.html", name=student.name, answers=answers, questions=quests, form=form)


@app.route('/my_quizzes/<id_stud>')
def my_quizzes(id_stud):
    db_sess = db_session.create_session()

    student = db_sess.query(Student).filter(Student.id_student == id_stud).first()
    quizzes = db_sess.query(Quiz).filter(Quiz.id_student == id_stud).all()

    dates = []
    marks = []
    questions = []
    answers = []
    comments = []
    all_mark = 0
    for i in quizzes:
        dates.append(i.date.date())
        tests = db_sess.query(Test).filter(Test.id_quiz == i.id_quiz).all()
        sm = 0
        for j in tests:
            questions.append(db_sess.query(Question).filter(Question.id_question == j.id_question).first())
            answers.append(j.stud_answers)
            comments.append(j.comment)
            sm += j.mark if type(j.mark) == int else 0
        all_mark += sm
        marks.append(sm / 5)

    quizzes_count = []
    for i in db_sess.query(Quiz).all():
        if i.date.date() not in quizzes_count:
            quizzes_count.append(i.date.date())

    all_mark /= (len(quizzes_count) * 5)

    return render_template('my_quizzes.html', len=len(quizzes), dates=dates, marks=marks, all_mark=all_mark,
                           questions=questions, answers=answers, comments=comments)


@app.route('/profile_admin')
@check_admin
def admin():
    return render_template("profile_admin.html")


@app.route('/profile_students')
def pointless():
    return render_template('profile_students.html')


if __name__ == '__main__':
    db_sess = db_session.create_session()
    # generate_full([1, 2], [1])
    main()