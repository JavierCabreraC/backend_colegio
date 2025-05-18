import sys
from pathlib import Path


# Configurar rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.helpers import APITester


def test_all_logins():
    tester = APITester()

    # Test credentials
    users = [
        ("director1@sistema.com", "director123"),
        ("director2@sistema.com", "director456"),
        ("profesor1@sistema.com", "prof123"),
        ("profesor2@sistema.com", "prof456"),
    ]

    print("🧪 Testing login para todos los usuarios...")
    for email, password in users:
        print(f"\n--- Testing {email} ---")
        result = tester.login(email, password)
        if result:
            print(f"✅ {email} - Login OK")
        else:
            print(f"❌ {email} - Login FALLÓ")


if __name__ == '__main__':
    test_all_logins()

