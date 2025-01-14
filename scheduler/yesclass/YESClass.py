from typing import List, Any
from scheduler.utils.utils import *
import scheduler.student.YESStudent as ys

class YESClass:
    def __init__(self, name: str = "<NONAME>", capacity: int = 16, teacher: str = "<NOTEACHER>", daytype: 'ys.DayType' = ys.DayType.FULL):
        self.name: str = name
        self.capacity: int = capacity
        self.teacher: str = teacher
        self.students: List['ys.YESStudent'] = []
        self.daytype: 'ys.DayType' = daytype
        
    def add_student(self, student: 'ys.YESStudent'):
        self.students.append(student)
        if len(self.students) >= self.capacity:
            print_color(f"Warning: Class {self.name} is full!", PrintColor.YELLOW)
            
    def remove_student(self, student: 'ys.YESStudent'):
        self.students.remove(student)
        
    def __str__(self):
        return f"Class({self.name} <{self.teacher}> {len(self.students)}/{self.capacity})"
    def short_str(self):
        return f"Class({self.name} {len(self.students)}/{self.capacity})"
    def __repr__(self): return self.__str__()