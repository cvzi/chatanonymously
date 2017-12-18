# Only run the HTML bot for local testing

import os
from AnonymousBot import getMyBot_html

def homepage():
    return "Running", 200


myBot = getMyBot_html()

myBot.getFlask().route("/", methods=['GET'], endpoint="routeHomepage")(homepage)

myBot.run(port=80)

