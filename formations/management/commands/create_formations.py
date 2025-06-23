from django.core.management.base import BaseCommand
from formations.models import Formation
from django.core.exceptions import MultipleObjectsReturned

class Command(BaseCommand):
    help = 'Crée ou met à jour les 3 formations de base (débutant, intermédiaire, avancé).'

    def handle(self, *args, **options):
        formations_data = [
            {
                'title': "Formule Initiation : Découvrez le code avec l'IA",
                'level': 'debutant',
                'price': 65000.00,
                'duration': '20 heures',
                'description': '''
                <h3>Initiez-vous à l'IA générative et à la programmation assistée</h3>
                <p>Cette formation est conçue pour les grands débutants. Vous apprendrez les bases de l'IA générative, comment préparer votre environnement de travail et faire vos premiers pas dans la création de code avec l'aide de l'IA.</p>
                <ul>
                    <li>Comprendre les modèles d'IA générative</li>
                    <li>Découvrir les outils modernes d'assistance au code</li>
                    <li>Installer et configurer votre environnement de développement</li>
                </ul>
                ''',
                'prerequisites': '''
                <ul>
                    <li>Aucune expérience en programmation requise</li>
                    <li>Curiosité et motivation</li>
                    <li>Un ordinateur avec accès internet</li>
                </ul>
                ''',
                'program': '''
                <h3>Programme</h3>
                <h4>Module 1 : Les Fondamentaux et l'Installation</h4>
                <ul>
                    <li><strong>Qu'est-ce que l'IA générative ?</strong> Son rôle pour les développeurs.</li>
                    <li><strong>Installation de Python :</strong> La base de tout notre travail.</li>
                    <li><strong>Mise en place d'un IDE :</strong> Installation et configuration de VS Code.</li>
                    <li><strong>Votre IA en local (sans internet) :</strong> Installation d'un outil comme Ollama pour utiliser des modèles de code en local.</li>
                    <li><strong>Configuration des assistants IA :</strong> Lier l'IA locale à votre éditeur de code.</li>
                </ul>

                <h4>Module 2 : Votre Premier Projet Django avec l'IA</h4>
                <ul>
                    <li><strong>Création du projet :</strong> Initialiser un projet Django simple.</li>
                    <li><strong>Générer votre première vue :</strong> Utiliser l'IA pour créer la logique d'une page.</li>
                    <li><strong>Définir votre première URL :</strong> Connecter une URL à votre vue.</li>
                    <li><strong>Construire votre premier template :</strong> Créer le fichier HTML qui sera affiché.</li>
                    <li><strong>Le cycle complet :</strong> Comprendre comment l'URL, la vue et le template fonctionnent ensemble.</li>
                </ul>

                <h4>Formats pédagogiques</h4>
                <ul>
                    <li>Vidéos courtes et pas à pas</li>
                    <li>Fiches pratiques téléchargeables</li>
                    <li>Quiz interactifs</li>
                </ul>
                '''
            },
            {
                'title': "Formule Création : Réalisez votre première application IA",
                'level': 'intermediaire',
                'price': 130000.00,
                'duration': '40 heures',
                'description': '''
                <h3>Passez à l'action avec un projet concret</h3>
                <p>Cette formation s'adresse à ceux qui veulent créer leur première application de A à Z avec l'aide de l'IA. Vous apprendrez à générer, corriger et organiser du code pour aboutir à un projet fonctionnel.</p>
                <ul>
                    <li>Utiliser des prompts efficaces pour générer du code</li>
                    <li>Vérifier et corriger le code généré</li>
                    <li>Développer une application simple de bout en bout</li>
                </ul>
                ''',
                'prerequisites': '''
                <ul>
                    <li>Avoir suivi la Formule Initiation ou équivalent</li>
                    <li>Notions de base en Python</li>
                </ul>
                ''',
                'program': '''
                <h3>Programme</h3>
                <h4>Module 1 : Rappel des fondamentaux IA & environnement</h4>
                <ul>
                    <li>Révision des outils et de l'environnement</li>
                </ul>
                <h4>🎁 Bonus : Votre Premier Script Utile avec l'IA</h4>
                <ul>
                    <li><strong>Projet guidé :</strong> Création d'un script d'automatisation (ex: trier des fichiers).</li>
                    <li>Mettez en pratique la méthode de génération de code sur un cas concret.</li>
                    <li>Obtenez un résultat tangible et un "quick win" pour booster votre motivation.</li>
                </ul>
                <h4>Module 2 : Génération et correction de code</h4>
                <ul>
                    <li>Prompts avancés</li>
                    <li>Analyse et correction du code généré</li>
                </ul>
                <h4>Module 3 : Création d'une application</h4>
                <ul>
                    <li>Développement guidé d'un projet (ex : to-do list, blog...)</li>
                    <li>Automatisation de tâches avec l'IA</li>
                </ul>
                <h4>Formats pédagogiques</h4>
                <ul>
                    <li>Vidéos pas à pas</li>
                    <li>Exercices guidés</li>
                    <li>Sessions interactives</li>
                </ul>
                '''
            },
            {
                'title': "Formule Maîtrise : Devenez autonome et performant avec l'IA",
                'level': 'avance',
                'price': 260000.00,
                'duration': '60 heures',
                'description': '''
                <h3>Atteignez l'excellence avec l'IA dans vos projets</h3>
                <p>Pour les apprenants qui veulent aller plus loin : optimisez, déployez et industrialisez vos applications avec l'IA, tout en bénéficiant d'un accompagnement personnalisé.</p>
                <ul>
                    <li>Optimiser la qualité et la performance du code</li>
                    <li>Déployer une application</li>
                    <li>Coaching individuel et corrections personnalisées</li>
                </ul>
                ''',
                'prerequisites': '''
                <ul>
                    <li>Avoir suivi la Formule Création ou équivalent</li>
                    <li>Expérience en développement web recommandée</li>
                </ul>
                ''',
                'program': '''
                <h3>Programme</h3>
                <h4>Module 1 : Optimisation et bonnes pratiques</h4>
                <ul>
                    <li>Amélioration de la qualité du code</li>
                    <li>Tests et automatisation</li>
                </ul>
                <h4>Module 2 : Déploiement</h4>
                <ul>
                    <li>Déploiement sur un serveur</li>
                    <li>Gestion des fichiers statiques et médias</li>
                </ul>
                <h4>Module 3 : Coaching & accompagnement</h4>
                <ul>
                    <li>Sessions individuelles</li>
                    <li>Corrections personnalisées</li>
                    <li>Suivi de projet</li>
                </ul>
                <h4>Formats pédagogiques</h4>
                <ul>
                    <li>Vidéos avancées</li>
                    <li>Coaching en direct</li>
                    <li>Forum d'entraide</li>
                </ul>
                '''
            }
        ]

        self.stdout.write("Mise à jour des formations de base...")

        for data in formations_data:
            level = data['level']
            
            try:
                # On cherche LA formation unique pour ce niveau
                formation = Formation.objects.get(level=level)
                
                # Si on la trouve, on la met à jour avec les nouvelles données
                Formation.objects.filter(pk=formation.pk).update(**data)
                
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Formation du niveau "{level}" mise à jour avec le titre : "{data["title"]}"'
                ))

            except Formation.DoesNotExist:
                # Si elle n'existe pas, on la crée
                Formation.objects.create(**data)
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Formation du niveau "{level}" créée avec le titre : "{data["title"]}"'
                ))

            except MultipleObjectsReturned:
                # Si plusieurs formations existent pour ce niveau, on ne peut pas choisir.
                self.stdout.write(self.style.ERROR(
                    f'❌ ERREUR: Plusieurs formations existent pour le niveau "{level}". '
                    'Mise à jour automatique impossible. '
                    'Veuillez ne conserver manuellement qu\'une seule formation pour chaque niveau (débutant, intermédiaire, avancé) via l\'interface admin, ou les supprimer pour que le script les recrée.'
                ))

        self.stdout.write(self.style.SUCCESS("\nOpération terminée !")) 