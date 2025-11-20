#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import yaml

AI_DOCS_DIR = Path(__file__).resolve().parents[1]
STATE_DIR = AI_DOCS_DIR / "state"
AGENTS_FILE = STATE_DIR / "agents.yaml"
ISSUES_FILE = STATE_DIR / "issues.yaml"
EVENTS_FILE = STATE_DIR / "events.yaml"
COMM_FILE = STATE_DIR / "communications.yaml"
PROMPTS_DIR = AI_DOCS_DIR / "prompts" / "roles"
SYSTEM_DIR = AI_DOCS_DIR / "system"
POLICIES_FILE = SYSTEM_DIR / "agent_policies.yaml"
INITIAL_TASKS_FILE = SYSTEM_DIR / "initial_tasks.yaml"
TODO_FILE = (AI_DOCS_DIR.parent) / "todo.txt"

DEFAULT_AGENTS = {"agents": []}
DEFAULT_ISSUES = {"issues": []}
DEFAULT_EVENTS = {"events": []}
DEFAULT_COMMUNICATIONS = {"messages": []}

STATUS_ORDER = [
    "New",
    "In Refinement",
    "Ready",
    "In Progress",
    "Blocked",
    "Review",
    "Done",
    "Archived",
]

STATUS_TRANSITIONS = {
    "New": {"In Refinement", "Archived"},
    "In Refinement": {"Ready", "Blocked", "Archived"},
    "Ready": {"In Progress", "Blocked", "Archived"},
    "In Progress": {"Review", "Blocked", "Done"},
    "Blocked": {"In Progress", "Archived"},
    "Review": {"In Progress", "Done"},
    "Done": {"Archived"},
    "Archived": set(),
}

ROLE_KEYWORDS = {
    "ARCH": ["architect", "architecture", "strategy"],
    "BE": ["backend", "api", "service", "database"],
    "FE": ["frontend", "ui", "ux", "handler", "keyboard"],
    "QA": ["qa", "test", "coverage", "quality"],
    "DO": ["devops", "ci", "cd", "deploy", "monitor"],
    "PO": ["product", "backlog", "research", "stakeholder"],
    "SM": ["scrum", "process", "coordination", "blocker"],
}


def iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def load_yaml(path: Path, template: dict) -> dict:
    if not path.exists():
        return template.copy()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return template.copy()
    return data


def save_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


class State:
    def __init__(self) -> None:
        ensure_state_files()
        self.agents_data = load_yaml(AGENTS_FILE, DEFAULT_AGENTS)
        self.issues_data = load_yaml(ISSUES_FILE, DEFAULT_ISSUES)
        self.events_data = load_yaml(EVENTS_FILE, DEFAULT_EVENTS)
        self.comm_data = load_yaml(COMM_FILE, DEFAULT_COMMUNICATIONS)

    @property
    def agents(self) -> list[dict]:
        return self.agents_data.setdefault("agents", [])

    @property
    def issues(self) -> list[dict]:
        return self.issues_data.setdefault("issues", [])

    @property
    def events(self) -> list[dict]:
        return self.events_data.setdefault("events", [])

    @property
    def communications(self) -> list[dict]:
        return self.comm_data.setdefault("messages", [])

    def persist(self) -> None:
        save_yaml(
            AGENTS_FILE, {"agents": sorted(self.agents, key=lambda a: a.get("id", ""))}
        )
        save_yaml(
            ISSUES_FILE, {"issues": sorted(self.issues, key=lambda i: i.get("id", ""))}
        )
        save_yaml(
            EVENTS_FILE,
            {"events": sorted(self.events, key=lambda e: e.get("timestamp", ""))},
        )
        save_yaml(
            COMM_FILE,
            {
                "messages": sorted(
                    self.communications, key=lambda m: m.get("timestamp", "")
                )
            },
        )
        update_todo_export(self.issues)


