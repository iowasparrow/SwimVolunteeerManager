
from flask import Flask
from flask import render_template, flash, request, redirect, url_for
import sqlite3
import smtplib
import logging




app = Flask(__name__)
app.secret_key = b'sdfg'
database = '/var/www/html/signup/signup.db'

logging.basicConfig(filename='/var/www/html/signup/demo.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    meetnumber = request.args.get('aMeetNumber')
    if not meetnumber:
        meetnumber = 'All'
    if meetnumber == 'All':
        sql = "SELECT tbl_tasks.task, tbl_meets.opponent, tbl_tasks.description, tbl_tasks.id, tbl_tasks.meetNumber, tbl_volunteers.task_id, tbl_meets.date, tbl_meets.location FROM (tbl_tasks LEFT JOIN tbl_volunteers ON tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_tasks.meetNumber = tbl_meets.meetNumber WHERE (((tbl_volunteers.task_id) Is Null)) ORDER BY tbl_tasks.meetNumber"
    else:
        sql = "SELECT tbl_tasks.task, tbl_tasks.description, tbl_tasks.id, tbl_meets.opponent, tbl_tasks.meetNumber, tbl_volunteers.task_id, tbl_meets.date, tbl_meets.location FROM (tbl_tasks LEFT JOIN tbl_volunteers ON tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_tasks.meetNumber = tbl_meets.meetNumber WHERE (((tbl_volunteers.task_id) Is Null)) AND tbl_meets.meetNumber =" + meetnumber +" ORDER BY tbl_tasks.task"
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    return render_template("index.html", len=len(rows), rows=rows, meetnumber=meetnumber)


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
    meetNumber = request.args.get('aMeetNumber')
    location = request.args.get('location')
    return render_template("signmeup.html", id=myid, rows=rows, meetNumber=meetNumber, location=location, mytask=mytask)


@app.route('/submitform')
def submitform():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    myid = request.args.get('aID')
    myname = request.args.get('aName')
    mynotes = request.args.get('aNotes')
    myemail = request.args.get('aEmail')
    meetnumber = request.args.get('aMeetNumber')
    mytask = request.args.get('aTask')
    mydescription = request.args.get('aDescription')
    try:
        curs.execute("INSERT INTO tbl_volunteers (name, email, notes, task_id, meetNumber) VALUES (?,?,?,?,?)", (myname, myemail, mynotes, myid, meetnumber))
        conn.commit()
        conn.close()
        email(myid, myemail, meetnumber, mytask, mydescription)
        logging.info(myemail + ' signed up for ' + mytask + ' at meet ' + meetnumber + '')
    except Exception as e:
        flash('The position has already been filled.')
        flash(str(e))
        conn.close()
        logging.warning(str(myemail) + ' tried to sign up for ' + str(mytask) + ' at meet ' + str(meetnumber) + ', already filled')
    return render_template('success.html', email=myemail)


@app.route('/viewSchedule')
def viewSchedule():
    sql = "SELECT tbl_tasks.name, tbl_tasks.task, tbl_tasks.meetNumber FROM tbl_tasks INNER JOIN tbl_meets ON tbl_tasks.meetNumber=tbl_meets.meetNumber"
    sql_filled_taskes_with_name = "SELECT tbl_volunteers.name, tbl_volunteers.task_id, tbl_volunteers.meetNumber, tbl_tasks.task FROM tbl_volunteers INNER JOIN tbl_tasks ON tbl_tasks.id=tbl_volunteers.task_id"
    sql_available_jobs = "SELECT tbl_tasks.task, tbl_tasks.id, tbl_tasks.meetNumber FROM tbl_tasks WHERE tbl_tasks.id NOT IN (SELECT tbl_volunteers.task_id FROM tbl_volunteers) "


@app.route('/filledTasks')
def filledTasks():
    conn = sqlite3.connect(database, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    meetnumber = request.args.get('aMeetNumber')
    sql = "SELECT tbl_tasks.task, tbl_tasks.description, tbl_tasks.id, tbl_tasks.meetNumber, tbl_meets.location, tbl_volunteers.name, tbl_volunteers.notes, tbl_meets.Date FROM (tbl_volunteers INNER JOIN tbl_tasks ON tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_volunteers.meetNumber = tbl_meets.meetNumber;"
    if meetnumber:
        sql2 = "SELECT tbl_tasks.task, tbl_tasks.description, tbl_tasks.id, tbl_tasks.meetNumber, tbl_meets.location, tbl_volunteers.name, tbl_volunteers.notes, tbl_meets.Date FROM (tbl_volunteers INNER JOIN tbl_tasks ON tbl_volunteers.task_id = tbl_tasks.id) INNER JOIN tbl_meets ON tbl_volunteers.meetNumber = tbl_meets.meetNumber WHERE tbl_volunteers.meetNumber = "+ meetnumber  +";"    	
        curs.execute(sql2)
    else:
        curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    admin = request.args.get('admin')
    return render_template("filled_tasks.html", len=len(rows), rows=rows, admin=admin)


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


def email(id_to_delete, email_to, meetnumber, mytask, mydescription):
    email_from = 'sdfgsdfg'
    header = 'To:' + email_to + '\n' + 'From: Sac Swim Team <' + email_from + '>\n' + 'Subject:Sac Swim Signup \n'
    msg_body = 'You signed up for ' + mytask + ' at  meet: ' + meetnumber + '\n' + mydescription + '\n'
    delete_message = '\n' + 'The link to delete this entry is \n' + 'http://fdsgdfsg/signup/delete?id=' + id_to_delete + '\n'
    email_msg = header + '\n' + msg_body + '\n' + delete_message + '\n\n'
    smtpserver = smtplib.SMTP("smtp.office365.com", 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    #smtpserver.login('sdfgsdfg', sdfg
    smtpserver.login('sdfg', sdfg
    email_msg_fixed = email_msg.encode('ascii', 'ignore')
    smtpserver.sendmail(email_from, email_to, email_msg_fixed)
    print(email_msg)
    smtpserver.quit()
    flash("Email sent")
    return render_template('success.html', email_msg=email_msg)



if __name__ == '__main__':
    app.run(debug = False)
