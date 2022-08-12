from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import sqlite3

DATABASE = "./Assignment3.db"

def get_db():
    # if there is a database, use it
    db = getattr(g, '_database', None)
    if db is None:
        # otherwise, create a database to use
        db = g._database = sqlite3.connect(DATABASE)
    return db

# converts the tuples from get_db() into dictionaries
# (don't worry if you don't understand this code)
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# given a query, executes and returns the result
# (don't worry if you don't understand this code)
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

app=Flask(__name__)
app.secret_key=b'anyString'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Assignment3.db"
db = SQLAlchemy(app)

@app.route('/')
def index():
    if not 'username' in session:
        return redirect(url_for('login'))
    else:
        username = session['username']
        return render_template('index.html', user = username)

@app.route('/index')
def index2():
    return redirect(url_for('index'))

@app.route('/team')
def team():
    if not 'username' in session:
        return redirect(url_for('login'))
    else:
        return render_template('team.html')
    
@app.route('/assignments')
def assignments():
    if not 'username' in session:
        return redirect(url_for('login'))
    else:
        return render_template('assignments.html')

@app.route('/syllabus')
def syllabus():
    if not 'username' in session:
        return redirect(url_for('login'))
    else:
        return render_template('syllabus.html')

@app.route('/feedback')
def feedback():
    if not 'username' in session:
        return redirect(url_for('login'))
    else:
        db = get_db()
        db.row_factory = make_dicts

        usertype = query_db('select * from users where username = ?',
                            [session['username']], one=True)

        type = usertype['type']
        if type == "student":

            instructors = query_db('select username, FirstName, LastName from Instructors')

            return render_template('feedback.html', instructors = instructors)

        elif type == "instructor":
            feedback = query_db('select * from Feedback where username = ?', [session['username']], one = False)

            return render_template("feedbackinstructor.html", feedback = feedback)



@app.route('/labs')
def labs():
    if not 'username' in session:
        return redirect(url_for('login'))
    else:
        return render_template('labs.html')

@app.route('/marks')
def marks():
    db = get_db()
    db.row_factory = make_dicts

    usertype = query_db('select * from users where username = ?',
                        [session['username']], one=True)
    type = usertype['type']
    username = session['username']
    if type == "student":
        results = query_db('select * from Student where username = ?',
                 [username], one=True)

        return render_template('grades.html', post=results)
    elif type == "instructor":
        results = query_db( 'SELECT * FROM Student')

        return render_template('gradesInstructor.html', data=results)


@app.route('/editmark', methods=['GET', 'POST'])
def editMark():
    if 'username' in session:
        if request.method =='POST':
            db = get_db()
            db.row_factory = make_dicts
            cur = db.cursor()
            students = query_db(
                'select username from Student')

            A1Mark=request.form['A1']
            A2Mark=request.form['A2']
            A3Mark=request.form['A3']
            quiz1Mark=request.form['Quiz1']
            quiz2Mark=request.form['Quiz2']
            quiz3Mark=request.form['Quiz3']
            midtermExamMark=request.form['Midterm']
            finalExamMark=request.form['Final']
            username=request.form['student']
            for student in students:
                if student['username'] == username:
                    cur.execute(
                        'UPDATE Student SET A1=(?), A2=(?), A3=(?), Quiz1=(?), Quiz2=(?), Quiz3=(?), Midterm=(?), Final=(?) WHERE username = (?); ',
                        [
                         A1Mark, A2Mark, A3Mark, quiz1Mark, quiz2Mark, quiz3Mark, midtermExamMark, finalExamMark, username
                     ])
                    db.commit()
                    cur.close()

                    return redirect(url_for('marks'))
            else:
                results = query_db('SELECT * FROM Student')
                cur.close()
                message = "The username you entered was incorrect, please try again"
                return render_template('gradesinstructor.html', message = message, data=results)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method=='POST':
        db = get_db()
        db.row_factory = make_dicts
        results =query_db(' SELECT * FROM users')
        for result in results:
            if result['username']==request.form['username']:
                if result['password']==request.form['password']:
                    session['username']=request.form['username']
                    return redirect(url_for('index'))

        error = "Invalid credentials. Please try again."
        return render_template('login.html', error=error)

    elif 'username' in session:
        return redirect(url_for('index'))

    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/submitfeedback', methods=['POST'])
