from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée les rôles Agent, Superviseur et Administrateur."

    def handle(self, *args, **options):
        droits = {
            "Agent": ["view_client", "view_demandecredit", "add_demandecredit"],
            "Superviseur": ["view_client", "change_client", "view_demandecredit", "change_demandecredit"],
            "Administrateur": [],
        }
        for nom, codenames in droits.items():
            groupe, _ = Group.objects.get_or_create(name=nom)
            if codenames:
                groupe.permissions.set(Permission.objects.filter(codename__in=codenames))
            self.stdout.write(self.style.SUCCESS(f"Rôle prêt : {nom}"))
