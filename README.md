# PawPal+ (Module 2 Project)

**PawPal+** is a pet care planner for busy owners. It keeps track of feedings, walks, medications and appointments for several pets, sorts them into one daily schedule, warns when two tasks clash, rolls recurring tasks forward when you finish them, and suggests a plan that moves lower-priority clashes to the next free slot.

The logic lives in `pawpal_system.py` and is used by both a CLI demo (`main.py`) and a Streamlit app (`app.py`).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Use Python 3.12–3.14. The Streamlit app segfaulted on a 3.15 beta during testing.

```bash
python main.py               # CLI demo
python -m streamlit run app.py   # web app
python -m pytest             # tests
```

## System design

Final UML: [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd). The first draft is in [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd), and `diagrams/uml.mmd` is a copy of the final version.

| Class | Responsibility |
|-------|----------------|
| `Task` (dataclass) | One care activity: description, `"HH:MM"` time, duration, priority, frequency (once/daily/weekly), due date, completion status and the pet it belongs to. It validates its own input, can `mark_complete()`, and builds its `next_occurrence()`. |
| `Pet` (dataclass) | Name, species and age, plus its list of tasks: `add_task`, `remove_task`, `list_tasks`, `pending_tasks`. |
| `Owner` | Name plus a list of uniquely named pets: `add_pet`, `get_pet`, `get_all_tasks`, and JSON `save_to_json` / `load_from_json`. |
| `Scheduler` | The "brain". It reads tasks from **all** of the owner's pets and sorts, filters, completes, conflict-checks and plans them. It doesn't store tasks itself. |
| `PlanEntry` (dataclass) | One row of the suggested plan: the task, its chosen start time and the reason. |

Owner → has many → Pet → has many → Task. The Scheduler reads from the Owner.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Sorts by `(due_date, minutes after midnight)` with a lambda key, so `"9:30"` correctly comes before `"10:00"` |
| Priority sorting | `Scheduler.sort_by_priority()` | High → medium → low, ties broken by time |
| Filtering | `Scheduler.filter_tasks(pet_name, completed, day)` | Any combination of pet (case-insensitive), done/pending, and day, across every pet |
| Conflict handling | `Scheduler.detect_conflicts(day)` | Flags any pending tasks whose time windows **overlap** (not just identical start times), for the same pet or different pets. Returns warning strings instead of raising |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a daily task creates a copy due `+ timedelta(days=1)`, a weekly one `+ timedelta(weeks=1)`. One-off tasks just complete. The earliest pending copy is completed first |
| Next available slot | `Scheduler.next_available_slot(duration, day, not_before)` | Scans the day's busy intervals (07:00–21:00 by default) for the first gap long enough |
| Time-blocked plan | `Scheduler.build_daily_plan(day)` | Places tasks in priority order. A task that clashes with something already placed moves to the next free slot, and each row explains why |

## 🖥️ Sample Output

Output of `python main.py`. Seven tasks for two pets are added out of order; ANSI colours are stripped here.

