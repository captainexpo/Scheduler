from scheduler.yesclass.YESClass import YESClass
from scheduler.student.YESStudent import YESStudent
from typing import List, Any

class YESScheduler:
    def __init__(self, classes: List[YESClass] = [], students: List[YESStudent] = []):
        self.classes: List[YESClass] = classes
        self.students: List[YESStudent] = students
        
    def add_class(self, new_class: YESClass):
        self.classes.append(new_class)
        
    def add_student(self, new_student: YESStudent):
        self.students.append(new_student)
        
    def remove_class(self, old_class: YESClass):
        self.classes.remove(old_class)
        
    def remove_student(self, old_student: YESStudent):
        self.students.remove(old_student)
        
    def assign_students(self):
        raise NotImplementedError("Assign_students not yet implemented")
    
    def __str__(self):
        out = "Scheduler(\n\tClasses: {\n"
        for c in self.classes:
            out += f"\t\t{c},\n"
        out += "\t},\n\tStudents: {\n"
        for s in self.students:
            out += f"\t\t{s},\n"
        out += "\t}\n)"
        out += ")"
        return out
        