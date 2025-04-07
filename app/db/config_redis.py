from pydantic_settings import BaseSettings, SettingsConfigDict

class SettingsRedis(BaseSettings):
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_HOST: str
    REDIS_DB: str

    @property
    def DATABASE_get_url_redis(self):
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = SettingsConfigDict(env_file="app/.env", extra="ignore")


settings_redis = SettingsRedis()