def ensure_state_files() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    for path, template in (
        (AGENTS_FILE, DEFAULT_AGENTS),
        (ISSUES_FILE, DEFAULT_ISSUES),
        (EVENTS_FILE, DEFAULT_EVENTS),
        (COMM_FILE, DEFAULT_COMMUNICATIONS),
    ):
        if not path.exists():
            save_yaml(path, template)


def load_policies() -> dict:
    policies = load_yaml(POLICIES_FILE, {})
    if "role_policies" not in policies:
        msg = "agent_policies.yaml должен содержать секцию role_policies"
        raise SystemExit(msg)
    policies.setdefault("role_priorities", list(policies["role_policies"].keys()))
    return policies


def load_initial_tasks() -> dict:
    data = load_yaml(INITIAL_TASKS_FILE, {"tasks": {}})
    return data.get("tasks", {})


def resolve_role(alias: str, policies: dict) -> str:
    alias_upper = alias.upper()
    role_policies = policies.get("role_policies", {})
    if alias_upper in role_policies:
        return alias_upper
    alias_lower = alias.lower()
    for role, policy in role_policies.items():
        title = (policy.get("title") or "").lower()
        if alias_lower == role.lower() or alias_lower in title:
            return role
    msg = f"Не удалось распознать роль '{alias}'"
    raise SystemExit(msg)


def infer_role(agent: dict, policies: dict) -> str | None:
    if agent.get("desired_role"):
        try:
            return resolve_role(agent["desired_role"], policies)
        except SystemExit:
            return None
    text = (agent.get("entry_message") or "").lower()
    competencies = [c.lower() for c in agent.get("competencies", [])]
    for role, keywords in ROLE_KEYWORDS.items():
        if any(word in text for word in keywords) or any(
            word in competencies for word in keywords
        ):
            return role
    return None


def generate_agent_id(role: str, agents: list[dict]) -> str:
    numbers: list[int] = []
    for entry in agents:
        agent_id = entry.get("id", "")
        if agent_id.startswith(f"{role}_"):
            try:
                numbers.append(int(agent_id.split("_")[1]))
            except (IndexError, ValueError):
                continue
    next_number = max(numbers, default=0) + 1
    return f"{role}_{next_number:03d}_v1"


def generate_pending_id(agents: list[dict]) -> str:
    numbers: list[int] = []
    for entry in agents:
        agent_id = entry.get("id", "")
        if agent_id.startswith("PENDING_"):
            try:
                numbers.append(int(agent_id.split("_")[1]))
            except (IndexError, ValueError):
                continue
    next_number = max(numbers, default=0) + 1
    return f"PENDING_{next_number:04d}"


def generate_issue_id(issues: list[dict]) -> str:
    numbers: list[int] = []
    for issue in issues:
        issue_id = issue.get("id", "")
        if issue_id.startswith("ISS-"):
            try:
                numbers.append(int(issue_id.split("-")[1]))
            except (IndexError, ValueError):
                continue
    next_number = max(numbers, default=0) + 1
    return f"ISS-{next_number:04d}"


def agent_roles(agent: dict) -> list[str]:
    roles = agent.get("roles")
    if roles:
        return sorted({role for role in roles if role})
    role = agent.get("role")
    return [role] if role else []


def get_role_counts(agents: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for agent in agents:
        if agent.get("status") != "active":
            continue
        for role in agent_roles(agent):
            counts[role] = counts.get(role, 0) + 1
    return counts


def select_role_for_agent(
    counts: dict[str, int],
    policies: dict,
    desired: str | None,
    message_source: dict,
) -> str | None:
    role_policies = policies.get("role_policies", {})
    priorities = policies.get("role_priorities", list(role_policies.keys()))
    if desired:
        try:
            return resolve_role(desired, policies)
        except SystemExit:
            pass
    inferred = infer_role(message_source, policies)
    if inferred:
        return inferred
    for role in priorities:
        policy = role_policies.get(role, {})
        minimum = policy.get("minimum", 0)
        if counts.get(role, 0) < minimum:
            return role
    for role in priorities:
        policy = role_policies.get(role, {})
        if not policy.get("auto_fill_capacity", False):
            continue
        capacity = policy.get("capacity", float("inf"))
        if counts.get(role, 0) < capacity:
            return role
    if priorities:

        def load_key(role: str) -> tuple[int, int]:
            return (counts.get(role, 0), priorities.index(role))

        return min(priorities, key=load_key)
    return None


def log_event(
    state: State, actor: str, message: str, entity: str | None = None
) -> None:
    state.events.append(
        {
            "timestamp": iso_now(),
            "actor": actor,
            "entity": entity,
            "message": message,
        }
    )


def record_communication(
    state: State,
    channel: str,
    sender: str,
    recipient: str | None,
    message: str,
    metadata: dict | None = None,
) -> None:
    state.communications.append(
        {
            "timestamp": iso_now(),
            "channel": channel,
            "sender": sender,
            "recipient": recipient,
            "message": message,
            "metadata": metadata or {},
        }
    )


def find_issue_by_id(issues: list[dict], issue_id: str) -> dict:
    for issue in issues:
        if issue.get("id") == issue_id:
            return issue
    msg = f"Issue {issue_id} не найден"
    raise SystemExit(msg)


def ensure_agent_exists(agents: list[dict], agent_id: str) -> dict:
    for agent in agents:
        if agent.get("id") == agent_id:
            return agent
    msg = f"Агент {agent_id} не найден"
    raise SystemExit(msg)


def create_issue(
    state: State,
    title: str,
    description: str,
    issue_type: str,
    role: str | None,
    assignee: str | None,
    priority: str,
    labels: list[str] | None = None,
    story_points: int | None = None,
    status: str = "New",
    reporter: str = "scheduler",
) -> dict:
    issue_id = generate_issue_id(state.issues)
    issue = {
        "id": issue_id,
        "title": title,
        "description": description,
        "type": issue_type,
        "status": status,
        "priority": priority,
        "role": role,
        "assignee": assignee,
        "reporter": reporter,
        "story_points": story_points,
        "labels": labels or [],
        "dependencies": [],
        "created_at": iso_now(),
        "updated_at": iso_now(),
        "origin": reporter,
    }
    state.issues.append(issue)
    log_event(
        state, reporter, f"Создано Issue {issue_id}: {title}", f"issue:{issue_id}"
    )
    return issue


def create_clarification_issue(state: State, agent: dict) -> None:
    title = f"Уточнить требования агента {agent['name']}"
    existing = [
        issue
        for issue in state.issues
        if issue.get("type") == "clarification"
        and issue.get("metadata", {}).get("agent_id") == agent.get("id")
    ]
    if existing:
        return
    description = agent.get("entry_message") or "Агент не предоставил контекст"
    issue = create_issue(
        state,
        title=title,
        description=description,
        issue_type="clarification",
        role="PO",
        assignee=None,
        priority="A",
        labels=["clarification", f"agent:{agent['id']}"],
        story_points=1,
        status="New",
        reporter="scheduler",
    )
    issue["metadata"] = {"agent_id": agent["id"]}
    record_communication(
        state,
        channel="product",
        sender="scheduler",
        recipient="PO",
        message=f"Требуется уточнение по агенту {agent['name']} ({agent['id']})",
        metadata={"issue_id": issue["id"]},
    )


def assign_role_to_agent(
    state: State,
    agent: dict,
    role: str,
    policies: dict,
    initial_tasks: dict,
) -> None:
    role_policy = policies.get("role_policies", {}).get(role)
    if not role_policy:
        msg = f"Для роли {role} не настроена политика"
        raise SystemExit(msg)
    agents = state.agents
    old_id = agent.get("id")
    new_id = generate_agent_id(role, agents)
    roles = agent_roles(agent)
    if role not in roles:
        roles.append(role)
    agent.update(
        {
            "id": new_id,
            "role": role,
            "roles": roles,
            "status": "active",
            "preferred_models": role_policy.get("preferred_models", []),
            "updated_at": iso_now(),
            "last_activity": iso_now(),
        }
    )
    if old_id != new_id:
        for entry in state.issues:
            if entry.get("assignee") == old_id:
                entry["assignee"] = new_id
            if entry.get("role") == old_id:
                entry["role"] = new_id
            labels = entry.get("labels", [])
            entry["labels"] = [label.replace(old_id, new_id) for label in labels]
        for message in state.communications:
            metadata = message.get("metadata", {})
            if metadata.get("agent_id") == old_id:
                metadata["agent_id"] = new_id
    log_event(
        state,
        "scheduler",
        f"Агент {old_id} получил роль {role} и новый ID {new_id}",
        f"agent:{new_id}",
    )
    build_agent_assets(agent, role_policy, state, initial_tasks)


def build_agent_assets(
    agent: dict, role_policy: dict, state: State, initial_tasks: dict
) -> None:
    agent_dir = STATE_DIR / "agents" / agent["id"]
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "logs").mkdir(exist_ok=True)
    profile = {
        "agent": {
            "id": agent["id"],
            "role": agent.get("role"),
            "roles": agent_roles(agent),
            "name": agent.get("name"),
            "created": agent.get("created_at", agent.get("updated_at", iso_now()))[:10],
            "status": agent.get("status"),
        },
        "workflow": role_policy.get("workflow", {}),
        "traits": {
            "preferred_models": agent.get("preferred_models", []),
        },
    }
    save_yaml(agent_dir / "profile.yaml", profile)
    prompt_path = Path(role_policy.get("prompt_path", ""))
    prompt_text = (
        prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
    )
    related_issue = next(
        (issue for issue in state.issues if issue.get("assignee") == agent["id"]), None
    )
    welcome_lines = [
        f"# Добро пожаловать, {agent['name']} ({agent['id']})",
        "",
    ]
    roles = agent_roles(agent)
    if len(roles) > 1:
        policies = load_policies()
        welcome_lines.append("## Роли")
        for role_code in roles:
            rp = policies.get("role_policies", {}).get(role_code, {})
            title = rp.get("title", role_code)
            descr = rp.get("description")
            line = f"- {role_code}: {title}"
            welcome_lines.append(line)
            if descr:
                welcome_lines.append(f"  {descr}")
        welcome_lines.append("")
    else:
        welcome_lines.append(f"## Роль: {role_policy.get('title', agent.get('role'))}")
        welcome_lines.append(role_policy.get("description", ""))
        welcome_lines.append("")
    models = agent.get("preferred_models", [])
    if models:
        welcome_lines.append("## Рекомендуемые модели")
        welcome_lines.extend([f"- {model}" for model in models])
        welcome_lines.append("")
    if related_issue:
        welcome_lines.append("## Текущая задача")
        welcome_lines.append(f"- ID: {related_issue['id']}")
        welcome_lines.append(f"- Статус: {related_issue['status']}")
        welcome_lines.append(f"- Заголовок: {related_issue['title']}")
        if related_issue.get("description"):
            welcome_lines.append(f"- Описание: {related_issue['description']}")
        welcome_lines.append("")
    if prompt_text:
        welcome_lines.append("## Промпт")
        welcome_lines.append(prompt_text.strip())
        welcome_lines.append("")
    (agent_dir / "welcome.md").write_text("\n".join(welcome_lines), encoding="utf-8")

    template_key = role_policy.get("initial_task_key")
    if template_key:
        template = initial_tasks.get(template_key)
        if template:
            ensure_initial_issue(state, agent, template)


