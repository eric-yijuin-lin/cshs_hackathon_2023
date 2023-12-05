from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
import json

def read_config(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as fs:
            return json.load(fs) # channelSecret & accessToken
    except FileNotFoundError:
        print('failed to load credential')
        quit("the LINE bot API is terminated")

app = Flask(__name__)
line_credential = read_config('./line-api-credential.json')
configuration = Configuration(access_token = line_credential['accessToken'])
handler = WebhookHandler(line_credential['channelSecret'])


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_id = event.source.user_id
        message = event.message.text
        reply_message = ""

        if message == "笑話":
            reply_message = "隨機挑選一則笑話"
        elif message == "閒聊":
            reply_message = "串接 ChatGPT API"

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_message)]
            )
        )


if __name__ == "__main__":
    app.run(port=9002)
