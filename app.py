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
    PushMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    TextMessageContent,
)
import utilities
from health_data_manager import HealthDataManager
from chatgpt import ChatGPT

app = Flask(__name__)
line_credential = utilities.read_config('./configs/line-api-credential.json')
configuration = Configuration(access_token = line_credential['accessToken'])
handler = WebhookHandler(line_credential['channelSecret'])
health_manager = HealthDataManager("./configs/health-data-config.json")
chatgpt = ChatGPT("./configs/chatgpt-credential.json")

# https://goattl.tw/cshs/hackathon/health-data?uid=debug-user&hb=120&bo=99&bt=37.5
# 127.0.0.1:9002/health-data?uid=debug-user&hb=120&bo=98&bt=37.5
@app.route("/health-data", methods=["GET"])
def handle_health_data():
    vital_signs = health_manager.vital_signs_from_request(request.args)
    health_manager.insert_vital_signs(vital_signs)
    health_judge = health_manager.get_health_judge(vital_signs)
    if health_judge:
        user_id = vital_signs[0]
        if user_id == "debug-user": # 如果 user id 設定為 debug-user，就用測試ID覆蓋掉原本的ID
            user_id = line_credential["debugUid"]
        user = health_manager.get_user_info(user_id)
        hospital = health_manager.get_nearest_hospital(user_id)
        message = health_manager.get_emergency_message(health_judge, user, hospital)

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=message)]
                )
            )
    return 'OK'

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

        if message == "心跳":
            value = health_manager.get_vital_sign(user_id, message)
            reply_message = f"最後一次測量心跳: {value}"
        elif message == "血氧":
            value = health_manager.get_vital_sign(user_id, message)
            reply_message = f"最後一次測量心跳: {value}"
        elif message == "體溫":
            value = health_manager.get_vital_sign(user_id, message)
            reply_message = f"最後一次測量心跳: {value}"
        elif message == "debug":
            row = health_manager.get_vital_sign(user_id, "all")
            reply_message = str(row)
        else:
            reply_message = chatgpt.chat(message)

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_message)]
            )
        )

@handler.add(FollowEvent)
def handle_follow(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_id = event.source.user_id
        profile = line_bot_api.get_profile(user_id)
        health_manager.create_user(event.source.user_id, profile.display_name)

if __name__ == "__main__":
    app.run(port=9002)
