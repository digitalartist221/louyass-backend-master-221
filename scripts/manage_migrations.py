import os
import sys
from alembic.config import Config
from alembic import command

# Ajouter le dossier app au PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration d'Alembic
alembic_cfg = Config("alembic.ini")


def create_migration(message: str):
    """Crée une nouvelle migration"""
    command.revision(alembic_cfg, message=message, autogenerate=True)


def upgrade_database():
    """Applique toutes les migrations non appliquées"""
    command.upgrade(alembic_cfg, "head")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestionnaire de migrations')
    
    # Créer une migration
    parser.add_argument('action', choices=['create', 'upgrade'], help='Action à effectuer')
    parser.add_argument('--message', help='Message de la migration (pour action=create)')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        if not args.message:
            print("L'option --message est requise pour créer une migration")
            sys.exit(1)
        create_migration(args.message)
    elif args.action == 'upgrade':
        upgrade_database()

if __name__ == '__main__':
    main()
