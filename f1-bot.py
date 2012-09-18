#!/home/users/vilkku/python/bin

import praw

username = "F1-Bot"
password = ""
subreddit = "formula1"

r = praw.Reddit(user_agent='F1-Bot (/u/F1-Bot) for /r/formula1 by /u/vilkku')

r.login(username, password)

f = open("testpost.txt")
text = f.read()
f.close()

title = "test title"

#s = r.submit(subreddit, title, text=text)
#s.set_flair(flair_css_class='star')
#s.distinguish()

settings = r.get_subreddit(subreddit).get_settings()
sidebar = settings["description"]

for item in sidebar.split("\n"):
    if "#####" in item:
        header = item
        break
        
print header

print "F1-Bot terminated."