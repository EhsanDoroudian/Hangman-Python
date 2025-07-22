import tkinter as tk
from tkinter import messagebox
import random
from collections import Counter
import os
try:
    import pygame
    pygame.mixer.init()
except ImportError:
    pass

# Define word categories
WORD_CATEGORIES = {
    'Fruits': '''apple banana mango strawberry orange grape pineapple apricot lemon coconut watermelon cherry papaya berry peach lychee muskmelon'''.split(),
    'Animals': '''tiger lion elephant giraffe kangaroo monkey zebra rabbit horse dog cat bear wolf fox deer goat sheep'''.split(),
    'Countries': '''canada brazil france germany india china japan egypt italy spain russia mexico turkey greece norway sweden'''.split(),
    'Movies': '''inception avatar titanic gladiator matrix godfather rocky jaws frozen shrek up coco moana aladdin dumbo'''.split(),
}

class CategorySelector:
    def __init__(self, root, on_category_selected, on_custom_word):
        self.root = root
        self.on_category_selected = on_category_selected
        self.on_custom_word = on_custom_word
        self.frame = tk.Frame(root, bg="#e6f3ff")
        self.frame.pack(expand=True, fill=tk.BOTH)
        label = tk.Label(self.frame, text="Select a Category", font=("Segoe UI", 22, "bold"), bg="#e6f3ff", fg="#1a3c66")
        label.pack(pady=30)
        for cat in WORD_CATEGORIES:
            btn = tk.Button(self.frame, text=cat, font=("Segoe UI", 16, "bold"), bg="#28a745", fg="white", relief="flat", padx=30, pady=10,
                            command=lambda c=cat: self.select_category(c))
            btn.pack(pady=10)
        # Custom word button
        btn_custom = tk.Button(self.frame, text="Custom Word", font=("Segoe UI", 16, "bold"), bg="#ff8800", fg="white", relief="flat", padx=30, pady=10,
                               command=self.custom_word)
        btn_custom.pack(pady=20)
    def select_category(self, category):
        self.frame.destroy()
        self.on_category_selected(category)
    def custom_word(self):
        self.frame.destroy()
        self.on_custom_word()

class DifficultySelector:
    def __init__(self, root, category, on_difficulty_selected):
        self.root = root
        self.category = category
        self.on_difficulty_selected = on_difficulty_selected
        self.frame = tk.Frame(root, bg="#e6f3ff")
        self.frame.pack(expand=True, fill=tk.BOTH)
        label = tk.Label(self.frame, text="Select Difficulty", font=("Segoe UI", 22, "bold"), bg="#e6f3ff", fg="#1a3c66")
        label.pack(pady=30)
        for diff in ["Easy", "Medium", "Hard"]:
            btn = tk.Button(self.frame, text=diff, font=("Segoe UI", 16, "bold"), bg="#007bff", fg="white", relief="flat", padx=30, pady=10,
                            command=lambda d=diff: self.select_difficulty(d))
            btn.pack(pady=10)
    def select_difficulty(self, difficulty):
        self.frame.destroy()
        self.on_difficulty_selected(self.category, difficulty)

class CustomWordDialog:
    def __init__(self, root, on_done):
        self.top = tk.Toplevel(root)
        self.top.title("Enter Custom Word")
        self.top.geometry("400x250")
        self.top.configure(bg="#e6f3ff")
        tk.Label(self.top, text="Enter a word:", font=("Segoe UI", 14), bg="#e6f3ff").pack(pady=10)
        self.entry_word = tk.Entry(self.top, font=("Segoe UI", 14), show="*")
        self.entry_word.pack(pady=5)
        tk.Label(self.top, text="Optional hint:", font=("Segoe UI", 12), bg="#e6f3ff").pack(pady=5)
        self.entry_hint = tk.Entry(self.top, font=("Segoe UI", 12))
        self.entry_hint.pack(pady=5)
        btn = tk.Button(self.top, text="Start Game", font=("Segoe UI", 12, "bold"), bg="#28a745", fg="white", relief="flat", command=self.submit)
        btn.pack(pady=15)
        self.on_done = on_done
        self.entry_word.focus_set()
        self.top.grab_set()
    def submit(self):
        word = self.entry_word.get().strip().lower()
        hint = self.entry_hint.get().strip()
        if not word.isalpha():
            tk.messagebox.showerror("Invalid Word", "Please enter a valid word (letters only).")
            return
        self.top.destroy()
        self.on_done(word, hint)

