from django.conf import settings
from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid import ApiClient

def get_plaid_client():
    # Map env string to Plaid base URL
    env_map = {
        "sandbox": "https://sandbox.plaid.com",
        "development": "https://development.plaid.com",
        "production": "https://production.plaid.com",
    }
    base_url = env_map.get(settings.PLAID_ENV, "https://sandbox.plaid.com")

    config = Configuration(
        host=base_url,
        api_key={
            "clientId": settings.PLAID_CLIENT_ID,
            "secret": settings.PLAID_SECRET,
        },
    )
    api_client = ApiClient(config)
    return plaid_api.PlaidApi(api_client)