def submitfeedback():
    username = request.form['username']
    firstname = request.form['firstname']
    a = request.form['question1']
    b = request.form['question2']
    c = request.form['question3']
    d = request.form['question4']


    db = get_db()
    db.row_factory = make_dicts

    instructors = query_db(
        'select username, FirstName, LastName from Instructors')

    for instructor in instructors:
        if instructor["username"] == username:
            if instructor["FirstName"] == firstname:

                cur = db.cursor()
                cur.execute(
                    'insert into Feedback (username,InstructorFirstName, FeedbackA, FeedbackB, FeedbackC, FeedbackD) values (?, ?, ?, ?, ?, ?)', [
                        username, firstname, a, b, c, d
                        ])
                db.commit()
                cur.close()
                return render_template('feedback.html', instructors=instructors)

    fail = "SORRY, THE USERNAME OR PASSWORD YOU ENTERED IS INCORRECT, PLEASE REDO YOUR SUBMISSION"
    return render_template('feedback.html', instructors=instructors, fail=fail)

@app.route('/signup')
def signup():
    if not 'username' in session:
        return render_template("signup.html")
    else:
        return redirect(url_for('index'))


@app.route('/signupform', methods=['GET', 'POST'])
def signupform():
    error = None
    if request.method=='POST':
        db = get_db()
        db.row_factory = make_dicts
        users = query_db('select * from users')
        cur = db.cursor()
        op = request.form["options"]

        for user in users:
            if user['username']== request.form['username']:
                message = "Sorry that username is taken, please enter a new one"
                return render_template("signup.html", message = message)

        cur.execute(
            'insert into users (username, password, type ) values (?, ?, ?)',                    
            [
                    request.form['username'], request.form['password'], request.form['options']
            ])
        if request.form["options"]=="student":
            cur.execute(
                'insert into Student (username, FirstName, LastName ) values (?, ?, ?)',
                [
                    request.form['username'],
                    request.form['firstname'],
                    request.form['lastname']
                ])
        elif request.form["options"]=="instructor":
            cur.execute(
                    'insert into Instructors (username, FirstName, LastName ) values (?, ?, ?)',
                [
                    request.form['username'],
                    request.form['firstname'],
                    request.form['lastname']
                ])
        db.commit()
        cur.close()
        return render_template("login.html")

        error = "Invalid credentials. Please try again."
        return render_template('signup.html', error=error)

@app.route('/regrademark', methods = ['POST'])
def regrademark():
    if request.method == 'POST':
        db = get_db()
        db.row_factory = make_dicts
        cur = db.cursor()
        remarka1 = request.form['A1']
        remarka2 = request.form['A2']
        remarka3 = request.form['A3']
        remarkquiz1 = request.form['Quiz1']
        remarkquiz2 = request.form['Quiz2']
        remarkquiz3 = request.form['Quiz3']
        remarkme = request.form['Midterm']
        remarkfe = request.form['Final']
        username = session['username']

        cur.execute('UPDATE student SET RemarkA1 = ?, RemarkA2 = ?, RemarkA3 = ?, RemarkQuiz1 = ?, RemarkQuiz2 = ?, RemarkQuiz3 = ?,'
                    'RemarkMidterm = ?, RemarkFinal = ? WHERE username = ?',[remarka1, remarka2,
             remarka3, remarkquiz1, remarkquiz2, remarkquiz3, remarkme, remarkfe, username])
        return redirect(url_for('marks'))

@app.route('/remarkrequests')
def remarkrequests():
    if 'username' in session:
        db = get_db()
        db.row_factory = make_dicts
        remarks = query_db('SELECT * FROM Student')
        return render_template('remarkrequests.html', data = remarks)




if __name__=="__main__":
    app.run(debug=True,host='0.0.0.0')