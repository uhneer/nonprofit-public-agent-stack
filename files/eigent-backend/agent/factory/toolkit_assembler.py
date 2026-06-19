# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

import functools
import inspect
import logging
import os
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from camel.toolkits import (
    FunctionTool,
    MCPToolkit,
    PlanningWorktreeToolkit,
    RegisteredAgentToolkit,
    ToolkitMessageIntegration,
    WebFetchToolkit,
)

from app.agent.toolkit.depth_limited_agent_toolkit import (
    DepthLimitedAgentToolkit,
    _normalize_nullish,
)
from app.agent.toolkit.file_write_toolkit import FileToolkit
from app.agent.toolkit.human_toolkit import HumanToolkit
from app.agent.toolkit.hybrid_browser_toolkit import HybridBrowserToolkit
from app.agent.toolkit.note_taking_toolkit import NoteTakingToolkit
from app.agent.toolkit.observable_todo_toolkit import ObservableTodoToolkit
from app.agent.toolkit.screenshot_toolkit import ScreenshotToolkit
from app.agent.toolkit.search_toolkit import SearchToolkit
from app.agent.toolkit.skill_toolkit import SkillToolkit
from app.agent.toolkit.terminal_toolkit import TerminalToolkit
from app.agent.toolkit.web_deploy_toolkit import WebDeployToolkit
from app.component.environment import env
from app.hands.interface import IHands
from app.model.chat import Chat
from app.service.task import Agents
from app.service.mcp_config import read_mcp_config
from app.utils.browser_launcher import normalize_cdp_url

logger = logging.getLogger("toolkit_assembler")

DEFAULT_SINGLE_AGENT_TOOLKIT_CONFIG: dict[str, Any] = {
    "human": {"enabled": True},
    "file": {"enabled": True},
    "web_deploy": {"enabled": True},
    "screenshot": {"enabled": True},
    "skill": {"enabled": True},
    "todo": {"enabled": True},
    "search": {"enabled": True},
    "browser": {"enabled": True},
    "terminal": {"enabled": True},
    "note": {"enabled": True},
    "web_fetch": {"enabled": True},
    "planning_worktree": {"enabled": True},
    "mcp": {"enabled": True},
    "agent": {"enabled": True},
}


@dataclass
class ToolkitAssembly:
    tools: list[FunctionTool | Callable] = field(default_factory=list)
    tool_names: list[str] = field(default_factory=list)
    toolkits_to_register_agent: list[RegisteredAgentToolkit] = field(
        default_factory=list
    )
    observable_todo_toolkit: ObservableTodoToolkit | None = None
    browser_toolkit: HybridBrowserToolkit | None = None
    browser_port: int | None = None
    browser_cdp_url: str | None = None
    browser_session_id: str | None = None
    browser_owned_by_hands: bool = False

    def add_tools(
        self,
        tools: list[FunctionTool | Callable],
        toolkit_name: str,
    ) -> None:
        if not tools:
            return
        _tag_tools(tools, toolkit_name)
        self.tools.extend(tools)
        if toolkit_name not in self.tool_names:
            self.tool_names.append(toolkit_name)


def _merged_config(options: Chat) -> dict[str, Any]:
    config = {
        key: dict(value) if isinstance(value, dict) else value
        for key, value in DEFAULT_SINGLE_AGENT_TOOLKIT_CONFIG.items()
    }
    for key, value in (options.toolkit_config or {}).items():
        config[key] = value
    return config


def _enabled(config: dict[str, Any], name: str, default: bool = True) -> bool:
    value = config.get(name)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        return bool(value.get("enabled", default))
    return bool(value)


def _options(config: dict[str, Any], name: str) -> dict[str, Any]:
    value = config.get(name)
    if not isinstance(value, dict):
        return {}
    return {key: item for key, item in value.items() if key != "enabled"}


def _tag_tools(
    tools: list[FunctionTool | Callable], toolkit_name: str
) -> None:
    for tool in tools:
        try:
            tool._toolkit_name = toolkit_name
        except Exception:
            pass


def _get_browser_port(browser: dict) -> int:
    raw_port = browser.get("port")
    if raw_port is not None:
        return int(raw_port)

    raw_endpoint = browser.get("endpoint") or browser.get("cdp_url")
    if raw_endpoint:
        _, _, port = normalize_cdp_url(str(raw_endpoint))
        return port

    return int(env("browser_port", "9222"))


