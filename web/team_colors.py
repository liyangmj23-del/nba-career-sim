"""
NBA 30支球队官方配色（主色/副色），用于游戏内动态换肤。
球员所在球队变化时，UI 主题色跟着切换成真实球队配色，增强NBA识别度。
数据来源：各队官方品牌色（近似值，用于UI主题，不追求印刷级精确）。
"""

TEAM_COLORS = {
    "ATL": {"primary": "#E03A3E", "secondary": "#C1D32F"},
    "BKN": {"primary": "#000000", "secondary": "#FFFFFF"},
    "BOS": {"primary": "#007A33", "secondary": "#BA9653"},
    "CHA": {"primary": "#1D1160", "secondary": "#00788C"},
    "CHI": {"primary": "#CE1141", "secondary": "#000000"},
    "CLE": {"primary": "#860038", "secondary": "#FDBB30"},
    "DAL": {"primary": "#00538C", "secondary": "#B8C4CA"},
    "DEN": {"primary": "#0E2240", "secondary": "#FEC524"},
    "DET": {"primary": "#C8102E", "secondary": "#1D42BA"},
    "GSW": {"primary": "#1D428A", "secondary": "#FFC72C"},
    "HOU": {"primary": "#CE1141", "secondary": "#C4CED4"},
    "IND": {"primary": "#002D62", "secondary": "#FDBB30"},
    "LAC": {"primary": "#C8102E", "secondary": "#1D428A"},
    "LAL": {"primary": "#552583", "secondary": "#FDB927"},
    "MEM": {"primary": "#5D76A9", "secondary": "#12173F"},
    "MIA": {"primary": "#98002E", "secondary": "#F9A01B"},
    "MIL": {"primary": "#00471B", "secondary": "#EEE1C6"},
    "MIN": {"primary": "#0C2340", "secondary": "#236192"},
    "NOP": {"primary": "#0C2340", "secondary": "#C8102E"},
    "NYK": {"primary": "#006BB6", "secondary": "#F58426"},
    "OKC": {"primary": "#007AC1", "secondary": "#EF3B24"},
    "ORL": {"primary": "#0077C0", "secondary": "#C4CED4"},
    "PHI": {"primary": "#006BB6", "secondary": "#ED174C"},
    "PHX": {"primary": "#1D1160", "secondary": "#E56020"},
    "POR": {"primary": "#E03A3E", "secondary": "#000000"},
    "SAC": {"primary": "#5A2D81", "secondary": "#63727A"},
    "SAS": {"primary": "#C4CED4", "secondary": "#000000"},
    "TOR": {"primary": "#CE1141", "secondary": "#000000"},
    "UTA": {"primary": "#002B5C", "secondary": "#F9A01B"},
    "WAS": {"primary": "#002B5C", "secondary": "#E31837"},
}

DEFAULT_COLORS = {"primary": "#4A7A94", "secondary": "#8B6F47", "logo": None}


def get_team_colors(abbreviation: str | None, team_id: int | None = None) -> dict:
    """按缩写查球队配色，查不到（自由球员/自定义球员无队）时返回默认配色。
    传了 team_id 时附带官方logo地址（NBA官方CDN，用真实球队ID直接拼URL）。"""
    if not abbreviation:
        return DEFAULT_COLORS
    colors = dict(TEAM_COLORS.get(abbreviation.upper(), DEFAULT_COLORS))
    colors["logo"] = f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg" if team_id else None
    return colors
