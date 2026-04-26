from weasyprint import HTML, CSS


def generate_pdf(raw: dict, r: dict) -> bytes:
    html = _build_html(raw, r)
    return HTML(string=html).write_pdf(stylesheets=[CSS(string=_css())])


def _build_html(raw: dict, r: dict) -> str:
    name    = raw.get('name', '')
    email   = raw.get('email', '')
    phone   = raw.get('phone', '')
    linkedin = raw.get('linkedin', '')
    github  = raw.get('github', '')

    contact = []
    if email:    contact.append(f'✉ {email}')
    if linkedin: contact.append(linkedin.replace('https://','').replace('http://','').strip('/'))
    if phone:    contact.append(f'📞 {phone}')
    if github:   contact.append('GitHub')
    contact_html = ' &nbsp;|&nbsp; '.join(contact)

    sk = r.get('skills', {})
    skills_html = ''
    if sk.get('languages'): skills_html += f'<p><b>Languages/Backend:</b> {sk["languages"]}</p>'
    if sk.get('database'):  skills_html += f'<p><b>Database/Cloud:</b> {sk["database"]}</p>'
    if sk.get('tools'):     skills_html += f'<p><b>Tools:</b> {sk["tools"]}</p>'

    edu_html = ''
    for e in (r.get('education') or raw.get('edu') or []):
        inst   = e.get('inst','')
        degree = e.get('degree', e.get('deg',''))
        score  = e.get('score','')
        year   = e.get('year','')
        if inst:
            edu_html += f'''
            <div class="entry">
              <div class="row"><span class="bold">{inst}</span><span class="date">{year}</span></div>
              <div class="sub">{degree}{(" | "+score) if score else ""}</div>
            </div>'''

    exp_html = ''
    for e in (r.get('experience') or []):
        role    = e.get('role','')
        company = e.get('company','')
        dur     = e.get('duration','')
        bullets = ''.join(f'<li>{b}</li>' for b in (e.get('bullets') or []))
        title   = f'{role} — {company}' if company else role
        exp_html += f'''
        <div class="entry">
          <div class="row"><span class="bold">{title}</span><span class="date">{dur}</span></div>
          <ul>{bullets}</ul>
        </div>'''

    proj_html = ''
    for p in (r.get('projects') or []):
        bullets = ''.join(f'<li>{b}</li>' for b in (p.get('bullets') or []))
        proj_html += f'''
        <div class="entry">
          <div class="bold">{p.get("name","")}</div>
          <div class="tech">{p.get("tech","")}</div>
          <ul>{bullets}</ul>
        </div>'''

    profile_block = f'<div class="section"><div class="sec-title">PROFILE</div><p class="profile">{r["profile"]}</p></div>' if r.get('profile') else ''
    skills_block  = f'<div class="section"><div class="sec-title">TECHNICAL SKILLS</div>{skills_html}</div>' if skills_html else ''
    edu_block     = f'<div class="section"><div class="sec-title">EDUCATION</div>{edu_html}</div>' if edu_html else ''
    exp_block     = f'<div class="section"><div class="sec-title">INTERNSHIP</div>{exp_html}</div>' if exp_html else ''
    proj_block    = f'<div class="section"><div class="sec-title">PROJECTS</div>{proj_html}</div>' if proj_html else ''

    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body>
  <div class="name">{name}</div>
  <div class="contact">{contact_html}</div>
  {profile_block}{skills_block}{edu_block}{exp_block}{proj_block}
</body></html>'''


def _css() -> str:
    return '''
@page { size: A4; margin: 16mm 15mm 14mm 15mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 10.5pt; color: #111; line-height: 1.5; }
.name { text-align: center; font-size: 21pt; font-weight: bold; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 5pt; }
.contact { text-align: center; font-size: 9pt; color: #444; margin-bottom: 13pt; }
.section { margin-bottom: 11pt; }
.sec-title { font-size: 9.5pt; font-weight: bold; text-transform: uppercase; letter-spacing: 0.07em; border-bottom: 1.5pt solid #111; padding-bottom: 2pt; margin-bottom: 7pt; }
p { font-size: 10pt; margin: 2pt 0; }
.profile { font-size: 10pt; color: #222; line-height: 1.6; }
b { font-weight: bold; }
.entry { margin-bottom: 8pt; }
.row { display: flex; justify-content: space-between; }
.bold { font-weight: bold; font-size: 10pt; }
.date { font-size: 9.5pt; color: #555; }
.sub { font-size: 9.5pt; color: #444; margin-bottom: 3pt; }
.tech { font-size: 9pt; color: #666; font-style: italic; margin-bottom: 3pt; }
ul { padding-left: 13pt; margin: 2pt 0 0; }
li { font-size: 10pt; color: #222; margin-bottom: 2pt; }
'''
