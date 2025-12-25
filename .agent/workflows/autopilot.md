---
description: Autopilot: Codex promptify -> Plan -> Codex review -> Implement -> Codex review (loop)
---

// turbo-all
1. Capture the user's raw request (everything after /autopilot) into:
   .agent/tmp/raw_request.txt

2. Run Codex to generate a high-quality expanded prompt:
   python tools/codex_promptify.py --raw .agent/tmp/raw_request.txt --out .agent/tmp/prompt.json

3. Open .agent/tmp/prompt.json and do the following:
   - Show the expanded_prompt to the user in the chat for transparency.
   - If antigravity_model_hint suggests a different model than the one currently selected, ask the user to switch to that model (one-click) before continuing.

4. Create IMPLEMENTATION_PLAN.md based on expanded_prompt with:
   - Goal / Non-goals
   - Proposed changes (files, functions)
   - Step-by-step plan
   - Verification plan (commands)
   - Rollback notes

5. Codex reviews the plan:
   python tools/codex_review_plan.py --plan IMPLEMENTATION_PLAN.md --out .agent/tmp/plan_review.json

6. If plan_review.decision == revise:
   - Apply required_changes to IMPLEMENTATION_PLAN.md
   - Re-run step 5 (max 3 loops)

7. Implement the changes following the plan.

8. Run verification commands (from prompt.json suggested_commands).
   Save the combined output to: .agent/tmp/test_output.txt

9. Codex reviews the implementation (diff + test output):
   python tools/codex_review_impl.py --out .agent/tmp/impl_review.json --testlog .agent/tmp/test_output.txt

10. If impl_review.decision == revise:
   - Apply required_changes
   - Re-run verification (step 8)
   - Re-run review (step 9) (max 3 loops)
   Else: summarize changes, show final verification results, and finish.
