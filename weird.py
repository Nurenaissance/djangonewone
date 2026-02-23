import jwt, datetime
from simplecrm import settings

def generate_service_token():
    payload = {
        "sub": "whatsapp_bot",
        "tenant_id": "hjiqohe",
        "role": "system",
        "tier": "enterprise",
        "scope": "service",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3365),
    }

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    print("\n-----------------------")
    print(" SERVICE TOKEN CREATED ")
    print("-----------------------")
    print(token, "\n")
    return token

if __name__ == "__main__":
    generate_service_token()
