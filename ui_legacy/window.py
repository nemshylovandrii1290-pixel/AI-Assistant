import tkinter as tk


def open_window(service):
    root = tk.Tk()
    root.title("AI Assistant")
    root.geometry("360x220")
    root.resizable(False, False)

    title = tk.Label(root, text="AI Assistant", font=("Segoe UI", 16, "bold"))
    title.pack(pady=(18, 8))

    status_var = tk.StringVar()
    message_var = tk.StringVar()

    def refresh_status():
        snapshot = service.snapshot()
        status_var.set(f"Статус: {snapshot['status']}")
        message_var.set(snapshot["message"] or "Працює у tray")
        root.after(900, refresh_status)

    def toggle_service():
        if service.is_running():
            service.stop()
        else:
            service.start()

    status_label = tk.Label(root, textvariable=status_var, font=("Segoe UI", 11, "bold"))
    status_label.pack(pady=(6, 8))

    message_label = tk.Label(
        root,
        textvariable=message_var,
        justify="center",
        wraplength=290,
        font=("Segoe UI", 10),
    )
    message_label.pack(padx=24, pady=8)

    actions = tk.Frame(root)
    actions.pack(pady=(12, 0))

    toggle_button = tk.Button(actions, text="Старт / Стоп", command=toggle_service, width=14)
    toggle_button.grid(row=0, column=0, padx=6)

    close_button = tk.Button(actions, text="Закрити", command=root.destroy, width=14)
    close_button.grid(row=0, column=1, padx=6)

    refresh_status()
    root.mainloop()
