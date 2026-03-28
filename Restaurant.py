import json
import os
import sys

# Constants for file storage
RESERVATIONS_FILE = "reservations.json"

# Constants for User storage
USERS_FILE = "users.json"

# Call load and save json file
def load_json(path):
    if not os.path.exists(path):
        return{}
    try:
        with open (path,"r") as f:
            return json.load(f)
    except:
        return{}
    

def save_json(path, data):
    """Saves user data to a JSON file (handles Customer objects)."""

    clean_data = {}

    # Loop through each user in the dictionary
    for key, value in data.items():

        # If the value is a Customer object, convert it to a dictionary
        if isinstance(value, Customer):
            clean_data[key] = {
                "email": value.email,
                "fname": value.fname,
                "lname": value.lname,
                "dob": value.dob,
                "password": value.password
            }

        # Otherwise just store the value as-is
        else:
            clean_data[key] = value

    # Open the file in write mode and save the cleaned data as JSON
    with open(path, "w") as f:
        json.dump(clean_data, f, indent=4)


# --- 1. Custom Exceptions ---
class MissingInformationError(Exception):
    """Exception raised when a required form field is left blank."""
    def __init__(self, field_name):
        self.message = f"Error: The '{field_name}' field cannot be empty."
        super().__init__(self.message)


# --- 2. Data Classes ---
class Customer:
    """Stores customer account details."""
    def __init__(self, email, fname, lname, dob, pwd):
        self.email = email
        self.fname = fname
        self.lname = lname
        self.dob = dob
        self.password = pwd # In production, hash this!

    def check_password(self, input_pwd):
        """Verifies given password against stored password."""
        return self.password == input_pwd

    def __str__(self):
        return f"Customer: {self.fname} {self.lname} ({self.email})"


class Reservation:
    """Stores reservation details."""
    def __init__(self, email, num_days, from_date, to_date, num_persons, num_rooms):
        self.email = email
        self.num_days = int(num_days)  # Convert to int
        self.from_date = from_date
        self.to_date = to_date
        self.num_persons = int(num_persons)  # Convert to int
        self.num_rooms = int(num_rooms)      # Convert to int

    def to_dict(self):
        """Converts object details to dictionary for JSON storage."""
        return self.__dict__


# --- 3. Helper Functions ---
def get_int_input(prompt):
    """Ensures user enters a valid integer."""
    while True:
        try:
            value = input(prompt).strip()
            if not value:
                raise MissingInformationError(prompt.split(':')[0].strip())
            return int(value)
        except ValueError:
            print("Invalid input! Please enter a whole number.")
        except MissingInformationError as e:
            print(e.message)


