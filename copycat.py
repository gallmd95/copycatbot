from slackclient import SlackClient
import os
from bottle import Bottle, request, run

app = Bottle()

BOT_NAME = 'copycatbot'

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
oauth_scope = os.environ["SLACK_BOT_SCOPE"]

@app.route("/begin_auth", methods=["GET"])
def pre_install():
  return '''
      <a href="https://slack.com/oauth/authorize?scope={0}&client_id={1}">
          Add to Slack
      </a>
  '''.format(oauth_scope, client_id)

@app.route("/finish_auth", methods=["GET", "POST"])
def post_install():
    # Retrieve the auth code from the request params
    auth_code = request.query['code']
    # An empty string is a valid token for this request
    sc = SlackClient("")
    # Request the auth tokens from Slack
    auth_response = sc.api_call(
        "oauth.access",
        client_id=client_id,
        client_secret=client_secret,
        code=auth_code
    )
    os.environ["SLACK_USER_TOKEN"] = auth_response['access_token']
    os.environ["SLACK_BOT_TOKEN"] = auth_response['bot']['bot_access_token']
    # Don't forget to let the user know that auth has succeeded!
    return "OAuth Successful!"

@app.route("/channels", methods=["GET", "POST"])
def get_channels():
    usc = SlackClient(os.environ["SLACK_USER_TOKEN"])
    bsc = SlackClient(os.environ["SLACK_BOT_TOKEN"])
    channels_slack = usc.api_call("channels.list")
    users_slack = usc.api_call("users.list")
    messages = {}
    names = {}
    bots = {}
    for bot in users_slack["members"]:
        if bot["is_bot"] == True:
            bots[bot["profile"]["bot_id"]] = bot["name"]
    for member in users_slack["members"]:
        names[member["id"]] = member["name"]
    for channel in channels_slack["channels"]:
        channel_name = channel["id"]+" "+channel["name"]
        messages[channel_name] = []
        history = usc.api_call("channels.history",channel=channel["id"])
        for message in history["messages"]:
            if "subtype" in message:
                if message["subtype"] == "bot_message":
                    if message["bot_id"] in bots:
                        messages[channel_name].append({ message["ts"]: {bots[message["bot_id"]] : message["text"]}})
            else:
                messages[channel_name].append({ message["ts"] : {names[message["user"]] : message["text"]}})
    return messages
        
def main():
    run(app,host='localhost', port=8081)

if __name__ == "__main__":
    main()