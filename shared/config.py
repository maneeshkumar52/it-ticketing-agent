from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    azure_openai_endpoint: str = Field(default="https://your-openai.openai.azure.com/", env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(default="your-key", env="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(default="2024-02-01", env="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment: str = Field(default="gpt-4o", env="AZURE_OPENAI_DEPLOYMENT")
    service_bus_connection_string: str = Field(default="", env="SERVICE_BUS_CONNECTION_STRING")
    service_bus_queue: str = Field(default="it-tickets", env="SERVICE_BUS_QUEUE")
    jira_base_url: str = Field(default="https://your-org.atlassian.net", env="JIRA_BASE_URL")
    jira_project_key: str = Field(default="IT", env="JIRA_PROJECT_KEY")
    teams_webhook_url: str = Field(default="", env="TEAMS_WEBHOOK_URL")
    local_mode: bool = Field(default=True, env="LOCAL_MODE")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
