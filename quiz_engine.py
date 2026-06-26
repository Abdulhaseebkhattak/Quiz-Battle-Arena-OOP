"""
quiz_engine.py — Python port of the JS quiz game engine.

Mirrors the OOP design in src/App.jsx using idiomatic Python:
    - ABC + @abstractmethod ............. abstract base classes
    - @property ......................... read-only getters
    - Name mangling (__score) ........... encapsulation
    - Enum .............................. typed constants
    - @dataclass ........................ value/record types
    - Factory, Strategy, Observer,
      Decorator, Template Method ........ design patterns
"""

from __future__ import annotations

import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ============================================================
# OOP CONCEPT: ENUMS (typed constants, not bare strings)
# ============================================================
class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GamePhase(str, Enum):
    LOBBY = "lobby"
    CATEGORY_SELECT = "category_select"
    PLAYING = "playing"
    ROUND_RESULT = "round_result"
    GAME_OVER = "game_over"


class PowerUpType(str, Enum):
    DOUBLE_POINTS = "double_points"
    FIFTY_FIFTY = "fifty_fifty"
    TIME_FREEZE = "time_freeze"
    STEAL_POINTS = "steal_points"


# Difficulty -> (base points, time limit in seconds)
_DIFFICULTY_TABLE: dict[Difficulty, tuple[int, int]] = {
    Difficulty.EASY: (100, 20),
    Difficulty.MEDIUM: (200, 15),
    Difficulty.HARD: (300, 10),
}


# ============================================================
# OOP CONCEPT: DATACLASS (lightweight record for an answer log entry)
# ============================================================
@dataclass(frozen=True)
class AnswerRecord:
    question_id: str
    correct: bool
    points: int
    time_ms: float
    timestamp: float


@dataclass(frozen=True)
class RoundResult:
    correct: bool
    points: int
    time_left: float
    answer_index: int


# ============================================================
# OOP CONCEPT: ABSTRACT BASE CLASS (ABC)
# Cannot be instantiated; mirrors `GameObject` in App.jsx.
# ============================================================
class GameObject(ABC):
    def __init__(self, obj_id: str, name: str) -> None:
        self._id = obj_id
        self._name = name
        self._created_at = time.time()

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._name!r})"

    @abstractmethod
    def describe(self) -> str:
        """Force subclasses to provide a description (forces ABC behavior)."""


# ============================================================
# OOP CONCEPT: INHERITANCE + ENCAPSULATION (name mangling via __score)
# ============================================================
class Player(GameObject):
    def __init__(self, player_id: str, name: str, avatar: str) -> None:
        super().__init__(player_id, name)
        # Double-underscore => name mangling -> _Player__score (encapsulation).
        self.__score: int = 0
        self.__streak: int = 0
        self.__power_ups: list["PowerUp"] = []
        self.__answers: list[AnswerRecord] = []
        self.__avatar = avatar
        self.__is_ready = False

    # @property exposes read-only access; no setter -> immutable from outside.
    @property
    def score(self) -> int:
        return self.__score

    @property
    def streak(self) -> int:
        return self.__streak

    @property
    def power_ups(self) -> list["PowerUp"]:
        return list(self.__power_ups)  # defensive copy

    @property
    def avatar(self) -> str:
        return self.__avatar

    @property
    def is_ready(self) -> bool:
        return self.__is_ready

    @property
    def stats(self) -> dict[str, int]:
        total = len(self.__answers)
        correct = sum(1 for a in self.__answers if a.correct)
        # best streak across history
        best = run = 0
        for a in self.__answers:
            run = run + 1 if a.correct else 0
            best = max(best, run)
        return {
            "total": total,
            "correct": correct,
            "accuracy": round((correct / total) * 100) if total else 0,
            "best_streak": best,
        }

    def toggle_ready(self) -> bool:
        self.__is_ready = not self.__is_ready
        return self.__is_ready

    def add_score(self, points: int) -> None:
        self.__score += points

    def increment_streak(self) -> None:
        self.__streak += 1

    def reset_streak(self) -> None:
        self.__streak = 0

    def add_power_up(self, power_up: "PowerUp") -> None:
        self.__power_ups.append(power_up)

    def use_power_up(self, p_type: PowerUpType) -> "PowerUp | None":
        for i, p in enumerate(self.__power_ups):
            if p.type == p_type:
                return self.__power_ups.pop(i)
        return None

    def record_answer(self, question_id: str, correct: bool, points: int, time_ms: float) -> None:
        self.__answers.append(
            AnswerRecord(question_id, correct, points, time_ms, time.time())
        )

    def reset(self) -> None:
        self.__score = 0
        self.__streak = 0
        self.__power_ups = []
        self.__answers = []

    def describe(self) -> str:
        return f"Player {self._name} (score={self.__score}, streak={self.__streak})"


