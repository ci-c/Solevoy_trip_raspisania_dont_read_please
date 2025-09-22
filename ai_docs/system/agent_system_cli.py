from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

SCRIPT_PATH = Path(__file__).resolve()
SYSTEM_DIR = SCRIPT_PATH.parent
AI_DOCS_DIR = SYSTEM_DIR.parent
REPO_ROOT = AI_DOCS_DIR.parent
STATE_DIR = AI_DOCS_DIR / "state"
AGENTS_DIR = STATE_DIR / "agents"
LOCKS_DIR = STATE_DIR / "locks"
AGENT_STATE_FILE = STATE_DIR / "agent_state.yaml"
TASKS_FILE = STATE_DIR / "tasks.yaml"
POLICIES_FILE = SYSTEM_DIR / "agent_policies.yaml"
INITIAL_TASKS_FILE = SYSTEM_DIR / "initial_tasks.yaml"
TODO_FILE = REPO_ROOT / "todo.txt"
LOGS_DIR = REPO_ROOT / "logs"
TEAM_LOG = LOGS_DIR / "team_communication.log"

STATE_TEMPLATE: Dict[str, List] = {
    "agents": [],
    "role_assignments": [],
    "pending_agents": [],
    "events": [],
}
TASKS_TEMPLATE: Dict[str, List] = {"tasks": []}


def error(message: str, code: int = 1) -> None:
    print(message)
    sys.exit(code)


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


def ensure_directories() -> None:
    for directory in (STATE_DIR, AGENTS_DIR, LOCKS_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    if not AGENT_STATE_FILE.exists():
        save_yaml(AGENT_STATE_FILE, STATE_TEMPLATE)
    if not TASKS_FILE.exists():
        save_yaml(TASKS_FILE, TASKS_TEMPLATE)


def load_state() -> Dict:
    state = load_yaml(AGENT_STATE_FILE, STATE_TEMPLATE)
    state.setdefault("agents", [])
    state.setdefault("pending_agents", [])
    state.setdefault("events", [])
    return state


def save_state(state: Dict) -> None:
    save_yaml(AGENT_STATE_FILE, state)


def load_tasks() -> Dict:
    tasks = load_yaml(TASKS_FILE, TASKS_TEMPLATE)
    tasks.setdefault("tasks", [])
    return tasks


def save_tasks(tasks: Dict) -> None:
    save_yaml(TASKS_FILE, tasks)


def load_policies() -> Dict:
    policies = load_yaml(POLICIES_FILE, {})
    if "role_policies" not in policies:
        error("agent_policies.yaml не содержит секцию role_policies")
    policies.setdefault("role_priorities", list(policies["role_policies"].keys()))
    return policies


def load_initial_tasks() -> Dict:
    return load_yaml(INITIAL_TASKS_FILE, {"tasks": {}}).get("tasks", {})


def current_timestamp() -> str:
    return datetime.now().isoformat(timespec="minutes")


def current_date() -> str:
    return date.today().isoformat()


def resolve_role(alias: str, policies: Dict) -> str:
    role_policies = policies.get("role_policies", {})
    alias_upper = alias.upper()
    if alias_upper in role_policies:
        return alias_upper
    alias_lower = alias.lower()
    for code, data in role_policies.items():
        name = (data.get("title") or "").lower()
        if alias_lower == code.lower() or alias_lower in name:
            return code
    error(f"Не удалось распознать роль '{alias}'")
    return alias_upper


def get_role_counts(state: Dict) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for agent in state.get("agents", []):
        if agent.get("status") == "active":
            role = agent.get("role")
            counts[role] = counts.get(role, 0) + 1
    return counts


def get_role_policy(role: str, policies: Dict) -> Dict:
    role_policies = policies.get("role_policies", {})
    if role not in role_policies:
        error(f"В конфигурации отсутствует политика для роли '{role}'")
    return role_policies[role]


def select_role(counts: Dict[str, int], policies: Dict, desired: Optional[str] = None) -> str:
    role_policies = policies.get("role_policies", {})
    priorities = policies.get("role_priorities", list(role_policies.keys()))

    if desired:
        desired_role = resolve_role(desired, policies)
        return desired_role

    # Сначала удовлетворяем минимум
    for role in priorities:
        policy = role_policies.get(role, {})
        minimum = policy.get("minimum", 0)
        if counts.get(role, 0) < minimum:
            return role

    # Затем ищем роль с незаполненной емкостью
    for role in priorities:
        policy = role_policies.get(role, {})
        capacity = policy.get("capacity", float("inf"))
        if counts.get(role, 0) < capacity:
            return role

    # Если все роли заполнены, выбираем роль с наименьшей загрузкой
    def load_key(role: str) -> Tuple[int, int]:
        return (counts.get(role, 0), priorities.index(role))

    return min(priorities, key=load_key)


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


def build_task_line(task: Dict) -> str:
    priority = task.get("priority", "B")
    created_at = task.get("created_at", current_date())
    title = task.get("title", "Без описания")
    tags = list(task.get("tags", []))
    if task.get("story_points"):
        tags.append(f"+{task['story_points']}sp")
    if task.get("agent_id"):
        tags.append(f"+agent_id:{task['agent_id']}")
    if task.get("id"):
        tags.append(f"+task_id:{task['id']}")
    role = task.get("role")
    parts = [f"({priority})", created_at, title]
    if role:
        parts.append(f"@{role.lower()}")
    parts.extend(tags)
    return " ".join(parts)


def generate_task_id(tasks: Dict) -> str:
    numbers = [
        int(task["id"].split("-")[1])
        for task in tasks.get("tasks", [])
        if task.get("id", "").startswith("TSK-")
    ]
    next_number = max(numbers, default=0) + 1
    return f"TSK-{next_number:04d}"


def ensure_agent_directory(agent_id: str) -> Path:
    agent_dir = AGENTS_DIR / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "logs").mkdir(exist_ok=True)
    return agent_dir


