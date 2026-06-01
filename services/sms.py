import os
import re

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


def validate_phone_number(phone: str) -> tuple[bool, str]:
    """
    Validate and normalize phone number.
    Returns (is_valid, normalized_phone)
    """
    # Remove any non-digit characters except +
    normalized = re.sub(r'[^\d+]', '', phone)
    
    # Check if it starts with +, if not add country code
    if not normalized.startswith('+'):
        if normalized.startswith('91'):
            normalized = '+' + normalized
        elif normalized.startswith('0'):
            normalized = '+91' + normalized[1:]
        else:
            normalized = '+91' + normalized
    
    # Check if phone is valid length (should be around 10-15 digits)
    digits_only = re.sub(r'\D', '', normalized)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False, normalized
    
    return True, normalized


def send_sms(to: str, message: str) -> dict:
    if not all([ACCOUNT_SID, AUTH_TOKEN, FROM_NUMBER]):
        print(f"[SMS SKIPPED] To: {to} | {message}")
        return {"status": "skipped", "reason": "Twilio not configured"}

    # Validate phone number
    is_valid, normalized_phone = validate_phone_number(to)
    if not is_valid:
        print(f"[SMS ERROR] Invalid phone number: {to} (normalized: {normalized_phone})")
        return {"status": "failed", "reason": f"Invalid phone number format: {to}"}

    try:
        from twilio.rest import Client
        
        print(f"[SMS ATTEMPT] Connecting to Twilio... To: {normalized_phone}")
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        
        print(f"[SMS ATTEMPT] Sending message from {FROM_NUMBER} to {normalized_phone}")
        msg = client.messages.create(body=message, from_=FROM_NUMBER, to=normalized_phone)
        
        # Check message status
        if msg and hasattr(msg, 'sid') and msg.sid:
            status_value = getattr(msg, 'status', 'sent')
            print(f"[SMS SUCCESS] To: {normalized_phone} | SID: {msg.sid} | Status: {status_value}")
            return {"status": "sent", "sid": msg.sid, "message_status": status_value}
        else:
            print(f"[SMS ERROR] Message created but no SID returned. To: {normalized_phone}")
            return {"status": "failed", "reason": "No SID returned from Twilio"}
            
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[SMS ERROR] {error_msg}")
        print(f"[SMS ERROR] To: {normalized_phone} | Message: {message[:50]}...")
        return {"status": "failed", "reason": error_msg}


def send_price_alert(farmer_name: str, phone: str, commodity: str, price: float, market: str) -> dict:
    message = (
        f"KrishiVani: Namaskara {farmer_name}! "
        f"{commodity} price at {market} is Rs.{price:.0f}/quintal today. "
        f"Plan your sell accordingly. - Krishi Vani Alerts & Prices"
    )
    return send_sms(phone, message)
