import yaml
import dotenv
from pathlib import Path


class LongDialogConfiguration:
    def __init__(self, config_data):
        self.enable = config_data["enable"]
        self.enable_keywords = config_data["enable_keywords"]
        self.update_summary_when_tokens_reach = config_data["update_summary_when_tokens_reach"]
        self.system_and_important_max_tokens = config_data["system_and_important_max_tokens"]

        self.save_to_file = config_data["save_to_file"]
        self.files_dir = config_data["files_dir"]
        self.save_timeout_min = config_data["save_timeout_min"]
        self.save_all_to_file = config_data["save_all_to_file"]

        self.save_all_timeout_min = config_data["save_all_timeout_min"]


config_dir = Path(__file__).parent.parent.resolve() / "config"

# load yaml config
with open(config_dir / "config.yml", 'r') as f:
    config_yaml = yaml.safe_load(f)

# load .env config
config_env = dotenv.dotenv_values(config_dir / "config.env")

# config parameters
telegram_token = config_yaml["telegram_token"]
openai_api_key = config_yaml["openai_api_key"]
openai_api_base = config_yaml.get("openai_api_base", None)
allowed_telegram_usernames = config_yaml["allowed_telegram_usernames"]
new_dialog_timeout = config_yaml["new_dialog_timeout"]
enable_message_streaming = config_yaml.get("enable_message_streaming", True)
long_dialog_config = LongDialogConfiguration(config_yaml['long_dialog'])
return_n_generated_images = config_yaml.get("return_n_generated_images", 1)
n_chat_modes_per_page = config_yaml.get("n_chat_modes_per_page", 5)
mongodb_uri = f"mongodb://mongo:{config_env['MONGODB_PORT']}"

# chat_modes
with open(config_dir / "chat_modes.yml", 'r') as f:
    chat_modes = yaml.safe_load(f)

# models
with open(config_dir / "models.yml", 'r') as f:
    models = yaml.safe_load(f)

# files
help_group_chat_video_path = Path(__file__).parent.parent.resolve() / "static" / "help_group_chat.mp4"
