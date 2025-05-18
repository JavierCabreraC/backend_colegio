import json
import requests


class APITester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token = None

    def login(self, email, password):
        """Hacer login y guardar token"""
        url = f"{self.base_url}/api/auth/login/"
        data = {"email": email, "password": password}

        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            self.token = result['access']
            print(f"✅ Login exitoso para {email}")
            print(f"🔑 Rol: {result['rol']}")
            return result
        else:
            print(f"❌ Login fallido: {response.text}")
            return None

    def make_request(self, method, endpoint, data=None):
        """Hacer petición autenticada"""
        if not self.token:
            print("❌ No hay token. Hacer login primero.")
            return None

        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.token}"}

        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        # ... otros métodos

        return response.json() if response.status_code < 400 else response.text


# Ejemplo de uso:
if __name__ == '__main__':
    tester = APITester()

    # Login como director
    tester.login("director1@sistema.com", "director123")

    # Hacer una petición
    result = tester.make_request("GET", "/api/academic/niveles/")
    print(json.dumps(result, indent=2))

