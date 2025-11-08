import requests
import pandas as pd
from typing import Optional, Dict, List
from datetime import date

class KartingAPIClient:
    """
    Client pour interagir avec l'API FastAPI de gestion des données de karting.
    Gère les requêtes vers les endpoints /circuits, /courses, /export et /import.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialise le client avec l'URL de base de l'API.

        Args:
            base_url (str): URL de base de l'API FastAPI.
        """
        self.base_url = base_url

    def _handle_request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict:
        """
        Gère une requête HTTP générique vers l'API.

        Args:
            endpoint (str): Endpoint de l'API (ex: "/circuits").
            method (str): Méthode HTTP ("GET", "POST", etc.).
            params (Dict, optional): Paramètres de requête (pour GET).
            data (Dict, optional): Données à envoyer (pour POST/PUT).
            files (Dict, optional): Fichiers à uploader (pour import CSV).

        Returns:
            Dict: Réponse JSON de l'API.

        Raises:
            requests.exceptions.RequestException: En cas d'erreur HTTP.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, params=params, json=data, files=files)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur lors de la requête vers {url}: {e}")

    # --- Circuits ---
    def get_circuits(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        Récupère la liste des circuits (avec pagination).

        Args:
            skip (int): Nombre d'éléments à sauter (pour la pagination).
            limit (int): Nombre maximal d'éléments à retourner.

        Returns:
            List[Dict]: Liste des circuits.
        """
        params = {"skip": skip, "limit": limit}
        return self._handle_request("/circuits", params=params)

    def export_circuits_to_csv(self, file_path: str) -> None:
        """
        Exporte les circuits au format CSV via l'endpoint /circuits/export.

        Args:
            file_path (str): Chemin où enregistrer le fichier CSV.
        """
        response = self._handle_request("/circuits/export")
        df = pd.DataFrame(response)
        df.to_csv(file_path, index=False)

    def import_circuits_from_csv(self, file_path: str) -> Dict:
        """
        Importe des circuits depuis un fichier CSV via l'endpoint /circuits/import.

        Args:
            file_path (str): Chemin du fichier CSV à importer.

        Returns:
            Dict: Réponse de l'API (statut, message).
        """
        files = {"file": open(file_path, "rb")}
        return self._handle_request("/circuits/import", method="POST", files=files)

    # --- Courses ---
    def get_courses(self, skip: int = 0, limit: int = 100, circuit_id: Optional[int] = None, date: Optional[date] = None) -> List[Dict]:
        """
        Récupère la liste des courses (avec pagination et filtres optionnels).

        Args:
            skip (int): Nombre d'éléments à sauter.
            limit (int): Nombre maximal d'éléments à retourner.
            circuit_id (int, optional): Filtrer par ID de circuit.
            date (date, optional): Filtrer par date de course.

        Returns:
            List[Dict]: Liste des courses.
        """
        params = {"skip": skip, "limit": limit}
        if circuit_id:
            params["circuit_id"] = circuit_id
        if date:
            params["date"] = date.isoformat()
        return self._handle_request("/courses", params=params)

    def export_courses_to_csv(self, file_path: str, circuit_id: Optional[int] = None, date: Optional[date] = None) -> None:
        """
        Exporte les courses au format CSV via l'endpoint /courses/export.

        Args:
            file_path (str): Chemin où enregistrer le fichier CSV.
            circuit_id (int, optional): Filtrer par ID de circuit.
            date (date, optional): Filtrer par date de course.
        """
        params = {}
        if circuit_id:
            params["circuit_id"] = circuit_id
        if date:
            params["date"] = date.isoformat()
        response = self._handle_request("/courses/export", params=params)
        df = pd.DataFrame(response)
        df.to_csv(file_path, index=False)

    def import_courses_from_csv(self, file_path: str) -> Dict:
        """
        Importe des courses depuis un fichier CSV via l'endpoint /courses/import.

        Args:
            file_path (str): Chemin du fichier CSV à importer.

        Returns:
            Dict: Réponse de l'API (statut, message).
        """
        files = {"file": open(file_path, "rb")}
        return self._handle_request("/courses/import", method="POST", files=files)

    # --- Utilitaires ---
    def get_circuit_by_id(self, circuit_id: int) -> Dict:
        """
        Récupère un circuit par son ID.

        Args:
            circuit_id (int): ID du circuit.

        Returns:
            Dict: Détails du circuit.
        """
        circuits = self.get_circuits()
        for circuit in circuits:
            if circuit["id"] == circuit_id:
                return circuit
        raise ValueError(f"Aucun circuit trouvé avec l'ID {circuit_id}.")

    def get_courses_by_pilot(self, pilot_name: str) -> List[Dict]:
        """
        Récupère toutes les courses d'un pilote donné.

        Args:
            pilot_name (str): Nom du pilote.

        Returns:
            List[Dict]: Liste des courses du pilote.
        """
        all_courses = []
        skip = 0
        limit = 100
        while True:
            courses = self.get_courses(skip=skip, limit=limit)
            if not courses:
                break
            filtered = [course for course in courses if course["Pilote"].lower() == pilot_name.lower()]
            all_courses.extend(filtered)
            if len(courses) < limit:
                break
            skip += limit
        return all_courses
