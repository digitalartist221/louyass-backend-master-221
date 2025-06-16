from albeemic.config import Config
from albeemic.models import Documentation
from albeemic.utils import generate_api_documentation

# Configuration de base d'Albeemic
albeemic_config = Config(
    title="Hebergement API Documentation",
    description="Documentation officielle de l'API Hebergement",
    version="1.0.0",
    contact={
        "name": "Support Hebergement",
        "email": "support@hebergement.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Documentation générale de l'API
documentation = Documentation(
    title="Hebergement API",
    description="API REST pour la gestion d'hébergement",
    version="1.0.0",
    terms_of_service="https://hebergement.com/terms",
    contact={
        "name": "Hebergement Support",
        "url": "https://hebergement.com/support",
        "email": "support@hebergement.com"
    }
)
