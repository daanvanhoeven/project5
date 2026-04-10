from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Project, Dienst, Aanmelding, Skill
from django.utils import timezone

User = get_user_model()


class DienstAanmeldingTests(TestCase):
	def setUp(self):
		self.user1 = User.objects.create_user(username='u1', password='pass')
		self.user2 = User.objects.create_user(username='u2', password='pass')
		self.user3 = User.objects.create_user(username='u3', password='pass')
		self.project = Project.objects.create(name='Test Project')
		self.dienst = Dienst.objects.create(
			project=self.project,
			titel='Test Dienst',
			datum=timezone.now().date(),
			begin_tijd='09:00',
			eind_tijd='12:00',
			max_personen=2,
		)

	def test_spots_and_waitlist(self):
		Aanmelding.objects.create(volunteer=self.user1, dienst=self.dienst, status='accepted')
		Aanmelding.objects.create(volunteer=self.user2, dienst=self.dienst, status='accepted')
		self.assertTrue(self.dienst.is_full())
		# Add third as waitlist
		Aanmelding.objects.create(volunteer=self.user3, dienst=self.dienst, status='waitlist')
		self.assertEqual(self.dienst.spots_left(), 0)


class LoginEnProfielTests(TestCase):
	def test_login_werkt_ook_zonder_bestaand_profiel(self):
		user = User.objects.create_user(username='zonderprofiel', password='pass1234')
		user.userprofile.delete()

		response = self.client.post(
			reverse('login'),
			{'username': 'zonderprofiel', 'password': 'pass1234'},
		)

		self.assertEqual(response.status_code, 302)
		self.assertTrue(response.url.endswith('/'))
		user.refresh_from_db()
		self.assertTrue(hasattr(user, 'userprofile'))

	def test_home_rendered_voor_ingelogde_gebruiker(self):
		user = User.objects.create_user(username='homegebruiker', password='pass1234')
		user.userprofile.delete()
		self.client.force_login(user)

		response = self.client.get(reverse('home'))

		self.assertEqual(response.status_code, 200)


class ProjectleiderDashboardTests(TestCase):
	def setUp(self):
		self.projectleider = User.objects.create_user(username='leider', password='pass1234')
		self.projectleider.userprofile.role = 'projectleider'
		self.projectleider.userprofile.save()

		self.vrijwilliger = User.objects.create_user(username='vrijwilliger1', password='pass1234')
		self.vrijwilliger.userprofile.role = 'vrijwilliger'
		self.vrijwilliger.userprofile.save()

		self.skill = Skill.objects.create(name='EHBO')
		self.vrijwilliger.userprofile.skills.add(self.skill)

		self.project = Project.objects.create(name='Projectleider Project', projectleider=self.projectleider)
		self.dienst = Dienst.objects.create(
			project=self.project,
			titel='Onderbezette dienst',
			datum=timezone.now().date(),
			begin_tijd='10:00',
			eind_tijd='12:00',
			max_personen=2,
			created_by=self.projectleider,
		)

	def test_dashboard_laadt_voor_projectleider(self):
		self.client.force_login(self.projectleider)

		response = self.client.get(reverse('projectleider_dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Projectleider dashboard')
		self.assertContains(response, 'Onderbezette dienst')

	def test_vrijwilligers_filter_op_skill(self):
		self.client.force_login(self.projectleider)

		response = self.client.get(reverse('vrijwilligers_filter'), {'skill': self.skill.id})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'vrijwilliger1')
		self.assertContains(response, 'EHBO')

# Create your tests here.
