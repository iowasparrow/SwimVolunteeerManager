from flask import Flask
from flask import render_template, flash, request, redirect, url_for, session
import sqlite3
import smtplib
import logging
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = b'_5#y2u"F4Q8z\n\xec]/'
database = '/var/www/html/signup/signup.db'
# database = 'signup.db'
# toptimesdatabase = '/var/www/html/signup/toptimes.db'
now = datetime.datetime.today().strftime('%#m/%d/%Y')  # the hash sign means to stip the leading zero


def get_meets():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    sql = 'SELECT meetNumber, location, opponent FROM tbl_meets ORDER BY meetNumber'
    #print(sql)
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    return rows


def get_meets_with_tasks():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    sql = "SELECT DISTINCT tbl_meets.date, tbl_meets.meetNumber, tbl_meets.location, tbl_meets.opponent FROM tbl_meets INNER JOIN tbl_tasks ON tbl_meets.meetNumber = tbl_tasks.meetNumber WHERE tbl_tasks.id not in (SELECT task_id from tbl_volunteers) AND tbl_tasks.disabled IS NULL ORDER BY tbl_meets.meetNumber"
    # print(sql)
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    meets_tasks_list = []
    if rows:
        for row in rows:
            meetdate = row['date']
            meetnumber = row['meetNumber']
            town = row['location']
            opponent = row['opponent']
            if not opponent:
                opponent = "Sac"
            if datetime.datetime.strptime(meetdate, '%m/%d/%Y') >= datetime.datetime.strptime(now, '%m/%d/%Y'):
                meets_tasks_list.append((meetnumber, str(opponent) + " @ " + str(town) + " - " + meetdate))
    return meets_tasks_list


def get_meets_in_future():
    """lets get meets that have available tasks and are still in the future, this is for the dropdownbox on the filled positions page."""
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    sql = 'SELECT meetNumber, location, date, opponent FROM tbl_meets ORDER BY meetNumber'
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    future_meets = []
    if rows:
        for row in rows:
            meetnumber = row['meetNumber']
            meetDate = row['date']
            town = row['location']
            opponent = row['opponent']
            if not opponent:
                opponent = "Sac"
            # convert our time strings to date objects, should have stored them in the db in the first place
            if datetime.datetime.strptime(meetDate, '%m/%d/%Y') >= datetime.datetime.strptime(now, '%m/%d/%Y'):
                # print(meetDate)
                future_meets.append((meetnumber, str(opponent),  meetDate, str(town)))
    return future_meets


def check_duplicate(meetnumber, email):
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    sql = 'SELECT email, meetNumber FROM tbl_volunteers WHERE meetNumber = ' + str(meetnumber) + ' AND email = "' + str(
        email) + '" '
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    if rows:
        flash('You already signed up for a job at this meet')
        return True


def get_city(meetnumber):
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    sql = 'SELECT location FROM tbl_meets WHERE meetNumber = ' + str(meetnumber) + ' '
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    for row in rows:
        town = row[0]
    return town


def get_map(meetnumber):
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    sql = 'SELECT address FROM tbl_meets WHERE meetNumber = ' + str(meetnumber) + ' '
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    address = ""
    for row in rows:
        address = row[0]
    return address


@app.route('/')
def index():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    meetnumber = request.args.get('aMeetNumber')
    number_of_meets = len(get_meets())
    available_meets = get_meets_with_tasks() # this is for the dropdown box
    if not meetnumber:
        meetnumber = 'All'
    if meetnumber == 'All':
        sql = "SELECT tbl_tasks.task, tbl_meets.opponent, tbl_tasks.description, tbl_tasks.id, tbl_tasks.meetNumber, tbl_volunteers.task_id, tbl_meets.date, tbl_meets.location, tbl_tasks.disabled FROM (tbl_tasks LEFT JOIN tbl_volunteers ON tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_tasks.meetNumber = tbl_meets.meetNumber WHERE (((tbl_volunteers.task_id) Is Null)) ORDER BY tbl_tasks.meetNumber"
    else:
        sql = "SELECT tbl_tasks.task, tbl_tasks.description, tbl_tasks.id, tbl_meets.opponent, tbl_tasks.meetNumber, tbl_volunteers.task_id, tbl_meets.date, tbl_meets.location, tbl_tasks.disabled FROM (tbl_tasks LEFT JOIN tbl_volunteers ON tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_tasks.meetNumber = tbl_meets.meetNumber WHERE (((tbl_volunteers.task_id) Is Null)) AND tbl_meets.meetNumber =" + meetnumber + " ORDER BY tbl_tasks.task"
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    #flash(sql)
    #flash("No practice on 6-15-22")
    return render_template("index.html", len=len(rows), rows=rows, available_meets=available_meets,  meetnumber=meetnumber, now=now)


