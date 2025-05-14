import tkinter as tk
from PIL import Image, ImageTk
import random
import threading
from playsound import playsound
import time

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
            self.start_game(mode="bot")
        elif 250 < x < 420 and 440 < y < 480:
            self.start_game(mode="multi")

    def enable_click_debug(self):
        self.canvas.bind("<Button-1>", self.print_click_position)

    def print_click_position(self, event):
        print(f"Mouse clicked at: ({event.x}, {event.y})")

    def start_game(self, mode):
        self.canvas.delete("all")
        self.canvas.unbind("<Button-1>")

        board_img = Image.open("img/board1.png").resize((1000, 800))
        self.board_tk = ImageTk.PhotoImage(board_img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.board_tk)

        self.players, self.token_ids, self.positions, self.shields, self.names = [], [], [], [], []

        self.mode = mode

        if mode == "bot":
            imgs = ["img/player-1.png", "img/botPlayer.png"]
            self.names = ["Player 1", "Bot"]
        else:
            imgs = ["img/player-1.png", "img/player-2.png", "img/player-3.png"]
            self.names = ["Player 1", "Player 2", "Player 3"]

        for i, img_path in enumerate(imgs):
            img = ImageTk.PhotoImage(Image.open(img_path).resize((50, 50)))
            token = self.canvas.create_image(50, 690 + i * 40, anchor='nw', image=img)
            self.players.append(img)
            self.token_ids.append(token)
            self.positions.append(0)
            self.shields.append(0)

        self.snakes = {
            99: 42,   # Long snake from top left to middle right
            92: 70,   # Snake in top-left area
            47: 28,   # Snake in middle right
            37: 4,   # Snake in middle left
            86: 56,   # Medium ladder in middle-right
            }  
              
        self.ladders = {
            9: 32,    # Ladder from bottom left going up
            23: 57,   # Ladder at bottom right
            45: 77,   # Long ladder from second row to middle
            53: 88,   # Medium ladder in middle-right
        }
        
        self.powerups = {2: "booster", 25: "booster", 40: "shield", 52: "shield", 64: "booster", 83: "shield",87: "booster" }

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

        # Add win probability labels
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

        self.pause_button = tk.Button(self.root, text="Pause", font=("Arial", 12), command=self.pause_game)
        self.restart_button = tk.Button(self.root, text="Restart", font=("Arial", 12), command=self.restart_game)
        self.canvas.create_window(1020, 650, anchor='nw', window=self.pause_button)
        self.canvas.create_window(1100, 650, anchor='nw', window=self.restart_button)

        self.paused = False

        self.enable_click_debug()
        
        # Calculate initial win probabilities
        self.update_win_probabilities()

        if self.names[self.turn] == "Bot":
            self.roll_button.config(state="disabled")
            self.root.after(1000, self.roll_dice)

    def calculate_win_probability(self, player_idx):
        """Calculate the win probability for a specific player based on various factors"""
        # Base probability based on position (closer to 100 = higher chance)
        position = self.positions[player_idx]
        
        # If someone has already won, give them 100%
        if position == 100:
            return 100.0
        
        # Base probability from position
        base_prob = (position / 100) * 60  # Position gives up to 60% probability
        
        # Adjust for proximity to finish line
        if position >= 90:
            proximity_bonus = 25  # Big boost when very close
        elif position >= 75:
            proximity_bonus = 15  # Solid advantage
        elif position >= 50:
            proximity_bonus = 5   # Small advantage
        else:
            proximity_bonus = 0
            
        # Shield bonus
        shield_bonus = self.shields[player_idx] * 2  # Each shield adds 2%
        
        # Proximity to ladders bonus (check if player is close to ladders)
        ladder_bonus = 0
        for ladder_start, ladder_end in self.ladders.items():
            if position < ladder_start and ladder_start - position <= 6:  # Within dice roll of ladder
                # The longer the ladder, the bigger the bonus
                ladder_bonus += (ladder_end - ladder_start) / 10
        
        # Snake risk (penalize if player is close to snakes)
        snake_penalty = 0
        for snake_start, snake_end in self.snakes.items():
            if position < snake_start and snake_start - position <= 6:  # Within dice roll of snake
                # The longer the snake drop, the bigger the penalty
                snake_penalty += (snake_start - snake_end) / 8
                
        # Power-up potential
        powerup_bonus = 0
        for powerup_pos, powerup_type in self.powerups.items():
            if position < powerup_pos and powerup_pos - position <= 6:  # Within dice roll
                if powerup_type == "booster":
                    powerup_bonus += 3  # Boosters are valuable
                elif powerup_type == "shield":
                    powerup_bonus += 2  # Shields are good too
        
        # Calculate relative position compared to other players
        position_advantage = 0
        num_players = len(self.positions)
        for i in range(num_players):
            if i != player_idx:  # Don't compare with self
                if position > self.positions[i]:
                    position_advantage += 5  # Bonus for being ahead of others
                elif position < self.positions[i]:
                    position_advantage -= 3  # Penalty for being behind
        
        # Calculate final probability
        probability = base_prob + proximity_bonus + shield_bonus + ladder_bonus - snake_penalty + powerup_bonus + position_advantage
        
        # Normalize probability (keep between 0 and 100)
        probability = max(0.1, min(99.9, probability))
        
        # If we're in bot mode, slightly adjust probability for dramatic effect
        if self.mode == "bot" and player_idx == 0:  # Player 1 (human)
            probability = min(probability * 1.05, 99.9)  # Give slight boost to human player for excitement
            
        return probability

    def update_win_probabilities(self):
        """Update win probability displays for all players"""
        for i in range(len(self.names)):
            prob = self.calculate_win_probability(i)
            self.win_prob_labels[i].config(text=f"{self.names[i]}: {prob:.1f}%")
            
            # Change color based on probability
            if prob > 70:
                color = "#38b000"  # High chance - green
            elif prob > 40:
                color = "#fb8500"  # Medium chance - orange
            else:
                color = "#d90429"  # Low chance - red
                
            self.win_prob_labels[i].config(fg=color)

    def get_tile_xy(self, tile_number):
        if tile_number == 0:
            return 70, 650
        start_x_even = 150
        start_x_odd = 915
        start_y = 690
        w, h = 90, 75
        row = (tile_number - 1) // 10
        col = (tile_number - 1) % 10
        y = start_y - row * h
        x = (start_x_even + col * w) if row % 2 == 0 else (start_x_odd - col * w)
        return int(x), int(y)

    def animate_dice_roll(self, count):
        if count < 10:
            # Shuffle random dice face
            temp_val = random.randint(1, 6)
            self.canvas.itemconfig(self.current_dice, image=self.dice_imgs[temp_val - 1])
            self.root.after(100, lambda: self.animate_dice_roll(count + 1))  # continue animation
        else:
            current_pos = self.positions[self.turn]
            weights = [1, 1, 1, 1, 1, 1]

            if current_pos >= 94:
                weights[5] += 5
            elif current_pos >= 80:
                weights[5] += 3
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

        # Start dice shuffle animation
        self.animate_dice_roll(0)


    def animate_move(self, value, booster_chain=False):
        current = self.positions[self.turn]

        for step in range(1, value + 1):
            if current + step > 100:
                break
            x, y = self.get_tile_xy(current + step)
            self.canvas.coords(self.token_ids[self.turn], x + self.turn * 20, y)
            self.root.update()
            time.sleep(0.2)

        new_pos = min(current + value, 100)
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
        
        # Update win probabilities after move
        self.update_win_probabilities()

        if self.positions[self.turn] == 100:
            self.roll_button.config(state='disabled')
            self.turn_label.config(text=f"{self.names[self.turn]} wins!")
            # Set win probabilities to reflect winner
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

        # Handle turn transition
        if not self.extra_turn_booster:
            # Regular turn change - move to next player
            self.turn = (self.turn + 1) % len(self.players)
            self.turn_label.config(text=f"{self.names[self.turn]}'s Turn")

            if self.names[self.turn] == "Bot":
                self.roll_button.config(state="disabled")
                self.root.after(1000, self.roll_dice)
            else:
                self.roll_button.config(state="normal")
        else:
            # If player had a booster, they already have the roll button enabled
            # Just reset the booster flag
            self.extra_turn_booster = False



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