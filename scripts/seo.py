"""SEO / GEO / local-search layer for the English pages. Runs before build_i18n.py, so every
language copy inherits it. Idempotent: safe to run on every build.

What it does
1. Keeps each page's title and meta description aligned with the keywords that www.mega.tc
   already ranks for (same URLs, same focus phrases).
2. Gives every page its own social-share image (og:image / twitter:image) from the page photo.
3. Adds BreadcrumbList structured data to every page and a LocalBusiness block (office + works,
   with map links) to the home and contact pages, so Google Maps / local search and AI answer
   engines can read MEGA's locations.
4. Writes llms.txt: a plain summary of MEGA and its key pages for AI search assistants.

Usage:  python scripts/seo.py
"""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '/NEWMEGA/'
SITE = 'https://www.mega.tc/'
SKIP = {'es', 'fr', 'pt', 'ru', 'ar', 'assets', 'media', 'content', 'scripts', 'i18n', 'admin', '.git', '.github'}

# Title / description per URL, matched to the focus phrases www.mega.tc already uses.
SEO = {
 '': ('MEGA Engineering | Ethanol, CO₂, Biogas & Process Plant EPC',
      'MEGA Engineering, Pune: turnkey EPC for distillery, fuel ethanol, CO₂ recovery, biogas and CBG, evaporation, dryers and ZLD plants. 100+ projects in 15+ countries since 2010.'),
 'co2-recovery-plants': ('Distillery CO₂ Recovery Technology and Automation Insights - Mega Engineering',
      "Find out how Mega Engineering's Distillery CO₂ Recovery ensures high-quality CO₂ with minimal operational costs: food-grade liquid CO₂ from fermentation gas."),
 'bio-cng-biogas-plant-epc-mega-engineering': ('Bio Gas & Bio CNG - Mega Engineering',
      'Planning a Compressed Biogas Plant? We Engineer and Build Efficient Bio-CNG Plants With Gas Purification and Compression. Request a proposal.'),
 'business-lines': ('Mega Engineering - Business Lines',
      "Explore Mega Engineering's business lines, including ethanol, evaporation, ZLD, process equipment, brewery, biogas and CO₂ recovery plants."),
 'contact-mega-engineering-epc-company': ('Contact - Mega Engineering | EPC Company in Pune, India',
      'Contact Mega Engineering, Pune, for ethanol, distillery, biogas and process plant projects. Call, email or send an enquiry for a quick quote.'),
 'critical-process-equipment': ('Critical Process Equipment Manufacturer Supplier Worldwide',
      'Mega Engineering offers Critical Process Equipment Manufacturer Supplier Worldwide with precision quality and reliable performance: vessels, heat exchangers, columns and reactors.'),
 'engineering-services': ('Process Engineering & Design Services | Mega Engineering',
      'Process, mechanical, piping and electrical engineering services for ethanol, distillery and chemical plants. Basic to detailed engineering.'),
 'evaporation-dryer': ('Evaporation & Dryer Plant Manufacturer | Industrial Solutions',
      'Evaporation & dryer plant manufacturer offering energy-efficient industrial solutions worldwide. Serving Africa, Asia and the Americas with multiple effect evaporators and dryers.'),
 'faqs': ('FAQs | Ethanol Plant & EPC Projects | Mega Engineering',
      "Answers to common questions about ethanol plant setup, EPC project timelines, costs and Mega Engineering's services. Find what you need."),
 'modular-process-skid': ('Modular Process Skid - Mega Engineering Modular Process Skid Manufacturer',
      'Pre-assembled, factory-tested modular process skids that cut site time and cost. Custom skid-mounted systems for distillery, chemical and process plants.'),
 'privacy-policy': ('Privacy Policy | Mega Engineering',
      "Read Mega Engineering's privacy policy to understand how we collect, use and protect information shared through our website and enquiries."),
 'terms-of-use': ('Terms of Use | Mega Engineering',
      'Read the terms of use that apply when you access and use the Mega Engineering website, its content and enquiry services.'),
 'zero-liquid-discharge-system': ('Zero Liquid Discharge System Manufacturer | Global ZLD Solutions',
      'Zero liquid discharge system manufacturer providing advanced ZLD solutions for global industries. Efficient, compliant and cost-effective evaporation, drying and water reuse.'),
 'about-us': ('About Us - Mega Engineering',
      'Mega Engineering is a Pune-based EPC company delivering turnkey ethanol, distillery and industrial plants. 100+ projects worldwide since 2010.'),
 'careers': ('Careers at Mega Engineering | Engineering Jobs',
      'Build your engineering career on real EPC projects. See current openings for process, mechanical and project engineers at Mega Engineering.'),
 'fuel-ethanol': ('Fuel Ethanol Plant Manufacturer & EPC | Mega Engineering',
      'End-to-end EPC for fuel ethanol plants: process engineering, equipment supply, erection and commissioning. 100+ projects delivered worldwide.'),
 'vinasse-dryer-manufacturer-from-india': ('Vinasse Dryer Manufacturer from India | Mega Engineering',
      'Mega Engineering is a trusted Vinasse Dryer Manufacturer from India offering advanced drying systems for distilleries: evaporation and spray drying for zero liquid discharge.'),
 'condensate-recovery-system-distillery-plants': ('Condensate Recovery System in Distillery Plants: Improving Energy Efficiency and Sustainability - Mega Engineering', None),
 'e-fuels-vs-ethanol-environmental-impact': ('E-Fuels vs Ethanol: Environmental Impact, Efficiency and Future of Sustainable Fuels - Mega Engineering', None),
 'life-industrial-export-manufacturing-how-mega-engineering-powers-global-industries': ('Life @ Industrial Export Manufacturing: How Mega Engineering Powers Global Industries - Mega Engineering', None),
 'indias-e85-ambition-opportunity-readiness-and-the-roadblocks-ahead': ('India’s E85 (Ethanol 85) Ambition: Opportunity, Readiness, and the Roadblocks Ahead - Mega Engineering', None),
 'biogas-purification-technology-choosing-the-right-upgrading-solution': ('Biogas Purification Technology: Choosing the Right Upgrading Solution - Mega Engineering', None),
 'high-gravity-fermentation-technical-insights-for-distillery-and-biofuel-plants': ('High-Gravity Fermentation: Technical Insights for Distillery and Biofuel Plants - Mega Engineering', None),
 'biogas-feedstocks-and-challenges': ('Biogas Feedstocks and Their Challenges - Mega Engineering', None),
}

