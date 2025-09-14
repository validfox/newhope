import tkinter as tk
from tkinter import filedialog, ttk, font
import os


class FolderCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("R2D2: A Folder Compare Tool")

        # Default font settings
        self.default_ui_font = ("Arial", 10)
        self.default_text_font = ("Consolas", 11)

        # Fonts (shared)
        self.ui_font = font.Font(family=self.default_ui_font[0], size=self.default_ui_font[1])
        self.text_font = font.Font(family=self.default_text_font[0], size=self.default_text_font[1])

        # Paned layout
        self.paned = ttk.Panedwindow(root, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Top frame: folder selection + file lists
        self.top_frame = ttk.Frame(self.paned)
        self.paned.add(self.top_frame, weight=1)

        self.left_frame = ttk.Frame(self.top_frame, padding=5)
        self.right_frame = ttk.Frame(self.top_frame, padding=5)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Left side
        ttk.Label(self.left_frame, text="Left Folder", font=self.ui_font).pack(anchor="w")
        self.left_btn = ttk.Button(self.left_frame, text="Select Folder", command=lambda: self.load_folder("left"))
        self.left_btn.pack(anchor="w", pady=2)
        self.left_list = tk.Listbox(self.left_frame, font=self.text_font, selectmode="browse",
                                    selectbackground="lightblue")
        self.left_list.pack(fill=tk.BOTH, expand=True)
        self.left_list.bind("<<ListboxSelect>>", self.file_selected)

        # Right side
        ttk.Label(self.right_frame, text="Right Folder", font=self.ui_font).pack(anchor="w")
        self.right_btn = ttk.Button(self.right_frame, text="Select Folder", command=lambda: self.load_folder("right"))
        self.right_btn.pack(anchor="w", pady=2)
        self.right_list = tk.Listbox(self.right_frame, font=self.text_font, selectmode="browse",
                                     selectbackground="lightblue")
        self.right_list.pack(fill=tk.BOTH, expand=True)
        self.right_list.bind("<<ListboxSelect>>", self.file_selected)

        # Bottom frame: file contents comparison
        self.bottom_frame = ttk.Frame(self.paned)
        self.paned.add(self.bottom_frame, weight=2)

        # Horizontal scrollbar at top
        self.hscrollbar = tk.Scrollbar(self.bottom_frame, orient="horizontal", command=self.sync_xscroll)
        self.hscrollbar.pack(side=tk.TOP, fill="x")

        # Left content
        self.left_text_frame = ttk.Frame(self.bottom_frame)
        self.left_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_line_numbers = tk.Text(self.left_text_frame, width=5, padx=3, takefocus=0,
                                         border=0, background="#f0f0f0", state="disabled",
                                         font=self.text_font)
        self.left_line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.left_text = tk.Text(self.left_text_frame, wrap="none", undo=True, font=self.text_font,
                                 xscrollcommand=self.hscrollbar.set)
        self.left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right content
        self.right_text_frame = ttk.Frame(self.bottom_frame)
        self.right_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_line_numbers = tk.Text(self.right_text_frame, width=5, padx=3, takefocus=0,
                                          border=0, background="#f0f0f0", state="disabled",
                                          font=self.text_font)
        self.right_line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.right_text = tk.Text(self.right_text_frame, wrap="none", undo=True, font=self.text_font,
                                  xscrollcommand=self.hscrollbar.set)
        self.right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Shared vertical scrollbar
        self.vscrollbar = tk.Scrollbar(self.bottom_frame, orient="vertical", command=self.sync_scroll)
        self.vscrollbar.pack(side=tk.RIGHT, fill="y")

        self.left_text.config(yscrollcommand=self.vscrollbar.set)
        self.right_text.config(yscrollcommand=self.vscrollbar.set)

        # Mouse wheel bindings
        for widget in (self.left_text, self.right_text):
            widget.bind("<MouseWheel>", self.on_mousewheel)
            widget.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)
            widget.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)
            widget.bind("<Button-4>", self.on_mousewheel)
            widget.bind("<Button-5>", self.on_mousewheel)
            widget.bind("<Button-1>", self.on_click_line)  # NEW: click to highlight line

        # Bottom buttons
        self.button_frame = ttk.Frame(root, padding=5)
        self.button_frame.pack(fill="x")

        self.first_btn = ttk.Button(self.button_frame, text="First Diff", command=self.goto_first_diff)
        self.first_btn.pack(side=tk.LEFT, padx=5)
        self.prev_btn = ttk.Button(self.button_frame, text="Prev Diff", command=self.goto_prev_diff)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        self.next_btn = ttk.Button(self.button_frame, text="Next Diff", command=self.goto_next_diff)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        self.last_btn = ttk.Button(self.button_frame, text="Last Diff", command=self.goto_last_diff)
        self.last_btn.pack(side=tk.LEFT, padx=5)

        # Font control buttons
        self.ui_plus = ttk.Button(self.button_frame, text="UI Font +", command=lambda: self.change_font(self.ui_font, 1))
        self.ui_plus.pack(side=tk.LEFT, padx=5)
        self.ui_minus = ttk.Button(self.button_frame, text="UI Font -", command=lambda: self.change_font(self.ui_font, -1))
        self.ui_minus.pack(side=tk.LEFT, padx=5)
        self.txt_plus = ttk.Button(self.button_frame, text="Content Font +", command=lambda: self.change_content_font(1))
        self.txt_plus.pack(side=tk.LEFT, padx=5)
        self.txt_minus = ttk.Button(self.button_frame, text="Content Font -", command=lambda: self.change_content_font(-1))
        self.txt_minus.pack(side=tk.LEFT, padx=5)
        self.font_select = ttk.Button(self.button_frame, text="Choose Font", command=self.select_font_dialog)
        self.font_select.pack(side=tk.LEFT, padx=5)
        self.reset_font_btn = ttk.Button(self.button_frame, text="Reset Fonts", command=self.reset_fonts)
        self.reset_font_btn.pack(side=tk.LEFT, padx=5)

        # Status bar (two parts: left/right)
        self.status_frame = ttk.Frame(root, relief="sunken")
        self.status_frame.pack(fill="x", side=tk.BOTTOM)
        self.status_left = ttk.Label(self.status_frame, text="No differences", anchor="w", font=self.ui_font)
        self.status_left.pack(side="left", fill="x", expand=True)
        self.status_right = ttk.Label(self.status_frame, text="", anchor="e", font=self.ui_font)
        self.status_right.pack(side="right")

        # State
        self.left_folder = ""
        self.right_folder = ""
        self.left_file = ""
        self.right_file = ""
        self.diff_lines = []
        self.current_diff_index = -1

    # -------- Font handling --------
    def change_font(self, font_obj, delta):
        size = font_obj.cget("size") + delta
        if size < 6:
            size = 6
        font_obj.configure(size=size)

    def change_content_font(self, delta):
        self.change_font(self.text_font, delta)
        self.left_list.config(font=self.text_font)
        self.right_list.config(font=self.text_font)

    def reset_fonts(self):
        self.ui_font.configure(family=self.default_ui_font[0], size=self.default_ui_font[1])
        self.text_font.configure(family=self.default_text_font[0], size=self.default_text_font[1])
        self.left_list.config(font=self.text_font)
        self.right_list.config(font=self.text_font)

    def select_font_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Font Selection")

        tk.Label(win, text="Font Family:").grid(row=0, column=0, padx=5, pady=5)
        families = list(font.families())
        families.sort()
        family_var = tk.StringVar(value=self.text_font.cget("family"))
        family_box = ttk.Combobox(win, textvariable=family_var, values=families, width=30)
        family_box.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(win, text="Font Size:").grid(row=1, column=0, padx=5, pady=5)
        size_var = tk.IntVar(value=self.text_font.cget("size"))
        size_spin = tk.Spinbox(win, from_=6, to=72, textvariable=size_var, width=5)
        size_spin.grid(row=1, column=1, padx=5, pady=5)

        preview_label = tk.Label(win, text="Preview Text", width=30, anchor="center")
        preview_label.grid(row=2, column=0, columnspan=2, pady=10)

        def update_preview(*args):
            preview_label.config(font=(family_var.get(), size_var.get()))

        family_var.trace("w", update_preview)
        size_var.trace("w", update_preview)
        update_preview()

        def apply_font():
            self.text_font.configure(family=family_var.get(), size=size_var.get())
            self.left_list.config(font=self.text_font)
            self.right_list.config(font=self.text_font)
            win.destroy()

        ttk.Button(win, text="Apply", command=apply_font).grid(row=3, column=0, columnspan=2, pady=10)

    def on_ctrl_mousewheel(self, event):
        delta = 1 if event.delta > 0 else -1
        self.change_content_font(delta)
        return "break"

    # -------- File handling --------
    def load_folder(self, side):
        folder = filedialog.askdirectory()
        if not folder:
            return
        if side == "left":
            self.left_folder = folder
            self.left_list.delete(0, tk.END)
            for f in os.listdir(folder):
                if os.path.isfile(os.path.join(folder, f)):
                    self.left_list.insert(tk.END, f)
        else:
            self.right_folder = folder
            self.right_list.delete(0, tk.END)
            for f in os.listdir(folder):
                if os.path.isfile(os.path.join(folder, f)):
                    self.right_list.insert(tk.END, f)

    def file_selected(self, event):
        if self.left_list.curselection():
            self.left_file = os.path.join(self.left_folder, self.left_list.get(self.left_list.curselection()))
        if self.right_list.curselection():
            self.right_file = os.path.join(self.right_folder, self.right_list.get(self.right_list.curselection()))
        if self.left_file and self.right_file:
            self.compare_files()

    def update_line_numbers(self, number_widget, total_lines):
        number_widget.config(state="normal")
        number_widget.delete("1.0", tk.END)
        for i in range(1, total_lines + 1):
            number_widget.insert(tk.END, f"{i}\n")
        number_widget.config(state="disabled")

    def compare_files(self):
        with open(self.left_file, "r", encoding="utf-8", errors="ignore") as f:
            left_lines = f.readlines()
        with open(self.right_file, "r", encoding="utf-8", errors="ignore") as f:
            right_lines = f.readlines()

        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)

        self.diff_lines = []
        self.current_diff_index = -1

        max_lines = max(len(left_lines), len(right_lines))

        for i in range(max_lines):
            left_line = left_lines[i].rstrip("\n") if i < len(left_lines) else ""
            right_line = right_lines[i].rstrip("\n") if i < len(right_lines) else ""

            self.left_text.insert(tk.END, left_line + "\n")
            self.right_text.insert(tk.END, right_line + "\n")

            if left_line != right_line:
                self.left_text.tag_add("diff", f"{i+1}.0", f"{i+1}.end")
                self.right_text.tag_add("diff", f"{i+1}.0", f"{i+1}.end")
                self.diff_lines.append(i + 1)

        self.left_text.tag_config("diff", background="yellow")
        self.right_text.tag_config("diff", background="yellow")

        self.update_line_numbers(self.left_line_numbers, max_lines)
        self.update_line_numbers(self.right_line_numbers, max_lines)

        left_name = os.path.basename(self.left_file)
        right_name = os.path.basename(self.right_file)
        if self.diff_lines:
            self.status_left.config(text=f"Comparing: {left_name} <-> {right_name}")
            self.status_right.config(text=f"{len(self.diff_lines)} differences")
        else:
            self.status_left.config(text=f"Comparing: {left_name} <-> {right_name}")
            self.status_right.config(text="Files are identical")

    # -------- Diff navigation --------
    def goto_diff(self, index):
        if not self.diff_lines:
            return
        if index < 0 or index >= len(self.diff_lines):
            return

        self.current_diff_index = index
        line = self.diff_lines[self.current_diff_index]

        self.left_text.see(f"{line}.0")
        self.right_text.see(f"{line}.0")
        self.left_line_numbers.see(f"{line}.0")
        self.right_line_numbers.see(f"{line}.0")

        self.left_text.tag_remove("current_diff", "1.0", tk.END)
        self.right_text.tag_remove("current_diff", "1.0", tk.END)

        self.left_text.tag_add("current_diff", f"{line}.0", f"{line}.end")
        self.right_text.tag_add("current_diff", f"{line}.0", f"{line}.end")

        self.left_text.tag_config("current_diff", background="orange")
        self.right_text.tag_config("current_diff", background="orange")

        self.status_right.config(text=f"Diff {self.current_diff_index+1}/{len(self.diff_lines)} (Line {line})")

    def goto_next_diff(self):
        if not self.diff_lines:
            return
        if hasattr(self, "clicked_line") and self.clicked_line:
            # find next diff after clicked line
            for i, l in enumerate(self.diff_lines):
                if l > self.clicked_line:
                    self.goto_diff(i)
                    self.clicked_line = 0
                    return
        # fallback: normal behavior
        if self.current_diff_index < len(self.diff_lines) - 1:
            self.goto_diff(self.current_diff_index + 1)

    def goto_prev_diff(self):
        if not self.diff_lines:
            return
        if hasattr(self, "clicked_line") and self.clicked_line:
            # find prev diff before clicked line
            for i in reversed(range(len(self.diff_lines))):
                if self.diff_lines[i] < self.clicked_line:
                    self.goto_diff(i)
                    self.clicked_line = 0
                    return
        # fallback: normal behavior
        if self.current_diff_index > 0:
            self.goto_diff(self.current_diff_index - 1)

    def goto_first_diff(self):
        self.goto_diff(0)

    def goto_last_diff(self):
        self.goto_diff(len(self.diff_lines) - 1)

    # -------- Sync scrolling --------
    def sync_scroll(self, *args):
        self.left_text.yview(*args)
        self.right_text.yview(*args)
        self.left_line_numbers.yview(*args)
        self.right_line_numbers.yview(*args)

    def sync_xscroll(self, *args):
        self.left_text.xview(*args)
        self.right_text.xview(*args)
        self.hscrollbar.set(*self.left_text.xview())

    def on_mousewheel(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1

        self.left_text.yview_scroll(delta, "units")
        self.right_text.yview_scroll(delta, "units")
        self.left_line_numbers.yview_scroll(delta, "units")
        self.right_line_numbers.yview_scroll(delta, "units")
        return "break"

    def on_shift_mousewheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.left_text.xview_scroll(delta, "units")
        self.right_text.xview_scroll(delta, "units")
        return "break"

    # -------- Line click highlight --------
    def on_click_line(self, event):
        widget = event.widget
        index = widget.index("current")
        line = int(index.split(".")[0])

        self.clicked_line = line  # NEW: save clicked line

        # Clear old highlight
        self.left_text.tag_remove("clicked_line", "1.0", tk.END)
        self.right_text.tag_remove("clicked_line", "1.0", tk.END)

        # Highlight both sides
        self.left_text.tag_add("clicked_line", f"{line}.0", f"{line}.end")
        self.right_text.tag_add("clicked_line", f"{line}.0", f"{line}.end")

        self.left_text.tag_config("clicked_line", background="lightgreen")
        self.right_text.tag_config("clicked_line", background="lightgreen")

        # Update status bar
        if line in self.diff_lines:
            idx = self.diff_lines.index(line) + 1
            self.status_right.config(text=f"Line {line} clicked (Diff {idx}/{len(self.diff_lines)})")
        else:
            self.status_right.config(text=f"Line {line} clicked (No diff)")


if __name__ == "__main__":
    root = tk.Tk()
    app = FolderCompareApp(root)
    root.mainloop()