```

🐾 Today's Schedule for Jordan (Thu Oct 22) — sorted by time
╭────────┬───────┬───────────────────┬──────────┬────────────┬───────────┬───────────╮
│ Time   │ Pet   │ Task              │ Length   │ Priority   │ Repeats   │ Status    │
├────────┼───────┼───────────────────┼──────────┼────────────┼───────────┼───────────┤
│ 07:30  │ Mochi │ 🦮 Morning walk    │ 30 min   │ 🔴 high     │ daily     │ ⏳ pending │
│ 08:00  │ Mochi │ 🍽️ Breakfast      │ 10 min   │ 🔴 high     │ daily     │ ⏳ pending │
│ 08:00  │ Luna  │ 🍽️ Breakfast      │ 10 min   │ 🔴 high     │ daily     │ ⏳ pending │
│ 09:00  │ Luna  │ 💊 Flea medication │ 5 min    │ 🔴 high     │ weekly    │ ⏳ pending │
│ 15:00  │ Mochi │ 🩺 Vet appointment │ 60 min   │ 🟡 medium   │ once      │ ⏳ pending │
│ 18:00  │ Luna  │ 🎾 Play session    │ 20 min   │ 🟢 low      │ daily     │ ⏳ pending │
│ 18:30  │ Mochi │ 🦮 Evening walk    │ 30 min   │ 🟡 medium   │ daily     │ ⏳ pending │
╰────────┴───────┴───────────────────┴──────────┴────────────┴───────────┴───────────╯

🔎 Filter: only Luna's tasks
╭────────┬───────┬───────────────────┬──────────┬────────────┬───────────┬───────────╮
│ Time   │ Pet   │ Task              │ Length   │ Priority   │ Repeats   │ Status    │
├────────┼───────┼───────────────────┼──────────┼────────────┼───────────┼───────────┤
│ 08:00  │ Luna  │ 🍽️ Breakfast      │ 10 min   │ 🔴 high     │ daily     │ ⏳ pending │
│ 09:00  │ Luna  │ 💊 Flea medication │ 5 min    │ 🔴 high     │ weekly    │ ⏳ pending │
│ 18:00  │ Luna  │ 🎾 Play session    │ 20 min   │ 🟢 low      │ daily     │ ⏳ pending │
╰────────┴───────┴───────────────────┴──────────┴────────────┴───────────┴───────────╯

⚠️  Conflict check
WARNING: 08:00 Mochi: Breakfast overlaps 08:00 Luna: Breakfast (different pets)

🔁 Completing Mochi's daily Morning walk
Done. Next occurrence created for Fri Oct 23 at 07:30
Pending today: 6 | Completed today: 1

⭐ Priority order (high first, then by time)
╭────────┬───────┬───────────────────┬──────────┬────────────┬───────────┬───────────╮
│ Time   │ Pet   │ Task              │ Length   │ Priority   │ Repeats   │ Status    │
├────────┼───────┼───────────────────┼──────────┼────────────┼───────────┼───────────┤
│ 08:00  │ Mochi │ 🍽️ Breakfast      │ 10 min   │ 🔴 high     │ daily     │ ⏳ pending │
│ 08:00  │ Luna  │ 🍽️ Breakfast      │ 10 min   │ 🔴 high     │ daily     │ ⏳ pending │
│ 09:00  │ Luna  │ 💊 Flea medication │ 5 min    │ 🔴 high     │ weekly    │ ⏳ pending │
│ 15:00  │ Mochi │ 🩺 Vet appointment │ 60 min   │ 🟡 medium   │ once      │ ⏳ pending │
│ 18:30  │ Mochi │ 🦮 Evening walk    │ 30 min   │ 🟡 medium   │ daily     │ ⏳ pending │
│ 18:00  │ Luna  │ 🎾 Play session    │ 20 min   │ 🟢 low      │ daily     │ ⏳ pending │
╰────────┴───────┴───────────────────┴──────────┴────────────┴───────────┴───────────╯

🧩 Time-blocked daily plan (clashes moved to the next free slot)
╭─────────┬───────┬───────────────────┬────────────────────────────────────────────────────────────────────╮
│ Start   │ Pet   │ Task              │ Why                                                                │
├─────────┼───────┼───────────────────┼────────────────────────────────────────────────────────────────────┤
│ 08:00   │ Mochi │ 🍽️ Breakfast      │ high priority, at requested time                                   │
│ 08:10   │ Luna  │ 🍽️ Breakfast      │ moved from 08:00: clashed with Mochi's 'Breakfast' (high priority) │
│ 09:00   │ Luna  │ 💊 Flea medication │ high priority, at requested time                                   │
│ 15:00   │ Mochi │ 🩺 Vet appointment │ medium priority, at requested time                                 │
│ 18:00   │ Luna  │ 🎾 Play session    │ low priority, at requested time                                    │
│ 18:30   │ Mochi │ 🦮 Evening walk    │ medium priority, at requested time                                 │
╰─────────┴───────┴───────────────────┴────────────────────────────────────────────────────────────────────╯

🕒 Next available 45-minute slot
Earliest free slot after 07:30: 08:10
Earliest free slot after 15:00: 16:00

💾 Persistence
Saved to data.json and reloaded: 2 pets, 8 tasks
```