def ensure_initial_issue(state: State, agent: dict, template: dict) -> None:
    existing = [
        issue
        for issue in state.issues
        if issue.get("assignee") == agent["id"]
        and issue.get("status") not in {"Done", "Archived"}
    ]
    if existing:
        return
    labels = [label.lstrip("+") for label in template.get("tags", [])]
    issue = create_issue(
        state,
        title=template.get("title", "Онбординг"),
        description=template.get("description", ""),
        issue_type="task",
        role=template.get("role") or agent_roles(agent)[0]
        if agent_roles(agent)
        else None,
        assignee=agent["id"],
        priority=template.get("priority", "B"),
        labels=labels,
        story_points=template.get("story_points"),
        status="In Refinement",
        reporter="scheduler",
    )
    issue["origin"] = "onboarding"


def update_todo_export(issues: list[dict]) -> None:
    lines: list[str] = []
    for issue in issues:
        if issue.get("status") == "Archived":
            continue
        priority = issue.get("priority", "B")
        created = issue.get("created_at", iso_now())[:10]
        title = issue.get("title", "")
        role = issue.get("role")
        line = f"({priority}) {created} {title}".strip()
        extras: list[str] = []
        if role:
            extras.append(f"@{role.lower()}")
        issue_id = issue.get("id")
        extras.append(f"+issue_id:{issue_id}")
        status = issue.get("status", "New").replace(" ", "_").lower()
        extras.append(f"+status:{status}")
        assignee = issue.get("assignee")
        if assignee:
            extras.append(f"+assignee:{assignee}")
        story_points = issue.get("story_points")
        if story_points is not None:
            extras.append(f"+sp{story_points}")
        for label in issue.get("labels", []):
            extras.append(f"+{label}")
        line = " ".join([line, *extras])
        lines.append(line.strip())
    TODO_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def ensure_status_transition(current: str, target: str) -> None:
    allowed = STATUS_TRANSITIONS.get(current)
    if allowed is None:
        msg = f"Неизвестный статус {current}"
        raise SystemExit(msg)
    if target not in allowed:
        msg = f"Статус {current} нельзя перевести в {target}"
        raise SystemExit(msg)