LOCAL = {
 "@context": "https://schema.org", "@type": "LocalBusiness", "@id": SITE + "#localbusiness",
 "name": "MEGA Engineering", "legalName": "MEGA EPC Projects Pvt. Ltd.", "url": SITE,
 "image": SITE + "assets/photos/mega-workshop-talegaon.jpg", "logo": SITE + "assets/mega-logo.png",
 "telephone": "+91-72760-11520", "email": "sales@mega.tc", "priceRange": "On request",
 "address": {"@type": "PostalAddress", "streetAddress": "Speciality Business Center, A204, Baner - Balewadi Rd, Balewadi",
             "addressLocality": "Pune", "addressRegion": "Maharashtra", "postalCode": "411045", "addressCountry": "IN"},
 "hasMap": "https://maps.app.goo.gl/qDJyUwLuz1FP1hdUA",
 "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
     "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], "opens": "09:00", "closes": "18:00"}],
 "areaServed": ["India", "Africa", "South East Asia", "Middle East", "Americas", "Oceania"],
 "department": [{"@type": "LocalBusiness", "name": "MEGA Engineering Manufacturing Works", "telephone": "+91-72760-11520",
     "image": SITE + "assets/photos/mega-workshop-talegaon.jpg",
     "address": {"@type": "PostalAddress", "streetAddress": "Talegaon Dabhade, Jadhavwadi", "addressLocality": "Pune",
                 "addressRegion": "Maharashtra", "postalCode": "410507", "addressCountry": "IN"},
     "hasMap": "https://maps.app.goo.gl/P9XkR1yzuTTSPBxQ9"}],
}

