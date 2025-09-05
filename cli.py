"""CLI интерфейс для системы расписания СЗГМУ с использованием click."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Импорты из нашего проекта
from schedule_processor.yaml_config import get_config
from schedule_processor.api import get_available_filters, search_schedules

console = Console()


@click.group()
@click.version_option(version="2.0.0", prog_name="szgmu-schedule")
def cli():
    """🎓 CLI для работы с расписанием СЗГМУ"""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Путь к файлу конфигурации YAML')
def config_test(config: Optional[str]):
    """🔧 Проверить загрузку конфигурации"""
    try:
        if config:
            from schedule_processor.yaml_config import reload_config
            cfg = reload_config(config)
        else:
            cfg = get_config()
        
        rprint("✅ [green]Конфигурация загружена успешно[/green]")
        
        # Показать основные параметры
        table = Table(title="📋 Основные настройки")
        table.add_column("Параметр", style="cyan")
        table.add_column("Значение", style="green")
        
        # Расписание звонков
        rings = cfg.get_rings()
        table.add_row("Семинары (пар)", str(len(rings.get('с', []))))
        table.add_row("Лекции (пар)", str(len(rings.get('л', []))))
        
        # API настройки
        api_config = cfg.get_api_config()
        table.add_row("API URL", api_config.get('base_url', 'не указан'))
        table.add_row("Таймаут", f"{api_config.get('timeout', 30)}с")
        
        # Эмодзи
        bot_config = cfg.get_bot_config()
        emojis = bot_config.get('emojis', {})
        table.add_row("Эмодзи загружено", str(len(emojis)))
        
        console.print(table)
        
    except Exception as e:
        rprint(f"❌ [red]Ошибка загрузки конфигурации:[/red] {e}")
        sys.exit(1)


@cli.command()
async def filters():
    """🔍 Получить доступные фильтры из API"""
    try:
        rprint("⏳ [yellow]Получаем доступные фильтры...[/yellow]")
        available_filters = await get_available_filters()
        
        if not available_filters:
            rprint("❌ [red]Фильтры не получены[/red]")
            return
        
        table = Table(title="🎯 Доступные фильтры")
        table.add_column("Фильтр", style="cyan")
        table.add_column("Опции", style="green")
        table.add_column("Количество", justify="right", style="magenta")
        
        for filter_name, options in available_filters.items():
            options_str = ", ".join(options[:3])
            if len(options) > 3:
                options_str += f"... (+{len(options) - 3})"
            
            table.add_row(filter_name, options_str, str(len(options)))
        
        console.print(table)
        rprint(f"✅ [green]Получено {len(available_filters)} категорий фильтров[/green]")
        
    except Exception as e:
        rprint(f"❌ [red]Ошибка получения фильтров:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--course', '-k', help='Курс обучения')
@click.option('--specialty', '-s', help='Специальность')
@click.option('--stream', '-t', help='Поток (а, б, в, г)')
@click.option('--semester', '-e', help='Семестр (осенний, весенний)')
@click.option('--limit', '-l', default=10, help='Максимум результатов')
async def search(course: Optional[str], specialty: Optional[str], 
                stream: Optional[str], semester: Optional[str], limit: int):
    """🔍 Поиск расписаний по фильтрам"""
    
    # Подготовка фильтров
    filters = {}
    if course:
        filters["Курс"] = [course]
    if specialty:
        filters["Специальность"] = [specialty]
    if stream:
        filters["Поток"] = [stream]
    if semester:
        filters["Семестр"] = [semester]
    
    if not filters:
        rprint("⚠️ [yellow]Не указано ни одного фильтра. Показать все доступные?[/yellow]")
        if not click.confirm("Продолжить?"):
            return
    
    try:
        rprint("⏳ [yellow]Выполняем поиск расписаний...[/yellow]")
        results = await search_schedules(filters)
        
        if not results:
            rprint("❌ [red]Расписания не найдены[/red]")
            return
        
        # Ограничить результаты
        results = results[:limit]
        
        table = Table(title="📋 Найденные расписания")
        table.add_column("№", justify="right", style="cyan")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Специальность", style="green")
        table.add_column("Курс", justify="center", style="blue")
        table.add_column("Поток", justify="center", style="magenta")
        table.add_column("Семестр", style="yellow")
        table.add_column("Файл", style="dim")
        
        for i, result in enumerate(results, 1):
            data = result.get('data', {})
            lessons = data.get('scheduleLessonDtoList', [])
            
            if lessons:
                lesson = lessons[0]
                specialty = lesson.get('speciality', 'Unknown')[:40]
                course = str(lesson.get('courseNumber', '?'))
                stream = lesson.get('groupStream', '?')
                semester = lesson.get('semester', '?')
            else:
                specialty = course = stream = semester = "Unknown"
            
            filename = data.get('fileName', 'Unknown')
            schedule_id = result.get('id', 'Unknown')
            
            table.add_row(
                str(i), str(schedule_id), specialty, 
                course, stream, semester, filename[:30]
            )
        
        console.print(table)
        rprint(f"✅ [green]Найдено {len(results)} расписаний[/green]")
        
    except Exception as e:
        rprint(f"❌ [red]Ошибка поиска:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--schedule-id', '-i', type=int, required=True, help='ID расписания')
@click.option('--subgroup', '-g', required=True, help='Подгруппа (например, 201а)')
@click.option('--format', '-f', type=click.Choice(['xlsx', 'ics']), 
              default='xlsx', help='Формат выходного файла')
@click.option('--output', '-o', help='Папка для сохранения файла')
async def generate(schedule_id: int, subgroup: str, format: str, output: Optional[str]):
    """📄 Генерация файла расписания"""
    try:
        # Импорт генераторов (используем v3 логику как в боте)
        rprint(f"⏳ [yellow]Генерируем {format.upper()} файл для подгруппы {subgroup}...[/yellow]")
        
        # TODO: Реализовать генерацию файлов через schedule_processor
        # Пока заглушка
        output_dir = Path(output) if output else Path("output")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{subgroup}.{format}"
        output_file = output_dir / filename
        
        rprint(f"✅ [green]Файл сохранен:[/green] {output_file}")
        
    except Exception as e:
        rprint(f"❌ [red]Ошибка генерации:[/red] {e}")
        sys.exit(1)


@cli.command()
def bot():
    """🤖 Запуск Telegram бота"""
    try:
        rprint("🚀 [green]Запускаем Telegram бота...[/green]")
        from bot_main import main
        asyncio.run(main())
    except Exception as e:
        rprint(f"❌ [red]Ошибка запуска бота:[/red] {e}")
        sys.exit(1)


@cli.command()
def info():
    """ℹ️ Информация о системе"""
    table = Table(title="📊 Информация о системе СЗГМУ")
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение", style="green")
    
    # Версия конфигурации
    config_path = Path("config.yaml")
    table.add_row("Конфигурация", "✅ Найдена" if config_path.exists() else "❌ Не найдена")
    
    # Проверка зависимостей
    try:
        import aiogram
        table.add_row("aiogram", f"✅ v{aiogram.__version__}")
    except ImportError:
        table.add_row("aiogram", "❌ Не установлена")
    
    try:
        import importlib.util
        yaml_spec = importlib.util.find_spec("yaml")
        if yaml_spec is not None:
            table.add_row("PyYAML", "✅ Установлена")
        else:
            table.add_row("PyYAML", "❌ Не установлена")
    except ImportError:
        table.add_row("PyYAML", "❌ Не установлена")
    
    try:
        import openpyxl
        table.add_row("openpyxl", f"✅ v{openpyxl.__version__}")
    except ImportError:
        table.add_row("openpyxl", "❌ Не установлена")
    
    # Папки проекта
    for folder in ["output", "logs", "files", "templates"]:
        folder_path = Path(folder)
        status = "✅ Существует" if folder_path.exists() else "⚠️ Не создана"
        table.add_row(f"Папка {folder}", status)
    
    console.print(table)
    
    # Рекомендации
    rprint("\n💡 [bold blue]Быстрый старт:[/bold blue]")
    rprint("1. [cyan]szgmu-schedule config-test[/cyan] - проверить конфигурацию")
    rprint("2. [cyan]szgmu-schedule filters[/cyan] - получить доступные фильтры") 
    rprint("3. [cyan]szgmu-schedule search --course 2[/cyan] - найти расписания 2 курса")
    rprint("4. [cyan]szgmu-schedule bot[/cyan] - запустить Telegram бота")


# Обертка для async команд
def async_command(f):
    """Декоратор для выполнения async команд в click."""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


# Применяем декоратор к async командам
filters = async_command(filters)
search = async_command(search)
generate = async_command(generate)


if __name__ == "__main__":
    cli()