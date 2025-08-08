from .goal import interpret_goal
from .penalty import interpret_penalty
from .shot_on_goal import interpret_shot_on_goal
from .hit import interpret_hit
from .faceoff import interpret_faceoff
from .blocked_shot import interpret_blocked_shot
from .missed_shot import interpret_missed_shot
from .giveaway import interpret_giveaway
from .takeaway import interpret_takeaway
from .delayed_penalty import interpret_delayed_penalty

EVENT_HANDLERS = {
    "goal": interpret_goal,
    "penalty": interpret_penalty,
    "shot-on-goal": interpret_shot_on_goal,
    "hit": interpret_hit,
    "faceoff": interpret_faceoff,
    "blocked-shot": interpret_blocked_shot,
    "missed-shot": interpret_missed_shot,
    "giveaway": interpret_giveaway,
    "takeaway": interpret_takeaway,
    "delayed-penalty": interpret_delayed_penalty,
}
