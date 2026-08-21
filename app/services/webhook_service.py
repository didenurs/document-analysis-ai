import httpx
from typing import Dict, Any

async def dispatch_webhook_event(webhook_url: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Harici sistemlere / Webhook adresine JSON olay bildirimi gönderir.
    """
    if not webhook_url or not webhook_url.startswith(("http://", "https://")):
        return {
            "success": False,
            "message": "Geçersiz Webhook URL adresi. URL 'http://' veya 'https://' ile başlamalıdır."
        }

    body = {
        "event_type": event_type,
        "timestamp": "2026-08-21T11:38:00Z",
        "service": "Doc Analysis AI (Faz 5 Engine)",
        "payload": payload
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(webhook_url, json=body)
            
        return {
            "success": response.is_success,
            "status_code": response.status_code,
            "message": f"Webhook bildirimi başarıyla iletildi (Durum Kodu: {response.status_code})" if response.is_success else f"Webhook sunucusu {response.status_code} hatası döndürdü."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Webhook çağrısı sırasında bağlantı hatası: {str(e)}"
        }
