from ...state import AgentState
from .enums import RoutesEnum

def route_next(state: AgentState) -> str:
    next_node = state.get('next', 'respond')

    if next_node not in RoutesEnum.VALID_ROUTES.value:
        return 'respond'

    return next_node