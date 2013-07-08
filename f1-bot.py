import praw
import mysql.connector
import re
import datetime

# Functions

def setTag(keyword, content, sidebar):
    p = re.compile('\[\]\(\/f1bot-'+keyword+'-s\)(.*)\[\]\(\/f1bot-'+keyword+'-e\)', re.IGNORECASE)
       
    if p.search(sidebar):
        for match in p.finditer(sidebar):
            sidebar = sidebar.replace(match.group(0), '[](/f1bot-'+keyword+'-s)'+content+' [](/f1bot-'+keyword+'-e)')
    return sidebar
    
def getCountdownTime():
    sessions = ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race', 'Hungary Practice 1']
    times = ['2013-07-05 11:00', '2013-07-05 15:00', '2013-07-06 12:00', '2013-07-06 15:00', '2013-07-07 15:00', '2013-07-26 11:00']
    lengths = [90, 90, 60, 90, 120, 90]
    i = 0
    for session in sessions:
        sessiontime = datetime.datetime.strptime(times[i], '%Y-%m-%d %H:%M')
        sessionlength = datetime.timedelta(0, lengths[i]*60)
        timeleft = sessiontime - datetime.datetime.now()
        
        # If the event time hasn't passed
        if timeleft > datetime.timedelta():
            d = datetime.datetime(1,1,1) + timeleft
            return ("**%s**: %dD %dH %dM" % (session, d.day-1, d.hour, d.minute))
            
        # If the event time has passed but the event isn't over
        if (timeleft + sessionlength) > datetime.timedelta():
            return "Live!"
            
        i += 1

# Reddit login

username = "" #There should probably be accepted as arguments to the script instead
password = ""
r = praw.Reddit(user_agent='F1-Bot (/u/F1-Bot) for /r/formula1 by /u/vilkku')
r.login(username, password)

# Connect to MySQL database

cnx = mysql.connector.connect(user='', password='', host='', database='', buffered=True)

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
        updateCursor.execute(update_query, { 'post_id': id })

cursor.close()
updateCursor.close()

# Update the sidebar

current_sidebar = r.get_subreddit("formula1").get_settings()["description"]
new_sidebar = current_sidebar
    
new_sidebar = setTag("countdown", getCountdownTime(), new_sidebar)
r.get_subreddit("formula1").update_settings(description=new_sidebar)

# Close the MySQL connection

cnx.close()
