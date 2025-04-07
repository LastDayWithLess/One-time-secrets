from pydantic import BaseModel
from datetime import datetime
from typing import Union

class SecretSchema(BaseModel):
    secret: str
    passphrase: Union[str, None]
    ttl_seconds: Union[int, None] = 300