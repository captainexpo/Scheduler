from scheduler.yesclass.YESClass import YESClass
from scheduler.student.YESStudent import YESStudent
from typing import List, Any
import random

class YESDataFaker:
    def __init__(self, class_names: List[str] = [], student_names: List[str] = []):
        self.classes: List[YESClass] = []
        self.students: List[YESStudent] = []
        
        self.class_names: List[str] = class_names
        self.student_names: List[str] = student_names
        
    def fake_class(self) -> YESClass:
        new_class = YESClass(self.class_names.pop(0))
        return new_class
    
    def fake_student(self, num_prefs: int = 5) -> YESStudent:
        name = random.choice(self.student_names)
        new_student = YESStudent(name, email=f"{name.lower()}@bsdvt.org", preferences=[random.choice(self.classes) for _ in range(num_prefs)])
        return new_student
    
    def fake_data(self, num_classes: int, num_students: int):
        for _ in range(num_classes):
            self.classes.append(self.fake_class())
        for _ in range(num_students):
            self.students.append(self.fake_student())
            