LLMS = """# MEGA Engineering

> MEGA Engineering (MEGA EPC Projects Pvt. Ltd.) is a technology and EPC company founded in 2010 in Pune, India. It designs, manufactures, erects and commissions process plants: distillery and fuel ethanol plants (5–300 KLPD), CO₂ recovery, biogas and compressed biogas (CBG), multiple effect evaporation, vinasse spray dryers, zero liquid discharge (ZLD), modular process skids and critical process equipment. 100+ projects in 15+ countries across Asia, Africa, the Americas and Oceania. ISO 9001, ISO 14001 and ISO 45001 certified by TÜV NORD. Own fabrication works (2,500+ tonnes per year) at Talegaon Dabhade, near Pune.

Contact: sales@mega.tc · +91 72760 11520 · Speciality Business Center, A204, Baner - Balewadi Rd, Balewadi, Pune, Maharashtra 411045, India.

## Solutions
- [Fuel Ethanol Plants](https://www.mega.tc/fuel-ethanol/): end-to-end EPC for fuel ethanol and ENA plants on cane juice, molasses and grain
- [CO₂ Recovery Plants](https://www.mega.tc/co2-recovery-plants/): food-grade liquid CO₂ from fermentation gas
- [Biogas & Bio-CNG](https://www.mega.tc/bio-cng-biogas-plant-epc-mega-engineering/): biogas and compressed biogas plants
- [CBG Plants · OEKOBIT Partnership](https://www.mega.tc/cbg-technology-partnership-oekobit/): German biogas technology delivered by MEGA as EPC
- [Evaporation & Dryers](https://www.mega.tc/evaporation-dryer/): multiple effect evaporators and industrial dryers
- [Vinasse Spray Dryer](https://www.mega.tc/vinasse-dryer-manufacturer-from-india/): spent wash evaporation and spray drying to potash-rich powder
- [Zero Liquid Discharge](https://www.mega.tc/zero-liquid-discharge-system/): ZLD systems with condensate polishing
- [Modular Process Skids](https://www.mega.tc/modular-process-skid/) and [Critical Process Equipment](https://www.mega.tc/critical-process-equipment/)
- [Craft Brewery Plants](https://www.mega.tc/craft-brewery-plants/)
- [Engineering Services](https://www.mega.tc/engineering-services/) and [Project Management Services](https://www.mega.tc/project-management-services/)

## Company
- [About Us](https://www.mega.tc/about-us/)
- [Project References](https://www.mega.tc/projects/)
- [Industries We Serve](https://www.mega.tc/industries/)
- [FAQs](https://www.mega.tc/faqs/)
- [Careers](https://www.mega.tc/careers/)
- [Contact](https://www.mega.tc/contact-mega-engineering-epc-company/)

## Insights
- [All articles](https://www.mega.tc/our-blogs-2/)
"""


def pages():
    yield '', ROOT / 'index.html'
    for p in sorted(ROOT.glob('*/index.html')):
        if p.parent.name not in SKIP:
            yield p.parent.name, p


def set_meta(t, attr, key, value):
    """Replace or add <meta attr=key content=value>, whichever attribute order the page uses."""
    v = html.escape(value, quote=True)
    pats = [rf'<meta {attr}="{re.escape(key)}" content="[^"]*"\s*/?>', rf'<meta content="[^"]*" {attr}="{re.escape(key)}"\s*/?>']
    for pat in pats:
        if re.search(pat, t):
            return re.sub(pat, f'<meta {attr}="{key}" content="{v}"/>', t, count=1)
    return t.replace('</head>', f'<meta {attr}="{key}" content="{v}"/></head>', 1)


def abs_url(src):
    src = src.strip().strip('\'"')
    if src.startswith('http'):
        return src
    return SITE + src.replace(BASE, '', 1).lstrip('/')


