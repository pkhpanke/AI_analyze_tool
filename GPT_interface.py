from openai import OpenAI
import requests
from typing import Optional
import logging
import tiktoken
# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

models_list = [
    # ["gpt-3.5-turbo", 3096], #4096, save 1000 tokens for result
    # ["gpt-3.5-turbo-16k", 15000], #16000, save 1000 tokens for result
    ["gpt-4o",126000],
]

class GPTInterface:
    def __init__(self,key = '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',host= None):
        api_key=key
        # Openai.api_key = key
        # openai.proxy = 'http=127.0.0.1:9981'
        if host == 'closeai':
            api_base = 'https://api.openai-proxy.org/v1'
        else:
            pass

    def chat(self,model_name= None, system_prompt = None, user_prompt = None, assistant_prompt = None, temperature=1,max_output_tokens= 1024 ) -> str:
        try:
            if model_name is None:
                model_name = "gpt-4o"
            messages = []
            messages.append({
                    "role": "system",
                    "content":system_prompt}
                    )
            messages.append({"role": "user",
                            "content": user_prompt}
                            )
            
            api_key = "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"  # 替换为您的实际 API 密钥
            logging.info(f"使用的api_key为{api_key}")
            client = OpenAI(api_key=api_key)
            logging.info("开始chat")
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature = temperature,
                max_tokens=max_output_tokens,
                response_format={ "type": "json_object" }
            )
            # Add the model's response to the message history if you want to retain context for future analyses
            # self.messages.append({
            #     "role": "assistant",
            #     "content": response.choices[0].message['content']
            # })
            
            """
            {
                "choices": [
                    {
                    "finish_reason": "stop",
                    "index": 0,
                    "message": {
                        "content": "The 2020 World Series was played in Texas at Globe Life Field in Arlington.",
                        "role": "assistant"
                    }
                    }
                ],
                "created": 1677664795,
                "id": "chatcmpl-7QyqpwdfhqwajicIEznoc6Q47XAyW",
                "model": "gpt-3.5-turbo-0613",
                "object": "chat.completion",
                "usage": {
                    "completion_tokens": 17,
                    "prompt_tokens": 57,
                    "total_tokens": 74
                }
            }
            """

            # Returning the assistant's analysis
            return {"status":True, "message":"finished","data":response}
        except requests.exceptions.RequestException as e:
            # Handle network-related errors here
            logging.error(f"A network error occurred: {e}")
            return {"status":False, "message":e,"data":None}
        # except openai.OpenAIError as e:
        #     # Handle OpenAI API errors here
        #     logging.error(f"An OpenAI API error occurred: {e}")
        #     return {"status":False, "message":e,"data":None}
        except Exception as e:
            # Handle other possible errors
            logging.error(f"An error occurred: {e}")
            return {"status":False, "message":e,"data":None}

    def _get_suitable_model(self, text: str) -> str:
        token_count = self.count_token(text, "gpt-3.5-turbo")
        logging.info("token_count: ",token_count)
        for model, limit in models_list:
            if token_count <= limit:
                return model
        # raise ValueError("Text too long for available models.")
        return None
    
    def count_token(self, string: str, encoding_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens


