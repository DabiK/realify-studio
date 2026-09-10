"""Rebuild analytics from the original TikTok CSV exports. Standard library only."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split()
LABELS = {
    '7543666837599423766': ('Les grands méchants', 'Méchants réalistes'),
    '7556003118211779862': ('Robin, Kid, Boa et compagnie', 'Format à identifier'),
    '7560465541811522838': ('Behind the Scenes · Part 3', 'Coulisses'),
    '7565294981427154179': ('Ultimate Live Action Compilation', 'Compilation live action'),
    '7551088567376809238': ('La Marine aux Jeux', 'Sport'),
    '7559367040478235926': ('Kaido / Doflamingo', 'Format à identifier'),
    '7549954038532525334': ('Les Mugiwara aux Jeux', 'Sport'),
    '7552568478474013974': ('Les Minks', 'Créatures réalistes'),
    '7543295716761046294': ('Les premiers antagonistes', 'Méchants réalistes'),
    '7557094976551701782': ('One Piece sur un plateau', 'Coulisses'),
    '7548119864716561686': ('Les Yonkos en politique', 'Politique fictive'),
    '7555216160984272130': ('Doflamingo entre en scène', 'Format à identifier'),
    '7547424244863585558': ('Les Grands Corsaires', 'Personnages réalistes'),
    '7555912966902811906': ('Interview de Robin', 'Interview'),
    '7553040845184781590': ('Les femmes de One Piece', 'Personnages réalistes'),
}


def read(name):
    with (ROOT / 'data/source' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def dated(rows):
    """Infer years from export start and ordered month rollover, never from mtime."""
    year, previous = 2025, 9
    output = []
    for raw in rows:
        day, month = raw['Date'].split(' ', 1)
        month = MONTHS.index(month) + 1
        if month < previous:
            year += 1
        previous = month
        output.append({'date': date(year, month, int(day)).isoformat(),
                       **{k: int(v) for k, v in raw.items() if k != 'Date'}})
    return output


def build():
    overview = dated(read('Overview.csv'))
    viewers = dated(read('Viewers.csv'))
    followers = dated(read('FollowerHistory.csv'))
    posts = []
    for r in read('Content.csv'):
        pid = r['Video link'].rstrip('/').split('/')[-1]
        title, family = LABELS.get(pid, (r['Video title'][:80], 'À identifier'))
        metrics = {k: int(r['Total ' + k]) for k in ('views', 'likes', 'comments', 'shares')}
        views = metrics['views']
        posts.append({'id': pid, 'title': title, 'family': family, 'caption': r['Video title'],
                      'url': r['Video link'], 'post_date_label': r['Post time'],
                      **metrics,
                      'interaction_rate': round(100 * sum(metrics[k] for k in ('likes', 'comments', 'shares')) / views, 3) if views else None,
                      'shares_per_1000': round(1000 * metrics['shares'] / views, 3) if views else None})
    posts.sort(key=lambda r: r['views'], reverse=True)
    totals = {k: sum(r[k] for r in overview) for k in overview[0] if k != 'date'}
    monthly = defaultdict(lambda: defaultdict(int))
    for r in overview:
        for k, v in r.items():
            if k != 'date':
                monthly[r['date'][:7]][k] += v
    hours = defaultdict(list)
    for r in read('FollowerActivity.csv'):
        if r['Date'] != '11 septembre':  # export-day partial row: zero-filled future hours
            hours[int(r['Hour'])].append(int(r['Active followers']))
    peak = max(followers, key=lambda r: r['Followers'])
    last30 = overview[-30:]
    return {
        'account': {'name': 'Realify AI', 'handle': 'realify.ai8', 'niche': 'One Piece uniquement'},
        'provenance': {'export_date': '2026-09-11', 'start': overview[0]['date'], 'end': overview[-1]['date'],
                       'year_inference': 'Nom du ZIP Overview et ordre des mois ; années absentes des CSV.',
                       'post_scope': '15 publications exportées ; compteurs Total, période de cumul non documentée. Ne pas assimiler au total Overview.',
                       'files': [{'file': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((ROOT / 'data/source').glob('*.csv'))]},
        'totals': totals, 'monthly': dict(monthly), 'daily': overview, 'posts': posts,
        'followers': {'current': followers[-1]['Followers'], 'peak': peak,
                      'net_since_peak': followers[-1]['Followers'] - peak['Followers'],
                      'last30_net': sum(r['Difference in followers from previous day'] for r in followers[-30:]),
                      'history': followers,
                      'gender': {r['Gender']: round(float(r['Distribution']) * 100, 2) for r in read('FollowerGender.csv')},
                      'territories': {r['Top territories']: round(float(r['Distribution']) * 100, 2) for r in read('FollowerTopTerritories.csv')},
                      'hourly_activity': [{'hour': h, 'mean': round(sum(v) / len(v), 1), 'days': len(v)} for h, v in sorted(hours.items())],
                      'activity_timezone': 'Non indiqué par le CSV ; ne pas convertir automatiquement en heure de Paris.'},
        'last30': {k: sum(r[k] for r in last30) for k in totals},
        'viewers': {'daily': viewers, 'daily_sum': {k: sum(r[k] for r in viewers) for k in viewers[0] if k != 'date'},
                    'note': 'Sommes de spectateurs quotidiens, PAS des personnes uniques sur un an. Décalage apparent avec Overview : pas de correction automatique.'},
        'caveats': ['Échantillon Content limité à 15 posts ; biais de sélection possible.',
                    'Pas de rétention, durée, source de trafic, sauvegardes, âge, ni abonnements par publication.',
                    'Comparaison des posts non contrôlée : âge, diffusion et format confondus.',
                    'Les commentaires quotidiens comprennent des valeurs négatives ; conserver les ajustements.',
                    'Un compteur d’abonnés stable ne mesure pas une audience encore engagée.',
                    'Captions = indices de classement éditorial, pas preuve visuelle du montage.'],
    }


if __name__ == '__main__':
    output = ROOT / 'data/analytics.json'
    output.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Analytics rebuilt: {output}')
