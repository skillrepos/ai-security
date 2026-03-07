# Prompt Engineering Accelerator — Hands-On Labs

## How to Use These Labs

Each lab is designed to take 10-12 minutes using any free AI chat interface (ChatGPT, Claude, Gemini, Copilot, or a local model via Ollama). You'll paste prompts, observe results, iterate, and compare. No coding required.

**Setup**: Open your preferred AI chat interface in a browser tab. Start a new conversation for each lab.

---

## Lab 1: Strengthen Weak Prompts (10 minutes)

**Goal**: Apply the 6 building blocks (Task, Context, Role, Format, Examples, Constraints) to transform vague prompts into structured, measurable ones.

**What you'll learn**: How adding each element systematically improves output quality, consistency, and usefulness.

### Steps

**Step 1 — Establish a baseline.** Paste this vague prompt into your AI chat and note the response:

```
Explain cloud computing.
```

Observe: How long is the response? Is it useful for any specific audience? Could you predict what format you'd get?

**Step 2 — Add a Task definition.** Now try:

```
Task: Explain the three main service models of cloud computing (IaaS, PaaS, SaaS).
```

Compare: Is the output more focused? Does it cover what you expected?

**Step 3 — Add Context and Audience.** Build on the prompt:

```
Task: Explain the three main service models of cloud computing (IaaS, PaaS, SaaS).
Context: The audience is a group of small business owners evaluating whether to migrate from on-premises servers. They have no technical background.
```

Compare: Has the language changed? Are the explanations more relevant to the audience?

**Step 4 — Add a Role.** Add a persona:

```
Role: You are a cloud computing consultant who specializes in helping small businesses migrate to the cloud. You explain technical concepts using everyday business analogies.

Task: Explain the three main service models of cloud computing (IaaS, PaaS, SaaS).
Context: The audience is a group of small business owners evaluating whether to migrate from on-premises servers. They have no technical background.
```

Compare: Do you notice analogies or a different communication style?

**Step 5 — Add Format requirements.** Specify the output structure:

```
Role: You are a cloud computing consultant who specializes in helping small businesses migrate to the cloud. You explain technical concepts using everyday business analogies.

Task: Explain the three main service models of cloud computing (IaaS, PaaS, SaaS).
Context: The audience is a group of small business owners evaluating whether to migrate from on-premises servers. They have no technical background.

Format: For each service model, provide:
- Name and one-sentence definition
- A real-world business analogy
- One example use case for a small business
- Estimated monthly cost range

Present as a comparison table.
```

Compare: Is the output now consistently structured and easy to scan?

**Step 6 — Add Constraints.** Add boundaries:

```
Role: You are a cloud computing consultant who specializes in helping small businesses migrate to the cloud. You explain technical concepts using everyday business analogies.

Task: Explain the three main service models of cloud computing (IaaS, PaaS, SaaS).
Context: The audience is a group of small business owners evaluating whether to migrate from on-premises servers. They have no technical background.

Format: For each service model, provide:
- Name and one-sentence definition
- A real-world business analogy
- One example use case for a small business
- Estimated monthly cost range

Present as a comparison table.

Constraints:
- No jargon without immediate explanation
- Keep total response under 300 words
- End with a one-sentence recommendation for a typical 10-person office
```

**Step 7 — Run the final prompt 3 times.** Paste the complete prompt from Step 6 three separate times (in new conversations or after clearing context). Compare the three outputs:
- Do they all follow the table format?
- Are the analogies consistent in quality?
- Does the recommendation stay relevant?

This is measuring **consistency** — a key quality metric.

**Step 8 — Reflect.** Rate each version (Steps 1-6) on a 1-5 scale for: specificity, usefulness, and consistency. Note which building block made the biggest difference for this task.

---
## Lab 2: Few-Shot & Chain of Thought Comparison (12 minutes)

**Goal**: Compare zero-shot, few-shot, and Chain of Thought (CoT) prompting on a classification task where the "correct" answer depends on company-specific rules that the AI can't infer on its own.

