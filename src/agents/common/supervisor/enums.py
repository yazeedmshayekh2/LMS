from enum import Enum

class RoutesEnum(Enum):
    VALID_ROUTES = {"assignment_maker", "quiz_generator", "summarizer", "respond"}

class ValidRoutesEnum(Enum):
    ASSIGNMENTMAKER = "assignment_maker"
    QUIZGENERATOR = "quiz_generator"
    SUMMARIZER = "summarizer"
    RESPOND = "respond"