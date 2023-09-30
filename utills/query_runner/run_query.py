import asyncio
import openai
import yaml


MODEL = "gpt-4" # "gpt-3.5-turbo-16k", "gpt-4"
OPENAI_COMPLETION_DEFAULT_OPTIONS = {
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "request_timeout": 120
}
OPENAI_KEY = ""


def main():
    data = None
    with open("input.yml", "r") as file:
        data = yaml.safe_load(file)
    if data is None:
        print('Error openning input.yml.')
        messages = []
    else:
        messages = [{"role": "system", "content": message["system"]} if "system" in message
                    else {"role": "user", "content": message["user"]} if "user" in message
                    else {"role": "assistant", "content": message["assistant"]} for message in data.get("messages")]

    openai.api_key = OPENAI_KEY
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        **OPENAI_COMPLETION_DEFAULT_OPTIONS
    )

    output_data = {
        "model": MODEL,
        "token_usage": response["usage"]["total_tokens"], # response.usage["total_tokens"],
        "choices": [choice["message"]["content"] for choice in response["choices"]]
    }

    with open("output.yml", "w") as output_file:
        yaml.dump(output_data, output_file, default_flow_style=False)

    print('Done!')


if __name__ == '__main__':
    main()
