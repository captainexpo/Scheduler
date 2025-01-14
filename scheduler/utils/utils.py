from enum import Enum

class PrintColor(Enum):
    NONE = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    
color_code = {
    PrintColor.NONE: "",
    PrintColor.RED: "\033[91m",
    PrintColor.GREEN: "\033[92m",
    PrintColor.YELLOW: "\033[93m",
    PrintColor.BLUE: "\033[94m",
    PrintColor.MAGENTA: "\033[95m",
    PrintColor.CYAN: "\033[96m"
}

def print_color(*args, color=PrintColor.NONE):
    print(color_code[color], end="")
    print(*args)
    print("\033[0m", end="")
    
    