def _get_browser_endpoint(browser: dict) -> str:
    raw_endpoint = browser.get("endpoint") or browser.get("cdp_url")
    if raw_endpoint:
        endpoint, _, _ = normalize_cdp_url(str(raw_endpoint))
        return endpoint

    return f"http://localhost:{_get_browser_port(browser)}"


def _browser_enabled_tools() -> list[str]:
    return [
        "browser_click",
        "browser_type",
        "browser_back",
        "browser_forward",
        "browser_select",
        "browser_console_exec",
        "browser_console_view",
        "browser_switch_tab",
        "browser_enter",
        "browser_visit_page",
        "browser_scroll",
        "browser_sheet_read",
        "browser_sheet_input",
        "browser_get_page_snapshot",
        "browser_open",
        "browser_upload_file",
        "browser_download_file",
    ]


def _mcp_config(options: Chat, hands: IHands | None) -> dict[str, Any] | None:
    # Per-task selection (options.installed_mcp) wins on conflict.
    # Disk config (~/.eigent/mcp.json via read_mcp_config()) fills in any
    # server not explicitly passed. This closes the gap where MCPs added via
    # UI never reach the agent because the frontend does not echo them into
    # the Chat request body. With this bridge, anything in the global MCP
    # config is available to single-agent + multi-agent runs by default.
    options_servers = dict(
        (options.installed_mcp or {}).get("mcpServers", {})
    )
    disk_servers: dict[str, Any] = {}
    try:
        disk_config = read_mcp_config() or {}
        disk_servers = dict(disk_config.get("mcpServers", {}))
    except Exception:
        logger.warning(
            "Failed to read disk MCP config from ~/.eigent/mcp.json",
            exc_info=True,
        )
    servers = {**disk_servers, **options_servers}
    if not servers:
        return None

    if hands is not None:
        servers = {
            name: cfg
            for name, cfg in servers.items()
            if hands.can_use_mcp(name)
        }
        if not servers:
            logger.info("Skipping MCPToolkit: no MCP servers allowed")
            return None

    normalized_servers = {}
    for name, cfg in servers.items():
        server_cfg = dict(cfg)
        server_env = dict(server_cfg.get("env", {}))
        server_env.setdefault(
            "MCP_REMOTE_CONFIG_DIR",
            env("MCP_REMOTE_CONFIG_DIR", os.path.expanduser("~/.mcp-auth")),
        )
        server_cfg["env"] = server_env
        normalized_servers[name] = _expand_env_placeholders(server_cfg)

    return {"mcpServers": normalized_servers}


_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _expand_env_placeholders(obj: Any) -> Any:
    r"""Recursively expand ${VAR} placeholders in strings using process env.

    MCP server configs commonly reference env vars for tokens (e.g.
    `"Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"`). Neither
    CAMEL's MCPClient nor Python's os.path.expandvars handle ${VAR} on
    Windows. Without this substitution the literal "${VAR}" string is sent
    as the header value and the remote MCP server rejects auth.

    Missing env vars leave the placeholder intact and emit a warning, so
    the connect() error includes the recognizable placeholder rather than
    an empty string.
    """
    if isinstance(obj, str):
        def _repl(match: re.Match[str]) -> str:
            var_name = match.group(1)
            value = os.environ.get(var_name)
            if value is None:
                logger.warning(
                    "MCP config references env var %s but it is not set; "
                    "literal placeholder will be passed through.",
                    var_name,
                )
                return match.group(0)
            return value

        return _ENV_PATTERN.sub(_repl, obj)
    if isinstance(obj, dict):
        return {k: _expand_env_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_placeholders(item) for item in obj]
    return obj


def _strip_nullish_kwargs(func: Callable) -> Callable:
    r"""Wrap a FunctionTool callable so GLM-emitted "null"/"none"/"" strings
    in optional kwargs are dropped before the call reaches the MCP server.

    GLM-5.2 tends to emit literal `"null"` for optional params instead of
    omitting them. Many MCP servers (e.g. mcp-searxng v1.7.1) strict-validate
    args: `pageno: "null"` fails `typeof === "number"` even though the field
    is optional. Dropping the kwarg entirely lets validators see `undefined`,
    which is the intended "not provided" state.

    Also recursively normalizes nested dicts (e.g. complex tool args) and
    coerces top-level nullish strings on positional args.
    """
    logger = logging.getLogger(__name__)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        cleaned_kwargs = {
            k: _deep_normalize(v)
            for k, v in kwargs.items()
            if not _is_nullish_string(v)
        }
        cleaned_args = tuple(
            _deep_normalize(a) for a in args if not _is_nullish_string(a)
        )
        if len(cleaned_kwargs) != len(kwargs) or len(cleaned_args) != len(args):
            dropped = [
                k for k, v in kwargs.items() if _is_nullish_string(v)
            ]
            logger.info(
                "MCP arg sanitizer: dropped nullish kwarg(s) %s from %s",
                dropped,
                getattr(func, "__name__", repr(func)),
            )
        return func(*cleaned_args, **cleaned_kwargs)

    return wrapper


