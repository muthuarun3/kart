from pydantic import ValidationError  # Import nécessaire pour la gestion des erreurs

from src.backend.schema import CircuitDeKarting, CourseDeKarting


def test_circuit_de_karting_validation():
    """
    Teste la classe CircuitDeKarting : succès et échec de validation.
    """
    print("--- Test de CircuitDeKarting ---")

    # Données VALIDES pour Kartland Moissy
    donnees_valides = {
        "Nom_Circuit": "Kartland Moissy",
        "Configuration_Piste": "Circuit court",
        "Longueur": "830m",
        "Adresse": "All. Edouard Branly, 77550 Moissy-Cramayel, France"
    }

    # Données INVALIDE (Adresse manquante)
    donnees_invalides = {
        "Nom_Circuit": "Kartland Moissy",
        "Configuration_Piste": "Circuit court",
        "Longueur": "830m",
        # 'Adresse' est manquant et obligatoire
    }

    # Cas de succès
    try:
        circuit = CircuitDeKarting(**donnees_valides)
        print(f"✅ Succès: Circuit '{circuit.Nom_Circuit} / {circuit.Configuration_Piste}' validé.")
    except ValidationError as e:
        print(f"❌ Échec inattendu de validation du circuit valide: {e}")
        return

    # Cas d'échec
    try:
        CircuitDeKarting(**donnees_invalides)
        print("❌ Échec: La validation aurait dû échouer pour l'adresse manquante.")
    except ValidationError as e:
        # Pydantic génère une ValidationError comme prévu
        print(f"✅ Succès: ValidationError capturée comme prévu pour les données invalides.")
        # print(e.errors()) # Pour voir les détails de l'erreur
    except Exception as e:
        print(f"❌ Échec: Une erreur inattendue est survenue: {e}")


# test_circuit_de_karting_validation()

from datetime import date  # Import nécessaire


def test_course_de_karting_validation():
    """
    Teste la classe CourseDeKarting : succès et échec de validation,
    y compris la structure imbriquée du circuit.
    """
    print("\n--- Test de CourseDeKarting ---")

    # Circuit valide nécessaire pour l'imbrication
    circuit_valide = {
        "Nom_Circuit": "RKC Cormeilles",
        "Configuration_Piste": "Standard",
        "Longueur": "1000m",
        "Adresse": "D915, « 95830 Cormeilles-en-Vexin, France »"
    }

    # Données VALIDES complètes
    donnees_course_valides = {
        "Section": 3,
        "Pilote": "Tony",
        "Date": date(2025, 11, 1),  # Utilisation de l'objet date pour Pydantic
        "Kart": 14,
        "Note": 2,
        "Meilleur_Tour": "1:06.065",
        "Ecart": None,
        "Tours": 0,
        "Humidite": 0.3,
        "Circuit": circuit_valide  # Objet imbriqué
    }

    # Données INVALIDE (Humidite est une chaîne de caractères au lieu d'un nombre)
    donnees_course_invalides = donnees_course_valides.copy()
    donnees_course_invalides["Humidite"] = "trop_humide"

    # Cas de succès
    try:
        course = CourseDeKarting(**donnees_course_valides)
        # Note: on peut vérifier ici que l'objet Circuit est bien présent et du bon type
        assert isinstance(course.Circuit, CircuitDeKarting)
        print(f"✅ Succès: Course de '{course.Pilote}' validée avec l'objet Circuit imbriqué.")
    except ValidationError as e:
        print(f"❌ Échec inattendu de validation de la course valide: {e}")
        return

    # Cas d'échec
    try:
        CourseDeKarting(**donnees_course_invalides)
        print("❌ Échec: La validation aurait dû échouer pour l'humidité non numérique.")
    except ValidationError as e:
        # Pydantic génère une ValidationError car "trop_humide" ne peut pas être converti en décimal
        print(f"✅ Succès: ValidationError capturée comme prévu pour l'humidité invalide.")
        # print(e.errors())
    except Exception as e:
        print(f"❌ Échec: Une erreur inattendue est survenue: {e}")

# test_course_de_karting_validation()
