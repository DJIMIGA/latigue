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
                'duration': '12 heures',
                'description': '''
                <h3>Apprenez le Vibe Coding — Créez des applications en parlant à l'IA</h3>
                <p>Cette formation est conçue pour les grands débutants. Grâce au <strong>vibe coding</strong>, vous apprendrez à créer des applications en décrivant simplement ce que vous voulez à une IA. Plus besoin de tout taper ligne par ligne — l'IA code pour vous, vous guidez.</p>
                <ul>
                    <li>Maîtriser Antigravity, l'IDE IA gratuit de Google</li>
                    <li>Créer votre première application Django par le dialogue</li>
                    <li>Comprendre le code généré et savoir l'améliorer</li>
                </ul>
                ''',
                'prerequisites': '''
                <ul>
                    <li>Aucune expérience en programmation requise</li>
                    <li>Curiosité et motivation</li>
                    <li>Un ordinateur avec accès internet</li>
                    <li>Un compte Google (pour Antigravity, gratuit)</li>
                </ul>
                ''',
                'program': '''
                <h3>Programme — Vibe Coding avec l'IA</h3>

                <h4>Module 1 : Votre Environnement de Vibe Coding (2h)</h4>
                <ul>
                    <li><strong>Le Vibe Coding, c'est quoi ?</strong> Coder en décrivant ce qu'on veut à l'IA — la révolution du développement.</li>
                    <li><strong>Installation de Python :</strong> La base de tout notre travail.</li>
                    <li><strong>Découverte d'Antigravity :</strong> L'IDE IA gratuit de Google — installation et premier lancement.</li>
                    <li><strong>L'interface Editor :</strong> Naviguer dans l'éditeur, le terminal, la sidebar agent.</li>
                    <li><strong>Votre premier prompt :</strong> Demander à l'IA de générer du code et comprendre le résultat.</li>
                </ul>

                <h4>Module 2 : Maîtriser les Agents IA (3h)</h4>
                <ul>
                    <li><strong>Tab completions :</strong> L'IA complète votre code en temps réel.</li>
                    <li><strong>Commandes inline :</strong> Modifier, corriger et améliorer du code par le dialogue.</li>
                    <li><strong>L'art du prompt :</strong> Écrire des instructions claires pour obtenir du bon code.</li>
                    <li><strong>Les Artifacts :</strong> Comprendre les plans, screenshots et rapports générés par l'agent.</li>
                    <li><strong>Exercice pratique :</strong> Créer un script Python utile entièrement par le dialogue.</li>
                </ul>

                <h4>Module 3 : Votre Premier Projet Django en Vibe Coding (5h)</h4>
                <ul>
                    <li><strong>Créer un projet Django :</strong> Demander à l'agent de générer la structure complète.</li>
                    <li><strong>Générer vos vues :</strong> Décrire les pages souhaitées, l'IA code la logique.</li>
                    <li><strong>Créer vos templates :</strong> L'IA génère le HTML/CSS à partir de vos descriptions.</li>
                    <li><strong>Le cycle URL → Vue → Template :</strong> Comprendre comment tout s'assemble.</li>
                    <li><strong>Itérer par le dialogue :</strong> Modifier le design et les fonctionnalités en parlant à l'agent.</li>
                </ul>

                <h4>Module 4 : Projet Final — Votre Application Personnelle (2h)</h4>
                <ul>
                    <li><strong>Choisir son projet :</strong> Portfolio, blog, outil perso — vous décidez.</li>
                    <li><strong>Développement autonome :</strong> Construire l'app de A à Z avec l'agent IA.</li>
                    <li><strong>Présentation :</strong> Montrer votre création au groupe.</li>
                </ul>

                <h4>Outils utilisés (tous gratuits)</h4>
                <ul>
                    <li><strong>Antigravity</strong> — IDE IA de Google (gratuit, modèles premium inclus)</li>
                    <li><strong>Python</strong> — Langage de programmation</li>
                    <li><strong>Django</strong> — Framework web</li>
                </ul>

                <h4>Formats pédagogiques</h4>
                <ul>
                    <li>Vidéos courtes et pas à pas</li>
                    <li>Exercices guidés en vibe coding</li>
                    <li>Projet personnel accompagné</li>
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