def _coerce_to_schema_type(value: Any, schema_type: str) -> Any:
    r"""Coerce value to match a JSON schema type hint.

    Used to fix LLM tool calls where GLM-5.2 emits numeric values as strings
    (e.g. `pageno: "1"`) which strict MCP validators reject. Only coerces
    when the source value is a string AND the target type is numeric/boolean.
    Never coerces away from `str` since string fields legitimately hold
    numeric-looking content like language codes or IDs.
    """
    if not isinstance(value, str) or _is_nullish_string(value):
        return value
    raw = value.strip()
    if schema_type in ("integer", "int", "number"):
        try:
            if schema_type == "integer":
                if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
                    return int(raw)
                return int(float(raw))
            return float(raw)
        except (ValueError, TypeError):
            return value
    if schema_type in ("boolean", "bool"):
        low = raw.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        return value
    if schema_type in ("object", "dict"):
        return {} if raw == "" else value
    if schema_type in ("array", "list"):
        return [] if raw == "" else value
    return value


_DROP_EMPTY_FOR_TYPES = {"integer", "int", "number", "boolean", "bool",
                          "object", "dict", "array", "list"}


def _schema_parameters(tool: FunctionTool) -> dict[str, Any]:
    r"""Return the ``parameters`` block from a FunctionTool's OpenAI schema.

    Handles two layouts:
      - Flat: ``schema["parameters"]`` (e.g. CAMEL-built native tools)
      - Nested (OpenAI tool-call format, used by MCPClient._build_tool_schema):
        ``schema["function"]["parameters"]``
    Returns ``{}`` if neither path exists.
    """
    schema = getattr(tool, "openai_tool_schema", None)
    if not isinstance(schema, dict):
        return {}
    params = schema.get("parameters")
    if not isinstance(params, dict):
        fn = schema.get("function")
        if isinstance(fn, dict):
            params = fn.get("parameters")
    if not isinstance(params, dict):
        return {}
    return params


def _schema_for_param(tool: FunctionTool, param: str) -> str | None:
    r"""Return the JSON-schema type hint for a parameter, if known.

    Used by the schema-aware sanitizer to decide when numeric-string coercion
    is safe. Returns None if the schema or property is missing.
    """
    params = _schema_parameters(tool)
    props = params.get("properties") or {}
    prop = props.get(param) if isinstance(props, dict) else None
    if not isinstance(prop, dict):
        return None
    t = prop.get("type")
    if isinstance(t, list) and t:
        return t[0]
    return t