# --- 4. File Persistence Logic ---
def load_all_reservations():
    """Loads all reservations from the JSON file."""
    if not os.path.exists(RESERVATIONS_FILE):
        return {}
    try:
        with open(RESERVATIONS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle empty or corrupted file by returning empty dict
        return {}


def save_all_reservations(all_res_dict):
    """Saves the entire reservation dictionary to the JSON file."""
    try:
        with open(RESERVATIONS_FILE, "w") as f:
            json.dump(all_res_dict, f, indent=4)
    except IOError as e:
        print(f"Error saving reservation file: {e}")


# Database for customer objects: {email: CustomerObject}
raw_users = load_json(USERS_FILE)

user_db = {}

for email, data in raw_users.items():
    user_db[email] = Customer(
        data["email"],
        data["fname"],
        data["lname"],
        data["dob"],
        data["password"]
    )


# --- 5. Application Functionality ---
def signup_page():
    """Handles new customer registration with custom exception."""
    print("\n--- Reservation System: Sign Up ---")
    
    fields = ["email", "first name", "last name", "date of birth", "password"]
    user_data = {}

    try:
        for field in fields:
            value = input(f"Enter {field}: ").strip()
            
            # Use custom exception for missing fields
            if not value:
                raise MissingInformationError(field)
            
            # Normalize email for case-insensitivity
            if field == "email":
                value = value.lower()
            
            user_data[field] = value
        
        # Check if email already exists
        if user_data["email"] in user_db:
            print("\nThe password or username you've entered is incorrect")
            return None

        new_customer = Customer(
            user_data["email"], 
            user_data["first name"], 
            user_data["last name"], 
            user_data["date of birth"], 
            user_data["password"]
        )
        
        # Store user data to json file
        user_db[new_customer.email] = new_customer
        save_json(USERS_FILE, user_db)

        print(f"\nAccount created successfully for {new_customer.fname}!")
        return new_customer

    except MissingInformationError as e:
        print(f"\n{e.message}")
        return None


def login_page():
    """Handles customer login."""
    print("\n--- Login to Reservation System ---")
    email = input("Email: ").strip().lower() # Case-insensitive
    password = input("Password: ").strip()

    # 1. Check user exists
    if email in user_db:
        user = user_db[email]
        # 2. Verify password
        if user.check_password(password):
            print(f"\nWelcome back, {user.fname}!")
            return user
        else:
            print("\nError: Incorrect password.")
    else:
        print("\nError: No account found with that email.")
    
    return None


def make_reservation(user_email):
    """Collects details and makes a new reservation, saving to file."""
    print("\n--- Create New Reservation ---")
    
    # Check if user already has a reservation (overwriting warning is implicitly handled by dict behavior)
    # all_reservations = load_all_reservations()
    # if user_email in all_reservations:
    #     print("Note: You already have a reservation. This will replace it.")

    try:
        from_date = input("From Date (DD/MM/YYYY): ").strip()
        if not from_date: raise MissingInformationError("From Date")
        
        to_date = input("To Date (DD/MM/YYYY): ").strip()
        if not to_date: raise MissingInformationError("To Date")
        
        # Using helper for numeric inputs
        num_days = get_int_input("Number of days: ")
        num_persons = get_int_input("Number of Persons: ")
        num_rooms = get_int_input("Number of rooms: ")

        confirm = input("\nEnter 'R' to Reserve or 'C' to Cancel: ").upper()
        
        if confirm == 'R':
            # Load existing data, key by email, and save
            all_reservations = load_all_reservations()
            
            # Create Reservation object to validate and standardize data types
            res_obj = Reservation(user_email, num_days, from_date, to_date, num_persons, num_rooms)
            
            all_reservations[user_email] = res_obj.to_dict()
            save_all_reservations(all_reservations)
            
            print("\nSuccess! Your reservation has been saved.")
        else:
            print("\nReservation cancelled.")

    except MissingInformationError as e:
        print(f"\n{e.message}")
    except Exception as e:
        print(f"\nAn error occurred making the reservation: {e}")


def modify_reservation(user_email):
    """Displays existing reservation, allows editing, and updates file."""
    # Load latest data
    all_res = load_all_reservations()

    # 1. Check reservation exists for user
    if user_email not in all_res:
        print("\nNo current reservation found for this account.")
        return

    res_data = all_res[user_email]
    print(f"\n--- Current Reservation for {user_email} ---")
    print(f"1. From Date: {res_data['from_date']}")
    print(f"2. To Date: {res_data['to_date']}")
    print(f"3. Number of Days: {res_data['num_days']}")
    print(f"4. Number of Persons: {res_data['num_persons']}")
    print(f"5. Number of Rooms: {res_data['num_rooms']}")
    
    choice = input("\nEnter the number of the field to edit (or 'Q' to quit): ")

    try:
        if choice == '1':
            res_data['from_date'] = input("Enter new From Date: ")
            if not res_data['from_date']: raise MissingInformationError("From Date")
        elif choice == '2':
            res_data['to_date'] = input("Enter new To Date: ")
            if not res_data['to_date']: raise MissingInformationError("To Date")
        elif choice == '3':
            res_data['num_days'] = get_int_input("Enter new Number of Days: ")
        elif choice == '4':
            res_data['num_persons'] = get_int_input("Enter new Number of Persons: ")
        elif choice == '5':
            res_data['num_rooms'] = get_int_input("Enter new Number of Rooms: ")
        elif choice.upper() == 'Q':
            print("Modification exited.")
            return
        else:
            print("Invalid option.")
            return

        # Update dictionary and save back to file
        all_res[user_email] = res_data
        save_all_reservations(all_res)
        print("\nReservation updated successfully!")

    except MissingInformationError as e:
        print(f"\n{e.message}")
    except Exception as e:
        print(f"\nError updating reservation: {e}")


def cancel_reservation(user_email):
    """Deletes user's reservation from file after confirmation."""
    all_res = load_all_reservations()

    if user_email not in all_res:
        print("\nNo reservation found to cancel.")
        return

    print("\n--- Cancel Reservation ---")
    print(f"Warning: This will delete the reservation for {user_email}.")
    confirm = input("Are you absolutely sure? (Y/N): ").upper()

    if confirm == 'Y':
        del all_res[user_email] # Remove entry
        save_all_reservations(all_res) # Overwrite file
        print("\nReservation successfully deleted.")
    else:
        print("\nCancellation aborted.")


# --- 6. Main Application Logic & Menus ---
def logged_in_menu(user):
    """Customer Menu loop (Point-3) entered after successful login."""
    while True:
        print(f"\n=== CUSTOMER MENU: {user.fname.upper()} ===")
        print("1. Make Reservation")
        print("2. Modify Reservation")
        print("3. Cancel Reservation")
        print("4. Logout")
        
        choice = input("Select an option: ")

        if choice == "1":
            make_reservation(user.email)
        elif choice == "2":
            modify_reservation(user.email)
            # Returns to this menu loop (Point-3)
        elif choice == "3":
            cancel_reservation(user.email)
            # Returns to this menu loop (Point-3)
        elif choice == "4":
            print(f"\nLogging out... Goodbye, {user.fname}!")
            return # Exit function, returning to main menu loop
        else:
            print("Invalid selection. Please enter 1, 2, 3, or 4.")


def main():
    """Main Menu loop and ultimate exit point."""
    while True:
        print("\n=== RESERVATION SYSTEM MAIN MENU ===")
        print("1. Register/Sign Up")
        print("2. Login")
        print("3. Exit System")
        
        choice = input("Select an option: ")

        try:
            if choice == "1":
                new_user = signup_page()
                if new_user:
                    # Store user object in database
                    user_db[new_user.email] = new_user
            
            elif choice == "2":
                user = login_page()
                if user:
                    # Enter secondary menu loop (Point-3)
                    logged_in_menu(user)
                    # When logged_in_menu returns, execution continues here,
                    # automatically redisplaying the MAIN MENU due to the while True loop.
            
            elif choice == "3":
                # The ONLY exit point, with custom message
                print("\nThank you for using our Reservation System")
                break # Exit main loop, ending the program
            
            else:
                print("Invalid selection. Please choose 1, 2, or 3.")

        except Exception as e:
            # Global catch-all to prevent unhandled system crashes
            print(f"\nAn unexpected system error occurred: {e}")
            print("Returning to Main Menu...")

if __name__ == "__main__":
    # Ensure reservation file exists initially to avoid first-run load errors
    if not os.path.exists(RESERVATIONS_FILE):
        save_all_reservations({})
        
    main()
