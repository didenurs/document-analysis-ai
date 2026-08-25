import socket
import ipaddress
from urllib.parse import urlparse
import httpx
from typing import Dict, Any, Tuple
from datetime import datetime, timezone

def is_safe_webhook_url(url: str) -> Tuple[bool, str]:
    """
    SSRF (Server-Side Request Forgery) koruması:
    URL'nin private/loopback IP veya cloud metadata adresine gitmesini engeller.
    """
    if not url:
        return False, "Webhook URL adresi boş olamaz."

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Geçersiz URL formatı."

    if parsed.scheme not in ("http", "https"):
        return False, "Geçersiz şema. Yalnızca 'http' veya 'https' desteklenir."

    hostname = parsed.hostname
    if not hostname:
        return False, "Geçersiz sunucu adı (hostname)."

    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return False, "Güvenlik Engeli (SSRF Koruması): Yerel sunucu adreslerine webhook gönderilemez."

    try:
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)

        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
            return False, f"Güvenlik Engeli (SSRF Koruması): Hedef IP adresi ({ip_str}) iç ağ veya korumalı blokta yer alıyor."
    except socket.gaierror:
        return False, f"Sunucu adı ({hostname}) DNS tarafından çözümlenemedi."
    except Exception as e:
        return False, f"URL doğrulama hatası: {str(e)}"

    return True, ""


async def dispatch_webhook_event(webhook_url: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Harici sistemlere / Webhook adresine JSON olay bildirimi gönderir.
    SSRF koruması ile kısıtlı ağlara erişim engellenir.
    """
    is_safe, error_msg = is_safe_webhook_url(webhook_url)
    if not is_safe:
        return {
            "success": False,
            "message": error_msg
        }

    body = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
