from pydantic import BaseModel
from typing import Dict, Optional


class ConfigUpdateRequest(BaseModel):
    section_name: str
    config_dict: Dict[str, str]
    overwrite: Optional[bool] = True
