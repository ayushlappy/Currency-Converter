import sqlite3
from tkinter import messagebox, Tk, StringVar, Toplevel, BOTH, W, END
from tkinter import ttk
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

API_URL = "https://v6.exchangerate-api.com/v6/f6e5adbe1daaf6fade2a5b1c/latest/"

# Database Setup
def setup_database():
    conn = sqlite3.connect("currency_converter.db")
    cursor = conn.cursor()
    
    # Create history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            base TEXT,
            target TEXT,
            amount REAL,
            rate REAL,
            result REAL,
            user_id INTEGER
        )
    ''')
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Save user credentials to the database
def save_user(username, password):
    conn = sqlite3.connect("currency_converter.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password) VALUES (?, ?)
        ''', (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")
        return False
    finally:
        conn.close()

# Validate user credentials
def validate_user(username, password):
    conn = sqlite3.connect("currency_converter.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM users WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Login Window
def open_login_window():
    login_window = Toplevel(root)
    login_window.title("Login")
    login_window.geometry("300x200")
    login_window.configure(bg="#e6f7ff")

    ttk.Label(login_window, text="Username:", style="Custom.TLabel").pack(pady=10)
    username_entry = ttk.Entry(login_window, font=("Helvetica", 12), width=20)
    username_entry.pack(pady=5)

    ttk.Label(login_window, text="Password:", style="Custom.TLabel").pack(pady=10)
    password_entry = ttk.Entry(login_window, font=("Helvetica", 12), width=20, show="*")
    password_entry.pack(pady=5)

    def login():
        username = username_entry.get()
        password = password_entry.get()
        user = validate_user(username, password)
        if user:
            global current_user_id
            current_user_id = user[0]
            messagebox.showinfo("Success", "Login successful!")
            login_window.destroy()
            show_currency_converter()  # Show the currency converter page after login
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    # Add text to the Login button
    ttk.Button(login_window, text="Login", command=login, style="Custom.TButton").pack(pady=20)

# Signup Window
def open_signup_window():
    signup_window = Toplevel(root)
    signup_window.title("Signup")
    signup_window.geometry("300x200")
    signup_window.configure(bg="#e6f7ff")

    ttk.Label(signup_window, text="Username:", style="Custom.TLabel").pack(pady=10)
    username_entry = ttk.Entry(signup_window, font=("Helvetica", 12), width=20)
    username_entry.pack(pady=5)

    ttk.Label(signup_window, text="Password:", style="Custom.TLabel").pack(pady=10)
    password_entry = ttk.Entry(signup_window, font=("Helvetica", 12), width=20, show="*")
    password_entry.pack(pady=5)

    def signup():
        username = username_entry.get()
        password = password_entry.get()
        if username and password:
            if save_user(username, password):
                messagebox.showinfo("Success", "Signup successful! Please login.")
                signup_window.destroy()
        else:
            messagebox.showerror("Error", "Please enter both username and password.")

    # Add text to the Signup button
    ttk.Button(signup_window, text="Signup", command=signup, style="Custom.TButton").pack(pady=20)

# Show Currency Converter Page
def show_currency_converter():
    # Hide the login/signup buttons
    login_button.pack_forget()
    signup_button.pack_forget()

    # Show the currency converter widgets
    frame.pack(fill=BOTH, expand=True)

# Save conversion history to the database
def save_to_database(conversion):
    conn = sqlite3.connect("currency_converter.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (time, base, target, amount, rate, result, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (conversion["time"], conversion["base"], conversion["target"], conversion["amount"], conversion["rate"], conversion["result"], current_user_id))
    conn.commit()
    conn.close()

# Fetch Currencies from API
def fetch_currencies():
    try:
        response = requests.get(API_URL + "USD")
        response.raise_for_status()
        data = response.json()
        if "conversion_rates" in data:
            return sorted(data["conversion_rates"].keys())  # Sort for better readability
        else:
            messagebox.showerror("API Error", "Conversion rates not found in API response.")
            return []
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch currencies: {e}")
        return ["USD", "EUR", "INR", "GBP", "JPY", "CAD", "AUD"]  # Fallback list

# Currency Conversion
def convert_currency():
    if not current_user_id:
        messagebox.showerror("Error", "Please login first.")
        return

    base_currency = base_currency_var.get()
    target_currency = target_currency_var.get()
    amount = amount_var.get()

    if base_currency == "Select Currency" or target_currency == "Select Currency":
        messagebox.showerror("Input Error", "Please select both currencies.")
        return

    if not amount:
        messagebox.showerror("Input Error", "Please enter an amount.")
        return

    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror("Input Error", "Amount must be a valid number.")
        return

    try:
        response = requests.get(API_URL + base_currency)
        response.raise_for_status()
        data = response.json()

        rate = data["conversion_rates"].get(target_currency)
        if rate:
            result = amount * rate
            result_var.set(f"{result:.2f} {target_currency}")

            # Save to database
            conversion = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "base": base_currency,
                "target": target_currency,
                "amount": amount,
                "rate": rate,
                "result": result,
            }
            save_to_database(conversion)
        else:
            messagebox.showerror("Error", f"Exchange rate for {target_currency} not available.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch exchange rates: {e}")

# Clear Input Fields
def clear_fields():
    base_currency_var.set("Select Currency")
    target_currency_var.set("Select Currency")
    amount_var.set("")
    result_var.set("")

# Visualize Exchange Rates (Line Chart)
def visualize_rates():
    base_currency = base_currency_var.get()

    if base_currency == "Select Currency":
        messagebox.showerror("Input Error", "Please select a base currency.")
        return

    try:
        response = requests.get(API_URL + base_currency)
        response.raise_for_status()
        data = response.json()

        rates = data["conversion_rates"]
        target_currencies = list(rates.keys())[:10]  # Top 10 currencies
        target_rates = [rates[currency] for currency in target_currencies]

        # Create a new window for visualization
        chart_window = Toplevel(root)
        chart_window.title(f"Exchange Rates for {base_currency}")
        chart_window.geometry("800x600")

        # Create the line chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(target_currencies, target_rates, marker='o', color='skyblue', label='Exchange Rate')

        # Title and labels
        ax.set_title(f"Exchange Rates for {base_currency} (Top 10 Currencies)", fontsize=14)
        ax.set_xlabel("Currencies", fontsize=12)
        ax.set_ylabel("Exchange Rate", fontsize=12)

        # Display grid and show the chart
        ax.grid(True)
        ax.legend()

        # Rotate the x-axis labels for better visibility
        plt.xticks(rotation=45)

        # Embed the matplotlib figure into the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch exchange rates: {e}")

# Show Conversion History
def show_history():
    if not current_user_id:
        messagebox.showerror("Error", "Please login first.")
        return

    conn = sqlite3.connect("currency_converter.db")
    cursor = conn.cursor()
    cursor.execute("SELECT time, base, target, amount, rate, result FROM history WHERE user_id = ? ORDER BY id DESC", (current_user_id,))
    records = cursor.fetchall()
    conn.close()

    history_window = Toplevel(root)
    history_window.title("Conversion History")
    history_window.geometry("800x500")

    tree = ttk.Treeview(history_window, columns=("time", "base", "target", "amount", "rate", "result"), show="headings")
    tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

    for col in ["time", "base", "target", "amount", "rate", "result"]:
        tree.heading(col, text=col.capitalize(), anchor=W)
        tree.column(col, width=120, anchor=W)

    for record in records:
        tree.insert("", END, values=record)

# Main Application
root = Tk()
root.title("Currency Converter & Visualization")
root.geometry("500x400")
root.configure(bg="#e6f7ff")

# Global variable to store the current user's ID
current_user_id = None

# Fetch currencies
currencies = fetch_currencies()
currencies.insert(0, "Select Currency")  # Add "Select Currency" as the first option

# Variables
base_currency_var = StringVar(value="Select Currency")
target_currency_var = StringVar(value="Select Currency")
amount_var = StringVar()
result_var = StringVar()

# Layout
frame = ttk.Frame(root, padding=20, style="Custom.TFrame")
frame.pack(fill=BOTH, expand=True)

style = ttk.Style()
style.configure("Custom.TFrame", background="#e6f7ff")
style.configure("Custom.TLabel", background="#e6f7ff", font=("Helvetica", 12))
style.configure("Custom.TButton", font=("Helvetica", 10, "bold"))

# Widgets
ttk.Label(frame, text="Base Currency:", style="Custom.TLabel").grid(row=0, column=0, padx=10, pady=10, sticky=W)
base_currency_menu = ttk.Combobox(frame, textvariable=base_currency_var, values=currencies, state="readonly", width=20)
base_currency_menu.grid(row=0, column=1, padx=10, pady=10)

ttk.Label(frame, text="Target Currency:", style="Custom.TLabel").grid(row=1, column=0, padx=10, pady=10, sticky=W)
target_currency_menu = ttk.Combobox(frame, textvariable=target_currency_var, values=currencies, state="readonly", width=20)
target_currency_menu.grid(row=1, column=1, padx=10, pady=10)

ttk.Label(frame, text="Amount:", style="Custom.TLabel").grid(row=2, column=0, padx=10, pady=10, sticky=W)
amount_entry = ttk.Entry(frame, textvariable=amount_var, font=("Helvetica", 12), width=22)
amount_entry.grid(row=2, column=1, padx=10, pady=10)

ttk.Label(frame, text="Result:", style="Custom.TLabel").grid(row=3, column=0, padx=10, pady=10, sticky=W)
ttk.Label(frame, textvariable=result_var, font=("Helvetica", 14, "bold"), foreground="blue", background="#e6f7ff").grid(row=3, column=1, padx=10, pady=10)

ttk.Button(frame, text="Convert", command=convert_currency, style="Custom.TButton").grid(row=4, column=0, pady=20, padx=10)
ttk.Button(frame, text="Clear", command=clear_fields, style="Custom.TButton").grid(row=4, column=1, pady=20, padx=10)
ttk.Button(frame, text="Visualize Rates", command=visualize_rates, style="Custom.TButton").grid(row=5, column=0, pady=20, padx=10)
ttk.Button(frame, text="View History", command=show_history, style="Custom.TButton").grid(row=5, column=1, pady=20, padx=10)

# Initially hide the currency converter frame
frame.pack_forget()

# Add Login and Signup Buttons
login_button = ttk.Button(root, text="Login", command=open_login_window, style="Custom.TButton")
login_button.pack(pady=20)

signup_button = ttk.Button(root, text="Signup", command=open_signup_window, style="Custom.TButton")
signup_button.pack(pady=20)

setup_database()
root.mainloop()