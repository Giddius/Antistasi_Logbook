from keyring.backends.Windows import WinVaultKeyring


class WebdavKeyRing(WinVaultKeyring):

    priority = 1

    def set_password(self, service: str, username: str, password: str) -> None:
        return super().set_password(service, username, password)
