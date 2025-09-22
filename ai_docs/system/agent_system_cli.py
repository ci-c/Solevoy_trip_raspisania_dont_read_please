from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

SCRIPT_PATH = Path(__file__).resolve()
SYSTEM_DIR = SCRIPT_PATH.parent
AI_DOCS_DIR = SYSTEM_DIR.parent
REPO_ROOT = AI_DOCS_DIR.parent
STATE_DIR = AI_DOCS_DIR / "state"
AGENT_DIR = STATE_DIR / "agents"
LOCKS_DIR = STATE_DIR / "locks"
AGENT_STATE_FILE = STATE_DIR / "agent_state.yaml"
TASKS_FILE = STATE_DIR / "tasks.yaml"
POLICIES_FILE = SYSTEM_DIR / "agent_policies.yaml"
TODO_FILE = REPO_ROOT / "todo.txt"
LOGS_DIR = REPO_ROOT / "logs"

STATE_TEMPLATE = {"agents": [], "role_assignments": [], "queue": []}
TASKS_TEMPLATE = {"tasks": []}


def error(message: str) -> None:
    print(message)
    sys.exit(1)


def load_yaml(path: Path, default: Optional[Dict] = None) -> Dict:
    if not path.exists():
        return default.copy() if default else {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return default.copy() if default else {}
    return data


def save_yaml(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _ensure_directories() -> None:
    for directory in (STATE_DIR, AGENT_DIR, LOCKS_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    if not AGENT_STATE_FILE.exists():
        save_yaml(AGENT_STATE_FILE, STATE_TEMPLATE)
    if not TASKS_FILE.exists():
        save_yaml(TASKS_FILE, TASKS_TEMPLATE)


def load_state() -> Dict:
    return load_yaml(AGENT_STATE_FILE, STATE_TEMPLATE)


def save_state(state: Dict) -> None:
    save_yaml(AGENT_STATE_FILE, state)


def load_tasks() -> Dict:
    return load_yaml(TASKS_FILE, TASKS_TEMPLATE)


def save_tasks(tasks: Dict) -> None:
    save_yaml(TASKS_FILE, tasks)


def load_policies() -> Dict:
    if not POLICIES_FILE.exists():
        error("Не найден файл agent_policies.yaml")
    return load_yaml(POLICIES_FILE, {})


def current_timestamp() -> str:
    return datetime.now().isoformat(timespec="minutes")


def current_date() -> str:
    return date.today().isoformat()


def ensure_role_exists(role: str, policies: Dict) -> None:
    roles = policies.get("roles", {})
    if role not in roles:
        error(f"Неизвестная роль '{role}'. Проверьте agent_policies.yaml")


def resolve_role(alias: str, policies: Dict) -> str:
    roles = policies.get("roles", {})
    alias_upper = alias.upper()
    if alias_upper in roles:
        return alias_upper
    alias_lower = alias.lower()
    for code, data in roles.items():
        name = data.get("name", "")
        if alias_lower == code.lower() or alias_lower in name.lower():
            return code
    error(f"Не удалось распознать роль '{alias}'")
    return alias_upper


def generate_agent_id(role: str, state: Dict) -> str:
    numbers = [
        int(agent["id"].split("_")[1])
        for agent in state.get("agents", [])
        if agent["role"] == role and agent["id"].startswith(f"{role}_")
    ]
    next_number = max(numbers, default=0) + 1
    return f"{role}_{next_number:03d}_v1"


def get_agent(state: Dict, agent_id: str) -> Optional[Dict]:
    for agent in state.get("agents", []):
        if agent["id"] == agent_id:
            return agent
    return None


def ensure_agent_exists(state: Dict, agent_id: str) -> Dict:
    agent = get_agent(state, agent_id)
    if agent is None:
        error(f"Агент '{agent_id}' не найден")
    return agent


def append_to_todo(line: str) -> None:
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    needs_newline = False
    if TODO_FILE.exists():
        content = TODO_FILE.read_text(encoding="utf-8")
        needs_newline = bool(content and not content.endswith("\n"))
    with TODO_FILE.open("a", encoding="utf-8") as fh:
        if needs_newline:
            fh.write("\n")
        fh.write(line + "\n")


def mark_todo_completed(task_tag: str) -> None:
    if not TODO_FILE.exists():
        return
    lines = TODO_FILE.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        if task_tag in line and not line.startswith("x "):
            lines[idx] = f"x {current_date()} {line}"
            TODO_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return


def handle_agents(args: argparse.Namespace) -> None:
    state = load_state()
    policies = load_policies()

    if args.action == "list":
        agents = state.get("agents", [])
        if args.role:
            role_code = resolve_role(args.role, policies)
            agents = [agent for agent in agents if agent["role"] == role_code]
        if not agents:
            print("Агенты не найдены")
            return
        for agent in agents:
            print(
                f"{agent['id']:>10} | {agent['role']:<4} | {agent['status']:<8} | "
                f"{agent['name']}"
            )

    elif args.action == "create":
        role_code = resolve_role(args.role, policies)
        agent_id = generate_agent_id(role_code, state)
        timestamp = current_timestamp()
        record = {
            "id": agent_id,
            "role": role_code,
            "name": args.name,
            "created_at": current_date(),
            "status": "active",
            "last_activity": timestamp,
        }
        state.setdefault("agents", []).append(record)
        state.setdefault("role_assignments", []).append(
            {
                "agent_name": args.name,
                "role": role_code,
                "status": "assigned",
                "timestamp": timestamp,
            }
        )
        save_state(state)

        agent_dir = AGENT_DIR / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        profile = {
            "agent": {
                "id": agent_id,
                "role": role_code,
                "name": args.name,
                "created": current_date(),
                "status": "active",
            },
            "workflow": policies["roles"][role_code].get("workflow", {}),
            "preferences": {
                "timezone": policies.get("workflow_defaults", {}).get("timezone", "Europe/Moscow"),
                "working_hours": policies.get("workflow_defaults", {}).get("workday", "09:00-18:00"),
            },
        }
        save_yaml(agent_dir / "profile.yaml", profile)
        (agent_dir / "logs").mkdir(exist_ok=True)
        print(f"Создан агент {agent_id} ({args.name})")

    elif args.action == "info":
        agent = ensure_agent_exists(state, args.agent_id)
        print(json.dumps(agent, ensure_ascii=False, indent=2))
        profile_path = AGENT_DIR / args.agent_id / "profile.yaml"
        if profile_path.exists():
            profile = load_yaml(profile_path, {})
            print("Профиль:")
            print(yaml.safe_dump(profile, allow_unicode=True, sort_keys=False))
        tasks_data = load_tasks()
        active_tasks = [
            task for task in tasks_data.get("tasks", [])
            if task.get("agent_id") == args.agent_id and task.get("status") != "completed"
        ]
        if active_tasks:
            print("Активные задачи:")
            for task in active_tasks:
                print(f"- {task['id']} [{task['priority']}] {task['title']}")

    elif args.action == "update-status":
        agent = ensure_agent_exists(state, args.agent_id)
        status_def = policies.get("status_definitions", {})
        if args.status not in status_def:
            error(f"Статус '{args.status}' не описан в agent_policies.yaml")
        agent["status"] = args.status
        agent["last_activity"] = current_timestamp()
        save_state(state)
        print(f"Статус агента {args.agent_id} обновлён: {args.status}")

    elif args.action == "touch":
        agent = ensure_agent_exists(state, args.agent_id)
        agent["last_activity"] = current_timestamp()
        save_state(state)
        print(f"Обновлена активность {args.agent_id}")

    elif args.action == "remove":
        agents = state.get("agents", [])
        new_agents = [agent for agent in agents if agent["id"] != args.agent_id]
        if len(new_agents) == len(agents):
            error(f"Агент {args.agent_id} не найден")
        state["agents"] = new_agents
        save_state(state)
        if args.purge:
            agent_path = AGENT_DIR / args.agent_id
            if agent_path.exists():
                shutil.rmtree(agent_path)
        print(f"Агент {args.agent_id} удалён")


def generate_task_id(tasks: Dict) -> str:
    numbers = [
        int(task["id"].split("-")[1])
        for task in tasks.get("tasks", [])
        if task.get("id", "").startswith("TSK-")
    ]
    next_number = max(numbers, default=0) + 1
    return f"TSK-{next_number:04d}"


def build_task_line(task: Dict) -> str:
    priority = task.get("priority", "B")
    created = task.get("created_at", current_date())
    title = task.get("title", "Без описания")
    tags = list(task.get("tags", []))
    if task.get("story_points"):
        tags.append(f"+{task['story_points']}sp")
    if agent_id := task.get("agent_id"):
        tags.append(f"+agent_id:{agent_id}")
    if task_id := task.get("id"):
        tags.append(f"+task_id:{task_id}")
    parts: List[str] = [f"({priority})", created, title]
    role = task.get("role")
    if role:
        parts.append(f"@{role.lower()}")
    parts.extend(tags)
    return " ".join(parts)


def handle_tasks(args: argparse.Namespace) -> None:
    tasks_data = load_tasks()
    state = load_state()
    policies = load_policies()

    if args.action == "add":
        valid_priorities = {"A", "B", "C", "D"}
        if args.priority not in valid_priorities:
            error(f"Недопустимый приоритет '{args.priority}'. Используйте A/B/C/D")
        if args.agent_id:
            ensure_agent_exists(state, args.agent_id)
        role_code = resolve_role(args.role, policies) if args.role else None

        task_id = generate_task_id(tasks_data)
        entry = {
            "id": task_id,
            "title": args.title if not args.notes else f"{args.title}. {args.notes}",
            "priority": args.priority,
            "status": "active",
            "created_at": current_date(),
            "agent_id": args.agent_id,
            "role": role_code,
            "story_points": args.story_points,
            "tags": [
                tag if tag.startswith("+") else f"+{tag}"
                for tag in (args.tags or [])
            ],
        }
        tasks_data.setdefault("tasks", []).append(entry)
        save_tasks(tasks_data)
        append_to_todo(build_task_line(entry))
        print(f"Создана задача {task_id}")

    elif args.action == "list":
        tasks = tasks_data.get("tasks", [])
        role_filter = resolve_role(args.role, policies) if args.role else None
        result = []
        for task in tasks:
            if args.agent_id and task.get("agent_id") != args.agent_id:
                continue
            if role_filter and task.get("role") != role_filter:
                continue
            if args.status and task.get("status") != args.status:
                continue
            if not args.include_completed and task.get("status") == "completed":
                continue
            result.append(task)
        if not result:
            print("Задачи не найдены")
            return
        for task in result:
            print(
                f"{task['id']:>8} | {task['priority']} | {task.get('status','?'):>10} | "
                f"{task.get('agent_id','-'):>10} | {task['title']}"
            )

    elif args.action == "complete":
        tasks = tasks_data.get("tasks", [])
        for task in tasks:
            if task.get("id") == args.task_id:
                if task.get("status") == "completed":
                    error("Задача уже завершена")
                task["status"] = "completed"
                task["completed_at"] = current_date()
                save_tasks(tasks_data)
                mark_todo_completed(f"+task_id:{args.task_id}")
                print(f"Задача {args.task_id} завершена")
                return
        error(f"Задача {args.task_id} не найдена")

    elif args.action == "info":
        for task in tasks_data.get("tasks", []):
            if task.get("id") == args.task_id:
                print(json.dumps(task, ensure_ascii=False, indent=2))
                return
        error(f"Задача {args.task_id} не найдена")


def handle_config(args: argparse.Namespace) -> None:
    policies = load_policies()
    if args.action == "roles":
        for role, data in policies.get("roles", {}).items():
            print(f"{role}: {data.get('name')}")
            print(f"  {data.get('description')}")
            allowed = ", ".join(data.get("allowed_actions", [])) or "-"
            print(f"  Доступные действия: {allowed}")
    elif args.action == "status":
        for key, value in policies.get("status_definitions", {}).items():
            print(f"{key}: {value.get('description')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI управления агентами и задачами")
    subparsers = parser.add_subparsers(dest="command")

    agents_parser = subparsers.add_parser("agents", help="Операции с агентами")
    agents_sub = agents_parser.add_subparsers(dest="action")

    list_parser = agents_sub.add_parser("list", help="Список агентов")
    list_parser.add_argument("--role", help="Фильтр по роли", default=None)

    create_parser = agents_sub.add_parser("create", help="Создать агента")
    create_parser.add_argument("role", help="Код роли")
    create_parser.add_argument("name", help="Имя или описание")

    info_parser = agents_sub.add_parser("info", help="Информация об агенте")
    info_parser.add_argument("agent_id")

    status_parser = agents_sub.add_parser("update-status", help="Изменить статус")
    status_parser.add_argument("agent_id")
    status_parser.add_argument("status")

    touch_parser = agents_sub.add_parser("touch", help="Обновить активность")
    touch_parser.add_argument("agent_id")

    remove_parser = agents_sub.add_parser("remove", help="Удалить агента")
    remove_parser.add_argument("agent_id")
    remove_parser.add_argument("--purge", action="store_true", help="Удалить данные агента")

    tasks_parser = subparsers.add_parser("tasks", help="Работа с задачами")
    tasks_sub = tasks_parser.add_subparsers(dest="action")

    add_parser = tasks_sub.add_parser("add", help="Создать задачу")
    add_parser.add_argument("title", help="Описание")
    add_parser.add_argument("--priority", default="B", help="Приоритет (A/B/C/D)")
    add_parser.add_argument("--agent-id", dest="agent_id", default=None, help="ID агента")
    add_parser.add_argument("--role", default=None, help="Контекстная роль")
    add_parser.add_argument("--tag", dest="tags", action="append", help="Дополнительный тег", default=None)
    add_parser.add_argument("--story-points", dest="story_points", type=int, default=None)
    add_parser.add_argument("--notes", default=None, help="Дополнительное описание")

    list_tasks_parser = tasks_sub.add_parser("list", help="Список задач")
    list_tasks_parser.add_argument("--agent-id", dest="agent_id", default=None)
    list_tasks_parser.add_argument("--role", default=None)
    list_tasks_parser.add_argument("--status", default=None)
    list_tasks_parser.add_argument("--include-completed", action="store_true")

    complete_parser = tasks_sub.add_parser("complete", help="Закрыть задачу")
    complete_parser.add_argument("task_id")

    task_info_parser = tasks_sub.add_parser("info", help="Инфо о задаче")
    task_info_parser.add_argument("task_id")

    config_parser = subparsers.add_parser("config", help="Просмотр конфигурации")
    config_sub = config_parser.add_subparsers(dest="action")

    config_sub.add_parser("roles", help="Показать роли")
    config_sub.add_parser("status", help="Показать статусы")

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "agents":
        handle_agents(args)
    elif args.command == "tasks":
        handle_tasks(args)
    elif args.command == "config":
        handle_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    _ensure_directories()
    main()
