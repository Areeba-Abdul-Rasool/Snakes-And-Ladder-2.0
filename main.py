import tkinter as tk
from tkinter import simpledialog, Toplevel
from PIL import Image, ImageTk
import random
import threading
from playsound import playsound
import time
import heapq

class SnakesLadders:
    def __init__(self, root):
        self.root = root
        self.root.title("Snakes and Ladders")

        self.window_width = 1250
        self.window_height = 850
        self.extra_turn_booster = False

        x = int((self.root.winfo_screenwidth() / 2) - (self.window_width / 2))
        y = int((self.root.winfo_screenheight() / 2) - (self.window_height / 2))
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

        self.canvas = tk.Canvas(root, width=self.window_width, height=self.window_height)
        self.canvas.pack()

        self.select_mode()

    def select_mode(self):
        playsound("sound/start-game.wav", block=False)
        self.canvas.delete("all")
        self.mode_img = ImageTk.PhotoImage(Image.open("img/selectPlayers.png").resize((self.window_width, self.window_height)))
        self.canvas.create_image(0, 0, anchor='nw', image=self.mode_img)
        self.canvas.bind("<Button-1>", self.select_mode_click)

    def select_mode_click(self, event):
        x, y = event.x, event.y
        if 150 < x < 290 and 260 < y < 320:
            self.get_player_names(mode="bot")
        elif 250 < x < 420 and 440 < y < 480:
            self.get_player_names(mode="multi")
            
    def get_player_names(self, mode):
        """Opens a dialog to get player names before starting the game"""
        self.canvas.delete("all")
        self.canvas.unbind("<Button-1>")
        
        self.name_frame = tk.Frame(self.root, bg="white", bd=5, relief=tk.RIDGE)
        self.name_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=400, height=300)
        
        tk.Label(self.name_frame, text="Enter Player Names", font=("Arial", 16, "bold"), 
                bg="white", fg="#fa5b61").pack(pady=10)
        
        self.name_entries = []
        
        if mode == "bot":
            tk.Label(self.name_frame, text="Player 1:", font=("Arial", 12), bg="white").pack(anchor=tk.W, padx=20)
            p1_entry = tk.Entry(self.name_frame, font=("Arial", 12), width=25)
            p1_entry.insert(0, "Player 1")  
            p1_entry.pack(padx=20, pady=5)
            self.name_entries.append(p1_entry)
            
            tk.Label(self.name_frame, text="Bot Player:", font=("Arial", 12), bg="white").pack(anchor=tk.W, padx=20)
            bot_entry = tk.Entry(self.name_frame, font=("Arial", 12), width=25)
            bot_entry.insert(0, "Bot")  
            bot_entry.pack(padx=20, pady=5)
            self.name_entries.append(bot_entry)
        else:
            for i in range(3):
                tk.Label(self.name_frame, text=f"Player {i+1}:", font=("Arial", 12), bg="white").pack(anchor=tk.W, padx=20)
                entry = tk.Entry(self.name_frame, font=("Arial", 12), width=25)
                entry.insert(0, f"Player {i+1}")  
                entry.pack(padx=20, pady=5)
                self.name_entries.append(entry)
        
        start_button = tk.Button(self.name_frame, text="Start Game", font=("Arial", 14, "bold"), 
                               bg="#fa5b61", fg="white", command=lambda: self.start_game_with_names(mode))
        start_button.pack(pady=20)
    
    def start_game_with_names(self, mode):
        """Start the game with the entered player names"""
        names = [entry.get() for entry in self.name_entries]
        
        #name validation
        for i, name in enumerate(names):
            if not name.strip():
                names[i] = f"Player {i+1}"
        
        self.name_frame.destroy()
        
        self.start_game(mode, custom_names=names)

    def enable_click_debug(self):
        self.canvas.bind("<Button-1>", self.print_click_position)

    def print_click_position(self, event):
        print(f"Mouse clicked at: ({event.x}, {event.y})")


    def start_game(self, mode, custom_names=None):
        self.canvas.delete("all")
        self.canvas.unbind("<Button-1>")

        board_img = Image.open("img/board1.png").resize((1000, 800))
        self.board_tk = ImageTk.PhotoImage(board_img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.board_tk)

        self.players, self.token_ids, self.positions, self.shields, self.names = [], [], [], [], []

        self.mode = mode

        if mode == "bot":
            imgs = ["img/player-1.png", "img/botPlayer.png"]
            if custom_names:
                self.names = custom_names
            else:
                self.names = ["Player 1", "Bot"]
        else:
            imgs = ["img/player-1.png", "img/player-2.png", "img/player-3.png"]
            if custom_names:
                self.names = custom_names
            else:
                self.names = ["Player 1", "Player 2", "Player 3"]

        for i, img_path in enumerate(imgs):
            img = ImageTk.PhotoImage(Image.open(img_path).resize((50, 50)))
            token = self.canvas.create_image(50, 690 + i * 40, anchor='nw', image=img)
            self.players.append(img)
            self.token_ids.append(token)
            self.positions.append(0)
            self.shields.append(0)

        self.snakes = {
            99: 42,   
            92: 70,   
            47: 28,   
            37: 4,   
            86: 56,   
            }  
              
        self.ladders = {
            9: 32,     
            23: 57,   
            45: 77,   
            53: 88,   
        }
        
        self.powerups = {2: "booster", 25: "booster", 40: "shield", 52: "shield", 64: "booster", 83: "shield", 87: "booster"}

        self.dice_imgs = [ImageTk.PhotoImage(Image.open(f"img/dice/{i}.png").resize((80, 80))) for i in range(1, 7)]
        self.current_dice = self.canvas.create_image(1020, 100, anchor='nw', image=self.dice_imgs[0])

        self.turn = 0

        self.turn_label = tk.Label(self.root, text=f"{self.names[self.turn]}'s Turn", font=("Arial", 16, "bold"), fg="#fa5b61", bg="white")
        self.canvas.create_window(1020, 50, anchor='nw', window=self.turn_label)

        self.powerup_label = tk.Label(self.root, text="Power-Up: None", font=("Arial", 12, "bold"), bg="white", fg="#007f5f")
        self.canvas.create_window(1020, 300, anchor='nw', window=self.powerup_label)

        self.score_labels = []
        for i, name in enumerate(self.names):
            label = tk.Label(self.root, text=f"{name}: 0", font=("Arial", 12), bg="white", fg="black")
            self.canvas.create_window(1020, 400 + i * 30, anchor='nw', window=label)
            self.score_labels.append(label)

        self.win_prob_title = tk.Label(self.root, text="Win Probability", font=("Arial", 14, "bold"), bg="white", fg="#3a0ca3")
        self.canvas.create_window(1020, 500, anchor='nw', window=self.win_prob_title)
        
        self.win_prob_labels = []
        for i, name in enumerate(self.names):
            prob_label = tk.Label(self.root, text=f"{name}: {self.calculate_win_probability(i):.1f}%", 
                                 font=("Arial", 12), bg="white", fg="#3a0ca3")
            self.canvas.create_window(1020, 530 + i * 30, anchor='nw', window=prob_label)
            self.win_prob_labels.append(prob_label)

        self.roll_button = tk.Button(self.root, text="Roll Dice", font=("Arial", 14, "bold"), bg="#fa5b61", fg="white", command=self.roll_dice)
        self.canvas.create_window(1020, 200, anchor='nw', window=self.roll_button)

        if mode == "bot":
            self.path_button = tk.Button(self.root, text="Show Best Path", font=("Arial", 12, "bold"), 
                                        bg="#3a86ff", fg="white", command=self.show_best_path)
            self.canvas.create_window(1020, 250, anchor='nw', window=self.path_button)

        self.pause_button = tk.Button(self.root, text="Pause", font=("Arial", 12), command=self.pause_game)
        self.restart_button = tk.Button(self.root, text="Restart", font=("Arial", 12), command=self.restart_game)
        self.canvas.create_window(1020, 650, anchor='nw', window=self.pause_button)
        self.canvas.create_window(1100, 650, anchor='nw', window=self.restart_button)

        self.paused = False

        self.enable_click_debug()
        
        self.update_win_probabilities()

        if self.names[self.turn] == "Bot":
            self.roll_button.config(state="disabled")
            self.root.after(1000, self.roll_dice)

    def calculate_win_probability(self, player_idx):
        position = self.positions[player_idx]
        
        if position == 100:
            return 100.0
        
        base_prob = (position / 100) * 60  # Position
        
        if position >= 90:
            proximity_bonus = 25  
        elif position >= 75:
            proximity_bonus = 15  
        elif position >= 50:
            proximity_bonus = 5   
        else:
            proximity_bonus = 0
            
        # Shield bonus
        shield_bonus = self.shields[player_idx] * 2  
        
        #ladder
        ladder_bonus = 0
        for ladder_start, ladder_end in self.ladders.items():
            if position < ladder_start and ladder_start - position <= 6:  
                ladder_bonus += (ladder_end - ladder_start) / 10
        
        # Snake
        snake_penalty = 0
        for snake_start, snake_end in self.snakes.items():
            if position < snake_start and snake_start - position <= 6:  
                snake_penalty += (snake_start - snake_end) / 8
                
        # Power-up
        powerup_bonus = 0
        for powerup_pos, powerup_type in self.powerups.items():
            if position < powerup_pos and powerup_pos - position <= 6:  
                if powerup_type == "booster":
                    powerup_bonus += 3  
                elif powerup_type == "shield":
                    powerup_bonus += 2  
        
        # relative position compared to other players
        position_advantage = 0
        num_players = len(self.positions)
        for i in range(num_players):
            if i != player_idx:  
                if position > self.positions[i]:
                    position_advantage += 5  
                elif position < self.positions[i]:
                    position_advantage -= 3  
        
        probability = base_prob + proximity_bonus + shield_bonus + ladder_bonus - snake_penalty + powerup_bonus + position_advantage
        
        probability = max(0.1, min(99.9, probability))
        
        if self.mode == "bot" and player_idx == 0:  
            probability = min(probability * 1.05, 99.9)  
            
        return probability

    def update_win_probabilities(self):
        for i in range(len(self.names)):
            prob = self.calculate_win_probability(i)
            self.win_prob_labels[i].config(text=f"{self.names[i]}: {prob:.1f}%")
            
            if prob > 70:
                color = "#38b000"  
            elif prob > 40:
                color = "#fb8500"  
            else:
                color = "#d90429"  
                
            self.win_prob_labels[i].config(fg=color)

    def get_tile_xy(self, tile_number):
        if tile_number == 0:
            return 70, 650
        start_x_even = 150
        start_x_odd = 910
        start_y = 690
        w, h = 85, 75
        row = (tile_number - 1) // 10
        col = (tile_number - 1) % 10
        y = start_y - row * h
        x = (start_x_even + col * w) if row % 2 == 0 else (start_x_odd - col * w)
        return int(x), int(y)

    def animate_dice_roll(self, count):
        if count < 10:
            temp_val = random.randint(1, 6)
            self.canvas.itemconfig(self.current_dice, image=self.dice_imgs[temp_val - 1])
            self.root.after(100, lambda: self.animate_dice_roll(count + 1))  # continue animation
        else:
            current_pos = self.positions[self.turn]
            weights = [1, 1, 1, 1, 1, 1]

            if current_pos >= 94:
                weights[5] += 6
            elif current_pos >= 80:
                weights[5] += 4
            elif current_pos >= 60:
                weights[5] += 1

            total_weight = sum(weights)
            probabilities = [w / total_weight for w in weights]

            value = random.choices(range(1, 7), weights=probabilities, k=1)[0]

            self.canvas.itemconfig(self.current_dice, image=self.dice_imgs[value - 1])

            try:
                playsound("sound/move.wav", block=False)
            except:
                pass

            threading.Thread(target=self.animate_move, args=(value,), daemon=True).start()

    def roll_dice(self):
        if self.paused:
            return

        self.roll_button.config(state='disabled')
        self.animate_dice_roll(0)

    def animate_move(self, value, booster_chain=False):
        current = self.positions[self.turn]
        
        if current + value > 100:
            self.turn_label.config(text=f"{self.names[self.turn]} needs exact roll to win!")
            self.root.update()
            time.sleep(1)
            if not self.extra_turn_booster:
                self.turn = (self.turn + 1) % len(self.players)
                self.turn_label.config(text=f"{self.names[self.turn]}'s Turn")
                
                if self.names[self.turn] == "Bot":
                    self.roll_button.config(state="disabled")
                    self.root.after(1000, self.roll_dice)
                else:
                    self.roll_button.config(state="normal")
            else:
                self.extra_turn_booster = False
                self.roll_button.config(state="normal")
            return

        for step in range(1, value + 1):
            x, y = self.get_tile_xy(current + step)
            self.canvas.coords(self.token_ids[self.turn], x + self.turn * 20, y)
            self.root.update()
            time.sleep(0.2)

        new_pos = current + value
        self.positions[self.turn] = new_pos

        if new_pos in self.ladders:
            try:
                playsound("sound/ladder.wav", block=False)
            except:
                pass
            new_pos = self.ladders[new_pos]
            self.positions[self.turn] = new_pos
            x, y = self.get_tile_xy(new_pos)
            self.canvas.coords(self.token_ids[self.turn], x + self.turn * 20, y)
            self.root.update()
            time.sleep(0.5)

        elif new_pos in self.snakes:
            if self.shields[self.turn] > 0:
                self.shields[self.turn] -= 1
            else:
                try:
                    playsound("sound/snake.wav", block=False)
                except:
                    pass
                new_pos = self.snakes[new_pos]
                self.positions[self.turn] = new_pos
                x, y = self.get_tile_xy(new_pos)
                self.canvas.coords(self.token_ids[self.turn], x + self.turn * 20, y)
                self.root.update()
                time.sleep(0.5)

        if new_pos in self.powerups:
            power = self.powerups[new_pos]
            if power == "shield":
                self.shields[self.turn] = 3
                self.powerup_label.config(text="Power-Up: Shield (3 uses)")
            elif power == "booster":
                self.powerup_label.config(text="Power-Up: Booster (Rolling again...)")
                self.root.update()
                time.sleep(0.5)
                next_roll = random.randint(1, 6)
                self.canvas.itemconfig(self.current_dice, image=self.dice_imgs[next_roll - 1])
                try:
                    playsound("sound/move.wav", block=False)
                except:
                    pass
                self.animate_move(next_roll, booster_chain=True)
                return
        else:
            self.powerup_label.config(text="Power-Up: None")

        self.score_labels[self.turn].config(text=f"{self.names[self.turn]}: {self.positions[self.turn]}")
        
        self.update_win_probabilities()

        if self.positions[self.turn] == 100:
            self.roll_button.config(state='disabled')
            self.turn_label.config(text=f"{self.names[self.turn]} wins!")
            for i in range(len(self.names)):
                if i == self.turn:
                    self.win_prob_labels[i].config(text=f"{self.names[i]}: 100.0%", fg="#38b000")
                else:
                    self.win_prob_labels[i].config(text=f"{self.names[i]}: 0.0%", fg="#d90429")
            try:
                playsound("sound/win.wav", block=False)
            except:
                pass
            return

        if not self.extra_turn_booster:
            self.turn = (self.turn + 1) % len(self.players)
            self.turn_label.config(text=f"{self.names[self.turn]}'s Turn")

            if self.names[self.turn] == "Bot":
                self.roll_button.config(state="disabled")
                self.root.after(1000, self.roll_dice)
            else:
                self.roll_button.config(state="normal")
        else:
            self.extra_turn_booster = False
            self.roll_button.config(state="normal")

    def find_best_path(self, start_pos=0, target_pos=100):
        #Dijkstra's algorithm
        
        pq = [(0, start_pos, [])]
        visited = set()
        
        while pq:
            turns, pos, path = heapq.heappop(pq)
            
            if pos == target_pos:
                return path
            
            if pos in visited:
                continue
                
            visited.add(pos)
            
            for dice in range(1, 7):
                new_pos = pos + dice
                
                if new_pos > target_pos:
                    continue
                    
                if new_pos in self.ladders:
                    new_pos = self.ladders[new_pos]
                    new_path = path + [(dice, f"Roll {dice}, climb ladder to {new_pos}")]
                elif new_pos in self.snakes:
                    new_pos = self.snakes[new_pos]
                    new_path = path + [(dice, f"Roll {dice}, hit snake to {new_pos}")]
                elif new_pos in self.powerups:
                    powerup = self.powerups[new_pos]
                    if powerup == "booster":
                        bonus_roll = 3 
                        bonus_pos = new_pos + bonus_roll
                        
                        if bonus_pos in self.ladders:
                            bonus_pos = self.ladders[bonus_pos]
                            new_path = path + [(dice, f"Roll {dice}, get booster, roll {bonus_roll}, climb ladder to {bonus_pos}")]
                        elif bonus_pos in self.snakes:
                            bonus_pos = self.snakes[bonus_pos]
                            new_path = path + [(dice, f"Roll {dice}, get booster, roll {bonus_roll}, hit snake to {bonus_pos}")]
                        else:
                            new_path = path + [(dice, f"Roll {dice}, get booster, roll {bonus_roll} to {bonus_pos}")]
                        
                        new_pos = bonus_pos
                    else:  
                        new_path = path + [(dice, f"Roll {dice}, get shield at {new_pos}")]
                else:
                    new_path = path + [(dice, f"Roll {dice} to {new_pos}")]
                
                if new_pos not in visited:
                    expected_turns = turns + 1
                    heapq.heappush(pq, (expected_turns, new_pos, new_path))
        
        return []  

    def show_best_path(self):
        """Shows the best path in a modal window"""
        bot_index = 1
        start_pos = self.positions[bot_index]
        
        path = self.find_best_path(start_pos)
        
        path_window = Toplevel(self.root)
        path_window.title("Bot's Best Path to Win")
        
        window_width = 500
        window_height = 600
        x = int((self.root.winfo_screenwidth() / 2) - (window_width / 2))
        y = int((self.root.winfo_screenheight() / 2) - (window_height / 2))
        path_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        path_window.configure(bg="white")
        
        tk.Label(path_window, text=f"Shortest Best Path for {self.names[bot_index]} to Win", 
                font=("Arial", 16, "bold"), bg="white", fg="#3a0ca3").pack(pady=10)
        
        tk.Label(path_window, text=f"Current Position: {start_pos}", 
                font=("Arial", 14), bg="white").pack(pady=5)
        
        frame = tk.Frame(path_window, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        path_text = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                           font=("Arial", 12), bg="white", bd=0)
        path_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=path_text.yview)
        
        if path:
            path_text.insert(tk.END, "Recommended moves:\n\n")
            for i, (dice, description) in enumerate(path):
                path_text.insert(tk.END, f"Move {i+1}: {description}\n")
                
                if "climb ladder" in description:
                    path_text.tag_add(f"ladder{i}", f"{i+2}.0", f"{i+3}.0")
                    path_text.tag_config(f"ladder{i}", foreground="#38b000")
                elif "hit snake" in description:
                    path_text.tag_add(f"snake{i}", f"{i+2}.0", f"{i+3}.0")
                    path_text.tag_config(f"snake{i}", foreground="#d90429")
                elif "get booster" in description:
                    path_text.tag_add(f"booster{i}", f"{i+2}.0", f"{i+3}.0")
                    path_text.tag_config(f"booster{i}", foreground="#fb8500")
                elif "get shield" in description:
                    path_text.tag_add(f"shield{i}", f"{i+2}.0", f"{i+3}.0")
                    path_text.tag_config(f"shield{i}", foreground="#3a86ff")
            
            path_text.insert(tk.END, f"\nEstimated moves to win: {len(path)}")
            
            win_prob = self.calculate_win_probability(bot_index)
            path_text.insert(tk.END, f"\nCurrent Win Probability: {win_prob:.1f}%")
        else:
            path_text.insert(tk.END, "No optimal path found.")
        
        path_text.config(state=tk.DISABLED) 
        
        close_button = tk.Button(path_window, text="Close", font=("Arial", 14), 
                               bg="#fa5b61", fg="white", command=path_window.destroy)
        close_button.pack(pady=15)

    def pause_game(self):
        self.paused = not self.paused
        self.pause_button.config(text="Resume" if self.paused else "Pause")

    def restart_game(self):
        self.canvas.delete("all")
        self.select_mode()

if __name__ == "__main__":
    root = tk.Tk()
    app = SnakesLadders(root)
    root.mainloop()