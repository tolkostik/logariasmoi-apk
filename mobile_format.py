"""Μετατροπή αποτελεσμάτων σε κείμενο για την οθόνη του κινητού (Kivy markup)."""
import engine
import store

GREEN = "#0F7B4F"
BLUE = "#2563C9"
GREY = "#6B7486"
RED = "#B4461B"

STYLE = {
    "h1": ("[size=20sp][b]", "[/b][/size]"),
    "big": (f"[size=30sp][b][color={GREEN}]", "[/color][/b][/size]"),
    "h2": ("[size=17sp][b]", "[/b][/size]"),
    "label": (f"[b][color={GREY}]", "[/color][/b]"),
    "bold": ("[b]", "[/b]"),
    "money": (f"[b][color={GREEN}]", "[/color][/b]"),
    "deal": (f"[color={BLUE}]", "[/color]"),
    "warn": (f"[color={RED}]", "[/color]"),
    "note": (f"[size=13sp][color={GREY}]", "[/color][/size]"),
    "mono": ("", ""),
}


def _esc(t):
    return t.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def report_markup(d):
    parts = []
    for text, tag in store.best_report(d):
        if tag == "mono":
            text = " ".join(text.split())  # χωρίς στοίχιση με κενά στο κινητό
            text = text + "\n"
        a, b = STYLE.get(tag, ("", ""))
        parts.append(a + _esc(text) + b)
    return "".join(parts)


def _detail(service, r):
    if service == "electricity":
        fee = "κλιμακωτό πάγιο" if r.get("fee_bands") else f"πάγιο {store.eur(r.get('fee') or 0)}"
        return f"{r['type']} · {r.get('price') or 0:.4f} €/kWh · {fee}".replace(".", ",", 1)
    if service == "gas":
        p = f"{r['price']:.4f} €/kWh".replace(".", ",") if r.get("price") else "μόνο με ρεύμα"
        return f"{r['type']} · {p} · πάγιο {store.eur(r.get('fee') or 0)}"
    if service == "internet":
        return f"{r['tech']} · {r['speed']} Mbps" + (f" · {r['note']}" if r.get("note") else "")
    gb = "απεριόριστα GB" if r["gb"] >= 9999 else f"{r['gb']:g} GB".replace(".", ",")
    voice = "απεριόριστη ομιλία" if r["unlimited_voice"] else "περιορισμένα λεπτά"
    return f"{r['type']} · {gb} · {voice}"


def row_markup(service, r, rank=None):
    inf = float("inf")
    cost = r["cost"]
    head = f"{rank}. " if rank else ""
    money = store.eur(cost) + "/μήνα" if cost < inf else "μόνο σε συνδυασμό"
    txt = (f"[b]{head}{_esc(r['provider'])}[/b]   [b][color={GREEN}]{money}[/color][/b]\n"
           f"{_esc(r['name'])}\n[size=13sp][color={GREY}]{_esc(_detail(service, r))}[/color][/size]")
    cp = r.get("cost_partner")
    if cp is not None and cp < cost - 0.005:
        partner = {"gas": "ρεύμα", "internet": "κινητή", "mobile": "internet"}.get(service, "")
        txt += f"\n[size=13sp][color={BLUE}]Με {partner} ίδιας εταιρείας: {store.eur(cp)}/μήνα[/color][/size]"
    return txt


def service_sections(d, service):
    """[(τίτλος, [(markup, url), ...]), ...] για μια υπηρεσία."""
    rows = engine.ranked(service, store.data_of(d)[service], d["profile"])
    best = engine.per_company(rows)
    return [
        ("Φθηνότερο πρόγραμμα κάθε εταιρείας",
         [(row_markup(service, r, i), r.get("url") or "") for i, r in enumerate(best, 1)]),
        (f"Όλα τα προγράμματα ({len(rows)})",
         [(row_markup(service, r), r.get("url") or "") for r in rows]),
    ]
