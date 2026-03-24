import tkinter as tk


def open_window():
    root = tk.Tk()
    root.title("AI Assistant")
    root.geometry("320x180")
    root.resizable(False, False)

    title = tk.Label(root, text="AI Assistant", font=("Segoe UI", 16, "bold"))
    title.pack(pady=(18, 8))

    status = tk.Label(
        root,
        text="Асистент працює у фоні через tray.\nТут можна буде додати налаштування.",
        justify="center",
        font=("Segoe UI", 10),
    )
    status.pack(padx=20, pady=8)

    close_button = tk.Button(root, text="Закрити", command=root.destroy, width=14)
    close_button.pack(pady=(12, 0))

    root.mainloop()
