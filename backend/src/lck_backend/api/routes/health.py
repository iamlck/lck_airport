import httpx
from fastapi import APIRouter
from lck_backend.schemas.health import HealthResponse, ServiceStatus
from lck_backend.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def check_health():
    services = {}

    # Check Ollama connectivity if using Ollama
    if "ollama" in settings.llm_model:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{settings.ollama_api_base}/api/tags")
                if res.status_code == 200:
                    services["ollama"] = ServiceStatus(status="connected", details={"models": [m["name"] for m in res.json().get("models", [])]})
                else:
                    services["ollama"] = ServiceStatus(status="degraded", details={"http_code": res.status_code})
        except Exception as e:
            services["ollama"] = ServiceStatus(status="unreachable", details={"error": str(e)})
    else:
        services["llm_provider"] = ServiceStatus(status="configured", details={"model": settings.llm_model})

    services["database"] = ServiceStatus(status="ok", details={"provider": settings.db_provider})

    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        environment=settings.app_env,
        active_llm=settings.llm_model,
        guardrail_model=settings.guardrail_model,
        services=services
    )