The plan table above is the **advanced scheduling** stretch feature. Both Breakfasts are high priority at 08:00. Mochi's was added first, so it keeps 08:00 and Luna's moves to 08:10, the next free 10-minute gap. Lower-priority tasks that don't clash keep their requested times.

## 🧪 Testing PawPal+

```bash
python -m pytest        # or: python -m pytest -v
```

`tests/test_pawpal.py` has 29 tests covering:

- **Core classes:** completion, adding/removing tasks, duplicate pet names rejected, the Owner collecting tasks from all pets, and input validation (bad times like `25:00`, unknown priority/frequency, zero duration).
- **Sorting:** chronological order across pets, times without a leading zero, and priority-then-time order.
- **Filtering:** by pet and by completion status.
- **Recurrence:** daily → next day, weekly → +7 days, one-off creates nothing, the earliest pending copy is completed first, and unknown tasks raise.
- **Conflicts:** exact same time across pets, overlapping durations for one pet, back-to-back tasks *not* flagged, and completed tasks ignored.
- **Planning:** next free slot (including the "gap too short" case), a full day returning `None`, and lower-priority clashes moving in the plan.
- **Edge cases and persistence:** a pet with no tasks, and a JSON save/load round trip.

```
cachedir: .pytest_cache
rootdir: .../ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collecting ... collected 29 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  3%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [  6%]
tests/test_pawpal.py::test_task_rejects_invalid_input[kwargs0] PASSED    [ 10%]
tests/test_pawpal.py::test_task_rejects_invalid_input[kwargs1] PASSED    [ 13%]
tests/test_pawpal.py::test_task_rejects_invalid_input[kwargs2] PASSED    [ 17%]
tests/test_pawpal.py::test_task_rejects_invalid_input[kwargs3] PASSED    [ 20%]
tests/test_pawpal.py::test_task_rejects_invalid_input[kwargs4] PASSED    [ 24%]
tests/test_pawpal.py::test_task_normalizes_time PASSED                   [ 27%]
tests/test_pawpal.py::test_remove_task PASSED                            [ 31%]
tests/test_pawpal.py::test_owner_rejects_duplicate_pet_names PASSED      [ 34%]
tests/test_pawpal.py::test_owner_collects_tasks_from_all_pets PASSED     [ 37%]
tests/test_pawpal.py::test_pet_with_no_tasks_gives_empty_schedule PASSED [ 41%]
tests/test_pawpal.py::test_sort_by_time_is_chronological_across_pets PASSED [ 44%]
tests/test_pawpal.py::test_sort_by_time_compares_as_times_not_strings PASSED [ 48%]
tests/test_pawpal.py::test_sort_by_priority_then_time PASSED             [ 51%]
tests/test_pawpal.py::test_filter_by_pet_and_status PASSED               [ 55%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_day_task PASSED [ 58%]
tests/test_pawpal.py::test_completing_weekly_task_creates_task_a_week_later PASSED [ 62%]
tests/test_pawpal.py::test_completing_one_off_task_creates_nothing PASSED [ 65%]
tests/test_pawpal.py::test_completing_picks_earliest_pending_copy PASSED [ 68%]
tests/test_pawpal.py::test_completing_unknown_task_raises PASSED         [ 72%]
tests/test_pawpal.py::test_detects_exact_same_time_across_pets PASSED    [ 75%]
tests/test_pawpal.py::test_detects_overlapping_durations_for_same_pet PASSED [ 79%]
tests/test_pawpal.py::test_back_to_back_tasks_do_not_conflict PASSED     [ 82%]
tests/test_pawpal.py::test_completed_tasks_are_not_conflicts PASSED      [ 86%]
tests/test_pawpal.py::test_next_available_slot_skips_busy_windows PASSED [ 89%]
tests/test_pawpal.py::test_next_available_slot_returns_none_when_day_is_full PASSED [ 93%]
tests/test_pawpal.py::test_daily_plan_moves_lower_priority_clash PASSED  [ 96%]
tests/test_pawpal.py::test_json_round_trip PASSED                        [100%]

============================== 29 passed in 0.03s ==============================
```