THEMES = {
    'Light': {
        'bg': '#e6f3ff',
        'fg': '#1a3c66',
        'label_fg': '#1a3c66',
        'word_fg': '#005566',
        'button_bg': '#28a745',
        'button_fg': 'white',
        'button_active': '#34c759',
        'restart_bg': '#dc3545',
        'restart_active': '#ff4d4d',
        'hint_bg': '#ffc107',
        'hint_active': '#ffe066',
        'hint_fg': '#1a3c66',
        'highscore_fg': '#ff8800',
        'message_fg': 'red',
        'canvas_bg': '#e6f3ff',
    },
    'Dark': {
        'bg': '#23272e',
        'fg': '#e6f3ff',
        'label_fg': '#e6f3ff',
        'word_fg': '#00e6e6',
        'button_bg': '#2dce89',
        'button_fg': '#23272e',
        'button_active': '#1dd1a1',
        'restart_bg': '#ff6b6b',
        'restart_active': '#ee5253',
        'hint_bg': '#feca57',
        'hint_active': '#fff6a9',
        'hint_fg': '#23272e',
        'highscore_fg': '#feca57',
        'message_fg': '#ff6b6b',
        'canvas_bg': '#23272e',
    }
}

class HangmanGUI:
    HIGHSCORE_FILE = "hangman_highscore.txt"
    def __init__(self, root, category, word_list, difficulty, custom_hint=None):
        self.root = root
        self.category = category
        self.difficulty = difficulty
        self.my_words = word_list
        self.custom_hint = custom_hint
        self.theme = 'Light'
        self.theme_vars = THEMES[self.theme]
        self.root.title("Hangman Game")
        self.root.geometry("1000x1000")
        self.root.resizable(False, False)
        self.root.configure(bg=self.theme_vars['bg'])
        self.wins = 0
        self.losses = 0
        self.highscore = self.load_highscore()
        self.reset_game()
        self.sound_available = False
        try:
            import pygame
            self.correct_sound = pygame.mixer.Sound("correct.wav")
            self.incorrect_sound = pygame.mixer.Sound("incorrect.wav")
            self.sound_available = True
        except:
            self.sound_available = False
        self.main_frame = tk.Frame(root, bg=self.theme_vars['bg'])
        self.main_frame.pack(pady=20, padx=20, expand=True)
        # Theme switcher button
        self.button_theme = tk.Button(
            self.main_frame,
            text=f"Theme: {self.theme}",
            command=self.switch_theme,
            font=("Segoe UI", 10, "bold"),
            bg=self.theme_vars['button_bg'],
            fg=self.theme_vars['button_fg'],
            activebackground=self.theme_vars['button_active'],
            relief="flat",
            padx=10,
            pady=4,
            borderwidth=0
        )
        self.button_theme.pack(anchor="ne", padx=5, pady=5)
        # Use custom hint if provided
        if self.custom_hint:
            hint_text = f"Guess the word! HINT: {self.custom_hint}"
        else:
            hint_text = f"Guess the word! HINT: It's a {self.category.lower()} name ({self.difficulty})"
        self.label_hint = tk.Label(
            self.main_frame,
            text=hint_text,
            font=("Segoe UI", 18, "bold"),
            bg=self.theme_vars['bg'],
            fg=self.theme_vars['label_fg']
        )
        self.label_hint.pack(pady=10)
        self.label_word = tk.Label(
            self.main_frame,
            text=self.get_display_word(),
            font=("Courier New", 28, "bold"),
            bg=self.theme_vars['bg'],
            fg=self.theme_vars['word_fg']
        )
        self.label_word.pack(pady=10)
        self.label_chances = tk.Label(
            self.main_frame,
            text=f"Chances remaining: {self.chances}",
            font=("Segoe UI", 14),
            bg=self.theme_vars['bg'],
            fg=self.theme_vars['label_fg']
        )
        self.label_chances.pack(pady=5)
        self.label_guessed = tk.Label(
            self.main_frame,
            text="Guessed letters: None",
            font=("Segoe UI", 14),
            bg=self.theme_vars['bg'],
            fg=self.theme_vars['label_fg']
        )
        self.label_guessed.pack(pady=5)
        self.label_score = tk.Label(
            self.main_frame,
            text=f"Wins: {self.wins} | Losses: {self.losses}",
            font=("Segoe UI", 14),
            bg=self.theme_vars['bg'],
            fg=self.theme_vars['label_fg']
        )
        self.label_score.pack(pady=5)
        self.label_highscore = tk.Label(
            self.main_frame,
            text=f"High Score (Win Streak): {self.highscore}",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme_vars['bg'],
            fg=self.theme_vars['highscore_fg']
        )
        self.label_highscore.pack(pady=5)
        self.label_stats = tk.Label(
            self.main_frame,
            text="Correct: 0 | Incorrect: 0",
            font=("Segoe UI", 14),
            bg=self.theme_vars['bg'],
            fg=self.theme_vars['label_fg']
        )
        self.label_stats.pack(pady=5)
        self.canvas = tk.Canvas(
            self.main_frame,
            width=200,
            height=200,
            bg=self.theme_vars['canvas_bg'],
            highlightthickness=0
        )
        self.canvas.pack(pady=20)
        self.draw_hangman(0)
        self.entry_guess = tk.Entry(
            self.main_frame,
            font=("Segoe UI", 14),
            width=5,
            bd=2,
            relief="flat",
            bg="#ffffff",
            fg=self.theme_vars['label_fg'],
            insertbackground=self.theme_vars['label_fg']
        )
        self.entry_guess.pack(pady=10)
        self.entry_guess.bind("<Return>", self.process_guess)
        self.entry_guess.bind("<FocusIn>", lambda e: self.entry_guess.config(bg="#f0f8ff"))
        self.entry_guess.bind("<FocusOut>", lambda e: self.entry_guess.config(bg="#ffffff"))
        self.entry_guess.focus_set()
        self.button_frame = tk.Frame(self.main_frame, bg=self.theme_vars['bg'])
        self.button_frame.pack(pady=10)
        self.button_guess = tk.Button(
            self.button_frame,
            text="Guess",
            command=self.process_guess,
            font=("Segoe UI", 12, "bold"),
            bg=self.theme_vars['button_bg'],
            fg=self.theme_vars['button_fg'],
            activebackground=self.theme_vars['button_active'],
            relief="flat",
            padx=15,
            pady=8,
            borderwidth=0
        )
        self.button_guess.pack(side=tk.LEFT, padx=5)
        self.button_guess.bind("<Enter>", lambda e: self.button_guess.config(bg=self.theme_vars['button_active']))
        self.button_guess.bind("<Leave>", lambda e: self.button_guess.config(bg=self.theme_vars['button_bg']))
        self.button_restart = tk.Button(
            self.button_frame,
            text="Restart",
            command=self.reset_game,
            font=("Segoe UI", 12, "bold"),
            bg=self.theme_vars['restart_bg'],
            fg=self.theme_vars['button_fg'],
            activebackground=self.theme_vars['restart_active'],
            relief="flat",
            padx=15,
            pady=8,
            borderwidth=0
        )
        self.button_restart.pack(side=tk.LEFT, padx=5)
        self.button_restart.bind("<Enter>", lambda e: self.button_restart.config(bg=self.theme_vars['restart_active']))
        self.button_restart.bind("<Leave>", lambda e: self.button_restart.config(bg=self.theme_vars['restart_bg']))
        self.button_hint = tk.Button(
            self.button_frame,
            text="Hint",
            command=self.use_hint,
            font=("Segoe UI", 12, "bold"),
            bg=self.theme_vars['hint_bg'],
            fg=self.theme_vars['hint_fg'],
            activebackground=self.theme_vars['hint_active'],
            relief="flat",
            padx=15,
            pady=8,
            borderwidth=0
        )
        self.button_hint.pack(side=tk.LEFT, padx=5)
        self.button_hint.bind("<Enter>", lambda e: self.button_hint.config(bg=self.theme_vars['hint_active']))
        self.button_hint.bind("<Leave>", lambda e: self.button_hint.config(bg=self.theme_vars['hint_bg']))
        self.hint_used = False
        self.label_message = tk.Label(
            self.main_frame,
            text="",
            font=("Segoe UI", 12),
            bg=self.theme_vars['bg'],
            fg=self.theme_vars['message_fg']
        )
        self.label_message.pack(pady=10)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def switch_theme(self):
        themes = list(THEMES.keys())
        idx = themes.index(self.theme)
        self.theme = themes[(idx + 1) % len(themes)]
        self.theme_vars = THEMES[self.theme]
        self.apply_theme()

    def apply_theme(self):
        self.root.configure(bg=self.theme_vars['bg'])
        self.main_frame.configure(bg=self.theme_vars['bg'])
        self.label_hint.configure(bg=self.theme_vars['bg'], fg=self.theme_vars['label_fg'])
        self.label_word.configure(bg=self.theme_vars['bg'], fg=self.theme_vars['word_fg'])
        self.label_chances.configure(bg=self.theme_vars['bg'], fg=self.theme_vars['label_fg'])
        self.label_guessed.configure(bg=self.theme_vars['bg'], fg=self.theme_vars['label_fg'])
        self.label_score.configure(bg=self.theme_vars['bg'], fg=self.theme_vars['label_fg'])
        self.label_highscore.configure(bg=self.theme_vars['bg'], fg=self.theme_vars['highscore_fg'])
        self.label_stats.configure(bg=self.theme_vars['bg'], fg=self.theme_vars['label_fg'])
        self.label_message.configure(bg=self.theme_vars['bg'], fg=self.theme_vars['message_fg'])
        self.canvas.configure(bg=self.theme_vars['canvas_bg'])
        self.button_guess.configure(bg=self.theme_vars['button_bg'], fg=self.theme_vars['button_fg'], activebackground=self.theme_vars['button_active'])
        self.button_restart.configure(bg=self.theme_vars['restart_bg'], fg=self.theme_vars['button_fg'], activebackground=self.theme_vars['restart_active'])
        self.button_hint.configure(bg=self.theme_vars['hint_bg'], fg=self.theme_vars['hint_fg'], activebackground=self.theme_vars['hint_active'])
        self.button_theme.configure(bg=self.theme_vars['button_bg'], fg=self.theme_vars['button_fg'], activebackground=self.theme_vars['button_active'], text=f"Theme: {self.theme}")
        self.button_frame.configure(bg=self.theme_vars['bg'])
        self.entry_guess.configure(fg=self.theme_vars['label_fg'], insertbackground=self.theme_vars['label_fg'])

    def draw_hangman(self, stage):
        """Draw hangman on canvas based on stage (0-7)."""
        self.canvas.delete("all")
        # Gallows
        self.canvas.create_line(20, 180, 180, 180, width=3, fill="#1a3c66")  # Base
        self.canvas.create_line(100, 180, 100, 20, width=3, fill="#1a3c66")  # Pole
        self.canvas.create_line(100, 20, 150, 20, width=3, fill="#1a3c66")   # Top
        self.canvas.create_line(150, 20, 150, 40, width=3, fill="#1a3c66")   # Rope
        
        if stage > 0:  # Head
            self.canvas.create_oval(140, 40, 160, 60, width=2, outline="#1a3c66")
        if stage > 1:  # Body
            self.canvas.create_line(150, 60, 150, 100, width=2, fill="#1a3c66")
        if stage > 2:  # Left arm
            self.canvas.create_line(150, 70, 130, 90, width=2, fill="#1a3c66")
        if stage > 3:  # Right arm
            self.canvas.create_line(150, 70, 170, 90, width=2, fill="#1a3c66")
        if stage > 4:  # Left leg
            self.canvas.create_line(150, 100, 130, 130, width=2, fill="#1a3c66")
        if stage > 5:  # Right leg
            self.canvas.create_line(150, 100, 170, 130, width=2, fill="#1a3c66")
        if stage > 6:  # "YOU LOSE!" text
            self.canvas.create_text(100, 160, text="YOU LOSE!", font=("Segoe UI", 12, "bold"), fill="red")
    
    def get_display_word(self):
        display = ""
        for char in self.word:
            if char in self.letter_guessed:
                display += char + " "
            else:
                display += "_ "
        return display.strip()
    
    def play_sound(self, sound_type):
        if self.sound_available:
            try:
                if sound_type == "correct":
                    self.correct_sound.play()
                elif sound_type == "incorrect":
                    self.incorrect_sound.play()
            except:
                pass
    
    def flash_message(self, text, color):
        """Flash the message label for emphasis."""
        self.label_message.config(text=text, fg=color)
        self.root.after(200, lambda: self.label_message.config(fg="#e6f3ff"))
        self.root.after(400, lambda: self.label_message.config(fg=color))
        self.root.after(600, lambda: self.label_message.config(fg="#e6f3ff"))
        self.root.after(800, lambda: self.label_message.config(fg=color))
    
    def process_guess(self, event=None):
        if self.game_over:
            return
        
        guess = self.entry_guess.get().lower()
        self.entry_guess.delete(0, tk.END)
        self.entry_guess.focus_set()
        
        # Input validation
        if not guess:
            self.flash_message("Please enter a letter!", "red")
            return
        if not guess.isalpha():
            self.flash_message("Enter only a LETTER!", "red")
            return
        if len(guess) > 1:
            self.flash_message("Enter only a SINGLE letter!", "red")
            return
        if guess in self.letter_guessed:
            self.flash_message("You have already guessed that letter!", "red")
            return
        
        # Valid guess
        self.label_message.config(text="")
        self.letter_guessed += guess
        self.label_guessed.config(text=f"Guessed letters: {', '.join(sorted(self.letter_guessed))}")
        
        # Update stats
        correct_count = sum(1 for char in self.word if char in self.letter_guessed)
        incorrect_count = len([g for g in self.letter_guessed if g not in self.word])
        self.label_stats.config(text=f"Correct: {correct_count} | Incorrect: {incorrect_count}")
        
        if guess in self.word:
            self.play_sound("correct")
            self.label_word.config(text=self.get_display_word())
            if Counter(self.letter_guessed) == Counter(self.word):
                self.wins += 1
                self.label_score.config(text=f"Wins: {self.wins} | Losses: {self.losses}")
                self.update_highscore()
                self.flash_message("Congratulations, You won!", "green")
                self.game_over = True
                messagebox.showinfo("Hangman", f"You won! The word was '{self.word}'.")
        else:
            self.play_sound("incorrect")
            self.chances -= 1
            self.label_chances.config(text=f"Chances remaining: {self.chances}")
            wrong_guesses = len([g for g in self.letter_guessed if g not in self.word])
            self.draw_hangman(wrong_guesses)
            
            if self.chances <= 0:
                self.losses += 1
                self.label_score.config(text=f"Wins: {self.wins} | Losses: {self.losses}")
                self.wins = 0  # Reset win streak on loss
                self.update_highscore()
                self.flash_message("You lost! Try again.", "red")
                self.game_over = True
                self.label_word.config(text=" ".join(self.word))
                messagebox.showinfo("Hangman", f"You lost! The word was '{self.word}'.")
    
    def use_hint(self):
        if self.game_over or self.hint_used:
            return
        unrevealed = [c for c in set(self.word) if c not in self.letter_guessed]
        if not unrevealed:
            self.flash_message("No hints available!", "red")
            return
        hint_letter = random.choice(unrevealed)
        self.letter_guessed += hint_letter
        self.label_guessed.config(text=f"Guessed letters: {', '.join(sorted(self.letter_guessed))}")
        self.label_word.config(text=self.get_display_word())
        self.chances -= 1
        self.label_chances.config(text=f"Chances remaining: {self.chances}")
        self.hint_used = True
        self.button_hint.config(state=tk.DISABLED)
        self.flash_message(f"Hint used! Letter '{hint_letter}' revealed.", "#1a3c66")
        # Update stats
        correct_count = sum(1 for char in self.word if char in self.letter_guessed)
        incorrect_count = len([g for g in self.letter_guessed if g not in self.word])
        self.label_stats.config(text=f"Correct: {correct_count} | Incorrect: {incorrect_count}")
        # Check for win/loss
        if Counter(self.letter_guessed) == Counter(self.word):
            self.wins += 1
            self.label_score.config(text=f"Wins: {self.wins} | Losses: {self.losses}")
            self.update_highscore()
            self.flash_message("Congratulations, You won!", "green")
            self.game_over = True
            messagebox.showinfo("Hangman", f"You won! The word was '{self.word}'.")
        elif self.chances <= 0:
            self.losses += 1
            self.label_score.config(text=f"Wins: {self.wins} | Losses: {self.losses}")
            self.wins = 0
            self.update_highscore()
            self.flash_message("You lost! Try again.", "red")
            self.game_over = True
            self.label_word.config(text=" ".join(self.word))
            messagebox.showinfo("Hangman", f"You lost! The word was '{self.word}'.")
    
    def reset_game(self):
        # If custom word, use it directly
        if self.category == "Custom":
            self.word = self.my_words[0]
            self.chances = min(9, len(self.word) + 2)
        else:
            # Filter word list by difficulty
            if self.difficulty == "Easy":
                filtered = [w for w in self.my_words if len(w) <= 5]
                self.chances_base = 9
            elif self.difficulty == "Medium":
                filtered = [w for w in self.my_words if 6 <= len(w) <= 8]
                self.chances_base = 7
            else:  # Hard
                filtered = [w for w in self.my_words if len(w) > 8]
                self.chances_base = 6
            if not filtered:
                filtered = self.my_words
            self.word = random.choice(filtered).lower()
            self.chances = min(self.chances_base, len(self.word) + 2)
        self.letter_guessed = ''
        self.game_over = False
        self.hint_used = False
        if hasattr(self, 'button_hint'):
            self.button_hint.config(state=tk.NORMAL)
        if hasattr(self, 'label_word'):
            self.label_word.config(text=self.get_display_word())
            self.label_chances.config(text=f"Chances remaining: {self.chances}")
            self.label_guessed.config(text="Guessed letters: None")
            self.label_stats.config(text="Correct: 0 | Incorrect: 0")
            self.label_message.config(text="")
            self.canvas.delete("all")
            self.draw_hangman(0)
            self.entry_guess.delete(0, tk.END)
            self.entry_guess.focus_set()
        if hasattr(self, 'label_highscore'):
            self.label_highscore.config(text=f"High Score (Win Streak): {self.highscore}")

    def load_highscore(self):
        if os.path.exists(self.HIGHSCORE_FILE):
            try:
                with open(self.HIGHSCORE_FILE, "r") as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0
    def save_highscore(self):
        try:
            with open(self.HIGHSCORE_FILE, "w") as f:
                f.write(str(self.highscore))
        except:
            pass
    def update_highscore(self):
        if self.wins > self.highscore:
            self.highscore = self.wins
            self.save_highscore()
            self.label_highscore.config(text=f"High Score (Win Streak): {self.highscore}")

    def on_closing(self):
        if not self.game_over:
            if messagebox.askokcancel("Quit", "Do you want to quit the game?"):
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    def start_game_with_category(category):
        def after_difficulty(category, difficulty):
            word_list = WORD_CATEGORIES[category]
            HangmanGUI(root, category, word_list, difficulty)
        DifficultySelector(root, category, after_difficulty)
    def start_game_with_custom_word():
        def on_custom_word(word, hint):
            HangmanGUI(root, "Custom", [word], "Easy", custom_hint=hint if hint else "Custom word")
        CustomWordDialog(root, on_custom_word)
    CategorySelector(root, start_game_with_category, start_game_with_custom_word)
    root.mainloop()