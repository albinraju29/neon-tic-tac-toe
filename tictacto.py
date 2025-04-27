import pygame
import sys
import random
import time
import socket
import threading
import pickle
from pygame import mixer
from pygame import gfxdraw

# Initialize PyGame
pygame.init()
mixer.init()

# Screen setup with scaling
SCALE = 1.0
BASE_WIDTH, BASE_HEIGHT = 600, 700
WIDTH, HEIGHT = int(BASE_WIDTH * SCALE), int(BASE_HEIGHT * SCALE)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("NEON TIC TAC TOE")

# Colors (Neon Theme)
BLACK = (0, 0, 0)
DARK_BG = (10, 10, 20)
NEON_BLUE = (0, 200, 255)
NEON_PINK = (255, 0, 128)
NEON_PURPLE = (180, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
GLOW = (100, 255, 255)

# Font initialization function
def init_fonts(scale=1.0):
    fonts = {
        'title': pygame.font.SysFont('Arial', int(40 * scale)),
        'main': pygame.font.SysFont('Arial', int(30 * scale)),
        'status': pygame.font.SysFont('Arial', int(24 * scale)),
        'score': pygame.font.SysFont('Arial', int(20 * scale))
    }
    # Make fonts bold
    for font in fonts.values():
        font.set_bold(True)
    return fonts

fonts = init_fonts(SCALE)

# Sound setup
sound_enabled = True
try:
    mixer.music.load("music.mp3")
    move_sound = mixer.Sound("music.mp3")
    win_sound = mixer.Sound("gameover.mp3")
    mixer.music.set_volume(0.3)
    move_sound.set_volume(0.5)
    win_sound.set_volume(0.7)
except:
    print("Sound files not found! Continuing without sound.")
    sound_enabled = False

# Game variables
board = [["", "", ""], ["", "", ""], ["", "", ""]]
current_player = "X"
winner = None
game_mode = None  # 1: vs AI, 2: 2P, 3: Online
difficulty = "Hard"  # Easy, Medium, Hard
scores = {"X": 0, "O": 0, "Draw": 0}
last_move_time = 0
online_role = None  # "host" or "client"
connection = None
ip_address = ""
game_history = []
win_line = None

def check_winner():
    global win_line
    # Check rows
    for i, row in enumerate(board):
        if row[0] == row[1] == row[2] != "":
            win_line = ("row", i)
            return row[0]
    # Check columns
    for i in range(3):
        if board[0][i] == board[1][i] == board[2][i] != "":
            win_line = ("col", i)
            return board[0][i]
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != "":
        win_line = ("diag", 0)
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != "":
        win_line = ("diag", 1)
        return board[0][2]
    # Check draw
    if all(cell != "" for row in board for cell in row):
        return "Draw"
    win_line = None
    return None

def is_board_full(board):
    return all(cell != "" for row in board for cell in row)

def reset_game(full=False):
    global board, current_player, winner, win_line
    board = [["", "", ""], ["", "", ""], ["", "", ""]]
    current_player = "X"
    winner = None
    win_line = None
    if full:
        scores.update({"X": 0, "O": 0, "Draw": 0})

def random_move():
    available = [(row, col) for row in range(3) for col in range(3) if board[row][col] == ""]
    return random.choice(available) if available else None

def minimax(board, depth, is_maximizing):
    winner = check_winner()
    if winner == "O":
        return 1
    elif winner == "X":
        return -1
    elif is_board_full(board):
        return 0

    if is_maximizing:
        best_score = -float('inf')
        for row in range(3):
            for col in range(3):
                if board[row][col] == "":
                    board[row][col] = "O"
                    score = minimax(board, depth + 1, False)
                    board[row][col] = ""
                    best_score = max(score, best_score)
        return best_score
    else:
        best_score = float('inf')
        for row in range(3):
            for col in range(3):
                if board[row][col] == "":
                    board[row][col] = "X"
                    score = minimax(board, depth + 1, True)
                    board[row][col] = ""
                    best_score = min(score, best_score)
        return best_score

def minimax_ai_move():
    best_score = -float('inf')
    best_move = None
    for row in range(3):
        for col in range(3):
            if board[row][col] == "":
                board[row][col] = "O"
                score = minimax(board, 0, False)
                board[row][col] = ""
                if score > best_score:
                    best_score = score
                    best_move = (row, col)
    return best_move

def medium_ai_move():
    if random.random() > 0.5:
        return minimax_ai_move()
    return random_move()

def get_computer_move():
    # Show "AI thinking..." message
    thinking_text = fonts['status'].render("AI thinking...", True, NEON_BLUE)
    screen.blit(thinking_text, (WIDTH//2 - thinking_text.get_width()//2, HEIGHT//2))
    pygame.display.flip()
    
    time.sleep(0.8)  # Dramatic pause
    
    if difficulty == "Easy":
        return random_move()
    elif difficulty == "Medium":
        return medium_ai_move()
    else:
        return minimax_ai_move()

def draw_board():
    # Calculate cell dimensions
    cell_width = WIDTH // 3
    cell_height = (HEIGHT - 150) // 3
    
    # Vertical lines
    pygame.draw.line(screen, NEON_PURPLE, (cell_width, 100), (cell_width, HEIGHT-50), 3)
    pygame.draw.line(screen, NEON_PURPLE, (cell_width*2, 100), (cell_width*2, HEIGHT-50), 3)
    
    # Horizontal lines
    pygame.draw.line(screen, NEON_PURPLE, (0, 100 + cell_height), (WIDTH, 100 + cell_height), 3)
    pygame.draw.line(screen, NEON_PURPLE, (0, 100 + cell_height*2), (WIDTH, 100 + cell_height*2), 3)
    
    # Grid dots at intersections
    for i in range(1, 3):
        for j in range(1, 3):
            pygame.draw.circle(screen, NEON_PURPLE, (i*cell_width, 100 + j*cell_height), 5)
    
    # Draw winning line if there's a winner
    if win_line:
        line_type, index = win_line
        color = GREEN if winner != "Draw" else GRAY
        if line_type == "row":
            y = 100 + index * cell_height + cell_height // 2
            pygame.draw.line(screen, color, (50, y), (WIDTH-50, y), 5)
        elif line_type == "col":
            x = index * cell_width + cell_width // 2
            pygame.draw.line(screen, color, (x, 150), (x, HEIGHT-100), 5)
        elif line_type == "diag":
            if index == 0:  # Top-left to bottom-right
                pygame.draw.line(screen, color, (50, 150), (WIDTH-50, HEIGHT-100), 5)
            else:  # Top-right to bottom-left
                pygame.draw.line(screen, color, (WIDTH-50, 150), (50, HEIGHT-100), 5)

def draw_symbols():
    cell_width = WIDTH // 3
    cell_height = (HEIGHT - 150) // 3
    
    for row in range(3):
        for col in range(3):
            center_x = col * cell_width + cell_width // 2
            center_y = 100 + row * cell_height + cell_height // 2
            symbol = board[row][col]
            
            if symbol == "X":
                color = NEON_BLUE
                for glow in range(3, 0, -1):
                    alpha = 50 + glow * 50
                    glow_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
                    pygame.draw.line(glow_surface, (*color, alpha), (0, 0), (60, 60), glow)
                    pygame.draw.line(glow_surface, (*color, alpha), (60, 0), (0, 60), glow)
                    screen.blit(glow_surface, (center_x - 30, center_y - 30))
                pygame.draw.line(screen, color, (center_x - 25, center_y - 25), (center_x + 25, center_y + 25), 3)
                pygame.draw.line(screen, color, (center_x + 25, center_y - 25), (center_x - 25, center_y + 25), 3)
            
            elif symbol == "O":
                color = NEON_PINK
                for glow in range(3, 0, -1):
                    alpha = 50 + glow * 50
                    glow_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (*color, alpha), (30, 30), 30, glow)
                    screen.blit(glow_surface, (center_x - 30, center_y - 30))
                pygame.draw.circle(screen, color, (center_x, center_y), 25, 3)

def draw_status():
    if winner:
        message = f"{winner} wins!" if winner != "Draw" else "It's a Draw!"
        color = GREEN if winner != "Draw" else GRAY
        text = fonts['status'].render(message, True, color)
    else:
        text = fonts['status'].render(f"Player {current_player}'s turn", True, NEON_BLUE)
    
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 30))
    
    # Control hints
    controls = [
        ("Press Q to quit", WIDTH - 10, HEIGHT - 30, "right"),
        ("Press R to reset", 10, HEIGHT - 30, "left"),
        ("ESC to menu", WIDTH//2, HEIGHT - 30, "center")
    ]
    
    for text, x, y, align in controls:
        rendered = fonts['score'].render(text, True, NEON_PURPLE)
        if align == "right":
            pos = (x - rendered.get_width(), y)
        elif align == "center":
            pos = (x - rendered.get_width()//2, y)
        else:
            pos = (x, y)
        screen.blit(rendered, pos)

def draw_scores():
    score_text = fonts['score'].render(f"X: {scores['X']}  |  O: {scores['O']}  |  Draws: {scores['Draw']}", True, NEON_PURPLE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 70))

def draw_main_menu():
    screen.fill(DARK_BG)
    
    # Animated background elements
    for _ in range(20):
        pos = (random.randint(0, WIDTH), random.randint(0, HEIGHT))
        pygame.draw.circle(screen, (*NEON_BLUE[:3], 50), pos, 3)
    
    # Title with glow effect
    title = fonts['title'].render("NEON TIC TAC TOE", True, NEON_BLUE)
    for glow in range(5, 0, -1):
        title_glow = fonts['title'].render("NEON TIC TAC TOE", True, (*NEON_BLUE, glow * 20))
        screen.blit(title_glow, (WIDTH//2 - title.get_width()//2 + random.randint(-1, 1), 
                                50 + random.randint(-1, 1)))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    # Menu options
    options = [
        ("1 - VS AI", 200, NEON_PURPLE),
        ("2 - 2 PLAYERS", 250, NEON_PURPLE),
        ("3 - ONLINE MATCH", 300, NEON_PURPLE)
    ]
    
    for text, y, color in options:
        text_surface = fonts['main'].render(text, True, color)
        for glow in range(3, 0, -1):
            glow_surface = fonts['main'].render(text, True, (*color, glow * 30))
            screen.blit(glow_surface, (WIDTH//2 - text_surface.get_width()//2, y))
        screen.blit(text_surface, (WIDTH//2 - text_surface.get_width()//2, y))
    
    pygame.display.flip()

def draw_difficulty_menu():
    screen.fill(DARK_BG)
    title = fonts['title'].render("SELECT DIFFICULTY", True, NEON_BLUE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    options = [
        ("1 - EASY", 200, NEON_PURPLE),
        ("2 - MEDIUM", 250, NEON_PURPLE),
        ("3 - HARD", 300, NEON_PURPLE)
    ]
    
    for text, y, color in options:
        text_surface = fonts['main'].render(text, True, color)
        screen.blit(text_surface, (WIDTH//2 - text_surface.get_width()//2, y))
    
    pygame.display.flip()

def draw_online_menu():
    screen.fill(DARK_BG)
    title = fonts['title'].render("ONLINE SETUP", True, NEON_BLUE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    options = [
        ("1 - HOST GAME", 200, NEON_PURPLE),
        ("2 - JOIN GAME", 250, NEON_PURPLE),
        (f"IP: {ip_address}", 350, NEON_BLUE if ip_address else GRAY)
    ]
    
    for text, y, color in options:
        text_surface = fonts['main'].render(text, True, color)
        screen.blit(text_surface, (WIDTH//2 - text_surface.get_width()//2, y))
    
    pygame.display.flip()

def play_sound(sound, override=False):
    if not sound_enabled and not override:
        return
    channel = mixer.find_channel(True)
    channel.set_volume(0.5 if sound == move_sound else 1.0)
    channel.play(sound)

def start_server():
    global connection, online_role
    online_role = "host"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 5555))
    server_socket.listen(1)
    
    # Show waiting message
    waiting_text = fonts['main'].render("Waiting for connection on port 5555...", True, NEON_BLUE)
    screen.blit(waiting_text, (WIDTH//2 - waiting_text.get_width()//2, HEIGHT//2))
    pygame.display.flip()
    
    connection, _ = server_socket.accept()
    threading.Thread(target=receive_data, daemon=True).start()

def connect_to_server(ip):
    global connection, online_role, ip_address
    online_role = "client"
    ip_address = ip
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if not all(part.isdigit() for part in ip.split('.')) or len(ip.split('.')) != 4:
            raise ValueError("Invalid IP format")
        
        # Show connecting message
        connecting_text = fonts['main'].render(f"Connecting to {ip}...", True, NEON_BLUE)
        screen.blit(connecting_text, (WIDTH//2 - connecting_text.get_width()//2, HEIGHT//2))
        pygame.display.flip()
        
        connection.connect((ip, 5555))
        threading.Thread(target=receive_data, daemon=True).start()
        return True
    except Exception as e:
        error_text = fonts['main'].render(f"Error: {str(e)}", True, NEON_PINK)
        screen.blit(error_text, (WIDTH//2 - error_text.get_width()//2, HEIGHT//2 + 50))
        pygame.display.flip()
        time.sleep(2)
        return False

def receive_data():
    global board, current_player, winner
    while True:
        try:
            data = connection.recv(1024).decode()
            if not data:
                break
            row, col = map(int, data.split(","))
            board[row][col] = "O"
            winner = check_winner()
            current_player = "X"
        except Exception as e:
            print(f"Connection error: {e}")
            break

def save_game():
    try:
        with open('savegame.dat', 'wb') as f:
            pickle.dump({
                'board': board,
                'scores': scores,
                'difficulty': difficulty,
                'game_mode': game_mode,
                'current_player': current_player
            }, f)
        return True
    except:
        return False

def load_game():
    try:
        with open('savegame.dat', 'rb') as f:
            data = pickle.load(f)
            global board, scores, difficulty, game_mode, current_player
            board = data['board']
            scores = data['scores']
            difficulty = data['difficulty']
            game_mode = data['game_mode']
            current_player = data['current_player']
        return True
    except:
        return False

def main():
    global current_player, winner, game_mode, difficulty, online_role, connection, ip_address, WIDTH, HEIGHT, SCALE, fonts
    
    if sound_enabled:
        mixer.music.play(-1)
    
    # Game state machine
    current_screen = "main_menu"
    clock = pygame.time.Clock()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption('Tic Tac Toe')

    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.VIDEORESIZE:
                SCALE = min(event.w/BASE_WIDTH, event.h/BASE_HEIGHT)
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                fonts = init_fonts(SCALE)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                
                if current_screen == "main_menu":
                    if event.key == pygame.K_1:
                        game_mode = 1
                        current_screen = "difficulty_menu"
                    elif event.key == pygame.K_2:
                        game_mode = 2
                        reset_game()
                        current_screen = "game"
                    elif event.key == pygame.K_3:
                        game_mode = 3
                        current_screen = "online_menu"
                    elif event.key == pygame.K_l:
                        if load_game():
                            current_screen = "game"
                
                elif current_screen == "difficulty_menu":
                    if event.key == pygame.K_1:
                        difficulty = "Easy"
                        reset_game()
                        current_screen = "game"
                    elif event.key == pygame.K_2:
                        difficulty = "Medium"
                        reset_game()
                        current_screen = "game"
                    elif event.key == pygame.K_3:
                        difficulty = "Hard"
                        reset_game()
                        current_screen = "game"
                    elif event.key == pygame.K_ESCAPE:
                        current_screen = "main_menu"
                
                elif current_screen == "online_menu":
                    if event.key == pygame.K_1:
                        online_role = "host"
                        threading.Thread(target=start_server, daemon=True).start()
                        reset_game()
                        current_screen = "game"
                    elif event.key == pygame.K_2:
                        ip = input("Enter host IP: ")  # In a real app, use a text input box
                        if connect_to_server(ip):
                            reset_game()
                            current_screen = "game"
                    elif event.key == pygame.K_ESCAPE:
                        current_screen = "main_menu"
                
                elif current_screen == "game":
                    if event.key == pygame.K_r:
                        reset_game()
                    elif event.key == pygame.K_s:
                        if save_game():
                            saved_text = fonts['status'].render("Game saved!", True, GREEN)
                            screen.blit(saved_text, (WIDTH//2 - saved_text.get_width()//2, HEIGHT//2))
                            pygame.display.flip()
                            time.sleep(1)
                    elif event.key == pygame.K_ESCAPE:
                        current_screen = "main_menu"
            
            elif event.type == pygame.MOUSEBUTTONDOWN and current_screen == "game" and not winner:
                if current_player == "X":
                    x, y = event.pos
                    if 100 <= y <= HEIGHT - 100:
                        row = (y - 100) // ((HEIGHT - 150) // 3)
                        col = x // (WIDTH // 3)
                        if 0 <= row < 3 and 0 <= col < 3 and board[row][col] == "":
                            board[row][col] = "X"
                            play_sound(move_sound)
                            winner = check_winner()
                            if winner:
                                scores[winner] += 1
                                play_sound(win_sound)
                                game_history.append({
                                    'date': time.strftime("%Y-%m-%d %H:%M"),
                                    'winner': winner,
                                    'moves': sum(1 for row in board for cell in row if cell != ""),
                                    'difficulty': difficulty if game_mode == 1 else None
                                })
                            elif game_mode == 1:  # AI move
                                move = get_computer_move()
                                if move:
                                    row, col = move
                                    board[row][col] = "O"
                                    play_sound(move_sound)
                                    winner = check_winner()
                                    if winner:
                                        scores[winner] += 1
                                        play_sound(win_sound)
                                        game_history.append({
                                            'date': time.strftime("%Y-%m-%d %H:%M"),
                                            'winner': winner,
                                            'moves': sum(1 for row in board for cell in row if cell != ""),
                                            'difficulty': difficulty
                                        })
                            elif game_mode == 3 and connection:  # Online
                                try:
                                    connection.send(f"{row},{col}".encode())
                                except:
                                    print("Connection error")
        
        # Drawing
        screen.fill(DARK_BG)
        
        if current_screen == "main_menu":
            draw_main_menu()
        elif current_screen == "difficulty_menu":
            draw_difficulty_menu()
        elif current_screen == "online_menu":
            draw_online_menu()
        elif current_screen == "game":
            draw_board()
            draw_symbols()
            draw_status()
            draw_scores()
        
        # Debug info (can be removed in production)
        debug_info = [
            f"FPS: {int(clock.get_fps())}",
            f"Mode: {game_mode}",
            f"Online: {online_role}"
        ]
        for i, text in enumerate(debug_info):
            debug_text = fonts['score'].render(text, True, NEON_BLUE)
            screen.blit(debug_text, (10, 10 + i*20))
        
        pygame.display.flip()
        clock.tick(60)  # Limit to 60 FPS
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()