# auth_server.py  –  Lab 4: Auth + Per-Tool Scopes
#
# FastAPI >= 0.110, python-jose, uvicorn
# Issues + introspects HS256-signed JWTs with per-tool scopes

from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
import uvicorn

SECRET_KEY = "mcp-lab-secret"          # symmetric key shared with the MCP server
ALGORITHM  = "HS256"
AUDIENCE   = "mcp-lab"
EXPIRES_IN = 3600                      # 1 hour

# 1) Client registry – each client gets specific tool scopes
_fake_clients = {
    "full-client": {
        "client_secret": "fullpass",
        "scopes": ["tools:add", "tools:multiply", "tools:divide"]
    },
    "limited-client": {
        "client_secret": "limitedpass",
        "scopes": ["tools:add"]
    }
}

app = FastAPI(title="MCP Lab – Auth Server")


# 2) Create a JWT that carries the client's allowed scopes
def _create_access_token(sub: str, scopes: list[str]) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": sub,
        "scope": " ".join(scopes),
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(seconds=EXPIRES_IN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/token")
def token(form: OAuth2PasswordRequestForm = Depends()):
    """OAuth-style form grant (client_id + secret) -> {access_token, expires_in}"""
    client = _fake_clients.get(form.username)
    if not client or client["client_secret"] != form.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid client credentials")
    # 3) Token carries the client's allowed scopes
    access_token = _create_access_token(form.username, client["scopes"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": EXPIRES_IN
    }


@app.post("/introspect")
def introspect(token: str = Body(..., embed=True)):
    """RFC 7662-style introspection – reveals token contents including scopes."""
    try:
        payload = jwt.decode(token, SECRET_KEY,
                             algorithms=[ALGORITHM], audience=AUDIENCE)
    except JWTError:
        return {"active": False}
    return {
        "active": True,
        "sub": payload["sub"],
        "scope": payload.get("scope", ""),
        "exp": payload["exp"]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
