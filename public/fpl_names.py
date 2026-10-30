"""Shared name helpers: Sofascore team/player names -> FPL bootstrap records."""
import unicodedata

# Sofascore full team names (player rows) -> FPL bootstrap names
FULL = {'Manchester City': 'Man City', 'Manchester United': 'Man Utd',
        'Tottenham Hotspur': 'Spurs', 'Nottingham Forest': "Nott'm Forest",
        'Newcastle United': 'Newcastle', 'Leeds United': 'Leeds',
        'Brighton & Hove Albion': 'Brighton', 'AFC Bournemouth': 'Bournemouth',
        'Liverpool FC': 'Liverpool', 'West Ham United': 'West Ham',
        'Wolverhampton': 'Wolves'}
# Sofascore SHORT team names (team rows, match JSONs) -> FPL bootstrap names
SHORT = {'Forest': "Nott'm Forest", 'Tottenham': 'Spurs', 'Hull': 'Hull City',
         'Coventry': 'Coventry City', 'Ipswich': 'Ipswich Town'}

ALIAS = {('alisson', 'Liverpool'): 'a.becker',
         ('lewis miley', 'Newcastle'): 'l.miley'}  # else matches Mason Miley


def fpl_team(name):
    name = name.replace(' FC', '') if name.endswith(' FC') else name
    return SHORT.get(name, FULL.get(name, name))


def norm(s):
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower().replace('-', ' ')


def build_fpl_lookup(boot):
    """{FPL team name: [element, ...]} from a bootstrap-static dump."""
    tname = {t['id']: t['name'] for t in boot['teams']}
    by_team = {}
    for e in boot['elements']:
        by_team.setdefault(tname[e['team']], []).append(e)
    return by_team


def _score(name_norm, e):
    parts = set(name_norm.split())
    wn, sn, fn = norm(e['web_name']), norm(e['second_name']), norm(e['first_name'])
    score = 0
    if wn and wn in name_norm:
        score += 2
    if sn and sn in name_norm:
        score += 2
    if fn and fn in name_norm:
        score += 1
    if parts & set(wn.replace('.', ' ').split()):
        score += 1
    return score


def fpl_match(name, team, fpl_by_team, min_score=2):
    """Best FPL element for a Sofascore player name within an FPL team.

    Falls back to a league-wide search with a stricter score (first AND
    last name must match) for players whose FPL club differs from the
    club they played that match for — mid-window transfers, e.g. a GW1
    appearance for a club he then left."""
    cands = fpl_by_team.get(team, [])
    n = norm(name)
    _al = ALIAS.get((n, team))
    if _al:
        for e in cands:
            if norm(e['web_name']) == _al:
                return e
    best = None
    for e in cands:
        s = _score(n, e)
        if s > 0 and (best is None or s > best[0]):
            best = (s, e)
    if best and best[0] >= min_score:
        return best[1]
    best = None
    for es in fpl_by_team.values():
        for e in es:
            s = _score(n, e)
            if s >= 4 and (best is None or s > best[0]):
                best = (s, e)
    return best[1] if best else None
