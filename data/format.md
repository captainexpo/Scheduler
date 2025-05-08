# Data Format

## Classes
```python
Name: str, 
Teacher: str, 
Capacity: int, 
Type: "Morning"|"Afternoon"|"Full"
```

## Students
```python
First Name: str, 
Last Name: str, 
Grade: int, 
Pref Class Type: "Half"|"Full", 
CTE / BTC: "Morning"|"Afternoon"|"None", 
Morning Pref 1: str|"",
... 
Morning Pref 5: str|"", 
Afternoon Pref 1: str|"",
... 
Afternoon Pref 5: str|"", 
Full Pref 1: str|"",
... 
Full Pref 5: str|"",
```

A pref will be empty only when it doesn't apply to the student. E.G when they have BTC or CTE on that time.