import tkinter as tk
from tkinter import messagebox
import sqlite3
import random
import string
import os
import re
import pyperclip

from cryptography.fernet import Fernet
from datetime import datetime

# ==========================================
# ENCRYPTION SETUP
# ==========================================

KEY_FILE = "secret.key"

def create_key():
    key = Fernet.generate_key()

    with open(KEY_FILE, "wb") as file:
        file.write(key)

if not os.path.exists(KEY_FILE):
    create_key()

with open(KEY_FILE, "rb") as file:
    key = file.read()

cipher = Fernet(key)

# ==========================================
# DATABASE SETUP
# ==========================================

conn = sqlite3.connect("password_manager.db")
cursor = conn.cursor()

# Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

# Passwords Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS passwords(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website TEXT,
    email TEXT,
    password BLOB,
    created_at TEXT
)
""")

conn.commit()

# ==========================================
# MAIN WINDOW
# ==========================================

root = tk.Tk()
root.title("Advanced Password Manager")
root.geometry("500x500")
root.config(bg="#1e1e1e")

# ==========================================
# PASSWORD STRENGTH CHECKER
# ==========================================

def check_strength(password):

    score = 0

    if len(password) >= 8:
        score += 1

    if re.search(r"[A-Z]", password):
        score += 1

    if re.search(r"[a-z]", password):
        score += 1

    if re.search(r"\d", password):
        score += 1

    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1

    if score <= 2:
        return "Weak"

    elif score <= 4:
        return "Medium"

    else:
        return "Strong"

# ==========================================
# REGISTER FUNCTION
# ==========================================

def register():

    username = username_entry.get()
    password = password_entry.get()

    if username == "" or password == "":
        messagebox.showerror(
            "Error",
            "All fields required"
        )
        return

    cursor.execute(
        "INSERT INTO users(username, password) VALUES (?, ?)",
        (username, password)
    )

    conn.commit()

    messagebox.showinfo(
        "Success",
        "Registration Successful"
    )

# ==========================================
# LOGIN FUNCTION
# ==========================================

def login():

    username = username_entry.get()
    password = password_entry.get()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()

    if user:
        messagebox.showinfo(
            "Success",
            "Login Successful"
        )

        open_password_manager()

    else:
        messagebox.showerror(
            "Error",
            "Invalid Credentials"
        )

# ==========================================
# PASSWORD MANAGER WINDOW
# ==========================================

def open_password_manager():

    manager = tk.Toplevel(root)

    manager.title("Password Manager")
    manager.geometry("500x650")
    manager.config(bg="#121212")

    # Website
    tk.Label(
        manager,
        text="Website",
        bg="#121212",
        fg="white",
        font=("Arial", 12)
    ).pack(pady=5)

    website_entry = tk.Entry(manager, width=40)
    website_entry.pack()

    # Email
    tk.Label(
        manager,
        text="Email",
        bg="#121212",
        fg="white",
        font=("Arial", 12)
    ).pack(pady=5)

    email_entry = tk.Entry(manager, width=40)
    email_entry.pack()

    # Password
    tk.Label(
        manager,
        text="Password",
        bg="#121212",
        fg="white",
        font=("Arial", 12)
    ).pack(pady=5)

    password_field = tk.Entry(
        manager,
        width=40,
        show="*"
    )

    password_field.pack()

    # Strength Label
    strength_label = tk.Label(
        manager,
        text="Strength: ",
        bg="#121212",
        fg="white"
    )

    strength_label.pack(pady=5)

    # ==========================================
    # GENERATE PASSWORD
    # ==========================================

    def generate_password():

        chars = (
            string.ascii_letters +
            string.digits +
            string.punctuation
        )

        password = ''.join(
            random.choice(chars)
            for _ in range(16)
        )

        password_field.delete(0, tk.END)
        password_field.insert(0, password)

        strength = check_strength(password)

        strength_label.config(
            text=f"Strength: {strength}"
        )

    # ==========================================
    # COPY PASSWORD
    # ==========================================

    def copy_password():

        password = password_field.get()

        pyperclip.copy(password)

        messagebox.showinfo(
            "Copied",
            "Password copied to clipboard"
        )

    # ==========================================
    # SAVE PASSWORD
    # ==========================================

    def save_password():

        website = website_entry.get()
        email = email_entry.get()
        password = password_field.get()

        if website == "" or email == "" or password == "":
            messagebox.showerror(
                "Error",
                "All fields required"
            )

            return

        encrypted_password = cipher.encrypt(
            password.encode()
        )

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute(
            """
            INSERT INTO passwords
            (website, email, password, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                website,
                email,
                encrypted_password,
                created_at
            )
        )

        conn.commit()

        messagebox.showinfo(
            "Saved",
            "Password Saved Successfully"
        )

    # ==========================================
    # VIEW PASSWORDS
    # ==========================================

    def view_passwords():

        view_window = tk.Toplevel(manager)

        view_window.title("Saved Passwords")
        view_window.geometry("600x400")
        view_window.config(bg="#1e1e1e")

        cursor.execute(
            "SELECT website, email, password, created_at FROM passwords"
        )

        records = cursor.fetchall()

        if not records:
            tk.Label(
                view_window,
                text="No passwords saved",
                bg="#1e1e1e",
                fg="white"
            ).pack(pady=20)

        for record in records:

            decrypted_password = cipher.decrypt(
                record[2]
            ).decode()

            text = f"""
Website: {record[0]}
Email: {record[1]}
Password: {decrypted_password}
Created At: {record[3]}
"""

            tk.Label(
                view_window,
                text=text,
                justify="left",
                bg="#1e1e1e",
                fg="white"
            ).pack(pady=10)

    # ==========================================
    # SHOW/HIDE PASSWORD
    # ==========================================

    show_password = tk.BooleanVar()

    def toggle_password():

        if show_password.get():
            password_field.config(show="")

        else:
            password_field.config(show="*")

    tk.Checkbutton(
        manager,
        text="Show Password",
        variable=show_password,
        command=toggle_password,
        bg="#121212",
        fg="white",
        selectcolor="#121212"
    ).pack()

    # ==========================================
    # BUTTONS
    # ==========================================

    tk.Button(
        manager,
        text="Generate Password",
        command=generate_password,
        bg="#333333",
        fg="white",
        width=20
    ).pack(pady=10)

    tk.Button(
        manager,
        text="Copy Password",
        command=copy_password,
        bg="#555555",
        fg="white",
        width=20
    ).pack(pady=10)

    tk.Button(
        manager,
        text="Save Password",
        command=save_password,
        bg="#444444",
        fg="white",
        width=20
    ).pack(pady=10)

    tk.Button(
        manager,
        text="View Passwords",
        command=view_passwords,
        bg="#666666",
        fg="white",
        width=20
    ).pack(pady=10)

# ==========================================
# LOGIN UI
# ==========================================

tk.Label(
    root,
    text="Advanced Password Manager",
    bg="#1e1e1e",
    fg="white",
    font=("Arial", 18, "bold")
).pack(pady=20)

tk.Label(
    root,
    text="Username",
    bg="#1e1e1e",
    fg="white"
).pack()

username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=5)

tk.Label(
    root,
    text="Password",
    bg="#1e1e1e",
    fg="white"
).pack()

password_entry = tk.Entry(
    root,
    show="*",
    width=30
)

password_entry.pack(pady=5)

tk.Button(
    root,
    text="Register",
    command=register,
    bg="#007acc",
    fg="white",
    width=20
).pack(pady=10)

tk.Button(
    root,
    text="Login",
    command=login,
    bg="#28a745",
    fg="white",
    width=20
).pack(pady=10)

# ==========================================
# RUN APPLICATION
# ==========================================

root.mainloop()

conn.close()