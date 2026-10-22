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

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
