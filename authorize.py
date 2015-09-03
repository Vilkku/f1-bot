import json
import praw
from os import path

# Read configuration file
dir = path.dirname(__file__)
config_data = open(path.join(dir, "config.json"), "r")
config = json.load(config_data)
config_data.close()

r = praw.Reddit(config['reddit']['user_agent'])
r.set_oauth_app_info(client_id=config['reddit']['client_id'], client_secret=config['reddit']['client_secret'], redirect_uri=config['reddit']['redirect_uri'])

url = r.get_authorize_url('f1bot', ['edit', 'flair', 'identity', 'modconfig', 'modflair', 'modposts', 'modwiki', 'submit', 'wikiedit', 'wikiread'], True)

print url
