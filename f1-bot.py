import praw
import mysql.connector
import re
import datetime
import json
from os import path

# Functions
def setTag(keyword, content, sidebar):
    p = re.compile('\[\]\(\/f1bot-'+keyword+'-s\)(.*)\[\]\(\/f1bot-'+keyword+'-e\)', re.IGNORECASE)

    if p.search(sidebar):
        for match in p.finditer(sidebar):
            sidebar = sidebar.replace(match.group(0), '[](/f1bot-'+keyword+'-s)'+content+' [](/f1bot-'+keyword+'-e)')
    return sidebar

def getCountdownTime():
    dir = path.dirname(__file__)
    sessions_data = open(path.join(dir, "schedule.json"), "r")
    sessions = json.load(sessions_data)
    sessions_data.close()
    lengths = {
        'Practice 1': 90,
        'Practice 2': 90,
        'Practice 3': 60,
        'Qualifying': 90,
        'Race': 120
    }
    for event in sessions['2014']:
        for (session, time) in event['times'].items():
            sessiontime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
            sessionlength = datetime.timedelta(0, lengths[session]*60)
            timeleft = sessiontime - datetime.datetime.now()

            # If the event time hasn't passed
            if timeleft > datetime.timedelta():
                d = datetime.datetime(1,1,1) + timeleft
                return ("**%s**: %dM %dD %dH %dM" % (session, d.month-1, d.day-1, d.hour, d.minute))
                #return ("**%s**: %dM %dD" % (session, d.month-1, d.day-1))

            # If the event time has passed but the event isn't over
            if (timeleft + sessionlength) > datetime.timedelta():
                return "Live!"

    return ""

# Read configuration file
dir = path.dirname(__file__)
config_data = open(path.join(dir, "config.json"), "r")
config = json.load(config_data)
config_data.close()

# Reddit login
r = praw.Reddit(config['reddit']['user_agent'])
r.login(config['reddit']['username'], config['reddit']['password'])

# Connect to MySQL database
cnx = mysql.connector.connect(
    user=config['mysql']['username'].encode(),
    password=config['mysql']['password'].encode(),
    host=config['mysql']['host'].encode(),
    database=config['mysql']['database'].encode(),
    buffered=True,
    collation='utf8_swedish_ci',
    charset='utf8')

# Search for rows where the difference between schedule and now is less than 3 hours
cursor = cnx.cursor()
updateCursor = cnx.cursor()
fetch_query = ("SELECT id, subreddit, title, text FROM f1_bot WHERE (TIME_TO_SEC(TIMEDIFF(schedule, NOW())) < 300) AND (posted = 0)")
update_query = ("UPDATE f1_bot SET posted=1 WHERE id=%(post_id)s")
cursor.execute(fetch_query)

if (cursor.rowcount > 0):
    for (id, subreddit, title, text) in cursor:
        s = r.submit(subreddit, title, text=text)
        s.set_flair(flair_css_class='star')
        s.distinguish()
        s.sticky()
        updateCursor.execute(update_query, { 'post_id': id })
        cnx.commit()

cursor.close()
updateCursor.close()

# Update the sidebar
current_sidebar = r.get_subreddit("formula1").get_settings()["description"]
new_sidebar = current_sidebar

new_sidebar = setTag("countdown", getCountdownTime(), new_sidebar)
r.get_subreddit("formula1").update_settings(description=new_sidebar)

# Close the MySQL connection
cnx.close()
