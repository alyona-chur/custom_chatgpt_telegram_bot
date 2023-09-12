import tiktoken

SUMMARY_MESSAGE_INTRO = "Say 'Sorry, we need to make a summary'."
DEFAULT_SUMMARY_FORMAT = "Use bullet points."


class UserState:
    def __init__(self, user_id: int):
        self._user_id = user_id

        self._prompt = None
        self._prev = None
        self._summary_format = None

        self._system_message = None
        self._system_message_n_tokens = 0
        self._summary_message = None
        self._summary_message_n_tokens = 0

    @property
    def system_message(self):
        return self._system_message

    @property
    def system_message_n_tokens(self):
        return self._system_message_n_tokens

    @property
    def summary_message(self):
        return self._summary_message

    @property
    def summary_message_n_tokens(self):
        return self._summary_message_n_tokens

    def _set_model(self, model):
        if self._system_message is None:
            return

        encoding = tiktoken.encoding_for_model(model)
        self._system_message_n_tokens = len(encoding.encode(self._system_message))
        self._summary_message_n_tokens = len(encoding.encode(self._summary_format))

    def set(self, prompt, prev, summary_format, model):
        self._prompt = prompt if prompt is not None else ""
        self._prev = prev if prev is not None else ""
        self._summary_format =  summary_format if summary_format is not None else DEFAULT_SUMMARY_FORMAT

        if prev is not None:
            self._system_message = "/n".join([self._prompt, self._prev])
        else:
            self._system_message = self._prompt
        if summary_format is not None:
            self._summary_message = "/n".join([SUMMARY_MESSAGE_INTRO, self._summary_format])

        self._set_model(model)

    def clear(self):
        self.prompt = None
        self.prev = None
        self.summary_format = None
        self._system_message = None
        self._system_message_n_tokens = 0
        self._summary_message = None
        self._summary_message_n_tokens = 0