def scheduler_run(state: State, policies: dict, initial_tasks: dict) -> list[str]:
    messages: list[str] = []
    counts = get_role_counts(state.agents)
    for agent in list(state.agents):
        if agent.get("status") != "pending":
            continue
        role = select_role_for_agent(counts, policies, agent.get("desired_role"), agent)
        if role:
            assign_role_to_agent(state, agent, role, policies, initial_tasks)
            counts[role] = counts.get(role, 0) + 1
            messages.append(f"Агент {agent['name']} получил роль {role}")
        else:
            create_clarification_issue(state, agent)
            messages.append(
                f"Агент {agent['name']} ожидает уточнения (роль не определена)"
            )
    return messages


def scheduler_status(state: State, policies: dict) -> None:
    counts = get_role_counts(state.agents)
    priorities = policies.get("role_priorities", [])
    for role in priorities:
        policy = policies.get("role_policies", {}).get(role, {})
        policy.get("capacity", "∞")
        policy.get("minimum", 0)
        counts.get(role, 0)
    pending = [agent for agent in state.agents if agent.get("status") == "pending"]
    if pending:
        for _agent in pending:
            pass
    if state.events:
        for _event in state.events[-5:]:
            pass


def ensure_role_exists(role: str, policies: dict) -> None:
    if role not in policies.get("role_policies", {}):
        msg = f"Политика для роли {role} не настроена"
        raise SystemExit(msg)


def list_agents(state: State, args: argparse.Namespace) -> None:
    agents = state.agents
    if args.role:
        policies = load_policies()
        role_code = resolve_role(args.role, policies)
        agents = [agent for agent in agents if role_code in agent_roles(agent)]
    if not agents:
        return
    for agent in agents:
        "/".join(agent_roles(agent)) or "-"


def info_agent(state: State, args: argparse.Namespace) -> None:
    agent = ensure_agent_exists(state.agents, args.agent_id)
    agent_copy = dict(agent)
    agent_copy["roles"] = agent_roles(agent)
    issues = [issue for issue in state.issues if issue.get("assignee") == agent["id"]]
    if issues:
        for _issue in issues:
            pass


