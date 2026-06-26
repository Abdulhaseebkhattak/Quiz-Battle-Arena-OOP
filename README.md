# 🎮 Quiz Battle Arena — Multiplayer Quiz Game Engine

A real-time, multiplayer quiz game engine built entirely from scratch utilizing robust **Object-Oriented Programming (OOP)** principles in Python. Players compete live in core topics like Computer Science, Artificial Intelligence, Mathematics, and OOP concepts, featuring dynamic scoring strategies, power-ups, and a competitive leaderboard system.

---

## 👥 Developers Information
* **Abdul Haseeb Ahmad** | Roll No: `F24-1640`
* **Aliyan Taimur Taj** | Roll No: `F24-1797`

### 🎓 Academic Context
* **University:** University of Haripur
* **Course:** Object-Oriented Programming (OOPs)
* **Instructor:** Sir Fahad Qurashi
* **Project Type:** Semester Project

---

## 🛠️ Tech Stack & Architecture
* **Backend Game Engine:** Python 3.12 (ABC, Enum, Dataclasses)
* **Frontend UI:** React 18
* **Database & Realtime Integration:** Firebase-backed online multiplayer
* **Hosting Platform:** Railway Cloud Deployment

---

## 🧬 Core OOP Concepts Demonstrated

This project serves as a practical implementation of the 5 pillars of Object-Oriented Programming:

### 1. Abstraction (`ABC` & `@abstractmethod`)
Abstract classes are implemented as strict structural templates. Core gameplay components like `GameObject` and `Question` cannot be instantiated directly; they enforce structural compliance on all child classes.
* **Implementation:** `GameObject` acts as the base layout. `Question` enforces that any question sub-type must explicitly implement its own `get_options()` and `check_answer()` routines.

### 2. Inheritance
Code reusability is maximized through hierarchical inheritance. Subclasses automatically inherit operational states and baseline magic methods from their parent blueprints.
* **Implementation:** `Player` inherits core identifiers (`id`, `name`, `__str__`, `__eq__`) directly from `GameObject`. Specific question archetypes like `MultipleChoiceQuestion`, `TrueFalseQuestion`, and `OrderQuestion` derive all global properties from the abstract `Question` parent class.

### 3. Polymorphism
Different question objects process identical method signatures in distinct, specialized behaviors. The global game loop triggers standard calls without needing to know the specific subclass under execution.
* **Implementation:** When the core engine handles user interaction, it simply executes `.get_options()`—an `MCQ` subclass dynamically outputs a 4-choice list, whereas a `TrueFalseQuestion` subclass polymorphically renders a binary `["True", "False"]` option frame.

### 4. Encapsulation (Access Control & `@property`)
State safety is heavily locked down to prevent direct data tampering or cheating. Sensitive player metrics, ongoing scores, and competitive streaks are structurally isolated using double-underscore private fields.
* **Implementation:** Direct assignments like `player.__score = 999` throw strict attribute errors. Instead, properties are safely exposed via read-only `@property` getters, and updates are strictly isolated to validation methods such as `player.add_score(points)`.

### 5. Composition
The lifecycle of transactional game data is strictly bounded within governing entity containers. Parent components create, manage, and entirely own their respective internal operational tracking states.
* **Implementation:** A `GameRound` strictly composes an active instance of a `Question` alongside a transient `answers` tracker dictionary. When the round structurally terminates, its tracking metrics are entirely decommissioned alongside it. The global `QuizGame` engine aggregates multiple composed `GameRound` cycles.

---

## 📊 Project Class Hierarchy Layout
```text
GameObject (ABC)
   └── Player
Question (ABC)
   ├── MultipleChoiceQuestion (MCQ)
   ├── TrueFalseQuestion
   └── OrderQuestion
Other Architecture Components:
   ├── ScoringStrategy (ABC Blueprint)
   ├── EventEmitter (Real-time updates)
   ├── PowerUp (ABC Strategy)
   ├── QuestionFactory
   ├── GameRound
   └── QuizGame