**What you'll learn**: When accuracy problems are caused by missing domain knowledge (not sloppy reasoning), few-shot examples fix the gap while CoT only makes the wrong reasoning visible — a useful distinction for choosing the right technique.

**Scenario**: You work at a growth-stage SaaS company that just raised Series B. The company has unusual but defensible priority rules driven by its current business strategy — and several of these rules *contradict* standard industry practice.

### Steps

**Step 1 — Predict, then test.** Read this ticket carefully:

> "Hey, just wanted to let you know that Competitor X released a feature similar to your dashboard. I'm still happy with your product, but thought you'd want to know!"

**Before pasting anything**, write down: what priority would you assign (P1-Critical, P2-High, P3-Medium, P4-Low)? And what priority do you think the AI will assign?

Now test your prediction:

```
You are a support ticket classifier. Assign exactly one priority level to the following support ticket: P1-Critical, P2-High, P3-Medium, or P4-Low.

Ticket: "Hey, just wanted to let you know that Competitor X released a feature similar to your dashboard. I'm still happy with your product, but thought you'd want to know!"
```

Were you right about the AI's answer? This seems low-priority — the customer is happy and just sharing info. But at this company, **any mention of a competitor is an immediate P1 churn signal**, because reducing churn is the board's #1 metric post-Series B.

**Step 2 — Batch classify.** Now test all 5 tickets at once to build a zero-shot baseline:

```
You are a support ticket classifier. Assign exactly one priority level to each ticket: P1-Critical, P2-High, P3-Medium, or P4-Low.

Classify each ticket independently. Present results as a table with columns: Ticket #, Short Description, Priority, Reasoning (1 sentence).

Ticket 1: "Hey, just wanted to let you know that Competitor X released a feature similar to your dashboard. I'm still happy with your product, but thought you'd want to know!"

Ticket 2: "URGENT: I accidentally deleted my project files and I need them back IMMEDIATELY. This is a disaster!"

Ticket 3: "The 'Get Started' button on your pricing page has a weird color glitch on mobile. Just FYI."

Ticket 4: "None of our 25-person team can access the platform since 8 AM. We have client meetings today."

Ticket 5: "I was charged $45 twice this month. Can someone look into this?"
```

Look at the results. The AI will classify based on **general industry norms**. But this company's actual rules are very different.

**Step 3 — Spot the mismatches.** Here is this company's actual priority policy — shaped by their growth strategy:

