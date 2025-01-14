from scheduler.scheduler import YESScheduler
from scheduler.faker import YESDataFaker    
import sys
def main():
    all_names = open(sys.argv[1], "r").read().split("\n")
    faker = YESDataFaker(
        class_names=["Math", "Science", "History", "English", "Art", "PE", "Music", "French", "Spanish", "Latin"],
        student_names=all_names
    )
    
    faker.fake_data(10, 10)
    
    scheduler = YESScheduler(faker.classes, faker.students)
    
    print(scheduler)
    
if __name__ == "__main__":
    main() 