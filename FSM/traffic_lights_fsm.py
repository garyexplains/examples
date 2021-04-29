class myFSM:
    def __init__(self):
        self.handlers = {}

    def add_state(self, name, handler):
        self.handlers[name] = handler

    def run(self, startingState, cargo):
        handler = self.handlers[startingState]
        while True:
            (newState, cargo) = handler(cargo)
            if newState == "END":
                print("END reached")
                break
            handler = self.handlers[newState]

def state_start_handler(cargo):
    return ("RED", cargo)

def state_red_handler(cargo):
    print("RED")
    return ("RED_AMBER", cargo)

def state_red_amber_handler(cargo):
    print("RED & AMBER")
    return ("GREEN", cargo)

def state_green_handler(cargo):
    print("GREEN")
    return ("AMBER", cargo)

def state_amber_handler(cargo):
    print("AMBER")
    cargo = cargo - 1
    if cargo > 0:
        return ("RED", cargo)
    else:
        return ("END", cargo)

fsm = myFSM()
fsm.add_state("START", state_start_handler)

fsm.add_state("RED", state_red_handler)
fsm.add_state("RED_AMBER", state_red_amber_handler)
fsm.add_state("GREEN", state_green_handler)
fsm.add_state("AMBER", state_amber_handler)

fsm.run("START", 3)