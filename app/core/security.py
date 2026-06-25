
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

def jwt_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if not token or token == "dummy":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return {"sub": "user-id"}