# ============================================================
# OOP CONCEPT: TEMPLATE METHOD PATTERN
# Question defines the common skeleton; subclasses fill in the abstract steps.
# Also showcases POLYMORPHISM: any Question subtype supports the same API.
# ============================================================
class Question(GameObject):
    def __init__(self, q_id: str, text: str, category: str, difficulty: Difficulty) -> None:
        super().__init__(q_id, text)
        self.__difficulty = difficulty
        self.__category = category
        points, time_limit = _DIFFICULTY_TABLE[difficulty]
        self.__points = points
        self.__time_limit = time_limit

    @property
    def text(self) -> str:
        return self._name

    @property
    def difficulty(self) -> Difficulty:
        return self.__difficulty

    @property
    def category(self) -> str:
        return self.__category

    @property
    def points(self) -> int:
        return self.__points

    @property
    def time_limit(self) -> int:
        return self.__time_limit

    # ---- abstract steps (Template Method hooks) ----
    @abstractmethod
    def get_options(self) -> list[str]: ...

    @abstractmethod
    def check_answer(self, answer_index: int) -> bool: ...

    @abstractmethod
    def get_correct_answer(self) -> str: ...

    # ---- shared concrete step ----
    def get_hint(self) -> str:
        return "No hint available"

    def describe(self) -> str:
        return f"[{self.__difficulty.value}/{self.__category}] {self._name}"


class MultipleChoiceQuestion(Question):
    def __init__(self, q_id, text, category, difficulty, options: list[str], correct_index: int) -> None:
        super().__init__(q_id, text, category, difficulty)
        self.__options = list(options)
        self.__correct_index = correct_index

    def get_options(self) -> list[str]:
        return list(self.__options)

    def check_answer(self, answer_index: int) -> bool:
        return answer_index == self.__correct_index

    def get_correct_answer(self) -> str:
        return self.__options[self.__correct_index]

    def get_hint(self) -> str:
        return f'The answer starts with "{self.get_correct_answer()[0]}"'


class TrueFalseQuestion(Question):
    def __init__(self, q_id, text, category, difficulty, answer: bool) -> None:
        super().__init__(q_id, text, category, difficulty)
        self.__answer = answer

    def get_options(self) -> list[str]:
        return ["True", "False"]

    def check_answer(self, answer_index: int) -> bool:
        return (answer_index == 0) == self.__answer

    def get_correct_answer(self) -> str:
        return "True" if self.__answer else "False"


class OrderQuestion(Question):
    def __init__(self, q_id, text, category, difficulty, items: list[str], correct_order: list[int]) -> None:
        super().__init__(q_id, text, category, difficulty)
        self.__items = list(items)
        self.__correct_order = list(correct_order)

    def get_options(self) -> list[str]:
        return list(self.__items)

    def check_answer(self, answer_index: int) -> bool:
        return answer_index == self.__correct_order[0]

    def get_correct_answer(self) -> str:
        return self.__items[self.__correct_order[0]]

    def get_hint(self) -> str:
        return f'First in order: "{self.__items[self.__correct_order[0]]}"'


# ============================================================
# OOP CONCEPT: FACTORY PATTERN
# Single entry point hides which concrete Question subclass is built.
# ============================================================
class QuestionFactory:
    _counter = 0

    @classmethod
    def create(cls, data: dict[str, Any]) -> Question:
        cls._counter += 1
        q_id = f"q_{cls._counter}"
        q_type = data["type"]
        if q_type == "mcq":
            return MultipleChoiceQuestion(
                q_id, data["text"], data["category"], data["difficulty"],
                data["options"], data["correct_index"],
            )
        if q_type == "tf":
            return TrueFalseQuestion(
                q_id, data["text"], data["category"], data["difficulty"], data["answer"],
            )
        if q_type == "order":
            return OrderQuestion(
                q_id, data["text"], data["category"], data["difficulty"],
                data["items"], data["correct_order"],
            )
        raise ValueError(f"Unknown question type: {q_type}")


