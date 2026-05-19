from simple_form import (
    Form, 
    TextField, 
    PasswordField,
    TextArea, 
    Button, 
    CheckBoxGroup, 
    CheckBox, 
    RadioGroup, 
    Radio, 
    Select,
    MultiSelect,
    NumberField,
    FilePath, 
    DirectoryPath,
    DatePicker,
    TimePicker,
    )
from simple_analysis import analyze_data
import pandas as pd
import logging
# make config
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@Form
class MyForm(Form):

    name_field = TextField(label="Name", default="John Doe")
    checkbox_field = CheckBox(label="Check me", default=True)
    checkbox_group = CheckBoxGroup(label="Options", options=[
        CheckBox(label="Option 1", default=True),
        CheckBox(label="Option 2"),
        CheckBox(label="Option 3"),
    ])
    radio_group = RadioGroup(label="Choose One", options=[
        Radio(label="Choice 1"),
        Radio(label="Choice 2", default=True),
        Radio(label="Choice 3"),
    ])
    password_field = PasswordField(label="Password")
    category_field = Select(label="Category", options=["Basic", "Pro", "Enterprise"], default="Pro")
    tags_field = MultiSelect(label="Tags", options=["UI", "Backend", "API", "Database", "DevOps"], default=["UI", "API"])
    amount_field = NumberField(label="Amount", default=10, min_value=0, max_value=100, step=0.5)
    path = FilePath(label="File Path", extensions={"excel files": ["*.xlsx", "*.xls"], "text files": ["*.txt"], "all files": ["*.*"]})
    directory = DirectoryPath(label="Directory")
    description_field = TextArea(label="Description")
    date_field = DatePicker(label="Date", default="18.05.2026", date_format="%d.%m.%Y")
    time_field = TimePicker(label="Time", time_format="%H:%M")
    submit_button = Button(label="Submit", on_click="submit1")

    def submit1(self):
        name = self.name_field.value
        description = self.description_field.value
        self.description_field.value = ""  # Clear the description field after submission
        print(f"Name: {name}")
        print(f"Description: {description}")
        print(f"Checkbox: {self.checkbox_field.value}")
        print(f"Radio Group: {self.radio_group.value}")
        print(f"Password: {self.password_field.value}")
        print(f"Category: {self.category_field.value}")
        print(f"Tags: {self.tags_field.value}")
        print(f"Amount: {self.amount_field.value}")
        print(f"File Path: {self.path.value}")
        print(f"Directory Path: {self.directory.value}")
        print(f"Date: {self.date_field.value}")
        print(f"Time: {self.time_field.value}")
        logging.info("Form submitted successfully.")
        logging.debug(f"Form data: Name={name}, Description={description}, Checkbox={self.checkbox_field.value}, Radio Group={self.radio_group.value}, Password={self.password_field.value}, Category={self.category_field.value}, Tags={self.tags_field.value}, Amount={self.amount_field.value}, File Path={self.path.value}, Directory Path={self.directory.value}, Date={self.date_field.value}, Time={self.time_field.value}")
        logging.warning("This is a warning message.")
        logging.error("This is an error message.")


if __name__ == "__main__":
    # MyForm(title="My Form Example", logging_enabled=True, logging_debug=True).run()
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy"],
        "Age": [25, 30, 35, 40, 28, 33, 29, 31, 27, 36],
        "City": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"],
        "Salary": [70000, 80000, 90000, 75000, 82000, 88000, 91000, 77000, 83000, 89000],
        "Department": ["HR", "IT", "Finance", "Marketing", "Sales", "Operations", "Legal", "R&D", "Customer Support", "Admin"],
        "Email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com", "eve@example.com", "frank@example.com", "grace@example.com", "heidi@example.com", "ivan@example.com", "judy@example.com"],
        "Phone": ["555-1001", None, "555-1003", "555-1004", "555-1005", "555-1006", "555-1007", "555-1008", "555-1009", "555-1010"],
        "Hire Date": ["2020-01-15", "2019-06-20", "2021-03-10", "2018-11-05", "2020-07-22", "2019-09-14", "2021-01-30", "2020-05-18", "2019-12-25", "2021-04-12"],
        "Performance": [4.5, 4.2, 4.8, 4.1, 4.3, 4.6, 4.7, 4.0, 4.4, 4.9],
        "Projects": [3, 5, 4, 6, 2, 5, 3, 4, 6, 2],
        "Status": ["Active", "Active", "Active", "Inactive", "Active", "Inactive", "Active", "Active", "Inactive", "Active"],
        "Experience": [5, 8, 3, 6, 4, 7, 5, 6, 4, 7],
        "Bonus": [5000, 7000, 8000, 6000, 7500, 8200, 8800, 7700, 8300, 8900],
        "Certifications": [2, 4, 3, 5, 3, 4, 2, 3, 4, 5],
        "Manager": ["John", "Sarah", "Mike", "Anna", "Tom", "Linda", "James", "Emily", "Robert", "Sophia"],
        "Office": ["NYC", "LA", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"],
        "Level": ["Senior", "Junior", "Mid", "Senior", "Junior", "Mid", "Senior", "Junior", "Mid", "Senior"],
        "Budget": [50000, 75000, 100000, 60000, 80000, 90000, 70000, 85000, 95000, 110000],
        "Team Size": [5, 8, 6, 7, 9, 5, 6, 8, 7, 10],
        "Availability": ["Full-time", "Full-time", "Contract", "Full-time", "Part-time", "Contract", "Full-time", "Full-time", "Part-time", "Contract"],
        "Remote": [True, False, True, False, True, False, True, False, True, False],
        "Last Review": ["2024-01-10", "2024-02-15", "2024-01-20", "2024-03-05", "2024-04-12", "2024-05-18", "2024-06-22", "2024-07-30", "2024-08-15", "2024-09-10"],
    })
    df = analyze_data(df, hide_index=True, rev_filter=["Status"])
    print(df)
    