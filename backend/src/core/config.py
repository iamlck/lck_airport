import os
from enum import Enum
from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class VectorStoreType(str, Enum):
    CHROMA = "chroma"
    QDRANT = "qdrant"
    FAISS = "faiss"
    IN_MEMORY = "in_memory"


class DBProviderType(str, Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MYSQL = "mysql"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 1. Server settings
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    app_name: str = "LCK Airport's AI Assistant"
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # 2. Guardrail LLM settings
    guardrail_enabled: bool = True
    guardrail_model: str = "ollama/llama3.2:3b"
    guardrail_temperature: float = 0.0
    guardrail_max_tokens: int = 100
    guardrail_timeout_seconds: float = 10.0

    # 3. Main LLM settings
    llm_model: str = "ollama/llama3.1:8b"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024
    llm_timeout_seconds: float = 60.0
    # Ollama defaults to a 2048-token context and silently truncates anything longer,
    # which is far smaller than the full knowledge snapshot. Ignored by hosted providers.
    llm_num_ctx: int = 16384

    # Provider endpoints & credentials (optional)
    ollama_api_base: str = "http://host.docker.internal:11434"
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None

    # 4. Embedding settings
    embedding_model: str = "ollama/nomic-embed-text"

    # 5. Knowledge & Storage settings
    storage_provider: str = "local"
    data_dir: str = "/app/data"
    manifest_path: str = "/app/data/manifest.json"
    knowledge_dir: str = "/app/data/lck_airport"

    # 6. RAG Retrieval settings
    vector_store_provider: VectorStoreType = VectorStoreType.IN_MEMORY
    vector_store_path: str = "/app/data/vector_db"
    rag_top_k: int = 5
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 100
    rag_hybrid_search_enabled: bool = True

    # 7. Database & Memory settings
    db_provider: DBProviderType = DBProviderType.SQLITE
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "lck_assistant"
    db_user: str | None = None
    db_password: SecretStr | None = None
    db_sqlite_path: str = "/app/storage/lck_assistant.db"

    memory_max_turns: int = 20
    memory_summarize_older: bool = True
    memory_session_ttl_minutes: int = 60
    memory_enable_user_linking: bool = True

    # 8. Cache & Streaming settings
    cache_knowledge_context: bool = True
    cache_ttl_seconds: int = 3600
    cache_provider_native: bool = True
    enable_streaming: bool = True
    okf_language_aware_context: bool = True

    # 9. Security settings
    auth_enabled: bool = True
    knowledge_admin_secret: SecretStr = Field(
        default=SecretStr("lck-admin-change-in-production-secure-token-512bit!")
    )

    def get_database_url(self) -> str:
        if self.db_provider == DBProviderType.SQLITE:
            db_dir = Path(self.db_sqlite_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{self.db_sqlite_path}"
        elif self.db_provider == DBProviderType.POSTGRES:
            pwd = self.db_password.get_secret_value() if self.db_password else ""
            user = self.db_user or "postgres"
            return f"postgresql+asyncpg://{user}:{pwd}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.db_provider == DBProviderType.MYSQL:
            pwd = self.db_password.get_secret_value() if self.db_password else ""
            user = self.db_user or "root"
            return f"mysql+aiomysql://{user}:{pwd}@{self.db_host}:{self.db_port}/{self.db_name}"
        return f"sqlite+aiosqlite:///{self.db_sqlite_path}"


settings = Settings()

