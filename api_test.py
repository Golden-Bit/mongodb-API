import requests

# Configurazione dell'URL dell'API
BASE_URL = "https://teatek-llm.theia-innovation.com/api/mongodb-api"
ENDPOINT = "/create_database/"

# Dati da inviare nel corpo della richiesta
payload = {
    "db_name": "test_database",
    "username": "admin",
    "password": "password123",
    "host": "mongodb",
    "port": 27017
}

# Headers per la richiesta
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

# Funzione per testare l'endpoint
def test_create_database():
    try:
        # Invio della richiesta POST
        response = requests.post(
            BASE_URL + ENDPOINT,
            json=payload,
            headers=headers
        )

        # Stampa dello stato della risposta e del contenuto
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
    except requests.exceptions.RequestException as e:
        print("Errore durante la richiesta:", e)

# Esegui il test
if __name__ == "__main__":
    test_create_database()
