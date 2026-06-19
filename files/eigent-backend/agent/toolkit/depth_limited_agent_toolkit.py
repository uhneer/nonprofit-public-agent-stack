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

import logging
from collections.abc import Callable
from typing import Any, Dict, Optional

from camel.toolkits import AgentToolkit, FunctionTool, RegisteredAgentToolkit

from app.agent.toolkit.abstract_toolkit import AbstractToolkit

logger = logging.getLogger(__name__)

_NULLISH_STRINGS = frozenset({"null", "none", ""})


def _normalize_nullish(value: Any) -> Any:
    if isinstance(value, str) and value.strip().lower() in _NULLISH_STRINGS:
        return None
    return value


def _is_agent_tool(tool: FunctionTool | Callable) -> bool:
    func = getattr(tool, "func", tool)
    toolkit = getattr(func, "__self__", None)
    return isinstance(toolkit, AgentToolkit)


class DepthLimitedAgentToolkit(AgentToolkit, AbstractToolkit):
    """CAMEL AgentToolkit with delegated-agent recursion disabled.

    CAMEL's native AgentToolkit clones the parent tool set into child agents.
    For Eigent single-agent mode we want root agents to delegate, while child
    agents must not delegate again. This adapter keeps the CAMEL toolkit API
    and removes AgentToolkit tools from child tool sets.
    """

    def __init__(
        self,
        *,
        current_depth: int = 0,
        max_depth: int = 1,
        timeout: float | None = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.current_depth = current_depth
        self.max_depth = max_depth

    def _resolve_child_tools(
        self,
        parent,
    ) -> tuple[
        list[FunctionTool | Callable] | None,
        list[RegisteredAgentToolkit] | None,
    ]:
        tools, toolkits_to_register = super()._resolve_child_tools(parent)
        if tools is None:
            return None, toolkits_to_register

        return (
            [tool for tool in tools if not _is_agent_tool(tool)],
            [
                toolkit
                for toolkit in (toolkits_to_register or [])
                if not isinstance(toolkit, AgentToolkit)
            ],
        )

    def _build_system_message(
        self,
        subagent_type: str,
        description: str,
    ) -> str:
        base = super()._build_system_message(subagent_type, description)
        return (
            base
            + "\nYou are a child sub-agent. Complete the assigned task "
            "directly and do not create or delegate to any further sub-agents."
            + "\n\nANTI-FABRICATION RULES (hard requirements, not suggestions):"
            + "\n1. For any verifiable operation (hashing, math, file reads, "
            "command output, API responses, dates, code execution), you MUST "
            "invoke the corresponding tool and use the tool's actual output. "
            "Pattern-likely strings you compose in your head are forbidden."
            + "\n2. If no tool on your surface can compute the answer, return "
            "'NO_TOOL_AVAILABLE: <what you needed>' instead of guessing."
            + "\n3. Every numeric, hex, base64, UUID, or hash-shaped string "
            "in your final answer must be copied verbatim from a tool result. "
            "If you cannot point to the tool call that produced it, omit it."
            + "\n4. Parent agent will verify your output against ground truth. "
            "Fabricated outputs fail the task; honest 'I could not compute' "
            "answers are recoverable."
        )

    def agent_run_subagent(
        self,
        prompt: str,
        description: str = "Specialized sub-agent task",
        subagent_type: str = "general-purpose",
        agent_id: Optional[str] = None,
        wait: bool = True,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        normalized_id = _normalize_nullish(agent_id)
        if normalized_id is None and agent_id is not None:
            logger.info(
                "agent_run_subagent: coerced agent_id %r -> None "
                "(GLM emits literal 'null' for optional args).",
                agent_id,
            )
        return super().agent_run_subagent(
            prompt=prompt,
            description=_normalize_nullish(description) or description,
            subagent_type=_normalize_nullish(subagent_type) or subagent_type,
            agent_id=normalized_id,
            wait=wait,
            timeout=_normalize_nullish(timeout) if timeout is not None else timeout,
        )

    @classmethod
    def toolkit_name(cls) -> str:
        return "AgentToolkit"


# Preserve the parent docstring so FunctionTool OpenAPI schema generation
# sees the same description and Args block as the original CAMEL method.
DepthLimitedAgentToolkit.agent_run_subagent.__doc__ = (
    AgentToolkit.agent_run_subagent.__doc__
)
