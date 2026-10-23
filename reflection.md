# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

1. Add a pet (name, species, age) to the owner's profile.
2. Schedule a care task for a pet (walk, feeding, meds, appointment) with a time, duration, priority and how often it repeats.
3. See today's schedule across all pets, in time order, with warnings when two tasks clash.

**a. Initial design**

The first UML (`diagrams/uml_draft.mmd`) had four classes:

- **Task** (dataclass): one care activity, holding description, time (`"HH:MM"`), duration, priority, frequency and completion status. It can mark itself complete.
- **Pet** (dataclass): name, species, age and its own list of tasks, with methods to add and list them.
- **Owner**: the owner's name and list of pets. It can add/find pets and collect every task across them.
- **Scheduler**: the "brain". It holds a reference to an Owner and sorts, filters and checks tasks across all pets. It doesn't store tasks itself.

Relationships: an Owner has many Pets, a Pet has many Tasks, and the Scheduler reads from the Owner.

**b. Design changes**

Yes, in four ways:

- **Tasks know their pet (`Task.pet_name`).** When the Scheduler pulled tasks from every pet into one list, it lost track of which pet each task belonged to, so the schedule couldn't say "Mochi: Morning walk" or filter by pet. `Pet.add_task` now stamps the pet's name on the task. It's a little redundant, but it keeps sorting and filtering to one flat list instead of passing (pet, task) pairs everywhere.
- **Tasks got a `due_date` and `duration_minutes` mattered more than planned.** Recurrence needs a date to move forward, and real conflict detection needs to know when a task ends, not just when it starts.
- **New `PlanEntry` class.** The time-blocked plan has to say *when* a task will actually happen and *why*, without changing the task's own requested time, so each plan row wraps the task with a start time and a reason.
- **Validation in `Task.__post_init__`.** Once the UI let people type times, `"25:00"` or `"noon"` would have crashed sorting much later. Checking when the Task is created moves the error to where the mistake happens.

`diagrams/uml_final.mmd` shows the final version.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers **time of day** (tasks are sorted by start time and must fit between 07:00 and 21:00), **duration** (two tasks conflict if their windows overlap), **priority** (high → medium → low decides what keeps its slot in the suggested plan), **recurrence** (daily/weekly) and **completion status** (finished tasks are never flagged as conflicts or planned again). Time and priority mattered most, because for a pet the important things (medication, feeding) usually have to happen at a specific time. Priority is how the plan decides who wins a clash.

**b. Tradeoffs**

The suggested plan is **greedy**. It places tasks in priority order and pushes a clashing task to the *next* free gap after its requested time. It never moves an already-placed task, and it never looks for a better overall arrangement. So a low-priority task can get pushed later than strictly necessary, and two equal-priority tasks at the same time are settled by the order they were added. That's reasonable here: a pet owner's day has maybe 5–15 tasks, the result is easy to explain in one sentence per row, and an "optimal" schedule that shuffles everything would be harder to trust. Conflict detection, on the other hand, checks real overlapping durations rather than only identical start times, because a 30-minute walk at 07:30 really does clash with breakfast at 07:40.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code in agent mode for the whole build, one phase at a time: drafting the Mermaid UML, writing the class skeleton, implementing the classes and algorithms, writing tests, connecting the Streamlit UI and drafting the docs. After each step it ran `python main.py` and `pytest`, and it drove the Streamlit app in a browser to check the UI. The most useful prompts were specific and could be checked, like "make sorting work for `HH:MM` strings" or "conflicts should warn, not crash". Asking for edge cases (a pet with no tasks, back-to-back tasks, a full day) also helped, because those became tests.

**b. Judgment and verification**

I gave two models (Claude Sonnet and Claude Haiku) the same prompt for `mark_task_complete` with recurrence. Both used `dataclasses.replace`, which I adopted. Both also completed the *first matching task in the list*, and running their code against my real classes showed that with Monday's and Tuesday's walk added Tuesday-first, they completed Tuesday's walk and left Monday's undone. I kept my own version, which completes the earliest pending copy, and added a regression test (`ai_interactions.md` has the details). I also didn't trust that the generated tests were right. One test accepted either of two answers, so I worked out the correct one by hand and pinned it. Verification was always: run the demo, run pytest, try it in the browser.

---

## 4. Testing and Verification

**a. What you tested**

29 tests in `tests/test_pawpal.py` cover:

- task completion and adding/removing tasks
- input validation
- sorting by time (including `9:30` vs `10:00`) and by priority
- filtering by pet and status
- daily and weekly recurrence, one-off tasks, and completing the earliest copy
- conflicts: same time across pets, overlap for the same pet, back-to-back tasks not flagged, completed tasks ignored
- next free slot and a full day
- the plan moving a lower-priority clash
- JSON round-trip

These matter because sorting, recurrence and conflicts are where the bugs would be quiet: a wrong order or a duplicated daily task doesn't crash anything, it just gives the owner a wrong schedule.

**b. Confidence**

4 out of 5. All the scheduling logic is tested, including edge cases, and the UI was checked by hand. Next I would test tasks that run past midnight (e.g. 23:30 for 60 minutes), what happens when you skip several days and then complete a daily task, and automated UI tests with Streamlit's `AppTest`.

---

## 5. Reflection

**a. What went well**

The suggested plan. It doesn't just say there's a conflict, it fixes it and explains why ("moved from 08:00: clashed with Mochi's 'Breakfast' (high priority)"). Keeping all the logic in `pawpal_system.py` also meant the CLI, the tests and the UI all use the same code.

**b. What you would improve**

I'd let the owner set their own day start/end and available minutes, let a task be edited instead of removed and re-added, and give tasks a unique id instead of matching by description.

**c. Key takeaway**

AI can write a lot of working code fast, but "it runs" is not the same as "it's right". The bugs in this project (the list-order recurrence bug, the stale UI count, the Python beta crash, the weak test) were only found by running things and checking edge cases, not by reading the code. Being the lead architect means deciding the design and the checks, and only accepting a suggestion once it has passed them.
