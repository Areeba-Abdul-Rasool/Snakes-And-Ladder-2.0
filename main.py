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

        self.window_width = 1200
        self.window_height = 800

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

    def start_game(self, mode):
        self.canvas.delete("all")
        self.canvas.unbind("<Button-1>")

        board_img = Image.open("img/board1.png").resize((1000, 800))
        self.board_tk = ImageTk.PhotoImage(board_img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.board_tk)

        self.players, self.token_ids, self.positions, self.shields, self.names = [], [], [], [], []

        if mode == "bot":
            imgs = ["img/player-1.png", "img/botPlayer.png"]
            self.names = ["Player 1", "Bot"]
        else:
            imgs = ["img/player-1.png", "img/player-2.png", "img/player-3.png"]
            self.names = ["Player 1", "Player 2", "Player 3"]

        for i, img_path in enumerate(imgs):
            img = ImageTk.PhotoImage(Image.open(img_path).resize((40, 40)))
            token = self.canvas.create_image(20, 720 + i * 40, anchor='nw', image=img)
            self.players.append(img)
            self.token_ids.append(token)
            self.positions.append(0)
            self.shields.append(0)

        self.snakes = {22: 3, 47: 15, 86: 65, 88: 51, 99: 38}
        self.ladders = {4: 38, 10: 32, 36: 75, 68: 74}
        self.powerups = {12: "shield", 16: "booster", 39: "booster", 43: "shield", 54: "shield", 85: "shield", 97: "booster"}

        self.dice_imgs = [ImageTk.PhotoImage(Image.open(f"img/dice/{i}.png").resize((80, 80))) for i in range(1, 7)]
        self.current_dice = self.canvas.create_image(1020, 100, anchor='nw', image=self.dice_imgs[0])

        self.turn = 0

        self.turn_label = tk.Label(self.root, text=f"{self.names[self.turn]}'s Turn", font=("Arial", 16, "bold"), fg="#fa5b61", bg="white")
        self.canvas.create_window(1020, 50, anchor='nw', window=self.turn_label)

        self.score_labels = []
        for i, name in enumerate(self.names):
            label = tk.Label(self.root, text=f"{name}: 0", font=("Arial", 12), bg="white", fg="black")
            self.canvas.create_window(1020, 400 + i * 30, anchor='nw', window=label)
            self.score_labels.append(label)

        self.roll_button = tk.Button(self.root, text="Roll Dice", font=("Arial", 14, "bold"), bg="#fa5b61", fg="white", command=self.roll_dice)
        self.canvas.create_window(1020, 200, anchor='nw', window=self.roll_button)

        self.pause_button = tk.Button(self.root, text="Pause", font=("Arial", 12), command=self.pause_game)
        self.restart_button = tk.Button(self.root, text="Restart", font=("Arial", 12), command=self.restart_game)
        self.canvas.create_window(1020, 600, anchor='nw', window=self.pause_button)
        self.canvas.create_window(1100, 600, anchor='nw', window=self.restart_button)

        self.paused = False

    def get_tile_xy(self, tile_number):
        if tile_number == 0:
            return 20, 720
        start_x_even = 150
        start_x_odd = 820
        start_y = 712
        w, h = 71, 72
        row = (tile_number - 1) // 10
        col = (tile_number - 1) % 10
        y = start_y - row * h
        x = (start_x_even + col * w) if row % 2 == 0 else (start_x_odd - col * w)
        return int(x), int(y)

    def roll_dice(self):
        if self.paused:
            return

        value = random.randint(1, 6)
        self.canvas.itemconfig(self.current_dice, image=self.dice_imgs[value - 1])
        playsound("sound/move.wav", block=False)
        threading.Thread(target=self.animate_move, args=(value,), daemon=True).start()

    def animate_move(self, value):
        current = self.positions[self.turn]
        for step in range(1, value + 1):
            if current + step > 100:
                break
            x, y = self.get_tile_xy(current + step)
            self.canvas.coords(self.token_ids[self.turn], x + self.turn * 20, y)
            time.sleep(0.2)

        new_pos = min(current + value, 100)

        if new_pos in self.ladders:
            playsound("sound/ladder.wav", block=False)
            new_pos = self.ladders[new_pos]

        elif new_pos in self.snakes:
            if self.shields[self.turn] > 0:
                self.shields[self.turn] -= 1
            else:
                playsound("sound/snake.wav", block=False)
                new_pos = self.snakes[new_pos]

        if new_pos in self.powerups:
            power = self.powerups[new_pos]
            if power == "shield":
                self.shields[self.turn] = 3
            elif power == "booster":
                time.sleep(0.5)
                self.animate_move(random.randint(1, 6))
                return

        self.positions[self.turn] = new_pos
        x, y = self.get_tile_xy(new_pos)
        self.canvas.coords(self.token_ids[self.turn], x + self.turn * 20, y)
        self.score_labels[self.turn].config(text=f"{self.names[self.turn]}: {new_pos}")

        if new_pos == 100:
            self.turn_label.config(text=f"🎉 {self.names[self.turn]} Wins!")
            self.roll_button.config(state='disabled')
            return

        self.turn = (self.turn + 1) % len(self.players)
        self.turn_label.config(text=f"{self.names[self.turn]}'s Turn")

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