from django.core.management.base import BaseCommand
from formations.models import Formation, Module, Lesson


class Command(BaseCommand):
    help = 'Crée les modules et leçons du Niveau 1 (Formule Initiation)'

    def handle(self, *args, **options):
        try:
            formation = Formation.objects.get(title__icontains="Initiation")
        except Formation.DoesNotExist:
            formation = Formation.objects.filter(level='debutant').first()
        
        if not formation:
            self.stderr.write("Aucune formation Initiation/débutant trouvée.")
            return

        modules_data = [
            {
                'title': 'Votre Environnement de Vibe Coding',
                'order': 1,
                'description': 'Installez et configurez tous les outils nécessaires pour coder avec l\'IA (2h)',
                'is_free': True,
                'lessons': [
                    {'title': 'Introduction au Vibe Coding', 'order': 1, 'lesson_type': 'video', 'duration_minutes': 20,
                     'content': '<p>Découvrez le concept de Vibe Coding : coder en décrivant ce que vous voulez à l\'IA.</p>'},
                    {'title': 'Installer Antigravity (IDE IA de Google)', 'order': 2, 'lesson_type': 'video', 'duration_minutes': 25,
                     'content': '<p>Guide pas à pas pour installer et configurer Antigravity, votre IDE IA gratuit.</p>'},
                    {'title': 'Configurer votre premier projet', 'order': 3, 'lesson_type': 'text', 'duration_minutes': 20,
                     'content': '<p>Créez votre premier projet et familiarisez-vous avec l\'interface.</p>'},
                    {'title': 'Les bases de Git et GitHub', 'order': 4, 'lesson_type': 'video', 'duration_minutes': 30,
                     'content': '<p>Apprenez à versionner votre code avec Git et à le publier sur GitHub.</p>'},
                    {'title': 'Quiz : Votre environnement', 'order': 5, 'lesson_type': 'quiz', 'duration_minutes': 15,
                     'content': '<p>Testez vos connaissances sur l\'environnement de développement.</p>'},
                ],
            },
            {
                'title': 'Maîtriser les Agents IA',
                'order': 2,
                'description': 'Apprenez à communiquer efficacement avec les agents IA pour générer du code (3h)',
                'is_free': False,
                'lessons': [
                    {'title': 'Comprendre les agents IA (Claude, GPT, Gemini)', 'order': 1, 'lesson_type': 'video', 'duration_minutes': 30,
                     'content': '<p>Tour d\'horizon des principaux agents IA et leurs forces respectives.</p>'},
                    {'title': 'L\'art du prompting pour le code', 'order': 2, 'lesson_type': 'video', 'duration_minutes': 40,
                     'content': '<p>Techniques de prompting efficaces pour obtenir du code de qualité.</p>'},
                    {'title': 'Itérer et affiner avec l\'IA', 'order': 3, 'lesson_type': 'text', 'duration_minutes': 35,
                     'content': '<p>Comment guider l\'IA étape par étape pour construire des fonctionnalités complexes.</p>'},
                    {'title': 'Débugger avec l\'IA', 'order': 4, 'lesson_type': 'video', 'duration_minutes': 30,
                     'content': '<p>Utilisez l\'IA pour identifier et corriger les bugs dans votre code.</p>'},
                    {'title': 'Quiz : Maîtrise des agents IA', 'order': 5, 'lesson_type': 'quiz', 'duration_minutes': 15,
                     'content': '<p>Évaluez votre compréhension des agents IA et du prompting.</p>'},
                ],
            },
            {
                'title': 'Votre Premier Projet Django',
                'order': 3,
                'description': 'Créez une application web complète avec Django et l\'IA (5h)',
                'is_free': False,
                'lessons': [
                    {'title': 'Introduction à Django avec l\'IA', 'order': 1, 'lesson_type': 'video', 'duration_minutes': 45,
                     'content': '<p>Découvrez Django et créez votre premier projet en guidant l\'IA.</p>'},
                    {'title': 'Créer vos modèles de données', 'order': 2, 'lesson_type': 'video', 'duration_minutes': 60,
                     'content': '<p>Définissez la structure de votre base de données avec l\'aide de l\'IA.</p>'},
                    {'title': 'Vues et templates', 'order': 3, 'lesson_type': 'video', 'duration_minutes': 60,
                     'content': '<p>Construisez les pages de votre application avec des vues et templates Django.</p>'},
                    {'title': 'Formulaires et interactions', 'order': 4, 'lesson_type': 'text', 'duration_minutes': 50,
                     'content': '<p>Ajoutez des formulaires et de l\'interactivité à votre application.</p>'},
                    {'title': 'Styliser avec Tailwind CSS', 'order': 5, 'lesson_type': 'video', 'duration_minutes': 45,
                     'content': '<p>Rendez votre application belle avec Tailwind CSS, guidé par l\'IA.</p>'},
                ],
            },
            {
                'title': 'Projet Final',
                'order': 4,
                'description': 'Mettez en pratique tout ce que vous avez appris (2h)',
                'is_free': False,
                'lessons': [
                    {'title': 'Cahier des charges du projet', 'order': 1, 'lesson_type': 'text', 'duration_minutes': 30,
                     'content': '<p>Définissez votre projet final et planifiez sa réalisation.</p>'},
                    {'title': 'Développement guidé', 'order': 2, 'lesson_type': 'video', 'duration_minutes': 60,
                     'content': '<p>Développez votre projet en suivant les bonnes pratiques apprises.</p>'},
                    {'title': 'Présentation et prochaines étapes', 'order': 3, 'lesson_type': 'text', 'duration_minutes': 30,
                     'content': '<p>Présentez votre projet et découvrez comment aller plus loin.</p>'},
                ],
            },
        ]

        for mod_data in modules_data:
            lessons = mod_data.pop('lessons')
            module, created = Module.objects.get_or_create(
                formation=formation,
                order=mod_data['order'],
                defaults=mod_data
            )
            action = 'Créé' if created else 'Existant'
            self.stdout.write(f"  {action}: Module {module.order} - {module.title}")
            
            for lesson_data in lessons:
                lesson, created = Lesson.objects.get_or_create(
                    module=module,
                    order=lesson_data['order'],
                    defaults=lesson_data
                )
                action = '  ✓' if created else '  ~'
                self.stdout.write(f"    {action} Leçon {lesson.order}: {lesson.title}")

        self.stdout.write(self.style.SUCCESS(f'\nDonnées créées pour "{formation.title}"'))
