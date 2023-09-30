import config
import datetime
from enum import Enum
from pathlib import Path
import re

import tiktoken
import yaml


ROOT_DIR = Path(__file__).resolve().parent.parent

METADATA_FILE_NAME_FORMAT = "{user_id}.yml"
COMPLETE_DATA_FILE_NAME_FORMAT = "{user_id}__{date}.yml"

REQUEST_SUMMARY_MESSAGE_FORMAT = \
    "You must start with 'Sorry, we need to make a summary of our conversation 😊.'. " \
    "Then summarize as follows:\n{summary_format}.\n" \
    "You must end with 'That's it. Is that right? Let't continue!'."
DEFAULT_SUMMARY_FORMAT = "Use bullet points."

TOKEN_LIMIT = {
    "text-davinci-003": 4097,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-3.5-turbo": 4096,
    "gpt-4": 8192
}

class UserKeywords(Enum):
    # TODO: Make a bot commands.
    UPDATE_FROM_FILE = "_UPDT"
    ADD_TO_SYSTEM_MESSAGES = "_SM"
    ADD_TO_IMPORTANT_MESSAGES = "_IM"


class DialogKeeper:
    def __init__(self, user_id):
        self._is_new_dialog_set = False
        self._last_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self._enable_keywords = True \
            if config.long_dialog_config.enable and config.long_dialog_config.enable_keywords else False

        # Metadata
        self._user_id = user_id
        self._model = None
        self._encoding = None
        self._chat_mode = None

        self._temperature = 0.7
        self._top_p = 1
        self._max_tokens = 1000
        self._frequency_penalty = 0
        self._presence_penalty = 0

        self._system_messages = []  # [prompts (opt.), prev (opt.), ...]
        self._system_message_n_tokens = 0
        self._is_prompt_set = None
        self._is_prev_set = None

        self._important_messages = []
        self._important_messages_n_tokens = 0

        self._request_summary_message = None
        self._request_summary_message_n_tokens = 0
        self._n_tokens_since_summary_request = 0

        # Long dialog
        self._long_dialog_token_limit = None
        self._long_dialog_update_summary_n_tokens = None

        # Save metadata to file
        # TODO: Add Redis option.
        self._metadata_file_path = \
            Path(config.long_dialog_config.files_dir) / Path(METADATA_FILE_NAME_FORMAT.format(
                user_id=user_id)) if config.long_dialog_config.enable and config.long_dialog_config.save_to_file else None
        self._last_metadata_save_datetime = None

        # Save complete data to file
        self._complete_data_file_path = \
            Path(config.long_dialog_config.files_dir) / Path(COMPLETE_DATA_FILE_NAME_FORMAT.format(
                user_id=user_id, date=self._last_date)) if config.long_dialog_config.enable and config.long_dialog_config.save_all_to_file else None
        self._last_complete_data_save_datetime = None
        self._unsaved_dialog = []

    @property
    def is_new_dialog_set(self):
        return self._is_new_dialog_set

    def _add_system_message(self, message):
        self._system_messages.append({"role": "system", "content": message})
        self._system_message_n_tokens += len(self._encoding.encode(message))
        if (
            self._system_message_n_tokens + self._important_messages_n_tokens
            > config.long_dialog_config.system_and_important_max_tokens * TOKEN_LIMIT[self._model]
        ):
            # TODO: Tell user, summarize or remove the oldest ones.
            raise NotImplementedError("Handling too many system messages is not implemented yet. "
                                      "Start a new dialog or modify system messages manually (knowledge/long_dialogs/user_id.yml) .")

    def _add_important_message(self, message):
        self._important_messages.append({"role": "user", "content": message})
        self._important_messages_n_tokens += len(self._encoding.encode(message))
        if (
            self._system_message_n_tokens + self._important_messages_n_tokens
            > config.long_dialog_config.system_and_important_max_tokens * TOKEN_LIMIT[self._model]
        ):
            # TODO: Tell user, summarize or remove the oldest ones.
            raise NotImplementedError("Handling too many important messages is not implemented yet. "
                                      "Start a new dialog or modify important messages manually (knowledge/long_dialogs/user_id.yml) and write UPDT.")

    def _set_request_summary_message(self, message):
        self._request_summary_message = message
        self._request_summary_message_n_tokens = len(self._encoding.encode(self._request_summary_message))
        # TODO: Check if too many tokens

    def __str__(self):
        return (
            f"user_id: {self._user_id}\n"
            f"model: {self._model}\n"
            f"chat_mode: {self._chat_mode}\n\n"
            f"temperature: {self._temperature}\n"
            f"top_p: {self._top_p}\n"
            f"max_tokens: {self._max_tokens}\n"
            f"frequency_penalty: {self._frequency_penalty}\n"
            f"presence_penalty: {self._presence_penalty}\n\n"
            f"system_messages: {self._system_messages}\n"
            f"important_messages: {self._important_messages}\n"
            f"request_summary_message: {self._request_summary_message}"
        )

    def _update_from_file(self):
        with open(self._metadata_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)

            if yaml_data["user_id"] != self._user_id:
                raise ValueError("Cannot modify user id from file.")
            if yaml_data["model"] != self._model:
                raise ValueError("Cannot modify model from file.")
            if yaml_data["chat_mode"] != self._chat_mode:
                raise ValueError("Cannot modify chat mode from file.")

            self._temperature = yaml_data["temperature"]
            self._top_p = yaml_data["top_p"]
            self._max_tokens = yaml_data["max_tokens"]
            self._frequency_penalty = yaml_data["frequency_penalty"]
            self._presence_penalty = yaml_data["presence_penalty"]

            self._system_messages = []
            for message in yaml_data["system_messages"]:
                self._add_system_message(message)
            self._important_messages = []
            for message in yaml_data["important_messages"]:
                self._add_important_message(message)
            self._set_request_summary_message(yaml_data["request_summary_message"])

    def _save_to_file(self):
        now_time = datetime.datetime.now()
        if (
            self._last_metadata_save_datetime is None or
            (now_time - self._last_metadata_save_datetime).total_seconds() > config.long_dialog_config.save_timeout_min * 60
        ):
            with open(self._metadata_file_path, 'w') as yaml_file:
                yaml.dump({
                    "user_id": self._user_id,
                    "model": self._model,
                    "chat_mode": self._chat_mode,
                    "temperature": self._temperature,
                    "top_p": self._top_p,
                    "max_tokens": self._max_tokens,
                    "frequency_penalty": self._frequency_penalty,
                    "presence_penalty": self._presence_penalty,
                    "system_messages": [message["content"] for message in self._system_messages],
                    "important_messages": [message["content"] for message in self._important_messages],
                    "request_summary_message": self._request_summary_message
                }, yaml_file, default_flow_style=False, sort_keys=False)
            self._last_metadata_save_datetime = now_time

        if (
            self._unsaved_dialog and(self._last_complete_data_save_datetime is None or
            (now_time - self._last_complete_data_save_datetime).total_seconds() > config.long_dialog_config.save_all_timeout_min * 60)
        ):
            dialog = []
            if self._complete_data_file_path.is_file():
                with open(self._complete_data_file_path, 'r') as yaml_file:
                    dialog = yaml.safe_load(yaml_file)["dialog"]

            dialog += self._unsaved_dialog
            with open(self._complete_data_file_path, 'w') as yaml_file:
                yaml.dump({"dialog": dialog}, yaml_file, default_flow_style=False, sort_keys=False)

            self._unsaved_dialog = []
            self._last_complete_data_save_datetime = now_time

    def _update_date(self):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if today == self._last_date:
            return
        self._last_date = today
        self._complete_data_file_path = \
            Path(config.long_dialog_config.files_dir) / Path(COMPLETE_DATA_FILE_NAME_FORMAT.format(
                user_id=self._user_id, date=self._last_date)) if self._complete_data_file_path is not None else None

    def _set_model(self, model):
        self._model = model
        self._encoding = tiktoken.encoding_for_model(model)

        # Long dialog
        self._long_dialog_token_limit = TOKEN_LIMIT[self._model] - self._max_tokens
        self._long_dialog_update_summary_n_tokens = self._long_dialog_token_limit * config.long_dialog_config.update_summary_when_tokens_reach

        # Recount tokens
        if not self._is_new_dialog_set:
            return

        self._system_message_n_tokens = 0
        for message in self._system_messages:
            self._system_message_n_tokens += len(self._encoding.encode(message))
        self._important_messages_n_tokens = 0
        for message in self._important_messages:
            self._important_messages_n_tokens += len(self._encoding.encode(message))
        self._request_summary_message_n_tokens = len(self._encoding.encode(self._request_summary_message))

    def _set_new_dialog(self, prompt, prev, summary_format):
        self._update_date()

        if prompt is None:
            self._is_prompt_set = False
        else:
            self._is_prompt_set = True
            self._add_system_message(prompt)  # TODO: What's better: one or many system messages?
        if prev is None:
            self._is_prev_set = False
        else:
            self._is_prev_set = True
            self._add_system_message(prev)

        summary_format =  summary_format if summary_format is not None else DEFAULT_SUMMARY_FORMAT
        self._set_request_summary_message(REQUEST_SUMMARY_MESSAGE_FORMAT.format(summary_format=summary_format))

        self._is_new_dialog_set = True

    def _clear(self):
        self._temperature = 0.7
        self._top_p = 1
        self._max_tokens = 1000
        self._frequency_penalty = 0
        self._presence_penalty = 0

        self._system_messages = []
        self._system_message_n_tokens = 0
        self._is_prompt_set = None
        self._is_prev_set = None

        self._important_messages = []
        self._important_messages_n_tokens = 0

        self._request_summary_message = ""
        self._request_summary_message_n_tokens = 0
        self._n_tokens_since_summary_request = 0

    def _collect_long_dialog(self, message, dialog_messages):
        # Uses summarization method
        # Returns messages for API and a value: True when user message is used, False when user message is replaced

        # summary request
        is_user_message_used = True
        self._n_tokens_since_summary_request += dialog_messages[-1]["n_tokens"] if dialog_messages else 0
        if self._n_tokens_since_summary_request >= self._long_dialog_update_summary_n_tokens:
            self._n_tokens_since_summary_request = 0
            is_user_message_used = False  # TODO: Add the current summary to system message

        # trimmed dialog
        message_n_tokens = len(self._encoding.encode(message))
        n_tokens = self._system_message_n_tokens + self._important_messages_n_tokens
        messages = []
        for dm_i in range(len(dialog_messages) - 1, 0, -1):
            dialog_message = dialog_messages[dm_i]
            if (
                is_user_message_used
                and (n_tokens + dialog_message["n_tokens"] + message_n_tokens >= self._long_dialog_token_limit)
                or not is_user_message_used
                and (n_tokens + dialog_message["n_tokens"] + self._request_summary_message_n_tokens >= self._long_dialog_token_limit)
            ):
                break

            # reversed order
            messages.append({"role": "assistant", "content": dialog_message["bot"]})
            messages.append({"role": "user", "content": dialog_message["user"]})
            n_tokens += dialog_message["n_tokens"]

        messages.extend(self._important_messages)
        messages.extend(self._system_messages)
        messages.reverse()
        if is_user_message_used:
            messages.append({"role": "user", "content": message})
        else:
            messages.append({"role": "user", "content": self._request_summary_message})
        return messages, is_user_message_used

    def _collect_dialog(self, message, dialog_messages):
        # Returns messages for API and a value: True when user message is used, False when user message is replaced

        if not self._is_new_dialog_set:
            self._set_new_dialog(*parse_custom_settings(message))
            return self._system_messages + [
                {"role": "user", "content": "Tell me who you are. Write a very short hello message."}], True

        if not config.long_dialog_config.enable:
            messages = self._system_messages + self._important_messages
            for dialog_message in dialog_messages:
                messages.append({"role": "user", "content": dialog_message["user"]})
                messages.append({"role": "assistant", "content": dialog_message["bot"]})
            messages.append({"role": "user", "content": message})
            return message, True

        return self._collect_long_dialog(message, dialog_messages)

    def _get_openai_completion_options(self):
        return {
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "top_p": self._top_p,
            "frequency_penalty": self._frequency_penalty,
            "presence_penalty": self._presence_penalty,
        }

    def start_new_dialog(self, model, chat_mode):
        self._clear()
        self._update_date()
        self._set_model(model)
        self._chat_mode = chat_mode

    def generate_api_options(self, message, dialog_messages):
        self._update_date()
        keywords = parse_keywords(message) if self._enable_keywords else None
        if keywords is not None and UserKeywords.ADD_TO_SYSTEM_MESSAGES in keywords and UserKeywords.ADD_TO_IMPORTANT_MESSAGES in keywords:
            raise ValueError("Cannot add to both system and important messages.")
        if keywords is not None and UserKeywords.UPDATE_FROM_FILE in keywords:
            self._update_from_file()
        if self._complete_data_file_path is not None and dialog_messages:
            self._unsaved_dialog.append(dialog_messages[-1])

        messages, is_user_message_used = self._collect_dialog(message, dialog_messages)
        if is_user_message_used and keywords is not None:
            if UserKeywords.ADD_TO_SYSTEM_MESSAGES in keywords:
                self._add_system_message(message)
            elif UserKeywords.ADD_TO_IMPORTANT_MESSAGES in keywords:
                self._add_important_message(message)

        openai_completion_options = self._get_openai_completion_options()
        self._save_to_file()

        return messages, openai_completion_options

def parse_keywords(message):
    keywords = set()
    for keyword in UserKeywords:
        if re.search(re.escape(keyword.value), message):
            keywords.add(keyword)
    return keywords

def parse_custom_settings(message):
    prompt_pattern = r'PROMPT:\s*([\s\S]*?)(?:PREV:|SUMMARY_FORMAT:|$)'
    prev_pattern = r'PREV:\s*([\s\S]*?)(?:SUMMARY_FORMAT:|$)'
    summary_format_pattern = r'SUMMARY_FORMAT:\s*([\s\S]*)$'

    prompt_match = re.search(prompt_pattern, message)
    prev_match = re.search(prev_pattern, message)
    summary_format_match = re.search(summary_format_pattern, message)

    return (prompt_match.group(1).strip() if prompt_match else None,
            prev_match.group(1).strip() if prev_match else None,
            summary_format_match.group(1).strip() if summary_format_match else None)
