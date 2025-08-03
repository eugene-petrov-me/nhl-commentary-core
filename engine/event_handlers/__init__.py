from .goal import interpret_goal
from .penalty import interpret_penalty
from .shot_on_goal import interpret_shot_on_goal

EVENT_HANDLERS = {
    "goal": interpret_goal,
    "penalty": interpret_penalty,
    "shot-on-goal": interpret_shot_on_goal,
}