import configparser
import os
from pathlib import Path

from agent.types.const import *

CONFIG_HOME = os.path.join(str(Path.home()), ".mle")
CONFIG_PATH = os.path.join(CONFIG_HOME, "config")


class Config:
    """
    Config: the overall system configuration for MLE-agent
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
        if os.path.isfile(CONFIG_PATH):
            self.reload_config(CONFIG_PATH)
        else:
            return None

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

    def write_section(self, section_name: str, config_dict: dict, overwrite: bool = True):
        """
        write_section: write the project configuration.

        @param section_name: the section name.
        @param config_dict: the configuration dictionary.
        @param overwrite: a boolean indicating whether to overwrite the existing configuration.

        """
        if not self.config.has_section(section_name):
            self.config.add_section(section_name)

        # save the new configuration and reload.
        with open(self.config_path, 'w') as configfile:
            if overwrite:
                self.config[section_name] = config_dict
                self.config.write(configfile)
                self.reload_config(self.config_path)
            else:
                existing_config = dict(self.read().get(section_name))
                existing_config.update({key: value for key, value in config_dict.items() if key not in existing_config})
                self.config[section_name] = existing_config
                self.config.write(configfile)
                self.reload_config(self.config_path)