def page_image(t):
    m = re.search(r'<video[^>]*poster="([^"]+)"', t)
    if m:
        return abs_url(m.group(1))
    m = re.search(r"--hero-img:url\('([^']+)'\)", t)
    if m:
        return abs_url(m.group(1))
    hero = re.search(r'<section class="hero".*?</section>', t, re.S)
    if hero:
        m = re.search(r'<img\b[^>]*\bsrc="([^"]+)"', hero.group(0))
        if m:
            return abs_url(m.group(1))
    main = re.search(r'<main\b.*?</main>', t, re.S)
    for m in re.finditer(r'<img\b[^>]*\bsrc="([^"]+)"', main.group(0) if main else t):
        if 'logo' not in m.group(1) and not m.group(1).endswith('.svg'):
            return abs_url(m.group(1))
    m = re.search(r'<video[^>]*poster="([^"]+)"', t)
    return abs_url(m.group(1)) if m else SITE + 'assets/photos/ashok-ssk-distillery.jpg'


def breadcrumbs(t, slug):
    if slug == '':
        return None
    crumb = re.search(r'<div class="crumb">(.*?)</div>', t, re.S)
    items = [("Home", SITE)]
    if crumb:
        for m in re.finditer(r'<a href="([^"]+)">(.*?)</a>', crumb.group(1)):
            name = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
            href = m.group(1)
            url = SITE if href in (BASE, '../', '/') else abs_url(href)
            if url != SITE:
                items.append((name, url))
        last = html.unescape(re.sub(r'<[^>]+>', '', crumb.group(1).split('/')[-1])).strip()
    else:
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
        last = html.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).strip() if h1 else slug.replace('-', ' ').title()
    items.append((last, SITE + slug + '/'))
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "@id": SITE + slug + "/#breadcrumb",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + '</script>'


def main():
    n = 0
    for slug, p in pages():
        t = p.read_text(encoding='utf-8')
        if 'http-equiv="refresh"' in t[:3000]:
            continue
        t0 = t
        title, desc = SEO.get(slug, (None, None))
        if title:
            t = re.sub(r'<title>.*?</title>', '<title>' + html.escape(title, quote=False) + '</title>', t, count=1, flags=re.S)
            t = set_meta(t, 'property', 'og:title', title)
        if desc:
            t = set_meta(t, 'name', 'description', desc)
            t = set_meta(t, 'property', 'og:description', desc)
        img = page_image(t)
        t = re.sub(r'<meta (?:property="og:image" content="[^"]*"|content="[^"]*" property="og:image")\s*/?>', '', t)
        t = re.sub(r'<meta (?:name="twitter:image" content="[^"]*"|content="[^"]*" name="twitter:image")\s*/?>', '', t)
        t = t.replace('</head>', f'<meta property="og:image" content="{img}"/><meta name="twitter:image" content="{img}"/></head>', 1)
        if 'name="twitter:card"' not in t and 'content="summary_large_image"' not in t:
            t = t.replace('</head>', '<meta name="twitter:card" content="summary_large_image"/></head>', 1)
        if 'property="og:site_name"' not in t:
            t = t.replace('</head>', '<meta property="og:site_name" content="MEGA Engineering"/></head>', 1)
        # structured data
        if '"BreadcrumbList"' not in t:
            bc = breadcrumbs(t, slug)
            if bc:
                t = t.replace('</head>', ld(bc) + '</head>', 1)
        if slug in ('', 'contact-mega-engineering-epc-company', 'about-us'):
            t = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "LocalBusiness", "@id": "https://www.mega.tc/#localbusiness".*?</script>', '', t, flags=re.S)
            t = t.replace('</head>', ld(LOCAL) + '</head>', 1)
        # removed business lines no longer listed as expertise
        t = t.replace(', "Solvent recovery"]', ', "Critical process equipment", "Craft brewery plants"]')
        if t != t0:
            p.write_text(t, encoding='utf-8'); n += 1
    (ROOT / 'llms.txt').write_text(LLMS, encoding='utf-8')
    print('SEO layer updated on', n, 'pages; llms.txt written')


if __name__ == '__main__':
    main()