**Confidence level: ★★★★☆ (4/5).** Every scheduling behaviour has a passing test, including the edge cases above. The missing star is for things that aren't tested: tasks that run past midnight, and the Streamlit UI, which was only checked by hand in the browser.

## 💾 Data persistence

Data is saved between runs in `data.json`, which is git-ignored.

- **Files modified:** `pawpal_system.py` (`Task.to_dict/from_dict`, `Pet.to_dict/from_dict`, `Owner.save_to_json/load_from_json`), `app.py`, and `main.py`.
- **How it works in the app:** on first load, `app.py` calls `Owner.load_from_json("data.json")` if the file exists and keeps the Owner in `st.session_state`. Every change (adding a pet or task, completing a task) calls `save()`, which writes the whole Owner back to the file. Restart the app and your pets and tasks are still there. If the file is corrupt, the app shows a warning and starts empty instead of crashing.
- **Format:** dates are stored as ISO strings. Each Pet stores its tasks nested inside it, and `pet_name` is rebuilt by `Pet.add_task` on load rather than stored twice.
- `main.py` ends by saving to `data.json`, reloading, and printing the counts as a round-trip check.

## 🎨 Output formatting

- **CLI (`main.py`):** the `tabulate` library (`tablefmt="rounded_outline"`) in `task_table()` and the plan table, ANSI bold/yellow/green codes for headings, warnings and confirmations, and emoji status (`✅ done` / `⏳ pending`).
- **Shared helpers in `pawpal_system.py`:** `task_emoji(description)` picks an emoji from keywords (walk 🦮, breakfast/feed 🍽️, med 💊, vet 🩺, play 🎾 …, default 🐾), and `PRIORITY_BADGE` maps priorities to 🔴/🟡/🟢 badges.
- **Streamlit (`app.py`):** `st.table` for the schedule and plan, `st.warning` for conflicts, `st.success`/`st.error` for actions and validation, and the same emoji and badges.

## 📸 Demo Walkthrough

1. **Start the app** with `python -m streamlit run app.py`. If `data.json` exists, your saved owner, pets and tasks load automatically. Otherwise you start with an empty profile for "Jordan" (you can rename the owner at the top).
2. **Add pets.** Enter a name, species and age under *Owner & pets* and click **Add pet**. The summary line updates, e.g. "**Mochi** (dog, 1y, 0 tasks) · **Luna** (dog, 1y, 0 tasks)". Adding a second pet with the same name shows an error.
3. **Schedule tasks.** Under *Schedule a task*, pick the pet and enter a description, date, time (`HH:MM`), duration, priority and repeat frequency. In testing, *Morning walk* was added for Mochi at 07:30 (high, daily) and *Breakfast* for Luna at 7:40. The app normalised the time to 07:40, confirmed "Scheduled Breakfast for Luna at 07:40." and warned straight away: "Heads up: 07:30 Mochi: Morning walk overlaps 07:40 Luna: Breakfast (different pets)". An invalid time such as `25:00` is rejected with an error.
4. **View the schedule.** The *Schedule* table lists the day's tasks across all pets with emoji, priority badges and status. You can filter by pet and status and sort by time or priority. A yellow **Schedule conflicts** box lists every overlap, and a day with no clashes shows "No conflicts on this day."
5. **Check the suggested plan.** The *Suggested plan* table kept the high-priority walk at 07:30 and moved Luna's Breakfast to 07:50, with the reason "moved from 07:40: clashed with Mochi's 'Morning walk' (high priority)".
6. **Complete a task.** Pick a pending task and click **Mark complete ✅**. Completing the daily walk showed "Marked Morning walk done. Next daily occurrence added for Fri Oct 23." and Mochi's count went to 2 tasks.
7. **Find a free slot.** Open *Find a free slot*, enter a length and day, and it reports the earliest gap between 07:00 and 21:00.
8. **Persistence.** Stop and restart the app (or open a new browser session): the pets and tasks are reloaded from `data.json`.

The CLI equivalent of the whole workflow is the sample output above.
