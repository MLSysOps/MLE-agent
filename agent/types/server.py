from typing import Dict, Optional

from pydantic import BaseModel


class ConfigUpdateRequest(BaseModel):
    section_name: str
    config_dict: Dict[str, str]
    overwrite: Optional[bool] = True
