import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY          = os.environ.get('SECRET_KEY', 'dev-change-this-in-prod')
    ANTHROPIC_API_KEY   = os.environ.get('ANTHROPIC_API_KEY', '')
    RAZORPAY_KEY_ID     = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
    # Price in paise: 9900 = ₹99
    PRICE_PAISE         = int(os.environ.get('PRICE_PAISE', 9900))
