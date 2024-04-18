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

    def write_section(self, section_name: str, config_dict: dict):
        """
        write_section: write the project configuration.

        @param section_name: the section name.
        @param config_dict: the configuration dictionary.

        """
        if not self.config.has_section(section_name):
            self.config.add_section(section_name)

        self.config[section_name] = config_dict

        # save the new configuration and reload.
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
            self.reload_config(self.config_path)
