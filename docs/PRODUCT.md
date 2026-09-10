# Studio — cockpit de création

## Décisions utilisateur (11 septembre 2026)

Application React responsive desktop/mobile, pas une app native. Moteur générique multi-projets. Realify AI est le premier univers, exclusivement One Piece ; aucune règle One Piece ne doit contaminer les autres projets.

L’app prépare des posts complets automatiquement. L’utilisateur choisit et télécharge ; il peut donner un feedback, relancer une image, ajouter du texte et modifier la fiche TikTok. Abonnement Codex uniquement, aucune API image payante. Mac d’abord, VPS ensuite. Upload TikTok manuel. Dépôt GitHub privé.

**Pas d’A/B testing ni de suivi d’expériences** : cette clarification remplace le cadrage initial. Le produit apprend des retours explicites et conserve ses analyses historiques, sans imposer un tableau de métriques à remplir.

## Parcours principal

1. Ouvrir le projet et cliquer « Préparer mon prochain post ». Aucun prompt requis.
2. L’app choisit la prochaine direction éditoriale. Codex reçoit la DA, les références, les sujets, les titres récents et les retours. Il conçoit un angle concret, génère cinq images, les inspecte et prépare titre, description et 1–5 hashtags.
3. Les images et la fiche deviennent disponibles. Le navigateur peut être fermé pendant le travail, tant que la machine et le serveur restent actifs.
4. Si besoin, ouvrir une image et demander une correction ou un texte exact à ajouter. Une nouvelle version est créée ; les autres images et l’original sont conservés. On peut restaurer une version.
5. Copier la fiche, télécharger le ZIP ou les images individuelles, ou utiliser le partage natif de fichiers si le navigateur le permet. Un ZIP ne s’enregistre pas automatiquement dans Photos.
6. Après l’upload manuel, marquer le post publié, avec son URL facultative. Si aucun autre brouillon n’attend et si l’option est active, l’app prépare le suivant automatiquement. Elle ne publie jamais sur TikTok.

## Automatisation réelle et limites

La file, les projets, les retours et les versions sont persistants. Un seul worker génère à la fois. La rotation de concepts de Realify est curatée à partir des archives et des résultats ; ce n’est pas une prédiction de viralité. Codex choisit les scènes et le texte au sein de cette direction. Les autres projets utilisent leur propre univers, sujets et style.

La préparation du prochain post est déclenchée à la demande ou après le marquage local de publication. Il n’y a ni calendrier autonome continu, ni connexion TikTok, ni scraping. Les feedbacks sont transmis comme contexte aux générations suivantes ; aucun modèle n’est réentraîné.

La fiche est rédigée pour le sujet réellement créé : titre clair, description naturelle, un appel pertinent à commenter, hashtags spécifiques. « Optimisée » décrit ce travail éditorial, pas un score SEO certifié ni des tendances vérifiées. Tous les champs restent éditables. Pas de hashtags ou chiffres inventés comme tendances actuelles.

L’ajout de texte passe par l’édition native d’image Codex. La précision typographique demande un contrôle humain ; le fichier source et la retouche restent tous deux disponibles. Les images créées sont de vraies sorties du moteur, pas des placeholders.

## Critères d’acceptation

- Post de cinq images généré avec une fiche complète sans prompt obligatoire.
- Correction d’une seule image, y compris un texte exact, sans écraser les versions.
- Retour conservé et transmis seulement aux futurs posts du même projet.
- Téléchargements ordonnés contenant les vrais fichiers et la fiche utilisée.
- Marquage publié idempotent ; préparation du prochain brouillon sans doublon volontaire ni boucle infinie.
- Au redémarrage, les travaux interrompus apparaissent comme à reprendre, sans relance silencieuse.
- Aucun fournisseur API payant ; indisponibilité de Codex = erreur visible.
- Interface React utilisable au clavier, sur desktop et petit écran.
- Nouvel univers avec DA, sujets, format et références indépendants.

## Suites possibles

Migration vers un VPS après choix de l’hôte et test réel de connexion Codex ; notifications ; planification horaire facultative ; import des nouveaux exports analytics ; gestion plus fine des identités visuelles ; ajout de texte déterministe ; clips animés. Ces évolutions ne sont pas présentées comme déjà livrées.