def ingest_agent(state: State, policies: dict, args: argparse.Namespace) -> None:
    pending_id = generate_pending_id(state.agents)
    entry = {
        "id": pending_id,
        "name": args.name,
        "status": "pending",
        "role": None,
        "competencies": args.competency or [],
        "desired_role": args.desired_role,
        "entry_message": args.message,
        "created_at": iso_now(),
        "updated_at": iso_now(),
        "last_activity": None,
        "preferred_models": [],
        "notes": None,
    }
    state.agents.append(entry)
    record_communication(
        state,
        channel="onboarding",
        sender=args.sender,
        recipient="scheduler",
        message=args.message,
        metadata={"agent_id": pending_id},
    )
    log_event(
        state,
        args.sender,
        f"Получен запрос на онбординг {pending_id}",
        f"agent:{pending_id}",
    )
    initial_tasks = load_initial_tasks()
    messages = scheduler_run(state, policies, initial_tasks)
    for _message in messages:
        pass


def create_manual_agent(
    state: State, policies: dict, initial_tasks: dict, args: argparse.Namespace
) -> None:
    role = resolve_role(args.role, policies)
    agent_entry = {
        "id": generate_agent_id(role, state.agents),
        "name": args.name,
        "status": "active",
        "role": role,
        "roles": [role],
        "competencies": [],
        "desired_role": None,
        "entry_message": None,
        "created_at": iso_now(),
        "updated_at": iso_now(),
        "last_activity": iso_now(),
        "preferred_models": [],
        "notes": None,
    }
    state.agents.append(agent_entry)
    assign_role_to_agent(state, agent_entry, role, policies, initial_tasks)


def set_agent_status(state: State, args: argparse.Namespace) -> None:
    agent = ensure_agent_exists(state.agents, args.agent_id)
    agent["status"] = args.status
    agent["updated_at"] = iso_now()
    if args.status == "active":
        agent["last_activity"] = iso_now()
    log_event(
        state,
        args.actor,
        f"Статус агента {args.agent_id} изменён на {args.status}",
        f"agent:{args.agent_id}",
    )


def touch_agent(state: State, args: argparse.Namespace) -> None:
    agent = ensure_agent_exists(state.agents, args.agent_id)
    agent["last_activity"] = iso_now()
    agent["updated_at"] = iso_now()
    log_event(
        state,
        args.actor,
        f"Обновлена активность {args.agent_id}",
        f"agent:{args.agent_id}",
    )


def remove_agent(state: State, args: argparse.Namespace) -> None:
    agent = ensure_agent_exists(state.agents, args.agent_id)
    state.agents.remove(agent)
    if args.purge:
        agent_dir = STATE_DIR / "agents" / args.agent_id
        if agent_dir.exists():
            for child in agent_dir.glob("**/*"):
                if child.is_file():
                    child.unlink()
            for child in sorted(agent_dir.glob("**/*"), reverse=True):
                if child.is_dir():
                    child.rmdir()
            agent_dir.rmdir()
    log_event(
        state, args.actor, f"Агент {args.agent_id} удалён", f"agent:{args.agent_id}"
    )


def list_issues(state: State, args: argparse.Namespace) -> None:
    issues = state.issues
    if args.role:
        policies = load_policies()
        role_code = resolve_role(args.role, policies)
        issues = [issue for issue in issues if issue.get("role") == role_code]
    if args.status:
        issues = [issue for issue in issues if issue.get("status") == args.status]
    if args.assignee:
        issues = [issue for issue in issues if issue.get("assignee") == args.assignee]
    if not issues:
        return
    for _issue in issues:
        pass


def info_issue(state: State, args: argparse.Namespace) -> None:
    find_issue_by_id(state.issues, args.issue_id)


def move_issue(state: State, args: argparse.Namespace) -> None:
    issue = find_issue_by_id(state.issues, args.issue_id)
    target = args.status
    ensure_status_transition(issue.get("status", "New"), target)
    issue["status"] = target
    issue["updated_at"] = iso_now()
    log_event(
        state, args.actor, f"Issue {issue['id']} → {target}", f"issue:{issue['id']}"
    )


