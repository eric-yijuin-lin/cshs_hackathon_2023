from openai import OpenAI
import utilities

class ChatGPT:
    def __init__(self, config_file: str) -> None:
        self.config = utilities.read_config(config_file)
        self.client = OpenAI(api_key=self.config["apiKey"])


    def chat(self, message: str) -> str:
        reply = ""
        try:
            stream = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "user", "content": message},
                    {"role": "system", "content": "reply in either Traditional Chinese or English"}
                ],
                temperature = self.config["temperature"],
                stream=True,
            )
            reply = "".join([chunk.choices[0].delta.content
                             for chunk in stream
                             if chunk.choices[0].delta.content is not None])
        except Exception as ex:
            reply = f"ChatGPT 發生錯誤\n({ex})"
        return reply
