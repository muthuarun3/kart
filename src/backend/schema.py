from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, condecimal


class CircuitDeKarting(BaseModel):
    """
    Modèle Pydantic pour les détails d'un circuit spécifique.
    (Basé sur : Circuit, Piste, Longueur, Adresse)
    """
    Nom_Circuit: str = Field(..., description="Nom du circuit principal (ex: Kartland Moissy).")
    Configuration_Piste: str = Field(...,
                                     description="Configuration spécifique de la piste (ex: Circuit court, Standard).")
    Longueur: str = Field(..., description="Longueur de la piste (ex: 830m, 1000m).")
    Adresse: str = Field(..., description="Adresse physique du circuit.")

    # Configuration Pydantic pour les données (optionnel)
    class Config:
        frozen = True  # Rendre l'objet immuable, car les détails du circuit ne devraient pas changer.


class CourseDeKarting(BaseModel):
    """
    Modèle Pydantic pour valider une ligne de données de course de karting,
    avec imbrication du modèle CircuitDeKarting.
    """
    Section: int = Field(..., description="Numéro de la section ou de la manche.")
    Pilote: str = Field(..., description="Nom du pilote.")
    Date: date = Field(..., description="Date de la course (AAAA-MM-JJ).")

    # >>> JONCTION : L'attribut 'Circuit' est maintenant un objet CircuitDeKarting <<<
    Circuit: CircuitDeKarting = Field(...,
                                      description="Détails complets du circuit et de la configuration de piste utilisée.")

    Kart: Optional[int] = Field(None, description="Numéro du kart utilisé, facultatif.")
    Note: int = Field(..., description="Note ou classement de la session.")
    Meilleur_Tour: str = Field(..., description="Meilleur temps au tour (format M:SS.mmm ou SS.mmm).")
    Ecart: Optional[str] = Field(None, description="Écart avec le meilleur temps, facultatif.")
    Tours: int = Field(..., description="Nombre de tours effectués.")
    Humidite: condecimal(max_digits=2, decimal_places=1) = Field(
        ...,
        description="Taux d'humidité ou facteur (ex: 0.3)."
    )