# ============================================================
# OOP CONCEPT: STRATEGY PATTERN
# Interchangeable scoring algorithms behind a common interface.
# ============================================================
class ScoringStrategy(ABC):
    @abstractmethod
    def calculate(self, base_points: int, time_left: float, time_limit: float, streak: int) -> int: ...


class StandardScoring(ScoringStrategy):
    def calculate(self, base_points, time_left, time_limit, streak) -> int:
        time_bonus = round((time_left / time_limit) * 50)
        streak_bonus = min(streak * 25, 150)
        return base_points + time_bonus + streak_bonus


class BlitzScoring(ScoringStrategy):
    def calculate(self, base_points, time_left, time_limit, streak) -> int:
        multiplier = 1 + (time_left / time_limit)
        return round(base_points * multiplier) + (streak * 50)


class SurvivalScoring(ScoringStrategy):
    def calculate(self, base_points, time_left, time_limit, streak) -> int:
        return base_points + (streak * streak * 10)


# ============================================================
# OOP CONCEPT: OBSERVER PATTERN
# Subscribers register callbacks; emit() fans out events.
# ============================================================
class EventEmitter:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[Any], None]]] = {}

    def on(self, event: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        self._listeners.setdefault(event, []).append(callback)
        return lambda: self.off(event, callback)

    def off(self, event: str, callback: Callable[[Any], None]) -> None:
        if event in self._listeners:
            self._listeners[event] = [cb for cb in self._listeners[event] if cb is not callback]

    def emit(self, event: str, data: Any = None) -> None:
        for cb in list(self._listeners.get(event, [])):
            cb(data)


# ============================================================
# OOP CONCEPT: DECORATOR PATTERN
# PowerUps wrap/augment the round's scoring context without changing
# the GameRound's interface.
# ============================================================
class PowerUp(ABC):
    def __init__(self, p_type: PowerUpType, name: str, icon: str, description: str) -> None:
        self.__type = p_type
        self.__name = name
        self.__icon = icon
        self.__description = description

    @property
    def type(self) -> PowerUpType:
        return self.__type

    @property
    def name(self) -> str:
        return self.__name

    @property
    def icon(self) -> str:
        return self.__icon

    @property
    def description(self) -> str:
        return self.__description

    @abstractmethod
    def apply(self, context: dict[str, Any]) -> None: ...


class DoublePointsPowerUp(PowerUp):
    def __init__(self) -> None:
        super().__init__(PowerUpType.DOUBLE_POINTS, "Double Points", "⚡", "2x points this round")

    def apply(self, context):
        context["point_multiplier"] = 2


class FiftyFiftyPowerUp(PowerUp):
    def __init__(self) -> None:
        super().__init__(PowerUpType.FIFTY_FIFTY, "50/50", "✂️", "Remove 2 wrong answers")

    def apply(self, context):
        context["eliminate_options"] = 2


class TimeFreezePowerUp(PowerUp):
    def __init__(self) -> None:
        super().__init__(PowerUpType.TIME_FREEZE, "Time Freeze", "🧊", "Extra 10 seconds")

    def apply(self, context):
        context["bonus_time"] = 10


class StealPointsPowerUp(PowerUp):
    def __init__(self) -> None:
        super().__init__(PowerUpType.STEAL_POINTS, "Point Steal", "🏴‍☠️", "Steal 50pts from opponent")

    def apply(self, context):
        context["steal_points"] = 50


# Factory for power-ups (Factory pattern again, scoped to a different family).
class PowerUpFactory:
    _registry: dict[PowerUpType, type[PowerUp]] = {
        PowerUpType.DOUBLE_POINTS: DoublePointsPowerUp,
        PowerUpType.FIFTY_FIFTY: FiftyFiftyPowerUp,
        PowerUpType.TIME_FREEZE: TimeFreezePowerUp,
        PowerUpType.STEAL_POINTS: StealPointsPowerUp,
    }

    @classmethod
    def create(cls, p_type: PowerUpType) -> PowerUp:
        if p_type not in cls._registry:
            raise ValueError(f"Unknown power-up: {p_type}")
        return cls._registry[p_type]()

    @classmethod
    def random(cls) -> PowerUp:
        return cls.create(random.choice(list(cls._registry.keys())))


# ============================================================
# OOP CONCEPT: COMPOSITION
# A GameRound is composed of a Question, a list of Players, and a ScoringStrategy.
# ============================================================
class GameRound:
    def __init__(self, question: Question, players: list[Player]) -> None:
        self.__question = question
        self.__players = players
        self.__answers: dict[str, RoundResult] = {}
        self.__start_time: float | None = None
        self.__active = False

    @property
    def question(self) -> Question:
        return self.__question

    @property
    def is_active(self) -> bool:
        return self.__active

    def start(self) -> None:
        self.__start_time = time.time()
        self.__active = True

    def submit_answer(
        self,
        player: Player,
        answer_index: int,
        scoring_strategy: ScoringStrategy,
        context: dict[str, Any] | None = None,
    ) -> RoundResult | None:
        context = context or {}
        if not self.__active or player.id in self.__answers or self.__start_time is None:
            return None

        elapsed = time.time() - self.__start_time
        time_limit = self.__question.time_limit + context.get("bonus_time", 0)
        time_left = max(0.0, time_limit - elapsed)
        correct = self.__question.check_answer(answer_index)

        points = 0
        if correct:
            player.increment_streak()
            raw = scoring_strategy.calculate(self.__question.points, time_left, time_limit, player.streak)
            points = round(raw * context.get("point_multiplier", 1))
            player.add_score(points)
        else:
            player.reset_streak()

        player.record_answer(self.__question.id, correct, points, elapsed * 1000)
        result = RoundResult(correct=correct, points=points, time_left=time_left, answer_index=answer_index)
        self.__answers[player.id] = result
        return result

    def end(self) -> None:
        self.__active = False

    def get_results(self) -> dict[str, Any]:
        return {"question": self.__question, "answers": dict(self.__answers)}


# ============================================================
# OOP CONCEPT: AGGREGATION + COMPOSITION + Observer
# QuizGame inherits EventEmitter (multiple roles via inheritance),
# owns players/rounds/strategy.
# ============================================================
_STRATEGY_REGISTRY: dict[str, type[ScoringStrategy]] = {
    "standard": StandardScoring,
    "blitz": BlitzScoring,
    "survival": SurvivalScoring,
}


class QuizGame(EventEmitter):
    def __init__(self, question_bank: list[dict[str, Any]], total_rounds: int = 10, scoring_mode: str = "standard") -> None:
        super().__init__()
        self.__players: dict[str, Player] = {}
        self.__current_round: GameRound | None = None
        self.__phase = GamePhase.LOBBY
        self.__total_rounds = total_rounds
        self.__round_index = 0
        self.__question_pool: list[Question] = []
        self.__question_bank = question_bank
        self.__scoring_strategy = _STRATEGY_REGISTRY[scoring_mode]()

    @property
    def phase(self) -> GamePhase:
        return self.__phase

    @property
    def players(self) -> list[Player]:
        return list(self.__players.values())

    @property
    def current_round(self) -> GameRound | None:
        return self.__current_round

    @property
    def round_index(self) -> int:
        return self.__round_index

    @property
    def total_rounds(self) -> int:
        return self.__total_rounds

    @property
    def scoring_strategy(self) -> ScoringStrategy:
        return self.__scoring_strategy

    def add_player(self, name: str, avatar: str) -> Player:
        p_id = f"p_{uuid.uuid4().hex[:8]}"
        player = Player(p_id, name, avatar)
        player.add_power_up(PowerUpFactory.random())
        player.add_power_up(PowerUpFactory.random())
        self.__players[p_id] = player
        self.emit("player_joined", player)
        return player

    def remove_player(self, p_id: str) -> None:
        self.__players.pop(p_id, None)
        self.emit("player_left", {"id": p_id})

    def set_questions(self, category: str | None) -> None:
        pool = [q for q in self.__question_bank if not category or q["category"] == category]
        random.shuffle(pool)
        self.__question_pool = [QuestionFactory.create(q) for q in pool[: self.__total_rounds]]

    def start_game(self, category: str | None = None) -> GameRound | None:
        self.set_questions(category)
        self.__phase = GamePhase.PLAYING
        self.__round_index = 0
        self.emit("game_started")
        return self.next_round()

    def next_round(self) -> GameRound | None:
        if self.__round_index >= len(self.__question_pool):
            self.__current_round = None
            self.end_game()
            return None
        question = self.__question_pool[self.__round_index]
        self.__current_round = GameRound(question, self.players)
        self.__current_round.start()
        self.__round_index += 1
        # Every 3 rounds, hand out a random power-up to every player.
        if self.__round_index % 3 == 0:
            for p in self.players:
                p.add_power_up(PowerUpFactory.random())
        self.emit("round_started", {"round": self.__round_index, "question": question})
        return self.__current_round

    def submit_answer(self, player_id: str, answer_index: int, context: dict[str, Any] | None = None) -> RoundResult | None:
        context = context or {}
        player = self.__players.get(player_id)
        if not player or not self.__current_round:
            return None
        result = self.__current_round.submit_answer(player, answer_index, self.__scoring_strategy, context)
        if result and context.get("steal_points") and result.correct:
            for other in self.players:
                if other.id != player_id:
                    other.add_score(-context["steal_points"])
        if result:
            self.emit("answer_submitted", {"player_id": player_id, "result": result})
        return result

    def end_round(self) -> None:
        if self.__current_round:
            self.__current_round.end()
            self.emit("round_ended", self.__current_round.get_results())

    def end_game(self) -> None:
        self.__phase = GamePhase.GAME_OVER
        leaderboard = sorted(self.players, key=lambda p: p.score, reverse=True)
        self.emit("game_over", {"leaderboard": leaderboard})

    def reset_game(self) -> None:
        for p in self.players:
            p.reset()
        self.__current_round = None
        self.__round_index = 0
        self.__phase = GamePhase.LOBBY
        self.emit("game_reset")


# ============================================================
# QUESTION BANK — focused on the Python & OOP category so the demo
# exercises the new content end-to-end.
# ============================================================
QUESTION_BANK: list[dict[str, Any]] = [
    {"type": "mcq", "text": "Which keyword defines a function in Python?",
     "category": "PythonOOP", "difficulty": Difficulty.EASY,
     "options": ["function", "def", "fn", "lambda"], "correct_index": 1},
    {"type": "mcq", "text": "What is the first parameter of an instance method conventionally named?",
     "category": "PythonOOP", "difficulty": Difficulty.EASY,
     "options": ["this", "self", "cls", "me"], "correct_index": 1},
    {"type": "mcq", "text": "Which dunder method is the constructor in Python?",
     "category": "PythonOOP", "difficulty": Difficulty.EASY,
     "options": ["__new__", "__init__", "__call__", "__construct__"], "correct_index": 1},
    {"type": "tf", "text": "`class Dog(Animal):` declares Dog as a subclass of Animal.",
     "category": "PythonOOP", "difficulty": Difficulty.EASY, "answer": True},
    {"type": "mcq", "text": "Which built-in calls a parent class's method from a subclass?",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["parent()", "base()", "super()", "this.parent()"], "correct_index": 2},
    {"type": "mcq", "text": "What does the @property decorator do?",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["Marks a class immutable", "Turns a method into a read-only attribute",
                 "Registers a callback", "Defines an abstract method"], "correct_index": 1},
    {"type": "mcq", "text": "Which module provides ABC and @abstractmethod?",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["typing", "abc", "dataclasses", "enum"], "correct_index": 1},
    {"type": "tf", "text": "A class with an @abstractmethod can be instantiated directly.",
     "category": "PythonOOP", "difficulty": Difficulty.EASY, "answer": False},
    {"type": "mcq", "text": "What does prefixing an attribute with double underscores (e.g. __score) trigger?",
     "category": "PythonOOP", "difficulty": Difficulty.HARD,
     "options": ["Compile-time privacy", "Name mangling", "Memoization", "Thread safety"], "correct_index": 1},
    {"type": "mcq", "text": "Which dunder method customizes the printable string form (used by str())?",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["__repr__", "__str__", "__format__", "__print__"], "correct_index": 1},
    {"type": "tf", "text": "Python supports multiple inheritance using method resolution order (MRO).",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM, "answer": True},
    {"type": "mcq", "text": "Which algorithm resolves method order in multiple inheritance?",
     "category": "PythonOOP", "difficulty": Difficulty.HARD,
     "options": ["DFS", "C3 linearization", "BFS", "Round Robin"], "correct_index": 1},
    {"type": "mcq", "text": "Which decorator auto-generates __init__, __repr__, __eq__?",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["@staticmethod", "@classmethod", "@dataclass", "@property"], "correct_index": 2},
    {"type": "mcq", "text": "Which OOP concept lets the same method behave differently across subclasses?",
     "category": "PythonOOP", "difficulty": Difficulty.EASY,
     "options": ["Encapsulation", "Polymorphism", "Abstraction", "Composition"], "correct_index": 1},
    {"type": "mcq", "text": "Encapsulation is BEST described as:",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["Hiding internal state and exposing controlled access",
                 "Inheriting from many classes", "Using lambdas everywhere", "Mutating globals"],
     "correct_index": 0},
    {"type": "tf", "text": "Abstraction means exposing only essential features and hiding implementation.",
     "category": "PythonOOP", "difficulty": Difficulty.EASY, "answer": True},
    {"type": "mcq", "text": "Which design pattern centralizes object creation behind a single method?",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["Observer", "Factory", "Decorator", "Adapter"], "correct_index": 1},
    {"type": "mcq", "text": "Which pattern lets you swap an algorithm at runtime?",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["Strategy", "Singleton", "Builder", "Memento"], "correct_index": 0},
    {"type": "mcq", "text": "Which pattern notifies many subscribers when state changes?",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM,
     "options": ["Visitor", "Observer", "Bridge", "Proxy"], "correct_index": 1},
    {"type": "mcq", "text": "Which pattern wraps an object to add behavior without changing its interface?",
     "category": "PythonOOP", "difficulty": Difficulty.HARD,
     "options": ["Decorator", "Facade", "Chain of Responsibility", "Mediator"], "correct_index": 0},
    {"type": "mcq", "text": "Which pattern defines an algorithm skeleton and defers steps to subclasses?",
     "category": "PythonOOP", "difficulty": Difficulty.HARD,
     "options": ["Template Method", "Iterator", "Command", "State"], "correct_index": 0},
    {"type": "tf", "text": "@classmethod receives the class itself as its first argument.",
     "category": "PythonOOP", "difficulty": Difficulty.MEDIUM, "answer": True},
]


# ============================================================
# DEMO — wire it all together when run as a script.
# ============================================================
def _demo() -> None:
    random.seed(42)  # make the run reproducible

    print("=" * 60)
    print("QuizGame demo — Python & OOP category")
    print("=" * 60)

    game = QuizGame(QUESTION_BANK, total_rounds=5, scoring_mode="standard")

    # Observer pattern: subscribe to events.
    game.on("player_joined", lambda p: print(f"  + {p.name} {p.avatar} joined"))
    game.on("round_started", lambda d: print(f"\n--- Round {d['round']} ---\nQ: {d['question'].text}"))
    game.on("answer_submitted",
            lambda d: print(f"  {d['player_id']}: {'OK' if d['result'].correct else 'X'} (+{d['result'].points})"))
    game.on("game_over", lambda d: None)  # we'll print leaderboard ourselves

    alice = game.add_player("Alice", "🦊")
    bob = game.add_player("Bob", "🐉")

    game.start_game(category="PythonOOP")

    # Play out the round pool. Alice picks index 1 every time, Bob picks 0.
    # (Both heuristics are silly on purpose — we just want a deterministic run.)
    while game.current_round is not None:
        question = game.current_round.question
        correct = question.get_correct_answer()
        options = question.get_options()
        print(f"   options: {options}")
        print(f"   correct: {correct}")

        game.submit_answer(alice.id, 1)
        game.submit_answer(bob.id, 0)
        game.end_round()
        game.next_round()

    print("\n" + "=" * 60)
    print("FINAL LEADERBOARD")
    print("=" * 60)
    leaderboard = sorted(game.players, key=lambda p: p.score, reverse=True)
    for rank, p in enumerate(leaderboard, 1):
        s = p.stats
        print(f"  {rank}. {p.avatar} {p.name:<10} score={p.score:<5} "
              f"correct={s['correct']}/{s['total']} acc={s['accuracy']}% best_streak={s['best_streak']}")


if __name__ == "__main__":
    _demo()
