from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import (
    User, PatientProfile, DoctorProfile, Specialization, 
    DoctorSpecialization, Review
)
from medlink.models import MedicalFile, AppointmentRequest, Appointment
from chat.models import Chat, Message
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup demo data for MedLink application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up demo data...')
        
        # Create specializations
        specializations = self.create_specializations()
        
        # Create users
        users = self.create_users()
        
        # Create profiles
        self.create_profiles(users, specializations)
        
        # Create medical files
        self.create_medical_files(users)
        
        # Create appointments
        self.create_appointments(users)
        
        # Create chat data
        self.create_chat_data(users)
        
        self.stdout.write(
            self.style.SUCCESS('Demo data setup completed successfully!')
        )

    def create_specializations(self):
        """Create medical specializations"""
        specializations_data = [
            {'name': 'Cardiology', 'description': 'Heart and cardiovascular system'},
            {'name': 'Dermatology', 'description': 'Skin, hair, and nails'},
            {'name': 'Neurology', 'description': 'Nervous system and brain'},
            {'name': 'Orthopedics', 'description': 'Bones, joints, and muscles'},
            {'name': 'Pediatrics', 'description': 'Children and adolescents'},
            {'name': 'Psychiatry', 'description': 'Mental health and behavior'},
            {'name': 'Oncology', 'description': 'Cancer treatment'},
            {'name': 'Gastroenterology', 'description': 'Digestive system'},
        ]
        
        specializations = []
        for spec_data in specializations_data:
            spec, created = Specialization.objects.get_or_create(
                name=spec_data['name'],
                defaults={'description': spec_data['description']}
            )
            specializations.append(spec)
            if created:
                self.stdout.write(f'Created specialization: {spec.name}')
        
        return specializations

    def create_users(self):
        """Create demo users"""
        users_data = [
            # Admins
            {'username': 'admin', 'role': 'admin', 'email': 'admin@medlink.com'},
            
            # Doctors
            {'username': 'dr_smith', 'role': 'doctor', 'email': 'dr.smith@medlink.com'},
            {'username': 'dr_johnson', 'role': 'doctor', 'email': 'dr.johnson@medlink.com'},
            {'username': 'dr_williams', 'role': 'doctor', 'email': 'dr.williams@medlink.com'},
            {'username': 'dr_brown', 'role': 'doctor', 'email': 'dr.brown@medlink.com'},
            
            # Patients
            {'username': 'patient1', 'role': 'patient', 'email': 'patient1@example.com'},
            {'username': 'patient2', 'role': 'patient', 'email': 'patient2@example.com'},
            {'username': 'patient3', 'role': 'patient', 'email': 'patient3@example.com'},
            {'username': 'patient4', 'role': 'patient', 'email': 'patient4@example.com'},
            
            # Receptionists
            {'username': 'receptionist1', 'role': 'receptionist', 'email': 'reception@medlink.com'},
        ]
        
        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'role': user_data['role'],
                    'first_name': user_data['username'].split('_')[0].title(),
                    'last_name': user_data['username'].split('_')[1].title() if '_' in user_data['username'] else 'User',
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password('demo123')
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            
            users.append(user)
        
        return users

    def create_profiles(self, users, specializations):
        """Create user profiles"""
        doctors = [u for u in users if u.role == 'doctor']
        patients = [u for u in users if u.role == 'patient']
        
        # Create doctor profiles
        for i, doctor in enumerate(doctors):
            profile, created = DoctorProfile.objects.get_or_create(
                user=doctor,
                defaults={
                    'qualifications': f'MD, {random.choice(["Cardiology", "Internal Medicine", "Family Medicine"])}',
                    'experience_years': random.randint(5, 25),
                    'bio': f'Experienced {doctor.username} with expertise in patient care.',
                    'rating': round(random.uniform(3.5, 5.0), 1),
                    'consultation_fee': round(random.uniform(50, 200), 2),
                    'working_hours_start': '09:00',
                    'working_hours_end': '17:00',
                    'working_days': 'monday,tuesday,wednesday,thursday,friday',
                }
            )
            
            if created:
                # Add specializations
                num_specs = random.randint(1, 3)
                selected_specs = random.sample(specializations, num_specs)
                for spec in selected_specs:
                    DoctorSpecialization.objects.get_or_create(
                        doctor=profile,
                        specialization=spec,
                        defaults={
                            'experience_years': random.randint(1, profile.experience_years),
                            'is_primary': selected_specs.index(spec) == 0
                        }
                    )
                
                self.stdout.write(f'Created doctor profile: {doctor.username}')
        
        # Create patient profiles
        for patient in patients:
            profile, created = PatientProfile.objects.get_or_create(
                user=patient,
                defaults={
                    'address': f'{random.randint(100, 9999)} Main St, City, State',
                    'emergency_contact_name': f'Emergency Contact for {patient.username}',
                    'emergency_contact_phone': f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'emergency_contact_relationship': random.choice(['Spouse', 'Parent', 'Sibling', 'Friend']),
                    'blood_type': random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
                    'allergies': random.choice(['None', 'Penicillin', 'Peanuts', 'Latex', 'Dairy']),
                    'bio': f'Patient profile for {patient.username}',
                }
            )
            
            if created:
                self.stdout.write(f'Created patient profile: {patient.username}')

    def create_medical_files(self, users):
        """Create demo medical files"""
        patients = [u for u in users if u.role == 'patient']
        
        file_types = ['pdf', 'doc', 'jpg', 'png']
        descriptions = [
            'Medical history report',
            'Lab results',
            'Prescription',
            'X-ray image',
            'Blood test results',
            'Vaccination record',
        ]
        
        for patient in patients:
            num_files = random.randint(1, 3)
            for _ in range(num_files):
                MedicalFile.objects.get_or_create(
                    patient=patient,
                    description=random.choice(descriptions),
                    defaults={
                        'uploaded_by': patient,
                        'file_type': random.choice(file_types),
                        'is_private': random.choice([True, False])
                    }
                )
        
        self.stdout.write('Created medical files')

    def create_appointments(self, users):
        """Create demo appointments"""
        doctors = [u for u in users if u.role == 'doctor']
        patients = [u for u in users if u.role == 'patient']
        
        if not doctors or not patients:
            return
        
        # Create appointment requests
        for patient in patients[:3]:  # Limit to first 3 patients
            doctor = random.choice(doctors)
            
            # Create appointment request
            request, created = AppointmentRequest.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                defaults={
                    'preferred_date': timezone.now().date() + timedelta(days=random.randint(1, 30)),
                    'preferred_time_slot': random.choice(['morning', 'afternoon', 'evening']),
                    'reason': f'Regular checkup for {patient.username}',
                    'urgency_level': random.choice(['low', 'medium', 'high']),
                    'notes': f'Demo appointment request for {patient.username}',
                }
            )
            
            if created:
                # Sometimes create an actual appointment
                if random.choice([True, False]):
                    appointment = Appointment.objects.create(
                        appointment_request=request,
                        scheduled_time=timezone.now() + timedelta(days=random.randint(1, 14), hours=random.randint(9, 17)),
                        duration=random.choice([30, 45, 60]),
                        accepted_by=doctor,
                        notes=f'Demo appointment for {patient.username}'
                    )
                    
                    # Update request status
                    request.status = 'accepted'
                    request.save()
                    
                    self.stdout.write(f'Created appointment: {patient.username} with {doctor.username}')
        
        self.stdout.write('Created appointments')

    def create_chat_data(self, users):
        """Create demo chat data"""
        doctors = [u for u in users if u.role == 'doctor']
        patients = [u for u in users if u.role == 'patient']
        
        if not doctors or not patients:
            return
        
        # Create a chat between a doctor and patient
        doctor = random.choice(doctors)
        patient = random.choice(patients)
        
        chat, created = Chat.objects.get_or_create(
            chat_type='patient_doctor',
            defaults={
                'title': f'Chat: {patient.username} - {doctor.username}'
            }
        )
        
        if created:
            chat.participants.add(doctor, patient)
            
            # Create some demo messages
            messages = [
                f'Hello Dr. {doctor.username}, I have a question about my appointment.',
                f'Hello {patient.username}, I\'m here to help. What would you like to know?',
                'I was wondering if we could reschedule to next week?',
                'Of course, let me check my availability and get back to you.',
                'Thank you, that would be great!',
                'You\'re welcome. I\'ll send you the new time shortly.',
            ]
            
            for i, message_text in enumerate(messages):
                sender = doctor if i % 2 == 0 else patient
                Message.objects.create(
                    chat=chat,
                    sender=sender,
                    text=message_text,
                    message_type='text',
                    timestamp=timezone.now() - timedelta(hours=len(messages) - i)
                )
            
            self.stdout.write(f'Created chat between {patient.username} and {doctor.username}')
        
        self.stdout.write('Created chat data')
