"""
Redmine プロキシサーバー
EC2上で動かし、LambdaからのリクエストをEC2のIPでRedmineに転送する
"""
import os
import httpx
from fastapi import FastAPI, Request, Response

app = FastAPI(title="Redmine Proxy")

REDMINE_URL = os.environ["REDMINE_URL"].rstrip("/")
REDMINE_API_KEY = os.environ["REDMINE_API_KEY"]


@app.get("/health")
def health():
    return {"status": "ok", "service": "redmine-proxy"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    """全リクエストをRedmineに転送する"""
    url = f"{REDMINE_URL}/{path}"
    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers={
                "X-Redmine-API-Key": REDMINE_API_KEY,
                "Content-Type": "application/json",
            },
            params=dict(request.query_params),
            content=body,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
