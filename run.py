import socket
import os
import uvicorn


def get_local_ip():
    """Finds the local IP address on the local network/Wi-Fi."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    local_ip = get_local_ip()

    print("\n" + "=" * 60)
    print("🚀 TRIP BUDGET MANAGER WEB APP")
    print("=" * 60)
    print(f"💻 Access from your PC / Browser : http://localhost:{port}")
    print(f"📱 Access from your Mobile Phone: http://{local_ip}:{port}")
    print("   (Ensure your phone and PC are connected to the same Wi-Fi)")
    print("=" * 60 + "\n")

    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