@app.route('/top_times')
def toptimes():
    conn = sqlite3.connect(toptimesdatabase, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    meetdate = request.args.get('meetdate')
    # meetdate = '7/10/2019'
    sql = "SELECT * from tbl_swimmers WHERE meetdate = '" + meetdate + "' ORDER BY event, time"
    curs.execute(sql)
    rows = curs.fetchall()
    return render_template("toptimes.html", rows=rows, meetdate=meetdate)


@app.route('/signmeup')
def signmeup():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    myid = request.args.get('id')
    sql = "SELECT * FROM tbl_tasks where id =" + myid + ""
    curs.execute(sql)
    rows = curs.fetchall()
    for row in rows:
        mytask = row['task']
    conn.close()
    meet_number = request.args.get('aMeetNumber')
    location = request.args.get('location')
    if 'name' in session:
        name = session['name']
        email = session['email']
    else:
        name = ''
        email = ''
    return render_template("signmeup.html", name=name, email=email, id=myid, rows=rows, meet_number=meet_number,
                           location=location, mytask=mytask)


@app.route('/submitform')
def submitform():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    myid = request.args.get('aID')
    myname = request.args.get('aName')
    session['name'] = myname
    mynotes = request.args.get('aNotes')
    myemail = request.args.get('aEmail')
    session['email'] = myemail
    meetnumber = request.args.get('aMeetNumber')
    mytask = request.args.get('aTask')
    mydescription = request.args.get('aDescription')
    if not check_duplicate(meetnumber, myemail):  # check to see if the person already has a job, they cant do two.
        try:
            curs.execute("INSERT INTO tbl_volunteers (name, email, notes, task_id, meetNumber) VALUES (?,?,?,?,?)",
                         (myname, myemail, mynotes, myid, meetnumber))
            conn.commit()
            conn.close()
            html_email(myid, myemail, meetnumber, mytask, mydescription)
            logging.info(myemail + ' signed up for ' + mytask + ' at meet ' + meetnumber + '')
        except Exception as e:
            flash('The position has already been filled.')
            flash(str(e))
            conn.close()
            logging.warning(
                str(myemail) + ' tried to sign up for ' + str(mytask) + ' at meet ' + str(
                    meetnumber) + ', already filled')
    return render_template('success.html', email=myemail, meetnumber=meetnumber)


@app.route('/filledTasks')
def filledTasks():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    meetnumber = request.args.get('aMeetNumber')
    email = request.args.get('aEmail')
    sql = "SELECT tbl_tasks.task, tbl_tasks.description, tbl_tasks.id, tbl_tasks.meetNumber, tbl_meets.location, tbl_volunteers.name, tbl_volunteers.notes, tbl_meets.Date FROM (tbl_volunteers INNER JOIN tbl_tasks ON tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_volunteers.meetNumber = tbl_meets.meetNumber WHERE tbl_meets.date > " + str(
        now) + " ORDER BY tbl_volunteers.meetNumber;"
    # print(sql)
    if meetnumber:
        sql2 = "SELECT tbl_tasks.task, tbl_tasks.description, tbl_tasks.id, tbl_tasks.meetNumber, tbl_meets.location, \
        tbl_volunteers.name, tbl_volunteers.notes, tbl_meets.Date FROM (tbl_volunteers INNER JOIN tbl_tasks ON \
        tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_volunteers.meetNumber = tbl_meets.meetNumber \
        WHERE tbl_volunteers.meetNumber = " + meetnumber + " ORDER BY tbl_volunteers.meetNumber;"
        curs.execute(sql2)
    elif email:
        sql3 = "SELECT tbl_tasks.task, tbl_tasks.description, tbl_tasks.id, tbl_tasks.meetNumber, tbl_meets.location, \
        tbl_volunteers.name, tbl_volunteers.notes, tbl_volunteers.email, tbl_meets.Date FROM (tbl_volunteers INNER JOIN tbl_tasks ON \
        tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_volunteers.meetNumber = tbl_meets.meetNumber \
        WHERE tbl_volunteers.email = '" + email + "' ORDER BY tbl_volunteers.meetNumber;"
        curs.execute(sql3)
    else:
        curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    if request.args.get('admin'):
        admin = '1'
        session['admin'] = '1'
    if 'admin' in session:
        admin = '1'
    else:
        admin = '0'
    meet_list = get_meets_in_future()
    return render_template("filled_tasks.html", len=len(rows), meet_list=meet_list, rows=rows, admin=admin)


@app.route('/delete')
def delete():
    taskid = request.args.get('id')
    delete = request.args.get('delete')
    if delete == 'yes':
        conn = sqlite3.connect(database, check_same_thread=False)
        curs = conn.cursor()
        sql = "DELETE FROM tbl_volunteers where task_id = " + taskid + " "
        curs.execute(sql)
        conn.commit()
        conn.close()
        flash('Deleted')
        logging.warning(str(taskid) + ' was deleted')
        return redirect(url_for('index'))
    else:
        return render_template("delete.html", taskid=taskid)


@app.route('/records')
def records():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    meetnumber = request.args.get('aMeetNumber')
    sql = "SELECT * from tbl_records ORDER BY tbl_records.event"
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    return render_template("records.html", len=len(rows), rows=rows, meetnumber=meetnumber)


@app.route('/maps')
def maps():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    sql = "SELECT * from tbl_meets ORDER BY tbl_meets.meetNumber"
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    return render_template("maps.html", len=len(rows), rows=rows)


@app.route('/addtask')
def add_task():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    task = request.args.get('atask')
    meetnumber = request.args.get('ameetnumber')
    description = request.args.get('adescription')
    curs.execute("INSERT INTO tbl_tasks (task, description, meetNumber) VALUES (?,?,?)",
                 (task, description, meetnumber))
    conn.commit()
    rows = curs.fetchall()
    conn.close()
    if task and description and meetnumber:
        flash(task + description + meetnumber)
    return render_template("add_task.html")


def html_email(id, email_to, meetnumber, mytask, description):
    email_from = "Sac Swim Team <xxxx@xxxxx.us>"
    city = get_city(meetnumber)
    address = get_map(meetnumber)
    # email_to = 'xxx@xxx.com'
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Sac Swim Signup Reminder"
    msg['From'] = email_from
    msg['To'] = email_to
    text_version = 'You signed up for ' + mytask + ' at: ' + str(meetnumber) + ' in ' + str(city) + '\n' ''
    html_version = """\
    <html>
      <head></head>
      <body>
        <p>You signed up for """ + mytask + """ at meet: """ + str(meetnumber) + """ in <b>""" + str(city) + """</b></p>
        <p>""" + description + """</p>
        <p><a href="http://xxxxxx.xxxx/filledTasks?aEmail=""" + email_to + """\">View all the jobs I signed up for</a></p>
        <p><a href=\"""" + address + """\">Directions to pool</a></p>
      <p><a href="http://xxxxxxx.xxxx/delete?id=""" + id + """\">Delete Job</a></p>
      </body>
    </html>
    """
    part1 = MIMEText(text_version, 'plain')
    part2 = MIMEText(html_version, 'html')
    msg.attach(part1)
    msg.attach(part2)
    smtpserver = smtplib.SMTP("smtp.office365.com", 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    # smtpserver.login('xxxx@gomxxxxaco.com', 'xxxxxx')
    smtpserver.login('xxxx@xxxx.us', 'xxxxxx')
    smtpserver.sendmail(email_from, email_to, msg.as_string())
    # print(msg.as_string())
    smtpserver.quit()
    flash("Email sent")


if __name__ == '__main__':
    app.run(debug=True)
