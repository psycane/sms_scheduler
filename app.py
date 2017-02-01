from flask import Flask, render_template, request, make_response, session
from twilio.rest import TwilioRestClient
from apscheduler.schedulers.background import BackgroundScheduler
import MySQLdb
import json
import logging
from tzlocal import get_localzone
import datetime

app = Flask(__name__)
app.secret_key = "\xc2S\xbdE%u\x9cP2Z\xa8ZrsY\xe2\x99\x95\xa6\xe5\xc3\xd0\xe9\x83"

# Database Setup
cnx = {'host': '0.0.0.0',
       'username': 'root',
       'password': 'root',
       'db': 'sms_scheduler'}

conn = MySQLdb.connect(cnx['host'], cnx['username'],
                       cnx['password'], cnx['db'])
cur = conn.cursor()

# Twilio Setup
account_sid = "ACaf850d688e921bf94696618718c8d0c8"
auth_token = "9bda7ec24ecd04438370b804d219398b"
client = TwilioRestClient(account_sid, auth_token)

# Scheduler Setup
logging.basicConfig(filename='logs.log', level=logging.DEBUG)
scheduler = BackgroundScheduler()
scheduler.start()


def send_sms(phone_no, max_retries, retry_count=0):
    try:
        if max_retries == retry_count:
            pass
        else:
            message = client.messages.create(
                to=phone_no, from_="+12015598658 ", body="Hey Buddy! Just in case you forgot, your name is John!")
    except Exception as e:
        logging.exception("message")
        send_sms(phone_no, max_retries, retry_count + 1)


@app.route('/')
def home():
    time = session.get('time')
    sql = "SELECT * FROM details ORDER BY ID DESC LIMIT 1"
    cur.execute(sql)
    details = cur.fetchone()
    phone_no = "+{0}{1}".format(details[2],
                                details[1].strip()) if details else details
    if time:
        date_obj = datetime.datetime.strptime(
            time[:-15], '%a %b %d %Y %H:%M:%S')
        date = {"year": date_obj.year,
                "month": date_obj.month - 1,
                "day": date_obj.day,
                "hour": date_obj.hour,
                "minute": date_obj.minute,
                "second": date_obj.second}
        return render_template("home.html", date_data=date, phone_no=phone_no)
    else:
        try:
            scheduler.remove_job("sending_sms", jobstore=None)
        except:
            pass
        return render_template("home.html", date_data={}, phone_no=phone_no)


@app.route('/update_info', methods=["GET", "POST"])
def update_info():
    try:
        dic = request.get_json(force=True)
        phone_no = dic["phone_no"].strip()
        country_code = dic["country"]
        if len(phone_no) == 10:
            sql = 'INSERT INTO details VALUES (NULL,{0},{1})'.format(
                phone_no, country_code)
            cur.execute(sql)
            conn.commit()
            if scheduler.get_jobs():
                phone_no = "+{0}{1}".format(country_code, phone_no)
                scheduler.modify_job("sending_sms", args=[phone_no, 5])
            return json.dumps({"message": "Phone No Updated Successfully!"})
        else:
            return json.dumps({"message": "Phone Number Is Not Correct!"})
    except:
        return json.dumps({"message": "Something Went Wrong!"})


@app.route('/start_service', methods=["GET", "POST"])
def start_service():
    try:
        if session.get("time"):
            return json.dumps({"message": "Service Already Running!"})
        else:
            dic = request.get_json(force=True)
            time = dic["date"]
            sql = "SELECT * FROM details ORDER BY ID DESC LIMIT 1"
            cur.execute(sql)
            details = cur.fetchone()
            if details:
                if len(details[1].strip()) == 10:
                    phone_no = "+{0}{1}".format(details[2], details[1].strip())
                    try:
                        job = scheduler.add_job(send_sms, trigger='cron', args=[
                                                phone_no, 5], hour="8-22", id="sending_sms", timezone=get_localzone())
                        session["time"] = time
                        return json.dumps({"message": "Service Started Successfully!"})
                    except:
                        return json.dumps({"message": "Service Already Running!"})
                else:
                    return json.dumps({"message": "Phone Number Is Not Correct!"})
            else:
                return json.dumps({"message": "Please Update Your Phone Number!"})
    except:
        return json.dumps({"message": "Something Went Wrong!"})


@app.route('/stop_service', methods=["GET", "POST"])
def stop_service():
    try:
        session.pop('time', None)
        scheduler.remove_job("sending_sms", jobstore=None)
        return json.dumps({"message": "Service Stopped Successfully!"})
    except:
        return json.dumps({"message": "No Service Running!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
