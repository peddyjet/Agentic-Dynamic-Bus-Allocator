class ReprimandableError(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"[REPRIMAND] {self.message}. This is your final warning."

class FatalError(Exception):
    def __init__(self, message: str, conclusion : str):
        self.message = message
        self.conclusion = conclusion

    def __str__(self):
        return (f"The model was unable to resolve a reprimand, and therefore the program has been terminated to avoid "
                f"trail-and-error. The model gave the following conclusion why this happened: {self.conclusion}. "
                f"Error Message: {self.message}")