def write_welcome(agent: Dict, role_policy: Dict, prompt_text: str, initial_task: Optional[Dict], task_id: Optional[str]) -> None:
    agent_dir = ensure_agent_directory(agent["id"])
    preferred_models = agent.get("preferred_models", [])
    lines = [
        f"# Добро пожаловать, {agent['name']} ({agent['id']})",
        "",
        f"## Роль: {role_policy.get('title', agent['role'])}",
        role_policy.get("description", ""),
        "",
    ]
    if preferred_models:
        lines.append("## Рекомендуемые модели")
        lines.extend([f"- {model}" for model in preferred_models])
        lines.append("")
    if initial_task and task_id:
        lines.append("## Первая задача")
        lines.append(f"- ID: {task_id}")
        lines.append(f"- Заголовок: {initial_task.get('title')}")
        if initial_task.get("description"):
            lines.append(f"- Описание: {initial_task['description']}")
        lines.append("")
    if prompt_text:
        lines.append("## Промпт")
        lines.append(prompt_text.strip())
        lines.append("")
    (agent_dir / "welcome.md").write_text("\n".join(lines), encoding="utf-8")


def update_profile(agent: Dict, role_policy: Dict) -> None:
    agent_dir = ensure_agent_directory(agent["id"])
    profile = {
        "agent": {
            "id": agent["id"],
            "role": agent["role"],
            "name": agent["name"],
            "created": agent["created_at"],
            "status": agent["status"],
        },
        "workflow": role_policy.get("workflow", {}),
        "traits": {
            "preferred_models": agent.get("preferred_models", []),
        },
    }
    (agent_dir / "profile.yaml").write_text(
        yaml.safe_dump(profile, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def log_event(message: str) -> None:
    ensure_directories()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with TEAM_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {message}\n")


def ensure_agent_exists(state: Dict, agent_id: str) -> Dict:
    for agent in state.get("agents", []):
        if agent.get("id") == agent_id:
            return agent
    error(f"Агент '{agent_id}' не найден")
    return {}


def add_initial_task(agent: Dict, role_policy: Dict, initial_tasks: Dict, tasks_data: Dict) -> Optional[str]:
    key = role_policy.get("initial_task_key")
    if not key:
        return None
    template = initial_tasks.get(key)
    if not template:
        log_event(f"Шаблон задачи '{key}' не найден для роли {agent['role']}")
        return None

    task_id = generate_task_id(tasks_data)
    entry = {
        "id": task_id,
        "title": template.get("title", "Задача"),
        "description": template.get("description", ""),
        "priority": template.get("priority", "B"),
        "status": "active",
        "created_at": current_date(),
        "agent_id": agent["id"],
        "role": agent.get("role"),
        "story_points": template.get("story_points"),
        "tags": template.get("tags", []) + ["+origin:scheduler"],
    }
    tasks_data.setdefault("tasks", []).append(entry)
    append_to_todo(build_task_line(entry))
    return task_id


def assign_role_to_agent(agent: Dict, role: str, policies: Dict, initial_tasks: Dict, tasks_data: Dict) -> Optional[str]:
    role_policy = get_role_policy(role, policies)
    agent["role"] = role
    agent["status"] = agent.get("status", "active")
    agent["preferred_models"] = role_policy.get("preferred_models", [])
    update_profile(agent, role_policy)

    prompt_path = Path(role_policy.get("prompt_path", ""))
    prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
    template = initial_tasks.get(role_policy.get("initial_task_key", ""))
    task_id = add_initial_task(agent, role_policy, initial_tasks, tasks_data)
    write_welcome(agent, role_policy, prompt_text, template, task_id)
    return task_id


def scheduler_assign_pending(state: Dict, policies: Dict, initial_tasks: Dict, tasks_data: Dict, counts: Dict[str, int]) -> Tuple[List[str], List[str]]:
    events: List[str] = []
    assigned_ids: List[str] = []
    remaining_pending = []
    for pending in state.get("pending_agents", []):
        desired = pending.get("desired_role")
        role = select_role(counts, policies, desired)
        agent_id = generate_agent_id_for_role(role, state)
        agent_record = {
            "id": agent_id,
            "role": role,
            "name": pending.get("name", agent_id),
            "created_at": current_date(),
            "status": "active",
            "last_activity": current_timestamp(),
            "preferred_models": [],
        }
        state.setdefault("agents", []).append(agent_record)
        assign_role_to_agent(agent_record, role, policies, initial_tasks, tasks_data)
        counts[role] = counts.get(role, 0) + 1
        events.append(f"Назначена роль {role} агенту {agent_id}")
        assigned_ids.append(agent_id)
    state["pending_agents"] = remaining_pending
    return events, assigned_ids


def generate_agent_id_for_role(role: str, state: Dict) -> str:
    existing = [agent["id"] for agent in state.get("agents", []) if agent.get("id", "").startswith(f"{role}_")]
    numbers = []
    for agent_id in existing:
        try:
            number = int(agent_id.split("_")[1])
            numbers.append(number)
        except (IndexError, ValueError):
            continue
    next_number = max(numbers, default=0) + 1
    return f"{role}_{next_number:03d}_v1"


def scheduler_reassign(state: Dict, policies: Dict, initial_tasks: Dict, tasks_data: Dict, counts: Dict[str, int], exclude_agents: Optional[List[str]] = None) -> List[str]:
    events: List[str] = []
    scheduler_cfg = policies.get("scheduler", {})
    if not scheduler_cfg.get("allow_auto_reassignment", True):
        return events
    max_reassign = scheduler_cfg.get("max_reassign_per_run", 1)
    role_policies = policies.get("role_policies", {})
    priorities = policies.get("role_priorities", list(role_policies.keys()))

    def shortage_roles() -> List[str]:
        roles = []
        for role in priorities:
            policy = role_policies.get(role, {})
            capacity = policy.get("capacity", float("inf"))
            minimum = policy.get("minimum", 0)
            count = counts.get(role, 0)
            if count < minimum:
                roles.append(role)
                continue
            if not policy.get("auto_fill_capacity", False):
                continue
            if count < capacity:
                roles.append(role)
        return roles

    reassignments = 0
    for role in shortage_roles():
        if reassignments >= max_reassign:
            break
        policy = role_policies.get(role, {})
        capacity = policy.get("capacity", float("inf"))
        if counts.get(role, 0) >= capacity:
            continue
        donor = find_donor_role(counts, role_policies, role, priorities)
        if not donor:
            continue
        agent = pick_agent_for_reassignment(state, donor, exclude_agents)
        if not agent:
            continue
        old_role = agent["role"]
        agent["role"] = role
        agent["last_activity"] = current_timestamp()
        agent["preferred_models"] = []
        assign_role_to_agent(agent, role, policies, initial_tasks, tasks_data)
        counts[role] = counts.get(role, 0) + 1
        counts[old_role] = max(counts.get(old_role, 1) - 1, 0)
        events.append(f"Агент {agent['id']} переведён с роли {old_role} на {role}")
        reassignments += 1
    return events


def find_donor_role(counts: Dict[str, int], role_policies: Dict, target_role: str, priorities: List[str]) -> Optional[str]:
    for role in reversed(priorities):
        if role == target_role:
            continue
        policy = role_policies.get(role, {})
        capacity = policy.get("capacity", float("inf"))
        minimum = policy.get("minimum", 0)
        count = counts.get(role, 0)
        if count > capacity:
            return role
        if count > minimum and count > 1:
            return role
    return None


def pick_agent_for_reassignment(state: Dict, role: str, exclude: Optional[List[str]] = None) -> Optional[Dict]:
    exclude = exclude or []
    for agent in reversed(state.get("agents", [])):
        if agent.get("role") == role and agent.get("status") == "active" and agent.get("id") not in exclude:
            return agent
    return None


def scheduler_run(state: Dict, policies: Dict, initial_tasks: Dict, tasks_data: Dict) -> List[str]:
    counts = get_role_counts(state)
    events_pending, assigned_ids = scheduler_assign_pending(state, policies, initial_tasks, tasks_data, counts)
    events = list(events_pending)
    events.extend(scheduler_reassign(state, policies, initial_tasks, tasks_data, counts, exclude_agents=assigned_ids))
    if events:
        for message in events:
            log_event(message)
            state.setdefault("events", []).append({
                "timestamp": current_timestamp(),
                "message": message,
            })
    return events


# ------------------------------- COMMAND HANDLERS -------------------------------- #


def handle_agents(args: argparse.Namespace) -> None:
    state = load_state()
    policies = load_policies()
    initial_tasks = load_initial_tasks()
    tasks_data = load_tasks()

    if args.action == "list":
        agents = state.get("agents", [])
        if args.role:
            role_code = resolve_role(args.role, policies)
            agents = [agent for agent in agents if agent.get("role") == role_code]
        if not agents:
            print("Агенты не найдены")
            return
        for agent in agents:
            print(
                f"{agent['id']:>12} | {agent['role']:<4} | {agent['status']:<8} | {agent['name']}"
            )
        if state.get("pending_agents"):
            print("\nОжидают распределения:")
            for pending in state["pending_agents"]:
                print(f"- {pending.get('name')} (запрошено {pending.get('requested_at')})")

    elif args.action == "info":
        agent = ensure_agent_exists(state, args.agent_id)
        print(json.dumps(agent, ensure_ascii=False, indent=2))
        agent_dir = ensure_agent_directory(agent["id"])
        profile_path = agent_dir / "profile.yaml"
        if profile_path.exists():
            print("Профиль:")
            print(yaml.safe_dump(load_yaml(profile_path), allow_unicode=True, sort_keys=False))
        tasks_data = load_tasks()
        active_tasks = [
            task for task in tasks_data.get("tasks", [])
            if task.get("agent_id") == agent["id"] and task.get("status") != "completed"
        ]
        if active_tasks:
            print("Активные задачи:")
            for task in active_tasks:
                print(f"- {task['id']} [{task['priority']}] {task['title']}")

    elif args.action == "create":
        counts = get_role_counts(state)
        role_code = resolve_role(args.role, policies)
        agent_id = generate_agent_id_for_role(role_code, state)
        record = {
            "id": agent_id,
            "role": role_code,
            "name": args.name,
            "created_at": current_date(),
            "status": "active",
            "last_activity": current_timestamp(),
            "preferred_models": [],
        }
        state.setdefault("agents", []).append(record)
        assign_role_to_agent(record, role_code, policies, initial_tasks, tasks_data)
        counts = get_role_counts(state)
        print(f"Создан агент {agent_id} с ролью {role_code}")
        save_state(state)
        save_tasks(tasks_data)

    elif args.action == "onboard":
        pending = {
            "name": args.name,
            "requested_at": current_timestamp(),
            "desired_role": args.desired_role,
        }
        state.setdefault("pending_agents", []).append(pending)
        events = scheduler_run(state, policies, initial_tasks, tasks_data)
        save_state(state)
        save_tasks(tasks_data)
        if events:
            print("\n".join(events))
        else:
            print("Агент поставлен в очередь на распределение")

    elif args.action == "update-status":
        agent = ensure_agent_exists(state, args.agent_id)
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
        new_agents = [agent for agent in agents if agent.get("id") != args.agent_id]
        if len(new_agents) == len(agents):
            error(f"Агент {args.agent_id} не найден")
        state["agents"] = new_agents
        save_state(state)
        if args.purge:
            agent_dir = AGENTS_DIR / args.agent_id
            if agent_dir.exists():
                shutil.rmtree(agent_dir)
        print(f"Агент {args.agent_id} удалён")


def handle_tasks(args: argparse.Namespace) -> None:
    policies = load_policies()
    initial_tasks = load_initial_tasks()
    tasks_data = load_tasks()
    state = load_state()

    if args.action == "add":
        role_code = resolve_role(args.role, policies) if args.role else None
        if args.agent_id:
            ensure_agent_exists(state, args.agent_id)
        if role_code is None and args.agent_id:
            agent = ensure_agent_exists(state, args.agent_id)
            role_code = agent.get("role")
        valid_priorities = {"A", "B", "C", "D"}
        if args.priority not in valid_priorities:
            error(f"Недопустимый приоритет '{args.priority}'. Используйте A/B/C/D")
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
            "tags": [tag if tag.startswith("+") else f"+{tag}" for tag in (args.tags or [])],
        }
        tasks_data.setdefault("tasks", []).append(entry)
        append_to_todo(build_task_line(entry))
        save_tasks(tasks_data)
        print(f"Создана задача {task_id}")

    elif args.action == "list":
        tasks = tasks_data.get("tasks", [])
        role_filter = resolve_role(args.role, policies) if args.role else None
        results = []
        for task in tasks:
            if args.agent_id and task.get("agent_id") != args.agent_id:
                continue
            if role_filter and task.get("role") != role_filter:
                continue
            if args.status and task.get("status") != args.status:
                continue
            if not args.include_completed and task.get("status") == "completed":
                continue
            results.append(task)
        if not results:
            print("Задачи не найдены")
            return
        for task in results:
            print(
                f"{task['id']:>8} | {task['priority']} | {task.get('status','?'):>10} | "
                f"{task.get('agent_id','-'):>12} | {task['title']}"
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
        for role, data in policies.get("role_policies", {}).items():
            print(f"{role}: {data.get('title')}")
            print(f"  {data.get('description')}")
            print(f"  Capacity: {data.get('capacity', '∞')} (min {data.get('minimum', 0)})")
            models = ", ".join(data.get("preferred_models", [])) or "-"
            print(f"  Модели: {models}")
    elif args.action == "status":
        for key, value in policies.get("status_definitions", {}).items():
            print(f"{key}: {value.get('description')}")


def handle_scheduler(args: argparse.Namespace) -> None:
    state = load_state()
    policies = load_policies()
    initial_tasks = load_initial_tasks()
    tasks_data = load_tasks()

    if args.action == "run":
        events = scheduler_run(state, policies, initial_tasks, tasks_data)
        save_state(state)
        save_tasks(tasks_data)
        if events:
            print("\n".join(events))
        else:
            print("Изменений нет")

    elif args.action == "status":
        counts = get_role_counts(state)
        role_policies = policies.get("role_policies", {})
        print("Распределение по ролям:")
        for role in policies.get("role_priorities", role_policies.keys()):
            policy = role_policies.get(role, {})
            capacity = policy.get("capacity", '∞')
            minimum = policy.get("minimum", 0)
            count = counts.get(role, 0)
            print(f"- {role}: {count} / {capacity} (минимум {minimum})")
        if state.get("pending_agents"):
            print("\nОжидают распределения:")
            for pending in state["pending_agents"]:
                print(f"- {pending.get('name')} (с {pending.get('requested_at')})")
        if state.get("events"):
            print("\nПоследние события:")
            for event in state["events"][-5:]:
                print(f"[{event['timestamp']}] {event['message']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Управление агентами и задачами")
    subparsers = parser.add_subparsers(dest="command")

    agents_parser = subparsers.add_parser("agents", help="Операции с агентами")
    agents_sub = agents_parser.add_subparsers(dest="action")

    list_parser = agents_sub.add_parser("list", help="Список агентов")
    list_parser.add_argument("--role", default=None, help="Фильтр по роли")

    info_parser = agents_sub.add_parser("info", help="Информация об агенте")
    info_parser.add_argument("agent_id")

    create_parser = agents_sub.add_parser("create", help="Создать агента с явной ролью")
    create_parser.add_argument("role", help="Код или название роли")
    create_parser.add_argument("name", help="Имя агента")

    onboard_parser = agents_sub.add_parser("onboard", help="Автоматическая регистрация агента")
    onboard_parser.add_argument("name", help="Имя или идентификатор входящего агента")
    onboard_parser.add_argument("--desired-role", dest="desired_role", default=None, help="Желаемая роль (опционально)")

    status_parser = agents_sub.add_parser("update-status", help="Обновить статус агента")
    status_parser.add_argument("agent_id")
    status_parser.add_argument("status", choices=["active", "paused", "retired"])

    touch_parser = agents_sub.add_parser("touch", help="Обновить активность")
    touch_parser.add_argument("agent_id")

    remove_parser = agents_sub.add_parser("remove", help="Удалить агента")
    remove_parser.add_argument("agent_id")
    remove_parser.add_argument("--purge", action="store_true", help="Удалить каталог агента")

    tasks_parser = subparsers.add_parser("tasks", help="Работа с задачами")
    tasks_sub = tasks_parser.add_subparsers(dest="action")

    add_parser = tasks_sub.add_parser("add", help="Создать задачу")
    add_parser.add_argument("title")
    add_parser.add_argument("--priority", default="B")
    add_parser.add_argument("--agent-id", dest="agent_id", default=None)
    add_parser.add_argument("--role", default=None)
    add_parser.add_argument("--tag", dest="tags", action="append", default=None)
    add_parser.add_argument("--story-points", dest="story_points", type=int, default=None)
    add_parser.add_argument("--notes", default=None)

    list_tasks_parser = tasks_sub.add_parser("list", help="Список задач")
    list_tasks_parser.add_argument("--agent-id", dest="agent_id", default=None)
    list_tasks_parser.add_argument("--role", default=None)
    list_tasks_parser.add_argument("--status", default=None)
    list_tasks_parser.add_argument("--include-completed", action="store_true")

    complete_parser = tasks_sub.add_parser("complete", help="Завершить задачу")
    complete_parser.add_argument("task_id")

    info_task_parser = tasks_sub.add_parser("info", help="Информация о задаче")
    info_task_parser.add_argument("task_id")

    config_parser = subparsers.add_parser("config", help="Просмотр конфигурации")
    config_sub = config_parser.add_subparsers(dest="action")
    config_sub.add_parser("roles")
    config_sub.add_parser("status")

    scheduler_parser = subparsers.add_parser("scheduler", help="Планировщик")
    scheduler_sub = scheduler_parser.add_subparsers(dest="action")
    scheduler_sub.add_parser("run", help="Запуск распределения")
    scheduler_sub.add_parser("status", help="Статус распределения")

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    ensure_directories()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "agents":
        handle_agents(args)
    elif args.command == "tasks":
        handle_tasks(args)
    elif args.command == "config":
        handle_config(args)
    elif args.command == "scheduler":
        handle_scheduler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
