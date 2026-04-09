from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Create default groups and assign basic permissions'

    def handle(self, *args, **options):
        group_names = ['Administrator', 'Projectleider', 'Vrijwilliger', 'Hulpvrager']
        for name in group_names:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Group already exists: {name}'))

        # Assign model permissions for the app models
        # Administrator group: get all permissions for this app
        admin_group = Group.objects.get(name='Administrator')
        perms = Permission.objects.filter(content_type__app_label='app')
        for p in perms:
            admin_group.permissions.add(p)

        # Projectleider: permissions to add/change/delete/view Dienst and Project
        pl_group = Group.objects.get(name='Projectleider')
        allowed_models = ['dienst', 'project']
        for model in allowed_models:
            perms = Permission.objects.filter(content_type__app_label='app', codename__contains=model)
            for p in perms:
                pl_group.permissions.add(p)

        # Vrijwilliger: can view Dienst and edit own profile
        v_group = Group.objects.get(name='Vrijwilliger')
        view_perms = Permission.objects.filter(content_type__app_label='app', codename__startswith='view_')
        for p in view_perms:
            v_group.permissions.add(p)

        # Hulpvrager: can view Dienst and create/view HulpAanvraag
        h_group = Group.objects.get(name='Hulpvrager')
        perms = Permission.objects.filter(content_type__app_label='app', codename__in=['add_hulpaanvraag', 'view_hulpaanvraag'])
        for p in perms:
            h_group.permissions.add(p)

        self.stdout.write(self.style.SUCCESS('Default groups and permissions initialized.'))
