from flask import Blueprint, render_template, request, jsonify, send_file, session, current_app
import anthropic
import json
import io
import time
import hmac
import hashlib

main = Blueprint('main', __name__)


# ─────────────────────────────────────────────
#  PAGES
# ─────────────────────────────────────────────

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/builder')
def builder():
    return render_template('builder.html')


# ─────────────────────────────────────────────
#  AI GENERATION
# ─────────────────────────────────────────────

def build_prompt(data: dict) -> str:
    return f"""You are an expert resume writer for Indian software engineering freshers.

Given the raw user data below, return ONLY a valid JSON object. No markdown, no backticks, no explanation — just the JSON.

Required JSON structure:
{{
  "profile": "2-3 sentence professional summary. Strong action verbs. Specific tech names. End with target job goal.",
  "skills": {{
    "languages": "exact value from input",
    "database": "exact value from input",
    "tools": "exact value from input"
  }},
  "education": [
    {{"inst": "...", "degree": "...", "score": "...", "year": "..."}}
  ],
  "experience": [
    {{
      "role": "Job Title",
      "company": "Company Name",
      "duration": "Mon YYYY – Mon YYYY",
      "bullets": ["Action verb + what + impact/metric", "..."]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "tech": "Tech1 | Tech2 | Tech3",
      "bullets": ["Action verb + what built + impact", "..."]
    }}
  ]
}}

RULES:
- Profile: 2-3 tight sentences, no fluff, real tech names, target role at end
- Every bullet must start with a strong past-tense action verb: Built, Designed, Optimised, Implemented, Developed, Reduced, Achieved, Integrated, Automated, Deployed
- Keep all numbers, percentages, metrics exactly as given
- Keep all tech stack names exactly as given
- Experience: 4-5 bullets each
- Projects: 3 bullets each

USER DATA:
Name: {data.get('name','')}
Target Role: {data.get('target_role','Software Engineer')}
Profile Notes: {data.get('profile_raw','')}
Skills - Languages: {data.get('skills_lang','')}
Skills - DB/Cloud: {data.get('skills_db','')}
Skills - Tools: {data.get('skills_tools','')}
Education: {json.dumps(data.get('edu',[]))}
Experience: {json.dumps(data.get('exp',[]))}
Projects: {json.dumps(data.get('proj',[]))}
"""

@main.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400

    api_key = current_app.config.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'ANTHROPIC_API_KEY not set on server'}), 500

    try:
        client  = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model      = 'claude-opus-4-5',
            max_tokens = 1500,
            messages   = [{'role': 'user', 'content': build_prompt(data)}]
        )
        raw = message.content[0].text.strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        resume_json = json.loads(raw)

        # Cache in session for PDF route
        session['resume_data'] = data
        session['resume_json'] = resume_json
        session['paid']        = False

        return jsonify({'success': True, 'resume': resume_json})

    except json.JSONDecodeError:
        return jsonify({'error': 'AI returned invalid JSON. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
#  PAYMENT (Razorpay)
# ─────────────────────────────────────────────

@main.route('/api/create-order', methods=['POST'])
def create_order():
    key_id     = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')

    # Dev mode: no Razorpay keys → skip payment
    if not key_id or not key_secret:
        return jsonify({'dev_mode': True})

    try:
        import razorpay
        client = razorpay.Client(auth=(key_id, key_secret))
        order  = client.order.create({
            'amount'         : current_app.config['PRICE_PAISE'],
            'currency'       : 'INR',
            'payment_capture': 1
        })
        return jsonify({
            'order_id': order['id'],
            'amount'  : order['amount'],
            'key'     : key_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main.route('/api/verify-payment', methods=['POST'])
def verify_payment():
    data       = request.get_json()
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', '')

    body     = data['razorpay_order_id'] + '|' + data['razorpay_payment_id']
    expected = hmac.new(key_secret.encode(), body.encode(), hashlib.sha256).hexdigest()

    if expected == data.get('razorpay_signature', ''):
        session['paid']       = True
        session['payment_id'] = data['razorpay_payment_id']
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Signature mismatch'}), 400


# ─────────────────────────────────────────────
#  PDF DOWNLOAD
# ─────────────────────────────────────────────

@main.route('/api/download-pdf', methods=['POST'])
def download_pdf():
    razorpay_configured = bool(current_app.config.get('RAZORPAY_KEY_ID'))

    # Block if payment required but not done
    if razorpay_configured and not session.get('paid'):
        return jsonify({'error': 'Payment required'}), 402

    body      = request.get_json() or {}
    raw_data  = body.get('raw_data',  session.get('resume_data', {}))
    resume    = body.get('resume',    session.get('resume_json', {}))

    if not resume:
        return jsonify({'error': 'No resume data. Please generate first.'}), 400

    try:
        from utils.pdf_generator import generate_pdf
        pdf_bytes = generate_pdf(raw_data, resume)
        filename  = (raw_data.get('name', 'Resume') or 'Resume').replace(' ', '_') + '_Resume.pdf'
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype        = 'application/pdf',
            as_attachment   = True,
            download_name   = filename
        )
    except Exception as e:
        return jsonify({'error': f'PDF error: {str(e)}'}), 500
