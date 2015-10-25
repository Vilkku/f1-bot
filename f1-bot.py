from collections import OrderedDict
from os import path

import datetime
import HTMLParser
import json
import mysql.connector
import OAuth2Util
import praw
import re

def main():
    # Read configuration files
    dir = path.dirname(__file__)

    config_data = open(path.join(dir, "config.json"), "r")
    config = json.load(config_data)
    config_data.close()

    sessions_data = open(path.join(dir, "schedule.json"), "r")
    sessions = json.load(sessions_data, object_pairs_hook=OrderedDict)
    sessions_data.close()

    # Reddit login
    r = praw.Reddit(config['reddit']['user_agent'])
    o = OAuth2Util.OAuth2Util(r)
    o.refresh(force=True)

    if (mysql in config):
        # Connect to MySQL database
        cnx = mysql.connector.connect(
            user=config['mysql']['username'].encode(),
            password=config['mysql']['password'].encode(),
            host=config['mysql']['host'].encode(),
            database=config['mysql']['database'].encode(),
            buffered=True,
            collation='utf8_swedish_ci',
            charset='utf8'
        )

        postScheduledPosts(cnx, r)

        # Close the MySQL connection
        cnx.close()

    # Update the sidebar
    h = HTMLParser.HTMLParser()
    current_sidebar = r.get_subreddit(config['reddit']['subreddit']).get_settings()["description"]
    current_sidebar = h.unescape(current_sidebar)
    new_sidebar = current_sidebar

    new_sidebar = setTag("countdown", getCountdownTime(sessions), new_sidebar)
    r.get_subreddit(config['reddit']['subreddit']).update_settings(description=new_sidebar)

# Take a sidebar, find [](/f1bot-keyword-s)<*>[](/f1bot-keyword-e), replace with
# [](/f1bot-keyword-s)<content>[](/f1bot-keyword-e), return updated sidebar
def setTag(keyword, content, sidebar):
    p = re.compile('\[\]\(\/f1bot-'+keyword+'-s\)(.*)\[\]\(\/f1bot-'+keyword+'-e\)', re.IGNORECASE)

    if p.search(sidebar):
        for match in p.finditer(sidebar):
            sidebar = sidebar.replace(match.group(0), '[](/f1bot-'+keyword+'-s)'+content+' [](/f1bot-'+keyword+'-e)')
    return sidebar

# Take session data, figure out what the next session is and return a formatted
# string saying how much time is left until that session begins. If the session
# is in progress, return a string stating that.
def getCountdownTime(sessions):
    lengths = {
        'Practice 1': 90,
        'Practice 2': 90,
        'Practice 3': 60,
        'Qualifying': 90,
        'Race': 120
    }
    for event in sessions['2015']:
        for (session, time) in event['times'].items():
            sessiontime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
            sessionlength = datetime.timedelta(0, lengths[session]*60)
            timeleft = sessiontime - datetime.datetime.now()

            # If the event time hasn't passed
            if timeleft > datetime.timedelta():
                d = datetime.datetime(1,1,1) + timeleft
                if (d.hour < 24):
                    return ("**%s**: %dH %dM" % (session, d.hour, d.minute))
                elif (d.day < 7):
                    return ("**%s**: %dD %dH" % (session, d.day-1, d.hour))
                elif (d.day < 30):
                    return ("**%s**: %dD" % (session, d.day-1))
                else:
                    return ("**%s**: %dM %dD" % (session, d.month-1, d.day-1))

            # If the event time has passed but the event isn't over
            if (timeleft + sessionlength) > datetime.timedelta():
                return "Live!"

    return ""

# Take a database connection and a reddit login, figure out if there are rows in the f1_bot table that have a
# scheduled time in the past and submit those posts to reddit according to the information in the table. If
# the logged in user has moderator powers, distinguish, add flair, sticky and post a comment.
def postScheduledPosts(cnx, reddit):
    # Search for rows where the difference between schedule and now is less than 3 hours
    cursor = cnx.cursor()
    updateCursor = cnx.cursor()
    fetch_query = ("SELECT id, subreddit, title, text, flair_text, flair_css FROM f1_bot WHERE (TIME_TO_SEC(TIMEDIFF(schedule, NOW())) < 300) AND (posted = 0)")
    update_query = ("UPDATE f1_bot SET posted=1 WHERE id=%(post_id)s")
    cursor.execute(fetch_query)

    if (cursor.rowcount > 0):
        for (post_id, subreddit, title, text, flair_text, flair_css) in cursor:
            s = reddit.submit(subreddit, title, text=text)
            updateCursor.execute(update_query, {'post_id': post_id})
            cnx.commit()

            moderators = reddit.get_subreddit(subreddit).get_moderators()
            if any(x for x in moderators if x.name == reddit.user.name):
                s.set_flair(flair_text=flair_text, flair_css_class=flair_css)
                s.distinguish()
                s.sticky()
                s.add_comment('Please post streams and stream requests as a reply to this comment.')

    cursor.close()
    updateCursor.close()

if __name__ == "__main__": main()
