"""Camada de leitura de emails do Outlook.

Interface abstrata para que possamos trocar a implementacao (pywin32 -> Microsoft
Graph API) sem mexer no resto do sistema. Veja PRD secao 7.3.

A implementacao v1 (OutlookDesktopSource) usa COM via pywin32 e exige:
- Outlook desktop instalado e logado
- O PC do Caio ligado e com o Outlook aberto
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

from loguru import logger

from .config import DOMINIOS_LAB, PASTA_LABORATORIO, INBOX_PRINCIPAL


@dataclass
class EmailMessage:
    """Representacao agnostica de um email coletado."""
    entry_id: str               # ID unico do Outlook (idempotencia)
    subject: str
    sender_email: str
    received_at: datetime
    body_text: str
    attachments: list["EmailAttachment"] = field(default_factory=list)
    folder_name: str = ""


@dataclass
class EmailAttachment:
    filename: str
    size_bytes: int
    # bytes do arquivo. Para a v1 salvamos imediatamente em disco e nao
    # carregamos tudo em memoria para emails grandes -- por isso o save_to.
    save_to: callable | None = None  # funcao que recebe Path e salva


# -----------------------------------------------------------------------------
class EmailSource(ABC):
    """Interface abstrata para fontes de email."""

    @abstractmethod
    def fetch_unprocessed(
        self,
        since: datetime | None = None,
        already_processed_ids: set[str] | None = None,
    ) -> Iterator[EmailMessage]:
        """Itera emails que ainda nao foram processados.

        Args:
            since: data minima de recebimento (None = sem limite).
            already_processed_ids: entry_ids ja processados (para dedup).
        """
        raise NotImplementedError


# -----------------------------------------------------------------------------
class OutlookDesktopSource(EmailSource):
    """Le emails do Outlook desktop via COM (pywin32).

    Usa MAPI namespace. Itera as pastas configuradas (laboratorio + inbox
    principal para pegar emails de Bullion que nao caem na pasta filtrada).
    """

    # Constantes do Outlook (https://learn.microsoft.com/en-us/office/vba/api/outlook)
    _OL_MAIL_ITEM = 43  # MailItem class
    _OL_FOLDER_INBOX = 6
    _OL_NAMESPACE = "MAPI"

    def __init__(
        self,
        pastas: list[str] | None = None,
        dominios_aceitos: tuple[str, ...] = DOMINIOS_LAB,
    ):
        self.pastas = pastas or [PASTA_LABORATORIO, INBOX_PRINCIPAL]
        self.dominios_aceitos = tuple(d.lower() for d in dominios_aceitos)
        self._outlook = None
        self._namespace = None

    # --- API pyblica ---------------------------------------------------------
    def fetch_unprocessed(
        self,
        since: datetime | None = None,
        already_processed_ids: set[str] | None = None,
    ) -> Iterator[EmailMessage]:
        already_processed_ids = already_processed_ids or set()
        self._connect()

        for pasta_nome in self.pastas:
            folder = self._find_folder(pasta_nome)
            if folder is None:
                logger.warning(f"Pasta nao encontrada no Outlook: {pasta_nome!r}")
                continue

            count = 0
            yielded = 0
            for item in self._iter_folder_items(folder, since):
                count += 1
                if not self._is_mail_item(item):
                    continue
                entry_id = getattr(item, "EntryID", None)
                if not entry_id or entry_id in already_processed_ids:
                    continue
                sender = self._extract_sender_email(item) or ""
                if not self._is_lab_domain(sender):
                    continue

                msg = self._build_message(item, pasta_nome)
                yielded += 1
                yield msg

            logger.info(
                f"Pasta {pasta_nome!r}: {count} itens varridos, {yielded} elegiveis."
            )

    # --- Helpers internos ----------------------------------------------------
    def _connect(self):
        if self._outlook is not None:
            return
        import win32com.client  # import local para nao quebrar testes em outros OS

        self._outlook = win32com.client.Dispatch("Outlook.Application")
        self._namespace = self._outlook.GetNamespace(self._OL_NAMESPACE)
        logger.debug("Conectado ao Outlook desktop via COM.")

    def _find_folder(self, nome: str):
        """Procura pasta no Inbox raiz e subpastas (Caixa de Entrada como fallback)."""
        # Tenta Inbox raiz (nome em PT-BR)
        try:
            inbox = self._namespace.GetDefaultFolder(self._OL_FOLDER_INBOX)
        except Exception as e:
            logger.error(f"Falha ao obter Inbox: {e}")
            return None

        # Inbox principal
        if nome.lower() in ("caixa de entrada", "inbox", inbox.Name.lower()):
            return inbox

        # Procura subpasta direta
        try:
            for sub in inbox.Folders:
                if sub.Name == nome:
                    return sub
        except Exception as e:
            logger.error(f"Falha ao iterar subpastas do Inbox: {e}")
        return None

    def _iter_folder_items(self, folder, since: datetime | None):
        """Itera itens da pasta usando Restrict() para nao explodir memoria.

        Outlook itera a colecao inteira sob demanda, mas em pastas grandes
        (> 4000 itens) acessar propriedades de cada item causa erro de memoria.
        Restrict() filtra dentro do proprio Outlook (server-side), o que e
        muito mais eficiente.
        """
        items = folder.Items
        try:
            items.Sort("[ReceivedTime]", True)  # True = descending
        except Exception:
            pass

        if since is not None:
            # Formato Outlook (US locale): MM/DD/YYYY HH:MM AM/PM
            filtro = (
                f"[ReceivedTime] >= '{since.strftime('%m/%d/%Y %I:%M %p')}'"
            )
            try:
                items = items.Restrict(filtro)
            except Exception as e:
                logger.warning(f"Falha ao aplicar Restrict({filtro!r}): {e}. "
                               "Vai iterar tudo (pode ser lento).")

        # GetFirst/GetNext e mais robusto que 'for' para colecoes grandes
        item = items.GetFirst()
        while item is not None:
            yield item
            item = items.GetNext()

    def _is_mail_item(self, item) -> bool:
        try:
            return item.Class == self._OL_MAIL_ITEM
        except Exception:
            return False

    def _extract_sender_email(self, item) -> str | None:
        """Tenta varios atributos do Outlook para obter o email do remetente.

        SenderEmailAddress as vezes vem como caminho LDAP em ambientes Exchange;
        nesse caso usamos SenderEmailType + Sender.GetExchangeUser() como fallback.
        """
        # Tentativa direta
        try:
            sender = item.SenderEmailAddress
            if sender and "@" in sender:
                return sender.lower()
        except Exception:
            pass

        # Fallback Exchange
        try:
            sender_obj = item.Sender
            if sender_obj is not None:
                try:
                    exchange_user = sender_obj.GetExchangeUser()
                    if exchange_user is not None:
                        primary = exchange_user.PrimarySmtpAddress
                        if primary and "@" in primary:
                            return primary.lower()
                except Exception:
                    pass
        except Exception:
            pass

        return None

    def _is_lab_domain(self, sender_email: str) -> bool:
        sender_email = sender_email.lower()
        return any(sender_email.endswith(d) for d in self.dominios_aceitos)

    def _build_message(self, item, folder_name: str) -> EmailMessage:
        entry_id = item.EntryID
        subject = str(item.Subject or "")
        sender = self._extract_sender_email(item) or ""
        try:
            received = item.ReceivedTime
            # pywin32 retorna pywintypes.datetime; converter para datetime padrao
            received_at = datetime(
                received.year, received.month, received.day,
                received.hour, received.minute, received.second,
            )
        except Exception:
            received_at = datetime.now()

        try:
            body = str(item.Body or "")
        except Exception:
            body = ""

        attachments: list[EmailAttachment] = []
        try:
            for att in item.Attachments:
                filename = str(att.FileName)
                size = int(getattr(att, "Size", 0))
                # Captura referencia para save posterior
                def _save_to(path: Path, _att=att) -> Path:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    _att.SaveAsFile(str(path))
                    return path
                attachments.append(
                    EmailAttachment(
                        filename=filename,
                        size_bytes=size,
                        save_to=_save_to,
                    )
                )
        except Exception as e:
            logger.warning(f"Falha ao iterar anexos do email {subject!r}: {e}")

        return EmailMessage(
            entry_id=entry_id,
            subject=subject,
            sender_email=sender,
            received_at=received_at,
            body_text=body,
            attachments=attachments,
            folder_name=folder_name,
        )
