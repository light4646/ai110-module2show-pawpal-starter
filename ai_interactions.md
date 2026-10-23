# AI Interactions Log

---

## Agent Workflow (SF7)

**Agent used:** Claude Code (Claude Opus) in agent mode, with access to the repo, a terminal and a browser.

**What task did you give the agent?**

Build PawPal+ phase by phase from the course instructions. That covered UML → skeleton → core classes → CLI demo → Streamlit wiring → algorithms → tests → docs. On top of the required features, it also had to add a third algorithmic capability (**next available slot**, plus a **time-blocked daily plan** that moves lower-priority clashes), JSON persistence, priority sorting, and formatted output.

**What did the agent do?**

| Files modified | What changed |
|----------------|--------------|
| `diagrams/uml_draft.mmd`, `pawpal_system.py` | Draft UML and dataclass skeletons (commit `chore: add class skeletons from UML`) |
| `pawpal_system.py`, `main.py`, `tests/test_pawpal.py`, `pytest.ini` | Core classes, CLI demo, first two tests |
| `pawpal_system.py`, `main.py`, `requirements.txt`, `.gitignore` | Sorting, filtering, recurrence, conflict detection, `next_available_slot`, `build_daily_plan`, JSON save/load, tabulate output |
| `tests/test_pawpal.py`, `pawpal_system.py` | Test suite (29 tests) and `Task.__post_init__` validation |
| `app.py` | Streamlit UI connected to the classes through `st.session_state` |
| `README.md`, `reflection.md`, `diagrams/uml_final.mmd`, `model_comparison/` | Documentation and the model comparison |

It ran `python main.py` and `python -m pytest` after each step, and drove the Streamlit app in a browser: adding pets and two clashing tasks, then completing a daily task.

**What did you have to verify or fix manually?**

These issues were caught by running things, not by reading the generated code:

1. **Segfault.** The first virtualenv used a Python 3.15 **beta**, and Streamlit crashed (exit code 139) as soon as the app rendered a table. The venv was rebuilt on Python 3.12, and the README now says which versions to use.
2. **Time picker.** Streamlit's `st.time_input` couldn't be filled in reliably by typing. It was replaced with an `HH:MM` text box, and `Task.__post_init__` validation was added so bad input like `25:00` shows an error instead of breaking sorting later.
3. **Stale UI.** After adding a task, the pet summary above the form still said "0 tasks", because Streamlit had already drawn it earlier in that run. The fix was to save, queue the message in `st.session_state.flash`, and call `st.rerun()`.
4. **Committed data file.** `data.json` was accidentally committed because the starter `.gitignore` had no trailing newline, so the new entry was glued onto `.DS_Store`. The `.gitignore` was rewritten and the commit amended.
5. **Weak test.** One test first passed if either of two answers came back (`== "18:20" or == "19:00"`). It was worked out by hand (the 10-minute gap at 18:20 is too short for a 30-minute task) and pinned to `"19:00"`.

---

## Prompt Comparison (SF11)

The same prompt was given to two models in fresh sessions with no repo access: write `Scheduler.mark_task_complete()` with daily/weekly recurrence. The prompt is in [`model_comparison/prompt.md`](model_comparison/prompt.md). The full answers are in [`claude_sonnet.md`](model_comparison/claude_sonnet.md) and [`claude_haiku.md`](model_comparison/claude_haiku.md). Both were then run against PawPal's real classes with [`run_comparison.py`](model_comparison/run_comparison.py), which wrote [`comparison_output.txt`](model_comparison/comparison_output.txt).

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude Sonnet | Claude Haiku |
| **Prompt** | Identical (see `prompt.md`) | Identical |
| **Response summary** | Finds the pet, takes the first *pending* task with that description, marks it done, then `dataclasses.replace(task, due_date=+delta, completed=False)` and adds the copy to the pet. Raises `ValueError` for a missing pet or task. | Almost the same code, with the timedelta table pulled out as a module-level `RECURRENCE` dict and a docstring listing the return and raise behaviour. |
| **What was useful** | `dataclasses.replace` copies every field, so new Task fields carry over automatically. It explained *why* it only matches pending tasks (otherwise you get duplicate chains) and listed tests worth writing. | The `RECURRENCE` lookup makes adding "monthly" a one-line change. The clearest docstring. It said up front that it hadn't run the code. |
| **Problems noticed** | Picks the first match **in list order**, not the earliest due date. In the run, a pet with Monday's and Tuesday's walk added Tuesday-first got **Tuesday's** walk completed, leaving Monday's pending. It can't complete a task for a specific day, which the UI needs. | Same list-order bug, same output. |
| **Decision** | Kept PawPal's own `mark_task_complete`, which picks the earliest pending copy by `(due_date, time)` and takes an optional `day`. Adopted `dataclasses.replace` inside `Task.next_occurrence()` in place of the hand-written constructor call. | The lookup-table idea was already in place (`RECURRENCE_STEP`), so nothing else changed. |

```
Both models   completed ['2026-10-20'], created 2026-10-21
PawPal final  completed ['2026-10-19'], created 2026-10-20
Both models   missing pet -> ValueError: No pet named 'Ghost'
PawPal final  missing pet -> ValueError: No pet named Ghost
```

**Which approach did you use in your final implementation and why?**

A mix. The models' `dataclasses.replace` is shorter and safer than listing every field by hand, so it went into `Task.next_occurrence()`. Their task selection is wrong when copies of a task exist out of order, so PawPal kept "earliest pending copy, optionally for a given day". A regression test now covers it (`test_completing_picks_earliest_pending_copy`). The two models were nearly identical on this task. Haiku's answer was slightly better organised, and Sonnet's explained its reasoning more and suggested tests.
