import os
import configparser
from pathlib import Path

from agent.const import *

CONFIG_HOME = os.path.join(str(Path.home()), ".mle")
CONFIG_PATH = os.path.join(CONFIG_HOME, "config")


class Config:
    """
    Config: the overall system configuration for Termax.
    """

    def __init__(self):
        self.home = CONFIG_HOME
        Path(self.home).mkdir(parents=True, exist_ok=True)

        self.config_path = CONFIG_PATH
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

    def read(self):
        """
        read: read the configuration file.

        Returns: a dictionary of the configuration.
        """
        self.reload_config(CONFIG_PATH)
        config_dict = {}

        for section in self.config.sections():
            options_dict = {option: self.config.get(section, option) for option in self.config.options(section)}
            config_dict[section] = options_dict

        return config_dict

    def reload_config(self, config_path):
        """
        reload_config: The default configuration will load ~/.mle/config, if user want to specify
        customize, the method is required.

        @param config_path: the path of new configuration file.
        """
        self.config.read(config_path)

    def load_openai_config(self):
        """
        load_openai_config: load a OpenAI configuration when required.
        """
        if self.config.has_section(LLM_TYPE_OPENAI):
            return self.config[LLM_TYPE_OPENAI]
        else:
            raise ValueError("there is no '[openai]' section found in the configuration file.")

    def write_general(self, config_dict: dict):
        """
        write_general: write the general configuration.

        @param config_dict: the configuration dictionary.

        """
        if not self.config.has_section(CONFIG_SEC_GENERAL):
            self.config.add_section(CONFIG_SEC_GENERAL)

        self.config[CONFIG_SEC_GENERAL] = config_dict

        # save the new configuration and reload.
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
            self.reload_config(self.config_path)

    def write_platform(
            self,
            config_dict: dict,
            platform: str = LLM_TYPE_OPENAI
    ):
        """
        write_platform: indicate and generate the platform related configuration.

        @param config_dict: the configuration dictionary.
        @param platform: the platform to configure.

        """
        # create the configuration to connect with OpenAI.
        if not self.config.has_section(platform):
            self.config.add_section(platform)

        self.config[platform] = config_dict

        # save the new configuration and reload.
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
            self.reload_config(self.config_path)
