# Objectif actif — production photo et accès agent

Demandes utilisateur du 11 septembre 2026. Ce fichier est la mémoire de travail ; les cases cochées décrivent du travail vérifié.

- [x] Revoir le producteur : scènes vécues, caméra invisible, regards dirigés vers l’action, lumière motivée, variété des plans, références d’identité distinctes des poses et tenues.
- [x] Transmettre cette direction durablement à Realify sans imposer One Piece aux autres projets.
- [x] Préparer un découpage consultable avant génération et contrôler la continuité entre images.
- [x] Fournir une CLI JSON pour Hermes : lancer une image ou un batch, suivre les jobs, corriger, reprendre et récupérer les fichiers. Partager Store et la file de l’app ; conserver un worker unique.
- [x] Tester le contrat agent, documenter l’usage local et via SSH sur VPS. MCP facultatif : la CLI répond au besoin initial.
- [ ] Reprendre le post Nami / Robin / Hancock avec la nouvelle direction et inspecter les vrais rendus. Conserver les versions précédentes.
- [ ] Pousser les changements sur le dépôt privé et préciser les limites de validation.

Contraintes : abonnement Codex uniquement ; pas d’A/B testing ; pas de publication automatique sur TikTok. Hermes n’est pas présenté comme connecté tant qu’un appel depuis son environnement n’a pas été vérifié.

Avancement : 13 tests backend passent, dont un parcours CLI avec fournisseur de test (aucun quota image consommé). Skill validé. Une génération cartoon lancée dans le studio a effectivement écrit son shot-plan.json avec le nouveau producteur. Le résultat photo premium et la connexion depuis Hermes restent à valider. Ne pas redémarrer le serveur pendant sa génération active ; le nouveau code Python sera chargé au prochain redémarrage, la CLI utilise déjà le code courant.
