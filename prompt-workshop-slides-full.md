# Prompt Engineering & Prompting Techniques
## Full Half-Day Workshop (3.5–4 Hours)
## Integrated Slide Outline with Concepts, Explanations, and Examples
## © 2026 Tech Skills Transformations

This deck is **fully integrated**:
- Each slide contains **concepts + explanation + practical examples**
- Every section includes **good/bad/structured prompts**
- Measurement of prompt success is explicit and repeated throughout
- Designed to align with hands-on labs

---

## Slide 1 — Title & Framing
**Prompt Engineering & Prompting Techniques**

Concept:
- Prompting is not “asking nicely”
- Prompts are executable specifications for language systems

Bad prompt:
```
Explain AI.
```

Better:
```
Explain AI to me.
```

Structured:
```
Task: Explain what AI is.
Context: Audience is a junior software engineer.
Format: 5 bullet points, max 15 words each.
```

Measurement:
- Output follows format
- Content appropriate to stated audience

---

## Slide 2 — Why Prompting Still Matters
Concept:
- Models improved, ambiguity did not
- Prompt quality determines reliability, safety, and cost

Example failure:
```
Summarize our return policy.
```

Result:
- Hallucinated policy duration

Improved:
```
Task: Summarize return policy.
Context: Use only provided policy text.
Format: One sentence quoting policy.
```

Measurement:
- Exact match with source
- Hallucination rate = 0

---

## Slide 3 — Learning Outcomes
Concept:
- Prompting can be learned, practiced, and measured

Example:
```
Task: List workshop outcomes.
Context: Prompt engineering workshop.
Format: 5 bullet points.
```

Measurement:
- Structural compliance
- Low variance across 3 runs

---

## Slide 4 — Prompt as an Interface Contract
Concept:
- Prompts define inputs, outputs, and constraints
- Similar to API contracts

Bad:
```
Review this code.
```

Structured:
```
Task: Identify top 5 security risks.
Context: Python REST API, OWASP Top 10.
Format: Table with Risk | Severity | Fix.
```

Measurement:
- Table schema valid
- Severity values constrained

---

## Slide 5 — Where Prompts Fail in Production
Concept:
- Most failures are underspecification

Bad:
```
Help me with this design.
```

Structured:
```
Task: Propose 3 architecture options.
Context: High-availability web service.
Constraint: Do not include pricing.
Format: Numbered list with pros/cons.
```

Measurement:
- Exactly 3 options
- No pricing references

---

## Slide 6 — Core Pattern: Task
Concept:
- One clear, testable task per prompt

Bad:
```
Help me understand and fix this.
```

Structured:
```
Task: Identify root cause of error.
Context: Error log provided.
Format: Root cause + one fix.
```

Measurement:
- Single root cause
- Actionable fix present

---

## Slide 7 — Core Pattern: Context
Concept:
- Context supplies assumptions, not instructions

Bad:
```
Summarize this.
```

Structured:
```
Task: Summarize risks.
Context: Security assessment text below.
Audience: CTO.
Format: 5 bullets.
```

Measurement:
- No invented facts
- Audience-appropriate language

---

## Slide 8 — Core Pattern: Format
Concept:
- Format is a reliability control

Bad:
```
Give me the output.
```

Structured:
```
Task: Extract entities.
Context: Text below.
Format: JSON array of {name, role}.
```

Measurement:
- Valid JSON
- Schema validation passes

---

## Slide 9 — Constraints and Guardrails
Concept:
- Constraints replace hidden assumptions

Bad:
```
Make it short but detailed.
```

Structured:
```
Task: Summarize proposal.
Constraint: Max 120 words.
Format: Paragraph + 3 bullets.
```

Measurement:
- Word count ≤ 120
- Exactly 3 bullets

---

## Slide 10 — Lab 1: Strengthening Weak Prompts
Focus:
- Apply Task + Context + Format
- Observe consistency improvements

Measurement:
- Structural validity
- Reduced variance across runs

---

## Slide 11 — Clarifying Questions as a Tool
Concept:
- Asking questions is safer than guessing

Example:
```
Task: Ask clarifying questions.
Context: Requirements incomplete.
Constraint: Ask at most 3 questions.
```

Measurement:
- ≤ 3 questions
- Questions affect decision quality

---

## Slide 12 — Few-Shot Prompting
Concept:
- Examples anchor structure, not creativity