def _schema_aware_sanitize(
    func: Callable,
    tool: FunctionTool,
) -> Callable:
    r"""Wrap a FunctionTool callable with nullish + schema-driven coercion.

    Logs every original kwarg dict at INFO so we can diagnose what GLM-5.2
    actually emits. Then:
      1. Drops nullish-string kwargs (null/none/empty).
      2. Coerces numeric/boolean strings when the schema declares a number/
         integer/boolean type for that parameter.
      3. Logs each transformation so failures are bisectable.
    """
    log = logging.getLogger(__name__)
    func_name = getattr(func, "__name__", repr(func))
    tool_name = tool.get_function_name() if tool else func_name

    def _clean_kwargs(raw_kwargs: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        allowed = _schema_param_names(tool)
        cleaned: dict[str, Any] = {}
        transformations: list[str] = []
        for k, v in raw_kwargs.items():
            if allowed and k not in allowed:
                transformations.append(
                    f"drop unknown kwarg {k}={v!r} (not in schema)"
                )
                continue
            if _is_nullish_string(v):
                transformations.append(f"drop {k}={v!r}")
                continue
            schema_type = _schema_for_param(tool, k)
            if (
                isinstance(v, str)
                and v.strip() == ""
                and schema_type in _DROP_EMPTY_FOR_TYPES
            ):
                transformations.append(
                    f"drop empty {k} (schema type={schema_type})"
                )
                continue
            coerced = _coerce_to_schema_type(v, schema_type) if schema_type else v
            if coerced is not v and coerced != v:
                transformations.append(
                    f"coerce {k}: {v!r} ({type(v).__name__}) -> "
                    f"{coerced!r} ({type(coerced).__name__}) "
                    f"[schema type={schema_type}]"
                )
            cleaned[k] = _deep_normalize(coerced)
        if raw_kwargs:
            log.info(
                "MCP arg sanitizer[%s]: raw kwargs=%s allowed=%s",
                tool_name,
                raw_kwargs,
                sorted(allowed),
            )
        if transformations:
            log.info(
                "MCP arg sanitizer[%s]: %s",
                tool_name,
                "; ".join(transformations),
            )
        return cleaned, transformations

    async def async_wrapper(**kwargs: Any) -> Any:
        cleaned, _ = _clean_kwargs(kwargs)
        return await func.async_call(**cleaned)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        sig_params = [
            p.name
            for p in inspect.signature(func).parameters.values()
        ][: len(args)]
        merged = {**dict(zip(sig_params, args)), **kwargs}
        cleaned, _ = _clean_kwargs(merged)
        return func(**cleaned)

    async_wrapper.__name__ = f"{func_name}_sanitized_async"
    return wrapper, async_wrapper


def _is_nullish_string(value: Any) -> bool:
    if value is None:
        return True
    return (
        isinstance(value, str)
        and value.strip().lower() in {"null", "none", ""}
    )


def _schema_param_names(tool: FunctionTool) -> set[str]:
    r"""Return the set of parameter names declared in the tool's OpenAPI schema.
    Used to drop stray kwargs that GLM emits but the MCP server doesn't know
    about (e.g. message_title/description/attachment injected by
    ToolkitMessageIntegration)."""
    params = _schema_parameters(tool)
    props = params.get("properties") or {}
    if isinstance(props, dict):
        return set(props.keys())
    return set()


def _deep_normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: _deep_normalize(v)
            for k, v in value.items()
            if not _is_nullish_string(v)
        }
    if isinstance(value, list):
        return [
            _deep_normalize(item)
            for item in value
            if not _is_nullish_string(item)
        ]
    norm = _normalize_nullish(value)
    return norm


def _sanitize_mcp_tools(tools: list[FunctionTool]) -> list[FunctionTool]:
    r"""Wrap each MCP-sourced FunctionTool so tool-call args are sanitized
    before being forwarded to the MCP server. Preserves the OpenAI tool
    schema (so the LLM sees the same surface) — only the call-time args
    are normalized.

    CRITICAL: Eigent's ChatAgent invokes MCP tools via ``tool.func.async_call``
    (see listen_chat_agent.py:656), NOT via ``FunctionTool.__call__`` or
    ``FunctionTool.async_call``. The CAMEL MCPClient attaches ``async_call`` as
    an attribute on the sync ``dynamic_fn`` (mcp_client.py:833), so wrapping
    only ``tool.func`` leaves the agent's actual dispatch path untouched.

    This function installs sanitizers on BOTH call surfaces:
      - ``tool.func`` (sync ``adaptive_dynamic_function``)
      - ``tool.func.async_call`` (the inner ``async_mcp_call`` closure)

    Two layers of defense against GLM-5.2 schema drift:
      - nullish string dropping (literal "null"/"none"/"")
      - schema-driven numeric/boolean coercion for known-typed params
    Plus an INFO log of every original kwarg dict so failures are bisectable.
    """
    for tool in tools:
        original = tool.func
        if getattr(original, "_eigent_nullish_sanitized", False):
            continue
        sync_wrapped, async_wrapped = _schema_aware_sanitize(original, tool)
        sync_wrapped._eigent_nullish_sanitized = True
        sync_wrapped.async_call = async_wrapped  # the path the agent uses
        tool.func = sync_wrapped
    return tools