- **Any mention of a competitor** = always P1, even if the customer sounds happy (churn prevention is the #1 board metric)
- **Data loss for single users** = P3, not P1 (automated backups recover files in 15 minutes — this is routine)
- **UI/cosmetic bugs on public-facing pages** (pricing, signup, landing) = P2 (these pages drive conversion — the growth team's top priority)
- **Service outages affecting teams** = P1 (standard)
- **Billing issues under $100** = P4 (self-service billing portal handles these automatically)

Compare the AI's zero-shot answers to this policy. How many of the 5 tickets did zero-shot get wrong?

**Step 4 — Try CoT without the company rules.** Start a new conversation. This time, give the AI a structured reasoning framework — but do NOT include the company-specific policy. We want to see if better *thinking* alone fixes the errors:

```
You are a support ticket classifier. Assign exactly one priority level to each ticket: P1-Critical, P2-High, P3-Medium, or P4-Low.

For each ticket, reason through these steps BEFORE assigning priority:
1. What is the actual technical or business issue? (Ignore emotional language.)
2. What is the blast radius? (One user, a team, all users, or a potential customer?)
3. Is there data loss, a security risk, or a revenue impact?
4. Does the customer have a workaround?
5. Based on business impact (not tone), assign priority.

Show your full reasoning for each ticket, then present a summary table.

Ticket 1: "Hey, just wanted to let you know that Competitor X released a feature similar to your dashboard. I'm still happy with your product, but thought you'd want to know!"

Ticket 2: "URGENT: I accidentally deleted my project files and I need them back IMMEDIATELY. This is a disaster!"

Ticket 3: "The 'Get Started' button on your pricing page has a weird color glitch on mobile. Just FYI."

Ticket 4: "None of our 25-person team can access the platform since 8 AM. We have client meetings today."

Ticket 5: "I was charged $45 twice this month. Can someone look into this?"
```

Compare to zero-shot. You'll likely find CoT produces **the same classifications** — and that's the key insight. The reasoning is now *visible* (you can read exactly how the AI thought through each ticket), but the answers don't improve. Why? Because the errors aren't caused by sloppy thinking — they're caused by **missing domain knowledge**. The AI reasons perfectly well about blast radius and business impact, but it has no way to know that this company treats competitor mentions as P1 or that single-user data loss is only P3 because of automated backups. CoT makes the reasoning auditable, which is great for debugging — but structured thinking can't substitute for information the model doesn't have.

**Step 5 — Teach the policy with examples.** Now paste this few-shot prompt — it teaches the company's policy through examples, not rules:

```
You are a support ticket classifier for a growth-stage SaaS company. Assign exactly one priority level: P1-Critical, P2-High, P3-Medium, or P4-Low.

Company priority rules (taught by example):

Ticket: "I noticed your competitor just launched a mobile app. I don't need one personally, but just a heads up."
Priority: P1-Critical
(Any mention of a competitor — even casual or positive — is P1. Churn prevention is our top metric.)

Ticket: "Help! I accidentally deleted my entire project folder. I need those files back!"
Priority: P3-Medium
(Single-user data loss is P3. Our automated backup system recovers files in 15 minutes.)

Ticket: "The testimonial carousel on the homepage is overlapping the signup button on tablets."
Priority: P2-High
(UI bugs on public-facing pages like homepage, pricing, or signup are P2 — they affect conversion rates.)

Ticket: "Our whole department of 40 people can't log in since this morning."
Priority: P1-Critical
(Service outages affecting teams are always P1.)

Ticket: "You double-charged me $29 on my last invoice. Please refund."
Priority: P4-Low
(Billing issues under $100 are P4 — our self-service billing portal handles these automatically.)

Ticket: "I just finished a demo of Competitor Y for my team. Still deciding between you two."
Priority: P1-Critical
(Active competitor evaluation = highest churn risk. Always P1 regardless of tone.)

Now classify these 5 tickets. Present as a table with: Ticket #, Short Description, Priority, Reasoning.

Ticket 1: "Hey, just wanted to let you know that Competitor X released a feature similar to your dashboard. I'm still happy with your product, but thought you'd want to know!"

Ticket 2: "URGENT: I accidentally deleted my project files and I need them back IMMEDIATELY. This is a disaster!"

Ticket 3: "The 'Get Started' button on your pricing page has a weird color glitch on mobile. Just FYI."

Ticket 4: "None of our 25-person team can access the platform since 8 AM. We have client meetings today."

Ticket 5: "I was charged $45 twice this month. Can someone look into this?"
```

Compare all three tables. Few-shot should nail all 5 — the examples directly taught the counterintuitive rules that neither zero-shot nor CoT could figure out. This is the payoff: examples don't just improve reasoning, they **transfer knowledge** the model couldn't access otherwise.

**Step 6 — Identify the pattern.** Look at your zero-shot, CoT, and few-shot results together. Notice that zero-shot and CoT likely produced the same classifications — the only difference is CoT shows its work. For each ticket, write down: what reasoning did CoT reveal, and why didn't that reasoning lead to the correct answer? What did the few-shot examples provide that structured thinking alone couldn't?

**Step 7 — Compare results.** Fill in your scorecard:

| Ticket (short) | Zero-Shot | CoT (no rules) | Few-Shot | Company Policy |
|----------------|-----------|----------------|----------|----------------|
| Competitor mention (happy) | | | | P1 |
| Deleted files (urgent) | | | | P3 |
| Pricing page glitch (casual) | | | | P2 |
| 25-person outage | | | | P1 |
| $45 double charge | | | | P4 |

You should see: zero-shot (~2/5), CoT (~2/5 — same answers, but with visible reasoning), few-shot (5/5). The takeaway: CoT adds **auditability** (you can see *why* the AI chose each priority), but it doesn't add **accuracy** when the problem is missing domain knowledge. Only few-shot — which transfers the company's actual rules through examples — closes the gap.

**Step 8 (Optional) — Write your own tricky ticket.** Write a support ticket designed to **fool the zero-shot classifier** given this company's unusual rules. Hint: try a ticket where the obvious priority and the company policy priority are as far apart as possible.

**Step 9 (Optional) — Test your adversarial ticket.** Paste your tricky ticket and ask:

```
Classify this ticket using all three approaches (zero-shot, few-shot with the company examples, and CoT with the company-specific reasoning framework). Show each approach's classification side by side.
```

Which technique handled your adversarial ticket best?

**Step 10 — Reflect.** Complete your final comparison:

| Technique | Tickets Correct (out of 5) | Best For |
|-----------|---------------------------|----------|
| Zero-shot | ___ | |
| Few-shot | ___ | |
| CoT | ___ | |

Key takeaway: CoT improves *how* the AI reasons but can't teach it rules it doesn't know. Few-shot teaches domain knowledge directly through examples. In production, combine both: few-shot examples to teach the rules, plus CoT to make every decision auditable. The AI "knows" standard industry practices — but it can't know *your* company's unique priorities unless you teach it.

---


## Lab 3: Production Prompt Engineering (12 minutes)

**Goal**: Build a structured, constrained prompt that produces consistent, machine-parseable JSON output suitable for feeding into a real system.

**What you'll learn**: How to combine schema, role, and constraints to create production-grade prompts — and why each layer solves a different problem.

### Steps

**Step 1 — Generate, then break.** Paste this deliberately vague prompt:

```
Write changelog entries for these three product updates:

1. We added the ability for users to export their dashboard data as a CSV file.
2. We redesigned the notification preferences page so users can choose per-channel settings for email, SMS, and in-app alerts.
3. We fixed a bug where the search bar would return no results if the query contained special characters like & or #.
```

Look at what you got. It's probably readable — maybe bullet points, maybe a nicely formatted list. Now imagine you need to feed this into an automated system that sends targeted emails to affected users, updates a status page, and files Jira tickets. Could a script reliably extract the data it needs from this output?

**Step 2 — Try to parse it.** Imagine writing code to process this output automatically. For each entry, you'd need to extract: a title, a change type (feature/bugfix/improvement), a description, which product areas are affected, and whether users need to do anything. Try to answer these questions:

- Is there a consistent, predictable structure a script could rely on?
- Could you extract the change type programmatically, or is it buried in prose?
- Are affected product areas listed in a standard way, or described differently each time?
- Is "user action required" explicitly stated, or would a script have to guess from context?
- If you ran this prompt 10 times, would the format be identical every time?

The output is fine for a human reader — but it's not **machine-parseable**. That's the production gap. List every reason a script would struggle with this output.

**Step 3 — Design a machine-readable format.** Based on the parsing problems you identified, draft a structured format (JSON, XML, or whatever you prefer) that a script could reliably consume. Define specific field names, data types, and allowed values. Spend 2 minutes designing your schema before looking at Step 4.

**Step 4 — Compare to a reference.** Start a new conversation and paste this fully constrained version:

```
Role: You are a technical writer producing entries for an automated notification system. Every entry must be identically formatted.

Task: Generate JSON changelog entries for these three product updates:

1. We added the ability for users to export their dashboard data as a CSV file.
2. We redesigned the notification preferences page so users can choose per-channel settings for email, SMS, and in-app alerts.
3. We fixed a bug where the search bar would return no results if the query contained special characters like & or #.

Output each entry as JSON with exactly this schema (no extra fields):
{
  "title": "string — max 10 words, sentence case, no trailing period",
  "type": "feature|improvement|bugfix|breaking_change",
  "description": "string — exactly 2-3 sentences. First: what changed. Second: why it matters. Third (optional): context.",
  "affected_areas": ["Use ONLY: dashboard, settings, search, auth, billing, notifications, api, reports"],
  "user_action_required": true|false,
  "details": "string — technical details or migration steps. Must be null if user_action_required is false."
}

Constraints:
- Output ONLY a valid JSON array, no markdown fences, no explanation before or after
- type must reflect: new capability = feature, enhancement = improvement, fix = bugfix, requires migration = breaking_change
```

Compare this output to your Step 1 results. Notice the difference: Step 1 produced human-readable prose; this produces machine-parseable JSON with controlled values. Run this constrained prompt 2-3 times in separate conversations — the output should be structurally identical every time. How does your schema from Step 3 compare to this reference?

**Step 5 — Stress-test with edge cases.** In the same conversation as Step 4, paste this:

```
Now generate changelog entries using the same constrained format for these two edge cases:

4. We migrated the authentication system from session-based cookies to JWT tokens. Existing sessions will be invalidated on March 15. Users will need to log in again, and any API integrations using session cookies must be updated to use bearer tokens. The new system supports refresh tokens with a 30-day expiry.

5. Fixed a typo in the footer — "Contant Us" now correctly reads "Contact Us".
```

These are the extremes: a complex breaking change with multiple impacts, and a trivial typo fix. Check:
- Did it correctly classify the JWT migration as "breaking_change" with user_action_required: true?
- Did it provide useful migration details (not just repeat the description)?
- Did it handle the typo gracefully — or did it inflate a one-line fix into a multi-sentence description to meet the "2-3 sentences" rule?

That last point is important: constraints that work for normal entries can create awkward results at the extremes. Note any rules that need adjusting.

**Step 6 — Make the AI self-validate.** Now ask the AI to check its own work:

```
Review all 5 changelog entries you generated. For each one, check against these rules and report any violations:
1. Valid JSON that parses without errors?
2. All required fields present with correct types?
3. Title under 10 words, sentence case, no period?
4. Description exactly 2-3 sentences?
5. affected_areas uses only standard names from the allowed list?
6. details is null when user_action_required is false?
```

Did the AI catch issues it introduced? This is a powerful production pattern: you can build validation directly into your prompts so the AI checks itself before returning results.

**Step 7 — Combine into one production prompt.** You've now built three layers: schema (Step 4), edge-case testing (Step 5), and self-validation (Step 6). In production, these all go into a single prompt. Start a new conversation and paste this combined version:

```
Role: You are a technical writer producing entries for an automated notification system.

Task: Generate JSON changelog entries for these product updates:

1. We added the ability for users to export their dashboard data as a CSV file.
2. We redesigned the notification preferences page so users can choose per-channel settings for email, SMS, and in-app alerts.
3. We fixed a bug where the search bar would return no results if the query contained special characters like & or #.
4. We migrated authentication from session-based cookies to JWT tokens. Existing sessions invalidated March 15. Users must log in again; API integrations using session cookies must switch to bearer tokens.
5. Fixed a typo in the footer — "Contant Us" now reads "Contact Us".

Schema (no extra fields):
{
  "title": "max 10 words, sentence case, no trailing period",
  "type": "feature|improvement|bugfix|breaking_change",
  "description": "2-3 sentences. First: what changed. Second: why it matters. Third (optional): context. For trivial fixes, 1 sentence is acceptable.",
  "affected_areas": ["ONLY: dashboard, settings, search, auth, billing, notifications, api, reports"],
  "user_action_required": true|false,
  "details": "migration steps or technical details. null if user_action_required is false."
}

Constraints:
- Output ONLY valid JSON array — no markdown, no commentary
- type: new capability = feature, enhancement = improvement, fix = bugfix, requires migration = breaking_change

After generating, self-validate: check every entry against the schema rules above. If any entry violates a rule, fix it and note what you corrected.
```

Notice the refinement: "For trivial fixes, 1 sentence is acceptable" — that's the edge-case fix from Step 5, built directly into the schema. And self-validation is baked into the prompt itself.

**Step 8 — Review the combined output.** Did the single production prompt produce clean results for all 5 entries — including the edge cases? Did self-validation catch anything? Compare this to the multi-step process from Steps 4-6. In production, one well-designed prompt replaces the iterative testing you did in this lab.

**Step 9 (Optional) — Apply to your own work.** Think of a structured output you need at work — a status report, an incident summary, a meeting recap, a product review. Design a production prompt for it with all three layers: schema, constraints, and self-validation. Test it with both typical and edge-case inputs.

**Step 10 — Reflect.** You built three layers of prompt quality: schema (structure), constraints (quality control), and self-validation (built-in error checking). The schema solves "can a script read this?" Constraints solve "will the data be reliable?" Self-validation solves "will it catch its own mistakes?" In production, all three go into one prompt — and you stress-test with edge cases before deploying.

---

## Lab 4: Multi-Expert & Reverse Prompting (12 minutes)

**Goal**: Use multi-expert prompting to get diverse perspectives on a complex decision, then use reverse prompting to discover hidden requirements.

**What you'll learn**: How simulating multiple expert viewpoints catches blind spots, and how letting the AI ask questions produces better specifications.

### Steps

**Step 1 — Generic baseline.** Paste this prompt:

```
Should our company adopt a 4-day work week? Give your recommendation.
```

Read the response. It's probably balanced and well-written. Now ask yourself: **could you actually make a decision based on this?** Look for specifics — does it give you a financial estimate of the cost? A concrete legal risk? A specific metric you could track? Note what *actionable details* (numbers, named risks, specific recommendations) it includes.

**Step 2 — Design your own expert panel.** Before looking ahead, think about this question: *Which 3-4 expert roles would give you the most useful range of perspectives on the 4-day work week decision?*

Write down your panel (just the role names and what each should focus on).

**Step 3 — Run the panel.** Paste a multi-expert prompt using either your own panel design or this reference:

```
Task: Analyze whether a 200-person software company should adopt a 4-day work week.

Simulate a panel of 4 experts. Each expert must provide their analysis independently:

Expert 1 - HR Director (15 years experience):
Focus on: employee retention, recruitment advantage, burnout, morale
Provide: Assessment + specific risk + specific benefit

Expert 2 - CFO:
Focus on: productivity impact, revenue implications, operational costs, client coverage
Provide: Assessment + financial estimate + key assumption

Expert 3 - Engineering Manager:
Focus on: sprint velocity, code quality, collaboration time, deep work
Provide: Assessment + metric prediction + mitigation strategy

Expert 4 - Employment Lawyer:
Focus on: labor law compliance, contract modifications, overtime implications, precedent cases
Provide: Assessment + top legal risk + required action

After all 4 experts present, provide:
- Points of agreement across experts
- Points of conflict between experts
- A synthesis recommendation with confidence level (low/medium/high)
- The single most important factor the decision hinges on
```

Now note the actionable details again — financial estimates, named legal risks, specific metrics, concrete recommendations. How many more did the panel surface compared to Step 1? The difference isn't just more perspectives — it's that each expert is forced to provide *specifics* rather than hedged generalities.

**Step 4 (Optional) — Apply the panel to your own decision.** Think of a real decision you're facing at work (adopting a tool, changing a process, launching something new). In the same conversation, ask:

```
Now apply the same multi-expert panel format to this decision: [describe your decision in 1-2 sentences]. Adapt the expert roles to be relevant to this specific domain.
```

Did the AI choose useful expert roles? Did any perspective surprise you?

**Step 5 — Flip the script with reverse prompting.** Now let the AI ask the questions. Paste:

```
I want to write a prompt that generates a comprehensive project proposal for a software project. But instead of me writing that prompt, I want you to help me discover what it needs.

Ask me a series of clarifying questions — one at a time — to understand:
- What kind of project this is for
- Who will read the proposal
- What sections are required
- What constraints exist
- What level of detail is needed

Ask your first question now. After I answer, ask the next one. After 4-5 questions, generate the complete prompt for me.
```

**Step 6 — Answer honestly.** Respond to each question the AI asks. Be as specific or vague as you'd naturally be — this tests whether the AI asks good follow-ups. Go through all the questions.

**Step 7 — Evaluate the generated prompt.** After the AI generates your prompt, score it:
- Did it include details you wouldn't have thought of on your own? (List 2-3 examples.)
- Does it incorporate all 6 building blocks from Lab 1?
- Is it more specific than what you would have written from scratch?

**Step 8 — Test the generated prompt.** Copy the prompt the AI built for you and run it. Does the output match what you described during the Q&A? Note any gaps — these reveal requirements the reverse prompting process missed.

**Step 9 — Think about combining.** Consider: if you fed this generated prompt into a multi-expert panel (like Lab 4), what 3 expert roles would add the most value? How would combining reverse prompting (to discover requirements) with multi-expert analysis (to stress-test) produce better results than either alone?

**Step 10 — Reflect on when to use each.** These techniques solve different problems:
- **Multi-expert** is best when you know the question but need to stress-test it from multiple angles.
- **Reverse prompting** is best when you don't know what you don't know — when the problem space is unfamiliar.
- **Combined**: Use reverse prompting first (discover requirements), then feed those into a multi-expert analysis (stress-test the decision). Write down one real situation where this two-step approach would be valuable.
---

## Lab 5: Optimization & Integration (10 minutes)

**Goal**: Apply probabilistic prompting and incentive framing to maximize quality on a high-stakes task, then build a reusable decision-making template.

**What you'll learn**: How multi-round self-critique and audience framing each independently improve output quality — and how combining them produces the most reliable results.

### Steps

**Step 1 — Baseline decision analysis.** Paste:

```
Recommend a database for a new e-commerce application that expects 10,000 daily active users, needs to store product catalogs, user profiles, and order history.

Options: PostgreSQL, MongoDB, DynamoDB

Which should we choose and why?
```

Before reading the response, predict: Will the AI acknowledge uncertainty and trade-offs, or just advocate for one option?

Now read it. Note whether it mentions any risks with its recommended choice.

**Step 2 — Add self-critique.** In the same conversation, ask:

```
Now redo this analysis in 3 rounds:

Round 1 - Initial assessment: Rate each option from 1-10 for fit, with a one-sentence justification.

Round 2 - Devil's advocate: For your top-rated option, list the 3 strongest arguments AGAINST choosing it. Then re-rate all options.

Round 3 - Final recommendation: State your choice with a confidence level (0-100%). Explain what would need to be true for your second-choice option to become the better pick.
```

Compare to Step 1:
- Did the ratings change between Round 1 and Round 2? (If so, the self-critique worked.)
- Did the devil's advocate surface risks that Step 1 ignored?

**Step 3 — Quantify the improvement.** Ask the AI:

```
Compare your Step 1 recommendation with your Round 3 recommendation. What risks or trade-offs did the 3-round analysis surface that the initial recommendation missed? List them.
```

Review the new considerations. This is the measurable value of self-critique — it surfaces risks that single-pass analysis misses.

**Step 4 — Isolate the incentive framing effect.** Now open a new conversation and paste the same analysis with only an audience frame added at the top:

```
This analysis will be presented to the CTO and VP of Engineering for a final architecture decision. The chosen database will serve as our primary data store for the next 3-5 years, so accuracy and completeness are critical.

Take your time and be thorough. Consider edge cases and failure modes that are easy to overlook.

Recommend a database for a new e-commerce application that expects 10,000 daily active users, needs to store product catalogs, user profiles, and order history.

Options: PostgreSQL, MongoDB, DynamoDB

Provide your analysis in 3 rounds:
Round 1 - Rate each option from 1-10 for fit, with a one-sentence justification.
Round 2 - For your top-rated option, list the 3 strongest arguments AGAINST it. Re-rate.
Round 3 - Final recommendation with confidence level (0-100%). What would change your recommendation?
```

**Step 5 — Compare framed vs. unframed.** Compare to Step 2's analysis (same structure, no incentive frame). Look for:
- Are the justifications longer or more detailed?
- Did it mention additional risk factors or edge cases?
- Is the language more precise (specific numbers vs. vague generalities)?
- Did the confidence percentage change?

**Step 6 — Test a different audience.** In the same conversation, ask:

```
Now redo the same analysis, but change the audience: this analysis will be presented to a junior developer who needs to pick a database for their first solo project. Adjust your framing and depth accordingly.
```

Compare: How does the same analysis change when the stakes and audience shift? Does the AI provide less detail, different recommendations, or different confidence levels?

**Step 7 — Build your reusable template.** Combine everything that worked:

```
[INCENTIVE FRAME]
This analysis will inform a critical decision for [stakeholder].
Accuracy and completeness are essential. Take your time.

[CONTEXT]
Decision: [What we're deciding]
Options: [Option A, Option B, Option C]
Current situation: [Key constraints and requirements]
Timeline: [When decision is needed and implementation horizon]

[MULTI-ROUND ANALYSIS]
Round 1: Rate each option (1-10) with one-line justification.
Round 2: For the top option, list 3 strongest counter-arguments. Re-rate.
Round 3: Final recommendation with:
- Confidence level (0-100%)
- Biggest risk of recommended option
- What would change your recommendation
- Revisit trigger for 6-month check-in

[FORMAT]
Present as structured sections with clear headers.
Keep total response under 500 words.
```

**Step 8 — Test on a real decision.** Apply your template to a decision you're actually facing — choosing a tool, vendor, approach, or process change. (If you don't have a real use case, you can make one up.) Fill in the brackets from the template prompt from step 7 and run it.

**Step 9 — Evaluate decision-readiness.** Ask yourself: Could you hand this output directly to a decision-maker? If not, what's missing? Ask the AI:

```
What additional information would a decision-maker need beyond this analysis to make a final call? List the gaps.
```

This is a useful meta-prompt for any high-stakes output — asking the AI to identify what it *didn't* cover.

**Step 10 — Transition.** You now have a complete toolkit for interactive prompting. But what happens when the AI needs to act autonomously — calling tools, handling errors, and making decisions without you in the loop? That's Lab 6.

---

## Appendix: Quick Reference Card

### The 6 Building Blocks
1. **Task** — One clear, testable instruction
2. **Context** — Background, audience, environment
3. **Role** — Persona with relevant expertise
4. **Format** — Output structure (table, JSON, bullets)
5. **Examples** — Input/output pairs (few-shot)
6. **Constraints** — Boundaries (length, tone, exclusions)

### Technique Selection Guide

| Situation | Technique | Why |
|-----------|-----------|-----|
| Simple, common task | Zero-shot | Fast, low cost |
| Need consistent format | Few-shot | Examples anchor structure |
| Complex reasoning | Chain of Thought | 20-40% accuracy boost |
| Multi-stakeholder decision | Multi-expert | Catches blind spots |
| Unclear requirements | Reverse prompting | AI discovers what you need |
| High-stakes output | Probabilistic + incentive | Maximum thoroughness |
| Production integration | Structured + constrained | Consistent, parseable output |

### Quality Metrics Checklist
- Does the output follow the requested format?
- Is it consistent across multiple runs?
- Is the content accurate and grounded?
- Could downstream systems parse it reliably?
- Would a domain expert approve the output?

---
*© 2026 Tech Skills Transformations*

