from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Project, Dienst, Aanmelding
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

# Create your tests here.