async def assemble_single_agent_toolkits(
    options: Chat,
    *,
    task_id: str,
    working_directory: str,
    hands: IHands | None,
    can_delegate: bool,
    current_depth: int = 0,
    max_depth: int = 1,
) -> ToolkitAssembly:
    config = _merged_config(options)
    assembly = ToolkitAssembly()

    human_toolkit = HumanToolkit(options.project_id, Agents.single_agent)
    message_integration = ToolkitMessageIntegration(
        message_handler=human_toolkit.send_message_to_user
    )

    if _enabled(config, "human"):
        assembly.add_tools(
            human_toolkit.get_tools(), HumanToolkit.toolkit_name()
        )

    if _enabled(config, "file"):
        file_options = {
            "working_directory": working_directory,
            **_options(config, "file"),
        }
        toolkit = FileToolkit(
            options.project_id,
            **file_options,
        )
        toolkit.agent_name = Agents.single_agent
        toolkit = message_integration.register_toolkits(toolkit)
        assembly.add_tools(toolkit.get_tools(), FileToolkit.toolkit_name())

    if _enabled(config, "web_deploy"):
        toolkit = WebDeployToolkit(
            api_task_id=options.project_id,
            **_options(config, "web_deploy"),
        )
        toolkit.agent_name = Agents.single_agent
        toolkit = message_integration.register_toolkits(toolkit)
        assembly.add_tools(
            toolkit.get_tools(), WebDeployToolkit.toolkit_name()
        )

    if _enabled(config, "screenshot"):
        screenshot_options = {
            "working_directory": working_directory,
            "agent_name": Agents.single_agent,
            **_options(config, "screenshot"),
        }
        toolkit = ScreenshotToolkit(
            options.project_id,
            **screenshot_options,
        )
        assembly.toolkits_to_register_agent.append(toolkit)
        registered = message_integration.register_toolkits(toolkit)
        assembly.add_tools(
            registered.get_tools(), ScreenshotToolkit.toolkit_name()
        )

    if _enabled(config, "skill"):
        skill_options = {
            "working_directory": working_directory,
            "user_id": options.skill_config_user_id(),
            **_options(config, "skill"),
        }
        toolkit = SkillToolkit(
            options.project_id,
            Agents.single_agent,
            **skill_options,
        )
        toolkit = message_integration.register_toolkits(toolkit)
        assembly.add_tools(toolkit.get_tools(), SkillToolkit.toolkit_name())

    if _enabled(config, "todo"):
        todo_options = {
            "working_dir": working_directory,
            **_options(config, "todo"),
        }
        todo_toolkit = ObservableTodoToolkit(
            api_task_id=options.project_id,
            task_id=task_id,
            **todo_options,
        )
        todo_toolkit.agent_name = Agents.single_agent
        assembly.observable_todo_toolkit = todo_toolkit
        assembly.add_tools(
            todo_toolkit.get_tools(), ObservableTodoToolkit.toolkit_name()
        )

    if _enabled(config, "search"):
        search_tools = SearchToolkit.get_can_use_tools(
            options.project_id, agent_name=Agents.single_agent
        )
        if search_tools:
            search_tools = message_integration.register_functions(search_tools)
            assembly.add_tools(search_tools, SearchToolkit.toolkit_name())

    if _enabled(config, "browser") and (
        hands is None or hands.can_use_browser()
    ):
        toolkit_session_id = str(uuid.uuid4())[:8]
        selected_port: int | None = None
        cdp_url: str | None = None
        cdp_owned_by_hands = False

        if options.cdp_browsers:
            # Reuse the same pool as the Browser Agent so concurrent projects
            # do not accidentally claim the same CDP browser tab set.
            from app.agent.factory.browser import _cdp_pool_manager

            selected_browser = _cdp_pool_manager.acquire_browser(
                options.cdp_browsers,
                toolkit_session_id,
                options.task_id,
            )
            if selected_browser is None:
                selected_browser = options.cdp_browsers[0]
                logger.warning(
                    "No available CDP browser in pool for Single Agent; "
                    "using first browser",
                    extra={
                        "project_id": options.project_id,
                        "task_id": options.task_id,
                    },
                )
            selected_port = _get_browser_port(selected_browser)
            cdp_url = _get_browser_endpoint(selected_browser)
        else:
            existing_cdp_url = env("EIGENT_CDP_URL", "").strip()
            selected_port = int(env("browser_port", "9222"))
            cdp_url = f"http://localhost:{selected_port}"
            if existing_cdp_url:
                cdp_url = existing_cdp_url
                try:
                    parsed = urlparse(existing_cdp_url)
                    if parsed.port is not None:
                        selected_port = parsed.port
                except Exception:
                    selected_port = int(env("browser_port", "9222"))
            elif hands is not None:
                try:
                    cdp_url = hands.acquire_resource(
                        "browser", toolkit_session_id, port=selected_port
                    )
                    cdp_owned_by_hands = True
                except (NotImplementedError, ValueError):
                    cdp_url = f"http://localhost:{selected_port}"

        cdp_keep_current = bool(options.cdp_browsers)
        default_start_url = None if cdp_keep_current else "about:blank"
        browser_options = {
            "cdp_keep_current_page": cdp_keep_current,
            "default_start_url": default_start_url,
            "headless": True,
            "browser_log_to_file": True,
            "stealth": True,
            "session_id": toolkit_session_id,
            "cdp_url": cdp_url,
            "enabled_tools": _browser_enabled_tools(),
            **_options(config, "browser"),
        }
        toolkit = HybridBrowserToolkit(options.project_id, **browser_options)
        toolkit.agent_name = Agents.single_agent
        assembly.browser_toolkit = toolkit
        assembly.browser_port = selected_port
        assembly.browser_cdp_url = cdp_url
        assembly.browser_session_id = toolkit_session_id
        assembly.browser_owned_by_hands = cdp_owned_by_hands
        assembly.toolkits_to_register_agent.append(toolkit)
        registered = message_integration.register_toolkits(toolkit)
        assembly.add_tools(
            registered.get_tools(), HybridBrowserToolkit.toolkit_name()
        )

    if _enabled(config, "terminal") and (
        hands is None or hands.can_execute_terminal()
    ):
        terminal_options = {
            "working_directory": working_directory,
            "safe_mode": True,
            "clone_current_env": True,
            **_options(config, "terminal"),
        }
        toolkit = TerminalToolkit(
            options.project_id,
            Agents.single_agent,
            **terminal_options,
        )
        toolkit = message_integration.register_toolkits(toolkit)
        assembly.add_tools(toolkit.get_tools(), TerminalToolkit.toolkit_name())

    if _enabled(config, "note", default=True):
        note_toolkit = NoteTakingToolkit(
            api_task_id=options.project_id,
            agent_name=Agents.single_agent,
            working_directory=working_directory,
            **_options(config, "note"),
        )
        note_toolkit = message_integration.register_toolkits(note_toolkit)
        assembly.add_tools(
            note_toolkit.get_tools(), NoteTakingToolkit.toolkit_name()
        )

    if _enabled(config, "web_fetch"):
        toolkit = WebFetchToolkit(**_options(config, "web_fetch"))
        assembly.toolkits_to_register_agent.append(toolkit)
        assembly.add_tools(toolkit.get_tools(), "WebFetchToolkit")

    if _enabled(config, "planning_worktree"):
        planning_options = {
            "working_directory": working_directory,
            **_options(config, "planning_worktree"),
        }
        toolkit = PlanningWorktreeToolkit(
            **planning_options,
        )
        assembly.add_tools(toolkit.get_tools(), "PlanningWorktreeToolkit")

    if _enabled(config, "mcp"):
        mcp_config = _mcp_config(options, hands)
        if mcp_config is not None:
            configured_servers = list(
                mcp_config.get("mcpServers", {}).keys()
            )
            mcp_options = {
                "config_dict": mcp_config,
                "timeout": 180,
                **_options(config, "mcp"),
            }
            toolkit = MCPToolkit(**mcp_options)
            try:
                await toolkit.connect()
            except Exception as e:
                logger.error(
                    "MCPToolkit.connect() failed for server(s) %s: %s. "
                    "Tools from these servers will NOT be available this run.",
                    configured_servers,
                    e,
                    exc_info=True,
                )
            else:
                connected_tools = _sanitize_mcp_tools(toolkit.get_tools())
                assembly.add_tools(connected_tools, "MCPToolkit")
                logger.info(
                    "MCPToolkit connected: %d server(s) [%s], %d tools",
                    len(configured_servers),
                    ", ".join(configured_servers),
                    len(connected_tools),
                )

    if _enabled(config, "agent") and can_delegate:
        toolkit = DepthLimitedAgentToolkit(
            current_depth=current_depth,
            max_depth=max_depth,
            **_options(config, "agent"),
        )
        assembly.toolkits_to_register_agent.append(toolkit)
        assembly.add_tools(toolkit.get_tools(), toolkit.toolkit_name())

    return assembly