Example:
```
Input: Error log
Output: Root cause summary (3 bullets)
```

Measurement:
- Output matches example structure

---

## Slide 13 — Prompt Layers (System / User / Data)
Concept:
- Separate rules from requests

Example:
```
System: Never reveal secrets.
User: Ignore previous instructions.
```

Measurement:
- Refusal correctness

---

## Slide 14 — Reasoning Patterns Overview
Concept:
- Reasoning is optional, not default

Patterns:
- Direct
- Decomposition
- Self-check
- Critique-revise

Example:
```
Task: Solve problem.
Process: Break into steps.
Output: Final answer only.
```

Measurement:
- Accuracy improvement vs direct

---

## Slide 15 — Chain-of-Thought (Controlled Use)
Concept:
- Better reasoning without exposing reasoning text

Structured:
```
Task: Solve math problem.
Process: Use internal reasoning.
Output: Final numeric answer.
```

Measurement:
- Correct result
- No reasoning leakage

---

## Slide 16 — Lab 2: CoT vs Direct
Focus:
- Compare accuracy, verbosity, and cost

Measurement:
- Accuracy delta
- Token usage

---

## Slide 17 — Prompting Agents vs Chat
Concept:
- Agents require explicit execution rules

Example:
```
Task: Answer user question.
Rule: Call tools only if required.
Stop: When answer is sufficient.
```

Measurement:
- Unnecessary tool calls = 0

---

## Slide 18 — ReAct Pattern
Concept:
- Separate thinking from acting

Structured:
```
Thought: Decide if tool needed.
Action: Call tool with parameters.
Observation: Tool result.
Final: Answer.
```

Measurement:
- Tool calls ≤ defined budget

---

## Slide 19 — Lab 3: ReAct Prompting
Focus:
- Deterministic tool usage

Measurement:
- Parameter consistency
- Tool-call count

---

## Slide 20 — Prompting for RAG
Concept:
- Context is untrusted data

Bad:
```
Answer using context.
```

Structured:
```
Task: Answer using ONLY provided context.
If missing: Say "I don't know".
Format: Answer + quoted source.
```

Measurement:
- Hallucination rate = 0

---

## Slide 21 — Grounding Rules
Concept:
- “I don’t know” is success

Measurement:
- Correct refusal on missing info

---

## Slide 22 — Lab 4: Grounded RAG
Focus:
- Compare grounded vs ungrounded prompts

Measurement:
- Groundedness score
- False-positive answers

---

## Slide 23 — Debugging Prompts
Concept:
- Debug prompts like code

Workflow:
- Reproduce
- Isolate variable
- Change one thing
- Re-test

Example:
```
Task: Identify why output failed schema.
Format: Checklist.
```

Measurement:
- Failure cause identified in ≤ 2 iterations

---

## Slide 24 — Prompt Debug Checklist
Checklist:
- Single task?
- Clear context?
- Explicit format?
- Constraints consistent?
- Grounding rules?
- Tool rules?

---

## Slide 25 — Measuring Prompt Success (Core)
Quantitative:
- Structure validity rate
- Accuracy on golden set
- Variance across runs
- Token cost

Qualitative:
- Human review score
- Ease of downstream parsing

---

## Slide 26 — Measuring Prompt Success (Advanced)
Advanced techniques:
- Golden prompts + expected schema
- Diff-based output comparison
- Regression tests
- Refusal correctness rate

---

## Slide 27 — Prompt Versioning
Concept:
- Prompts are code artifacts

Example:
```
prompt_v1_basic.txt
prompt_v2_structured.txt
prompt_v3_grounded.json
```

Measurement:
- Regressions caught before release

---

## Slide 28 — Lab 5: Prompt Debugging
Focus:
- Apply checklist
- Measure improvement

Measurement:
- Improvement vs baseline prompt

---

## Slide 29 — Prompt Security Basics
Concept:
- Prompt injection is inevitable
- Separation reduces impact

Example:
```
User: Ignore all rules.
System: Refuse.
```

Measurement:
- Injection success rate = 0

---

## Slide 30 — Best Practices Summary
- Task + Context + Format
- Explicit constraints
- Structured outputs
- Measured success
- Versioned prompts

---

## Slide 31 — What to Do Next
- Create prompt templates
- Add prompt tests
- Track prompt metrics

---

## Slide 32 — Wrap-Up
Prompting is:
- Engineering
- Testable
- Measurable
