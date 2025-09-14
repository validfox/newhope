import tkinter as tk
from tkinter import filedialog, ttk, font
import os
import difflib


class FolderCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("R2D2: A Folder Compare Tool")

        # Default font settings
        self.default_ui_font = ("times", 10)
        self.default_text_font = ("times", 11)

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

        # Disable mouse scroll on line numbers
        for widget in (self.left_line_numbers, self.right_line_numbers):
            widget.bind("<MouseWheel>", lambda e: "break")
            widget.bind("<Button-4>", lambda e: "break")
            widget.bind("<Button-5>", lambda e: "break")

        # Mouse wheel bindings (content only)
        for widget in (self.left_text, self.right_text):
            widget.bind("<MouseWheel>", self.on_mousewheel)
            widget.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)
            widget.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)
            widget.bind("<Button-4>", self.on_mousewheel)
            widget.bind("<Button-5>", self.on_mousewheel)
            widget.bind("<Button-1>", self.on_click_line)

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
        self.ui_font_select = ttk.Button(self.button_frame, text="Choose UI Font", command=self.select_ui_font_dialog)
        self.ui_font_select.pack(side=tk.LEFT, padx=5)
        self.text_font_select = ttk.Button(self.button_frame, text="Choose Content Font", command=self.select_text_font_dialog)
        self.text_font_select.pack(side=tk.LEFT, padx=5)
        self.reset_font_btn = ttk.Button(self.button_frame, text="Reset Fonts", command=self.reset_fonts)
        self.reset_font_btn.pack(side=tk.LEFT, padx=5)

        # Status bar
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
        self.diff_ranges = []
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

    def open_font_dialog(self, target_font, dialog_attr, title, apply_callback=None):
        if getattr(self, dialog_attr, None) is not None:
            getattr(self, dialog_attr).lift()
            return

        win = tk.Toplevel(self.root)
        setattr(self, dialog_attr, win)
        win.title(title)
        win.transient(self.root)
        win.grab_set()
        win.attributes("-topmost", True)

        def on_close():
            setattr(self, dialog_attr, None)
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)

        tk.Label(win, text="Font Family:").grid(row=0, column=0, padx=5, pady=5)
        families = sorted(font.families())
        family_var = tk.StringVar(value=target_font.cget("family"))
        family_box = ttk.Combobox(win, textvariable=family_var, values=families, width=30)
        family_box.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(win, text="Font Size:").grid(row=1, column=0, padx=5, pady=5)
        size_var = tk.IntVar(value=target_font.cget("size"))
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
            target_font.configure(family=family_var.get(), size=size_var.get())
            if apply_callback:
                apply_callback()
            on_close()

        ttk.Button(win, text="Apply", command=apply_font).grid(row=3, column=0, columnspan=2, pady=10)

    def select_ui_font_dialog(self):
        self.open_font_dialog(
            target_font=self.ui_font,
            dialog_attr="ui_font_dialog",
            title="UI Font Selection"
        )

    def select_text_font_dialog(self):
        self.open_font_dialog(
            target_font=self.text_font,
            dialog_attr="text_font_dialog",
            title="Content Font Selection",
            apply_callback=lambda: (
                self.left_list.config(font=self.text_font),
                self.right_list.config(font=self.text_font)
            )
        )

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

        self.diff_ranges = []
        self.current_diff_index = -1

        matcher = difflib.SequenceMatcher(None, left_lines, right_lines)
        opcodes = matcher.get_opcodes()

        max_lines = max(len(left_lines), len(right_lines))
        self.update_line_numbers(self.left_line_numbers, max_lines)
        self.update_line_numbers(self.right_line_numbers, max_lines)

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                for i in range(i1, i2):
                    self.left_text.insert(tk.END, left_lines[i])
                for j in range(j1, j2):
                    self.right_text.insert(tk.END, right_lines[j])
            else:
                self.diff_ranges.append(((i1+1, i2), (j1+1, j2)))
                if tag in ("replace", "delete"):
                    for i in range(i1, i2):
                        self.left_text.insert(tk.END, left_lines[i], tag)
                if tag in ("replace", "insert"):
                    for j in range(j1, j2):
                        self.right_text.insert(tk.END, right_lines[j], tag)

        self.left_text.tag_config("replace", background="lightyellow")
        self.right_text.tag_config("replace", background="lightyellow")
        self.left_text.tag_config("delete", background="lightcoral")
        self.right_text.tag_config("insert", background="lightgreen")
        self.left_text.tag_config("current_diff", background="orange")
        self.right_text.tag_config("current_diff", background="orange")

        left_name = os.path.basename(self.left_file)
        right_name = os.path.basename(self.right_file)
        if self.diff_ranges:
            self.status_left.config(text=f"Comparing: {left_name} <-> {right_name}")
            self.status_right.config(text=f"{len(self.diff_ranges)} differences")
        else:
            self.status_left.config(text=f"Comparing: {left_name} <-> {right_name}")
            self.status_right.config(text="Files are identical")

    # -------- Diff navigation --------
    def goto_diff(self, index):
        if not self.diff_ranges:
            return
        if index < 0 or index >= len(self.diff_ranges):
            return

        self.current_diff_index = index
        (l_start, l_end), (r_start, r_end) = self.diff_ranges[index]

        self.left_text.tag_remove("current_diff", "1.0", tk.END)
        self.right_text.tag_remove("current_diff", "1.0", tk.END)

        if l_start <= l_end:
            self.left_text.tag_add("current_diff", f"{l_start}.0", f"{l_end}.0 lineend")
        if r_start <= r_end:
            self.right_text.tag_add("current_diff", f"{r_start}.0", f"{r_end}.0 lineend")

        self.left_text.see(f"{l_start}.0")
        self.right_text.see(f"{r_start}.0")
        self.left_line_numbers.see(f"{l_start}.0")
        self.right_line_numbers.see(f"{r_start}.0")

        self.status_right.config(text=f"Diff {self.current_diff_index+1}/{len(self.diff_ranges)} "
                                      f"(Left {l_start}-{l_end}, Right {r_start}-{r_end})")

    def goto_next_diff(self):
        if not self.diff_ranges:
            return
        if self.current_diff_index < len(self.diff_ranges) - 1:
            self.goto_diff(self.current_diff_index + 1)

    def goto_prev_diff(self):
        if not self.diff_ranges:
            return
        if self.current_diff_index > 0:
            self.goto_diff(self.current_diff_index - 1)

    def goto_first_diff(self):
        self.goto_diff(0)

    def goto_last_diff(self):
        self.goto_diff(len(self.diff_ranges) - 1)

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

    def on_click_line(self, event):
        pass  # No special behavior for clicking lines


if __name__ == "__main__":
    root = tk.Tk()
    app = FolderCompareApp(root)
    root.mainloop()

