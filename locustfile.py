from locust import HttpUser, task, between
import re

class HospitalUser(HttpUser):
    wait_time = between(1, 5)  # Espera entre 1 y 5 segundos entre acciones
    
    # Credenciales de prueba (Asegúrate de tener este usuario creado en tu BD)
    username = "matrona1" 
    password = "Hospital2025" 

    def on_start(self):
        """Se ejecuta al iniciar cada usuario simulado: Realiza el Login"""
        self.client.verify = False  # Ignorar SSL si es local
        
        # 1. Obtener la página de login para sacar el CSRF token
        response = self.client.get("/accounts/login/")
        csrftoken = response.cookies.get('csrftoken')
        
        if not csrftoken:
            print("Error: No se pudo obtener CSRF token")
            return

        # 2. Realizar el POST de login
        response = self.client.post("/accounts/login/", {
            "username": self.username,
            "password": self.password,
            "csrfmiddlewaretoken": csrftoken
        }, headers={"Referer": self.client.base_url + "/accounts/login/"})

        if "Bienvenido" not in response.text and response.status_code != 200:
            print(f"Fallo en login: {response.status_code}")

    @task(3)
    def ver_dashboard(self):
        """Carga el dashboard (Alto consumo de CPU por desencriptación)"""
        self.client.get("/sistema/dashboard/")

    @task(2)
    def listar_madres(self):
        """Lista las madres (Prueba paginación y desencriptación masiva)"""
        self.client.get("/sistema/madre/")

    @task(1)
    def cargar_formulario_parto(self):
        """Simula abrir el formulario de crear parto"""
        self.client.get("/sistema/parto/crear/")

    @task(1)
    def api_notificaciones(self):
        """Simula el polling de notificaciones"""
        self.client.get("/notifications/api/conteo/")