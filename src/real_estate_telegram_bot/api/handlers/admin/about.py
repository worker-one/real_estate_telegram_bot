"""Handler to show information about the application configuration."""

import logging
import logging.config

from omegaconf import OmegaConf

# Set up logging
# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load configuration
config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")


def register_handlers(bot):
    """Register about handlers"""
    logger.info("Registering `about` handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "about")
    def about_handler(call):
        user_id = call.from_user.id

        config_str = OmegaConf.to_yaml(config.app)

        # Send config
        bot.send_message(user_id, f"```yaml\n{config_str}\n```", parse_mode="Markdown")
