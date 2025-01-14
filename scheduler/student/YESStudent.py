import scheduler.yesclass.YESClass as yc
from typing import List, Any, Tuple
from enum import Enum

class DayType(Enum):
    NO_PREF = 0
    HALF = 1
    FULL = 2
    NULL = 3
    

class YESStudent:
    def __init__(self, name="<NONAME>", email="<NOEMAIL>", grade=12, preferences = [], student_id: int = -1, day_pref: DayType = DayType.NO_PREF):
        self.name: str = name
        self.email: str = email
        self.grade: int = grade
        self.student_id: int = student_id
        
        self.preferences: List['yc.YESClass'] = sorted(
            list(
                set(
                    preferences
                )
            ),
            key=lambda x: x.name
        )
        
        self.selected_class: List['yc.YESClass']|'yc.YESClass' = None
        self.day_type: DayType = DayType.NULL
        self.day_pref: DayType = day_pref
        
    @property
    def is_assigned(self):
        if self.day_type == DayType.NULL:
            return False
        if self.day_type == DayType.FULL:
            return isinstance(self.selected_class, yc.YESClass)
        if self.day_type == DayType.HALF:
            return isinstance(self.selected_class, List) and all([isinstance(i, yc.YESClass) for i in self.selected_class])
        
    def add_preference(self, preference: 'yc.YESClass'):
        print(f"Adding preference {preference} to {self}")
        self.preferences.append(preference)
    
    def remove_preference(self, preference: 'yc.YESClass'):
        self.preferences.remove(preference)
        
    def set_selected_class(self, selected_class: 'yc.YESClass', day_type: DayType = DayType.FULL):
        if self.selected_class is not None:
            self.selected_class.remove_student(self)
        if day_type == DayType.FULL:
            self.selected_class = selected_class
            self.day_type = DayType.FULL
        elif day_type == DayType.HALF:
            if isinstance(self.selected_class, List):
                if len(self.selected_class) < 2:
                    self.selected_class.append(selected_class)
                else:
                    raise ValueError("Cannot add more than 2 half classes")
            else:
                self.selected_class = [selected_class]
            self.day_type = DayType.HALF
        else:
            raise ValueError("Invalid day type")
            
        self.selected_class.add_student(self)
        
    def __str__(self):
        return f"Student({self.name} <{self.email}> prefs=[{', '.join([i.short_str() for i in self.preferences])}] ass={self.is_assigned})"
        