#!/usr/bin/env python3
"""
Supervisor Multi-Agent Pattern with Budgets

A tight, lab-friendly example:
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage


def approx_tokens(text: str) -> int:
# Simple heuristic: 1 token ≈ 4 chars (good enough for budgeting demos)
  return max(1, len(text) // 4)

@dataclass
class Budget:
    max_turns: int
    max_tokens_out: int
    turns_used: int = 0
    tokens_out_used: int = 0


	
@dataclass
class HandoffPacket:
    """
    The ONLY thing that gets passed between agents.
    This is intentionally compact: enterprise workflows should avoid dumping full transcripts.
    """

class Agent:
    def __init__(self, role: Role, llm: ChatOllama, system_prompt: str):
        self.role = role
        self.llm = llm
        self.system_prompt = system_prompt

    def run(self, packet: HandoffPacket, instruction: str, max_output_chars: int = 2000) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=self._format_input(packet, instruction)),
        ]
        resp = self.llm.invoke(messages)
        text = (resp.content or "").strip()
        if len(text) > max_output_chars:
            text = text[:max_output_chars].rstrip() + "\n[TRUNCATED BY BUDGET]"
        return text

    def _format_input(self, packet: HandoffPacket, instruction: str) -> str:
        # Keep inputs compact and structured (handoff packet)
        return (
        )

class Supervisor:
    """
    """
    def __init__(
        self,
        planner: Agent,
        implementer: Agent,
        reviewer: Agent,
        budgets: Dict[Role, Budget],
    ):
        self.planner = planner
        self.implementer = implementer
        self.reviewer = reviewer
        self.budgets = budgets

    def run(self, user_goal: str) -> HandoffPacket:
        packet = HandoffPacket(user_goal=user_goal)
        print("\n=== SUPERVISOR: START ===")
        print(f"Goal: {user_goal}\n")
            self._call_agent(
                agent=self.implementer,
                role="implementer",
                packet=packet,
                instruction=(
                    "Apply the review fixes. Produce a revised implementation artifact. "
                    "Keep it compact."
                ),
                save_to="implementation",
            )
        
            if self.budgets["reviewer"].can_run():
                self._call_agent(
                    agent=self.reviewer,
                    role="reviewer",
                    packet=packet,
                    instruction="Re-review the revised implementation. If acceptable, say 'APPROVED'.",
                    save_to="review",
                )

        print("\n=== SUPERVISOR: END ===")
        self._print_budget_summary()
        return packet

    def _call_agent(
        self,
        agent: Agent,
        role: Role,
        packet: HandoffPacket,
        instruction: str,
        save_to: Literal["plan", "implementation", "review"],
    ) -> None:
        budget = self.budgets[role]
        if not budget.can_run():
            packet.notes.append(f"Supervisor: Budget exhausted for {role}. Skipping.")
            print(f"[SUPERVISOR] Budget exhausted for {role}. Skipping.")
            return

        print(f"[SUPERVISOR] Calling {role.upper()} (turn {budget.turns_used + 1}/{budget.max_turns})...")
        output = agent.run(packet, instruction, max_output_chars=2000)
        budget.record(output)

        setattr(packet, save_to, output)
        print(f"\n--- {role.upper()} OUTPUT ---")
        print(output)
        print("--- END OUTPUT ---\n")

    def _print_budget_summary(self) -> None:
        print("\n=== BUDGET SUMMARY ===")
        for role, b in self.budgets.items():
            print(
                f"{role:12} turns={b.turns_used}/{b.max_turns} "
                f"tokens_out~={b.tokens_out_used}/{b.max_tokens_out}"
            )
        print("======================\n")

def main() -> None:
    # Local model via Ollama (consistent with other labs)
    # num_predict limits output tokens for faster generation
    llm = ChatOllama(model="llama3.2:1b", temperature=0, num_predict=400)

    planner = Agent(
        role="planner",
        llm=llm,
    )
    implementer = Agent(
        role="implementer",
        llm=llm,
    )
    reviewer = Agent(
        role="reviewer",
        llm=llm,
    budgets: Dict[Role, Budget] = {
    }

    supervisor = Supervisor(planner, implementer, reviewer, budgets)

    print("Supervisor Multi-Agent with Budgets")
    print("Type a request and press Enter. Type 'exit' to quit.\n")

    while True:
        goal = input("Request > ").strip()
        if not goal or goal.lower() == "exit":
            break
        _ = supervisor.run(goal)

    print("\nDone.")

if __name__ == "__main__":
    main()