def assign_issue(state: State, args: argparse.Namespace) -> None:
    issue = find_issue_by_id(state.issues, args.issue_id)
    agent = ensure_agent_exists(state.agents, args.agent_id)
    issue["assignee"] = agent["id"]
    current_role = issue.get("role")
    roles = agent_roles(agent)
    if current_role and current_role not in roles:
        msg = f"Агент {agent['id']} не обладает ролью {current_role}"
        raise SystemExit(msg)
    if not current_role and roles:
        issue["role"] = roles[0]
    issue["updated_at"] = iso_now()
    log_event(
        state,
        args.actor,
        f"Issue {issue['id']} назначено {agent['id']}",
        f"issue:{issue['id']}",
    )


def create_issue_cli(state: State, args: argparse.Namespace) -> None:
    policies = load_policies()
    role = resolve_role(args.role, policies) if args.role else None
    issue = create_issue(
        state,
        title=args.title,
        description=args.description or "",
        issue_type=args.type,
        role=role,
        assignee=args.assignee,
        priority=args.priority,
        labels=[label.lstrip("+") for label in (args.label or [])],
        story_points=args.story_points,
        status=args.status,
        reporter=args.actor,
    )
    if args.assignee:
        issue["assignee"] = args.assignee


def communications_send_cli(state: State, args: argparse.Namespace) -> None:
    metadata = {"agent_id": args.agent_id} if args.agent_id else {}
    record_communication(
        state, args.channel, args.sender, args.recipient, args.message, metadata
    )
    log_event(state, args.sender, f"Сообщение в канал {args.channel}: {args.message}")
    if args.create_issue:
        load_policies()
        issue = create_issue(
            state,
            title=f"Запрос пользователя: {args.message[:60]}",
            description=args.message,
            issue_type="story",
            role="PO",
            assignee=args.recipient if args.recipient else None,
            priority="A",
            labels=["user-request"],
            story_points=1,
            status="New",
            reporter=args.sender,
        )
        issue.setdefault("metadata", {})["source_channel"] = args.channel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Оркестратор агентов и задач")
    sub = parser.add_subparsers(dest="command")

    agents = sub.add_parser("agents", help="Операции с агентами")
    agents_sub = agents.add_subparsers(dest="action")

    list_cmd = agents_sub.add_parser("list")
    list_cmd.add_argument("--role", default=None)

    info_cmd = agents_sub.add_parser("info")
    info_cmd.add_argument("agent_id")

    ingest_cmd = agents_sub.add_parser(
        "ingest", help="Зарегистрировать входящего агента"
    )
    ingest_cmd.add_argument("name")
    ingest_cmd.add_argument("message")
    ingest_cmd.add_argument("--competency", action="append", default=None)
    ingest_cmd.add_argument("--desired-role", default=None)
    ingest_cmd.add_argument("--sender", default="user")

    onboard_cmd = agents_sub.add_parser("onboard", help="Синоним ingest")
    onboard_cmd.add_argument("name")
    onboard_cmd.add_argument("message")
    onboard_cmd.add_argument("--competency", action="append", default=None)
    onboard_cmd.add_argument("--desired-role", default=None)
    onboard_cmd.add_argument("--sender", default="user")

    create_cmd = agents_sub.add_parser("create", help="Создать агента с явной ролью")
    create_cmd.add_argument("role")
    create_cmd.add_argument("name")

    status_cmd = agents_sub.add_parser("update-status")
    status_cmd.add_argument("agent_id")
    status_cmd.add_argument(
        "status", choices=["active", "paused", "retired", "pending"]
    )
    status_cmd.add_argument("--actor", default="operator")

    touch_cmd = agents_sub.add_parser("touch")
    touch_cmd.add_argument("agent_id")
    touch_cmd.add_argument("--actor", default="operator")

    remove_cmd = agents_sub.add_parser("remove")
    remove_cmd.add_argument("agent_id")
    remove_cmd.add_argument("--purge", action="store_true")
    remove_cmd.add_argument("--actor", default="operator")

    issues = sub.add_parser("issues", help="Работа с задачами")
    issues_sub = issues.add_subparsers(dest="action")

    issues_list = issues_sub.add_parser("list")
    issues_list.add_argument("--role", default=None)
    issues_list.add_argument("--status", default=None)
    issues_list.add_argument("--assignee", default=None)

    issues_info = issues_sub.add_parser("info")
    issues_info.add_argument("issue_id")

    issues_move = issues_sub.add_parser("move")
    issues_move.add_argument("issue_id")
    issues_move.add_argument("status", choices=STATUS_TRANSITIONS.keys())
    issues_move.add_argument("--actor", default="operator")

    issues_assign = issues_sub.add_parser("assign")
    issues_assign.add_argument("issue_id")
    issues_assign.add_argument("agent_id")
    issues_assign.add_argument("--actor", default="operator")

    issues_create = issues_sub.add_parser("create")
    issues_create.add_argument("title")
    issues_create.add_argument("--description", default="")
    issues_create.add_argument("--type", default="task")
    issues_create.add_argument("--role", default=None)
    issues_create.add_argument("--assignee", default=None)
    issues_create.add_argument("--priority", default="B")
    issues_create.add_argument("--label", action="append", default=None)
    issues_create.add_argument(
        "--story-points", dest="story_points", type=int, default=None
    )
    issues_create.add_argument("--status", default="New")
    issues_create.add_argument("--actor", default="operator")

    comm = sub.add_parser("communications", help="Коммуникация")
    comm_sub = comm.add_subparsers(dest="action")
    comm_send = comm_sub.add_parser("send")
    comm_send.add_argument("channel")
    comm_send.add_argument("message")
    comm_send.add_argument("--sender", default="user")
    comm_send.add_argument("--recipient", default="PO")
    comm_send.add_argument("--agent-id", dest="agent_id", default=None)
    comm_send.add_argument("--create-issue", action="store_true")

    scheduler = sub.add_parser("scheduler", help="Планировщик")
    scheduler_sub = scheduler.add_subparsers(dest="action")
    scheduler_sub.add_parser("run")
    scheduler_sub.add_parser("status")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return
    state = State()
    policies = load_policies()
    initial_tasks = load_initial_tasks()

    if args.command == "agents":
        if args.action == "list":
            list_agents(state, args)
        elif args.action == "info":
            info_agent(state, args)
        elif args.action in {"ingest", "onboard"}:
            ingest_agent(state, policies, args)
        elif args.action == "create":
            create_manual_agent(state, policies, initial_tasks, args)
        elif args.action == "update-status":
            set_agent_status(state, args)
        elif args.action == "touch":
            touch_agent(state, args)
        elif args.action == "remove":
            remove_agent(state, args)
        else:
            msg = "Неизвестная команда agents"
            raise SystemExit(msg)
    elif args.command == "issues":
        if args.action == "list":
            list_issues(state, args)
        elif args.action == "info":
            info_issue(state, args)
        elif args.action == "move":
            move_issue(state, args)
        elif args.action == "assign":
            assign_issue(state, args)
        elif args.action == "create":
            create_issue_cli(state, args)
        else:
            msg = "Неизвестная команда issues"
            raise SystemExit(msg)
    elif args.command == "communications":
        if args.action == "send":
            communications_send_cli(state, args)
        else:
            msg = "Неизвестная команда communications"
            raise SystemExit(msg)
    elif args.command == "scheduler":
        if args.action == "run":
            messages = scheduler_run(state, policies, initial_tasks)
            if messages:
                for _message in messages:
                    pass
            else:
                pass
        elif args.action == "status":
            scheduler_status(state, policies)
        else:
            msg = "Неизвестная команда scheduler"
            raise SystemExit(msg)
    else:
        msg = "Неизвестная команда"
        raise SystemExit(msg)

    state.persist()


if __name__ == "__main__":
    main()
