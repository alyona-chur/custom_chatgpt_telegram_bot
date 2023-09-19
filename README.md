# Knowing ChatGPT Telegram Bot

This repo is ChatGPT re-created as Telegram Bot.

This fork aims to customize and enhance the functionality with a primary focus on engaging in lengthy conversations while providing access to files and a knowledge base.

This may be used to create a personal advisor that is available on all devices through text and voice messages, while maintaining the privacy standards of the Chat GPT API (which are better than in web version).

**Link to Original Repository:** [Original Repository](https://github.com/karfly/chatgpt_telegram_bot)

## Original Features
- Low latency replies (it usually takes about 3-5 seconds)
- No request limits
- Message streaming (watch demo)
- GPT-4 support
- Group Chat support (/help_group_chat to get instructions)
- DALLE 2 (choose 👩‍🎨 Artist mode to generate images)
- Voice message recognition
- Code highlighting
- 15 special chat modes: 👩🏼‍🎓 Assistant, 👩🏼‍💻 Code Assistant, 👩‍🎨 Artist, 🧠 Psychologist, 🚀 Elon Musk and other. You can easily create your own chat modes by editing `config/chat_modes.yml`
- Support of [ChatGPT API](https://platform.openai.com/docs/guides/chat/introduction)
- List of allowed Telegram users
- Track $ balance spent on OpenAI API

## Added Features

- 1 more special chat mode: 🎯 Custom, in which you have the ability to set your own system prompts. This allows for a more personalized and tailored conversation experience.
- **Long conversations**: Engage in extended and uninterrupted chats with the bot, maintaining context throughout lengthy interactions (for custom mode only)
- Keywords support: Use _IM keyword to mark a message as important (never to be trimmed), _SM to mark message as system message (add to system prompts), _UPDT to load manual updates from long conversation metadata file (/knowledge/long_dialogs/user_id.yml).

## Coming Features

- **Knowledge retrieval**: Request the bot to access data stored in knowledge files locally
- Knowledge writing: Ability to add or update information in the knowledge base. Eventually it will allow file processing with Chat GPT.
- Adjustable ChatGPT parameters such as temperature, max_tokens etc. Currently they can be set in long conversation metadata file.
- Long conversations supported in all available modes, including custom mode and for the 'text-davinci-003' model

## Long Conversations

The bot ensures limitless conversations by monitoring token usage and trimming earlier messages when the dialogue becomes too long. Periodically, the model is prompted to create or update a summary that remains intact. You can even define your own summary format. Messages marked as system or important messages are never trimmed.

---

## Bot commands
- `/retry` – Regenerate last bot answer
- `/new` – Start new dialog
- `/mode` – Select chat mode
- `/balance` – Show balance
- `/settings` – Show settings
- `/help` – Show help

## Bot Keywords
- `_IM` – Add message ti important messages
- `_SM` – Add message to system messages
- `_UPDT` – Load update from file

## Setup
1. Get your [OpenAI API](https://openai.com/api/) key

2. Get your Telegram bot token from [@BotFather](https://t.me/BotFather)

3. Edit `config/config.example.yml` to set your tokens and run 2 commands below (*if you're advanced user, you can also edit* `config/config.example.env`):
    ```bash
    mv config/config.example.yml config/config.yml
    mv config/config.example.env config/config.env
    ```

4. 🔥 And now **run**:
    ```bash
    docker-compose --env-file config/config.env up --build
    ```
