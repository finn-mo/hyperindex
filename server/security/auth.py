from fastapi import HTTPException, status, Request

def verify_token(request: Request):
    token = request.headers.get("Authorization")
    if token != "Bearer example-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    return True