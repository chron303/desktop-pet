"""
behavior.py — Personality-driven state machine.

Personality now directly changes transition weights:
  playful  — more tricks, less sleep, more curious
  lazy     — more sleep, less walking, very little curious
  curious  — lots of curious state, moderate everything
  loyal    — follows cursor more readily, steady states
  hyper    — constant movement, almost never sleeps, high trick rate
"""

import random, time
from enum import Enum, auto

class State(Enum):
    IDLE    = auto()
    WALK    = auto()
    SLEEP   = auto()
    CURIOUS = auto()
    TRICK   = auto()
    FOLLOW  = auto()

# Base transition weights — (State, weight)
_BASE_IDLE = [(State.IDLE,60),(State.WALK,25),(State.SLEEP,10),(State.CURIOUS,5)]
_BASE_WALK = [(State.WALK,50),(State.IDLE,38),(State.CURIOUS,8),(State.SLEEP,4)]

# Personality multipliers applied to each state's weight
PERSONALITY_BIAS = {
    #              IDLE  WALK  SLEEP CURIOUS TRICK
    "playful": {State.IDLE:0.7, State.WALK:1.4, State.SLEEP:0.4,
                State.CURIOUS:1.6, State.TRICK:2.0},
    "lazy":    {State.IDLE:1.5, State.WALK:0.5, State.SLEEP:3.5,
                State.CURIOUS:0.4, State.TRICK:0.3},
    "curious": {State.IDLE:0.8, State.WALK:1.0, State.SLEEP:0.6,
                State.CURIOUS:3.0, State.TRICK:0.8},
    "loyal":   {State.IDLE:1.0, State.WALK:1.0, State.SLEEP:0.8,
                State.CURIOUS:1.2, State.TRICK:1.0},
    "hyper":   {State.IDLE:0.3, State.WALK:2.5, State.SLEEP:0.1,
                State.CURIOUS:1.8, State.TRICK:3.5},
}

MIN_DURATION = {
    State.IDLE:2.5, State.WALK:3.5, State.SLEEP:10.0,
    State.CURIOUS:1.2, State.TRICK:0.0, State.FOLLOW:0.0,
}

# Personality also affects how quickly these timers expire
DURATION_MULT = {
    "playful":{"sleep":0.5,"idle":0.7},
    "lazy":   {"sleep":2.0,"idle":1.5,"walk":0.7},
    "curious":{"curious":2.0,"idle":0.8},
    "loyal":  {},
    "hyper":  {"sleep":0.1,"idle":0.4,"walk":1.8},
}


def _weighted(choices):
    states, weights = zip(*choices)
    return random.choices(states, weights=weights)[0]


def _apply_personality(transitions, personality):
    bias = PERSONALITY_BIAS.get(personality, {})
    if not bias:
        return transitions
    new = []
    for state, weight in transitions:
        multiplier = bias.get(state, 1.0)
        new.append((state, max(0.5, weight * multiplier)))
    return new


class BehaviorMachine:
    CURSOR_NEAR_PX = 110
    SLEEP_TICKS    = 25

    def __init__(self, personality: str = "playful"):
        self.state          = State.IDLE
        self.follow_mode    = False
        self.current_trick  = None
        self.move_dir       = random.choice(["left","right"])
        self._last_change   = time.monotonic()
        self._idle_count    = 0
        self._queued_trick  = None
        self.personality    = personality

    def set_personality(self, personality: str):
        """Update personality — affects future transitions immediately."""
        self.personality = personality

    def on_left_click(self):
        self._queued_trick = random.choice([
            "jump","spin","dance","wiggle","backflip","leg_shake",
            "sneeze","hiccup","dizzy","moonwalk","roll_over"
        ])

    def on_right_click(self):
        self.follow_mode = not self.follow_mode
        if self.follow_mode: self._set(State.FOLLOW)
        else:                self._set(State.IDLE)

    def update(self, cursor_pos: tuple, pet_center: tuple) -> State:
        # Queued trick fires immediately
        if self._queued_trick:
            self.current_trick  = self._queued_trick
            self._queued_trick  = None
            return self._set(State.TRICK)

        if self.state == State.TRICK:
            return self.state

        if self.follow_mode:
            return self._set(State.FOLLOW)

        # Min duration guard (personality-adjusted)
        elapsed  = time.monotonic() - self._last_change
        dur_mult = DURATION_MULT.get(self.personality, {})
        state_key = self.state.name.lower()
        adjusted_min = MIN_DURATION[self.state] * dur_mult.get(state_key, 1.0)

        if elapsed < adjusted_min:
            return self.state

        # Cursor proximity → CURIOUS
        if self._near(cursor_pos, pet_center):
            return self._set(State.CURIOUS)

        # Long idle → sleep (personality-gated)
        if self.state == State.IDLE:
            self._idle_count += 1
            # Hyper almost never sleeps naturally, lazy sleeps very fast
            sleep_ticks = {
                "playful": 20, "lazy": 8, "curious": 22,
                "loyal": 18, "hyper": 60,
            }.get(self.personality, self.SLEEP_TICKS)
            if self._idle_count >= sleep_ticks:
                self._idle_count = 0
                return self._set(State.SLEEP)
            # Hyper personality occasionally self-triggers tricks from idle
            if self.personality == "hyper" and random.random() < 0.05:
                self.current_trick = random.choice(["spin","jump","wiggle"])
                return self._set(State.TRICK)

            trans = _apply_personality(_BASE_IDLE, self.personality)
            return self._set(_weighted(trans))

        elif self.state == State.WALK:
            self._idle_count = 0
            trans = _apply_personality(_BASE_WALK, self.personality)
            new = _weighted(trans)
            if new == State.WALK and random.random() < 0.2:
                self._flip()
            return self._set(new)

        elif self.state == State.SLEEP:
            # Wake probability scales with personality
            wake_p = {"playful":0.06,"lazy":0.015,"curious":0.05,
                      "loyal":0.04,"hyper":0.15}.get(self.personality, 0.04)
            if random.random() < wake_p:
                self._idle_count = 0
                return self._set(State.IDLE)

        elif self.state == State.CURIOUS:
            if not self._near(cursor_pos, pet_center):
                return self._set(State.IDLE)

        return self.state

    def finish_trick(self):
        self.current_trick = None
        self._set(State.IDLE)

    def _set(self, state: State) -> State:
        if state != self.state:
            self.state       = state
            self._last_change = time.monotonic()
        return self.state

    def _flip(self):
        self.move_dir = "right" if self.move_dir == "left" else "left"

    def _near(self, cursor, center) -> bool:
        return (abs(cursor[0]-center[0]) < self.CURSOR_NEAR_PX and
                abs(cursor[1]-center[1]) < self.CURSOR_NEAR_PX)