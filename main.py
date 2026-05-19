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
    MyForm(title="My Form Example", logging_enabled=True, logging_debug=True).run()