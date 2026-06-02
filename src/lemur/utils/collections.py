class VarTable:
    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def define(self, name, value):
        self.scopes[-1][name] = value # -1 is last item in the list, which is the current scope

    def get(self, name, default=None):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return default
    
    def to_dict(self):
        variables = {}
        for scope in self.scopes:
            variables.update(scope)
        return variables
    
    def __init__(self, variables: dict = None):
        if variables is None:
            variables = {}
            
        self.scopes = []   # initially empty list of scopes
        self.enter_scope() # start with a global scope
        
        for name, value in variables.items():
            self.define(name, value)