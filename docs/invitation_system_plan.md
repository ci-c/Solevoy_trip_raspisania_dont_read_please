# План системы инвайтов и подписок

## Архитектура системы инвайтов

### 1. Модель данных

```python
@dataclass
class Invitation:
    code: str  # Уникальный код инвайта
    created_by: str  # user_id создателя
    created_at: datetime
    expires_at: Optional[datetime]  # None = бессрочный
    max_uses: Optional[int]  # None = неограниченно
    current_uses: int = 0
    is_active: bool = True
    subscription_level: str = "basic"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass  
class UserInvitation:
    user_id: str
    invitation_code: str
    used_at: datetime
    invited_by: str
```

### 2. Уровни доступа

#### Гостевой доступ (guest)
- Только просмотр справочной информации об аттестации
- Разовый поиск расписаний (ограниченно)
- Уведомление о необходимости инвайта

#### Базовый доступ (basic) - по инвайту
- Создание профиля студента
- Полный функционал дневника и оценок
- Неограниченный поиск расписаний
- Система заявлений
- Расчет ОСБ/КНЛ/КНС

#### Тестерский доступ (tester)
- Все функции basic
- Доступ к экспериментальным функциям
- Расширенная статистика
- Приоритетная техподдержка
- Возможность создавать 3 инвайта в месяц

#### Админский доступ (admin)
- Все функции tester
- Управление инвайтами (создание, удаление, статистика)
- Просмотр статистики пользователей
- Управление пользователями
- Неограниченное создание инвайтов
- Доступ к логам и аналитике

### 3. Система генерации инвайтов

```python
class InvitationManager:
    def generate_invitation(
        self, 
        creator_id: str, 
        subscription_level: str = "basic",
        expires_in_days: Optional[int] = None,
        max_uses: Optional[int] = None
    ) -> str
    
    def validate_invitation(self, code: str) -> bool
    
    def use_invitation(self, code: str, user_id: str) -> bool
    
    def get_user_invitations(self, user_id: str) -> List[Invitation]
    
    def get_invitation_stats(self, user_id: str) -> Dict[str, Any]
```

### 4. Интеграция в бот

#### Middleware для проверки доступа
```python
class AccessControlMiddleware:
    async def __call__(self, handler, event, data):
        user_id = str(event.from_user.id)
        user_level = await self.get_user_access_level(user_id)
        
        # Проверяем доступ к функциям
        if not self.check_access(handler, user_level):
            await self.show_access_denied(event)
            return
            
        data['user_access_level'] = user_level
        return await handler(event, data)
```

#### Новые состояния FSM
```python
class InvitationStates(StatesGroup):
    entering_code = State()
    viewing_invitations = State()
    creating_invitation = State()
    managing_users = State()  # Только для админов
```

## Архитектура уровней подписок

### 1. Модель пользователя с подпиской

```python
@dataclass
class UserSubscription:
    user_id: str
    level: str  # "guest", "basic", "tester", "admin"
    granted_at: datetime
    granted_by: str  # user_id того, кто предоставил доступ
    expires_at: Optional[datetime]  # None = бессрочно
    features: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2. Система ограничений по функциям

```python
FEATURE_PERMISSIONS = {
    "guest": [
        "view_attestation_info",
        "limited_schedule_search"  # До 3 поисков в день
    ],
    "basic": [
        "create_profile",
        "full_diary",
        "unlimited_schedule_search", 
        "applications_system",
        "grade_calculator"
    ],
    "tester": [
        "all_basic_features",
        "experimental_features",
        "advanced_statistics",
        "create_invitations",  # До 3 в месяц
        "priority_support"
    ],
    "admin": [
        "all_tester_features",
        "user_management",
        "invitation_management",
        "system_analytics",
        "unlimited_invitations",
        "access_logs"
    ]
}
```

### 3. Декораторы для проверки доступа

```python
def require_access_level(min_level: str):
    def decorator(handler):
        async def wrapper(message, state, **kwargs):
            user_level = kwargs.get('user_access_level', 'guest')
            
            if not AccessChecker.has_access(user_level, min_level):
                await message.answer("🚫 Недостаточно прав доступа")
                return
                
            return await handler(message, state, **kwargs)
        return wrapper
    return decorator

def require_feature(feature_name: str):
    def decorator(handler):
        async def wrapper(message, state, **kwargs):
            user_level = kwargs.get('user_access_level', 'guest')
            
            if not AccessChecker.has_feature(user_level, feature_name):
                await message.answer("🚫 Функция недоступна для вашего уровня доступа")
                return
                
            return await handler(message, state, **kwargs)
        return wrapper
    return decorator
```

## UX для инвайт-системы

### 1. Для новых пользователей (guest)

```
🎓 Добро пожаловать в СЗГМУ Бот!

👀 Доступно в режиме просмотра:
• Справочник по аттестации
• Разовый поиск расписаний (3 в день)

🔑 Для полного доступа нужен инвайт-код
[Ввести код] [Запросить доступ]
```

### 2. Ввод инвайт-кода

```
🔑 Введите инвайт-код:

Код можно получить от действующего пользователя
или администратора бота.

[Отмена]
```

### 3. Успешная активация

```
✅ Инвайт-код активирован!

🎉 Теперь доступны все функции:
• Персональный профиль
• Дневник и оценки  
• Расчет ОСБ/КНЛ/КНС
• Система заявлений

[Настроить профиль] [Главное меню]
```

### 4. Управление инвайтами (для тестеров/админов)

```
🔑 Мои инвайты

📊 Статистика:
• Создано: 5
• Использовано: 3
• Доступно: 2 (лимит: 3/мес)

[Создать инвайт] [История] [Настройки]
```

## Этапы внедрения

### Этап 1: Базовая система инвайтов
1. Создать модели данных
2. Реализовать InvitationManager
3. Добавить middleware проверки доступа
4. Базовый UX для ввода кодов

### Этап 2: Уровни подписок  
1. Реализовать UserSubscription
2. Добавить декораторы доступа
3. Интегрировать в существующие обработчики
4. Создать админ-панель

### Этап 3: Расширенное управление
1. Статистика и аналитика
2. Автоматическое управление истечением
3. Система уведомлений
4. API для внешних интеграций

### Этап 4: Монетизация (опционально)
1. Премиум-подписки с расширенными лимитами
2. Интеграция платежных систем
3. Реферальная система
4. Корпоративные аккаунты для деканатов

## Технические детали

### Хранение данных
- SQLite для инвайтов и подписок
- JSON для кэширования уровней доступа
- Redis для rate limiting (опционально)

### Безопасность  
- Хеширование инвайт-кодов
- Rate limiting на создание инвайтов
- Логирование всех действий с доступом
- Валидация прав на каждом запросе

### Мониторинг
- Метрики использования по уровням
- Статистика активации инвайтов
- Трекинг популярных функций
- Система алертов для админов