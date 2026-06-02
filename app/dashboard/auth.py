"""Autenticacao usando streamlit-authenticator.

Le credenciais de st.secrets["auth"] (configurado no Streamlit Cloud).
Estrutura esperada em .streamlit/secrets.toml:

    [auth]
    cookie_name = "auralab_auth"
    cookie_key  = "<chave aleatoria longa>"
    cookie_days = 7

    [auth.usuarios.caio_ferreira]
    nome  = "Caio Leite Brandao Ferreira"
    email = "caio.ferreira@auraminerals.com"
    senha = "<hash bcrypt>"
    perfil = "admin"

    [auth.usuarios.relyson]
    nome  = "Relyson Oliveira"
    email = "..."
    senha = "<hash bcrypt>"
    perfil = "user"
"""
from __future__ import annotations

import streamlit as st


def _carregar_config() -> dict | None:
    """Le secrets.toml com a config de autenticacao."""
    try:
        auth = st.secrets["auth"]
    except (KeyError, FileNotFoundError):
        return None

    credentials = {"usernames": {}}
    for username, info in auth.get("usuarios", {}).items():
        credentials["usernames"][username] = {
            "name": info.get("nome", username),
            "email": info.get("email", ""),
            "password": info.get("senha", ""),
            "roles": [info.get("perfil", "user")],
        }
    return {
        "credentials": credentials,
        "cookie_name": auth.get("cookie_name", "auralab_auth"),
        "cookie_key": auth.get("cookie_key", "MUDE_ESTA_CHAVE"),
        "cookie_days": int(auth.get("cookie_days", 7)),
    }


def login_obrigatorio() -> tuple[str, str] | None:
    """Tela de login bloqueando o app. Retorna (username, nome) se OK; None se nao.

    Se nao houver secrets configurados, libera o acesso (modo local sem login).
    """
    cfg = _carregar_config()
    if cfg is None:
        # Sem secrets configurados (rodando localmente sem login) -- libera.
        return ("local", "Usuario Local")

    import streamlit_authenticator as stauth

    authenticator = stauth.Authenticate(
        cfg["credentials"],
        cfg["cookie_name"],
        cfg["cookie_key"],
        cfg["cookie_days"],
    )

    # Tela de login centralizada
    authenticator.login(
        location="main",
        fields={
            "Form name": "AuraLab Borborema",
            "Username": "Usuário",
            "Password": "Senha",
            "Login": "Entrar",
        },
    )

    auth_status = st.session_state.get("authentication_status")
    nome = st.session_state.get("name")
    username = st.session_state.get("username")

    if auth_status is False:
        st.error("❌ Usuário ou senha inválidos.")
        st.stop()
    elif auth_status is None:
        st.warning("Faça login para acessar.")
        st.stop()

    # Sucesso -- mostra botao de logout na sidebar e devolve identidade
    with st.sidebar:
        authenticator.logout("Sair", "sidebar", key="logout_btn")
        st.markdown(
            f'<div style="color:#fff; font-size:10pt; padding:4px 0;">'
            f'👤 <strong>{nome}</strong></div>',
            unsafe_allow_html=True,
        )

    return (username, nome)
