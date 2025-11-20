"""Модуль для работы с дисклеймерами и соглашениями."""

import json
from datetime import datetime, timezone
from pathlib import Path


class DisclaimerManager:
    """Менеджер дисклеймеров и пользовательских соглашений."""

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.agreements_file = self.storage_path / "user_agreements.json"
        self._load_agreements()

    def _load_agreements(self) -> None:
        """Загрузить соглашения пользователей."""
        if self.agreements_file.exists():
            try:
                with open(self.agreements_file, encoding="utf-8") as f:
                    self.agreements = json.load(f)
            except Exception:
                self.agreements = {}
        else:
            self.agreements = {}

    def _save_agreements(self) -> None:
        """Сохранить соглашения пользователей."""
        try:
            with open(self.agreements_file, "w", encoding="utf-8") as f:
                json.dump(self.agreements, f, ensure_ascii=False, indent=2)
        except Exception as e:
            from loguru import logger

            logger.error(f"Unexpected error: {e}")
            logger.error(f"Traceback: {e.__traceback__}")

    def has_user_agreed(self, user_id: str, version: str = "1.0") -> bool:
        """Проверить, согласился ли пользователь с дисклеймером."""
        user_agreement = self.agreements.get(user_id)
        if not user_agreement:
            return False

        return user_agreement.get("version") == version and user_agreement.get(
            "agreed", False,
        )

    def record_user_agreement(self, user_id: str, version: str = "1.0") -> None:
        """Записать согласие пользователя."""
        self.agreements[user_id] = {
            "agreed": True,
            "version": version,
            "agreed_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        self._save_agreements()

    def get_disclaimer_text(self) -> str:
        """Получить текст дисклеймера."""
        return """📋 **Важная информация**

🎓 **О расписаниях**
Данные получены из публичных источников СЗГМУ.
При важных решениях проверяйте информацию в деканате.

📚 **О регламентах**
Информация актуальна на момент добавления.
Официальные изменения отслеживайте на сайте университета.

🤝 **О проекте**
Бот создан студентами для помощи в учебе.
Мы стараемся поддерживать актуальность данных.

⚖️ **Ответственность**
Разработчики не несут ответственности за неточности.
Всегда сверяйтесь с официальными источниками."""

    def get_short_disclaimer(self) -> str:
        """Короткий дисклеймер для футеров."""
        return "ℹ️ Данные из открытых источников СЗГМУ • Проверяйте в деканате"

    def get_welcome_agreement(self) -> str:
        """Соглашение при первом запуске."""
        return """✅ **Добро пожаловать!**

📋 **Краткое соглашение:**
• Расписания берутся из публичных источников СЗГМУ
• При важных решениях проверяйте в деканате
• Бот создан студентами для помощи в учебе

Продолжая работу, вы соглашаетесь с условиями использования."""
