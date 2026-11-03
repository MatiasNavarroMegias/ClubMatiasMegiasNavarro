import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> None:
    api_host = os.environ.get("REMINDER_API_URL", "").strip()
    secret = os.environ.get("REMINDER_INTERNAL_SECRET", "").strip()

    if not api_host:
        raise RuntimeError("REMINDER_API_URL no esta configurada.")
    if not secret:
        raise RuntimeError("REMINDER_INTERNAL_SECRET no esta configurada.")

    base_url = api_host if api_host.startswith(("http://", "https://")) else f"https://{api_host}"
    request = Request(
        f"{base_url.rstrip('/')}/internal/reminders",
        method="POST",
        headers={"X-Reminder-Secret": secret},
    )

    try:
        with urlopen(request, timeout=30) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"El endpoint de recordatorios devolvio HTTP {response.status}.")
    except HTTPError as error:
        raise RuntimeError(f"El endpoint de recordatorios devolvio HTTP {error.code}.") from error
    except URLError as error:
        raise RuntimeError("No se pudo conectar con la API de recordatorios.") from error


if __name__ == "__main__":
    main()
