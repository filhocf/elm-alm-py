"""CLI for elm-alm-py — credential setup and testing."""

import base64
import getpass
import json
import os
import sys

import httpx

CRED_FILE = os.path.expanduser("~/.elm_creds.json")


def login():
    """Authenticate to ELM and save credentials."""
    url = input("ELM URL (e.g. https://elm.example.com): ").strip()
    if not url:
        print("❌ ELM URL is required.")
        sys.exit(1)
    username = input("Usuário ELM (LDAP): ").strip()
    password = getpass.getpass("Senha ELM: ")

    print(f"\nTestando autenticação em {url}...")
    try:
        client = httpx.Client(verify=False, timeout=30, follow_redirects=True)
        resp = client.post(
            f"{url}/jts/j_security_check",
            data={"j_username": username, "j_password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if "X-com-ibm-team-repository-web-auth-msg" in resp.headers:
            print("❌ Autenticação falhou. Verifique usuário/senha.")
            sys.exit(1)

        # Validate by fetching rootservices
        resp = client.get(f"{url}/ccm/rootservices", headers={"Accept": "application/rdf+xml"})
        if resp.status_code != 200:
            print(f"❌ Rootservices retornou {resp.status_code}")
            sys.exit(1)

        print("✅ Autenticação OK!")
    except httpx.ConnectError as e:
        print(f"❌ Erro de conexão: {e}")
        sys.exit(1)
    finally:
        client.close()

    # Save credentials
    creds = {
        "url": url,
        "username": username,
        "password": base64.b64encode(password.encode()).decode(),
    }

    with open(CRED_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    os.chmod(CRED_FILE, 0o600)

    print(f"✅ Credenciais salvas em {CRED_FILE} (senha em base64, chmod 600)")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        login()
    elif len(sys.argv) < 2 or sys.argv[1] == "serve":
        from .server import main as serve

        serve()
    else:
        print("Uso: elm-alm-py [login|serve]")
        sys.exit(1)


if __name__ == "__main__":
    main()
