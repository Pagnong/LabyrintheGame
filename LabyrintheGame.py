import pygame
import random
import time
import sys
from collections import deque

# Initialisation de Pygame
pygame.init()

# Constantes
CELL_SIZE = 40
MINI_MAP_CELL_SIZE = 5

PLAYER_RADIUS = 15
WALL_COLOR = (0, 0, 0)
PATH_COLOR = (255, 255, 255)

PLAYER_COLOR = (0, 255, 0)  # ✅ Joueur VERT
EXIT_COLOR = (255, 0, 0)    # ✅ Sortie ROUGE
START_COLOR = (0, 200, 0)   # ✅ Position de départ VERTE

VISITED_COLOR = (200, 200, 255)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER_COLOR = (120, 120, 220)
TEXT_COLOR = (255, 255, 255)
UI_BG_COLOR = (70, 70, 70)
DFS_PATH_COLOR = (255, 100, 100)  # ✅ Couleur pour les chemins DFS
BFS_PATH_COLOR = (100, 100, 255)  # ✅ Couleur pour le chemin BFS

# Difficultés
DIFFICULTIES = {
    "Facile": {"width": 15, "height": 15, "view_range": 5},
    "Moyen": {"width": 35, "height": 35, "view_range": 3},
    "Difficile": {"width": 55, "height": 55, "view_range": 2}
}

class MazeGenerator:
    def __init__(self, width, height, difficulty):
        self.width = width
        self.height = height
        self.difficulty = difficulty
        self.maze = [[1 for _ in range(width)] for _ in range(height)]
        
    def generate(self):
        start_x, start_y = 1, 1
        self.maze[start_y][start_x] = 0
        
        stack = [(start_x, start_y)]
        
        while stack:
            current_x, current_y = stack[-1]
            
            neighbors = []
            for dx, dy in [(0, -2), (2, 0), (0, 2), (-2, 0)]:
                nx, ny = current_x + dx, current_y + dy
                if 0 < nx < self.width - 1 and 0 < ny < self.height - 1 and self.maze[ny][nx] == 1:
                    neighbors.append((nx, ny, dx, dy))
            
            if neighbors:
                nx, ny, dx, dy = random.choice(neighbors)
                
                self.maze[current_y + dy//2][current_x + dx//2] = 0
                self.maze[ny][nx] = 0
                
                stack.append((nx, ny))
            else:
                stack.pop()
        
        # Ajouter des chemins supplémentaires selon la difficulté
        if self.difficulty == "Moyen":
            self._add_alternative_paths(2)  # 2 chemins pour le niveau moyen
        elif self.difficulty == "Difficile":
            self._add_alternative_paths(3)  # 3 chemins pour le niveau difficile
        
        self.maze[1][0] = 0
        self.maze[self.height-2][self.width-1] = 0
        
        return self.maze
    
    def _add_alternative_paths(self, num_paths):
        """Ajoute des chemins alternatifs selon le nombre spécifié"""
        paths_created = 0
        max_attempts = 100  # Éviter les boucles infinies
        
        for attempt in range(max_attempts):
            if paths_created >= num_paths:
                break
                
            # Choisir un point aléatoire dans le labyrinthe qui est un mur
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            
            # Vérifier si c'est un mur et s'il peut créer un nouveau chemin
            if self.maze[y][x] == 1 and self._can_create_path(x, y):
                self.maze[y][x] = 0
                paths_created += 1
                
                # Pour les niveaux difficiles, ajouter aussi des connections autour
                if num_paths >= 3 and random.random() < 0.3:
                    for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if (0 < nx < self.width - 1 and 0 < ny < self.height - 1 and 
                            self.maze[ny][nx] == 1 and self._can_create_path(nx, ny)):
                            self.maze[ny][nx] = 0
    
    def _can_create_path(self, x, y):
        """Vérifie si créer un chemin à cette position créerait une boucle ou un nouveau chemin"""
        # Compter les chemins adjacents
        adjacent_paths = 0
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height and self.maze[ny][nx] == 0:
                adjacent_paths += 1
        
        # Un mur peut être cassé s'il connecte exactement 2 chemins (créerait une boucle)
        # ou s'il connecte 1 chemin (créerait un cul-de-sac)
        return adjacent_paths >= 1

class MazeGame:
    def __init__(self):
        self.screen = None
        self.clock = pygame.time.Clock()
        self.difficulty = None
        self.maze = None
        self.player_pos = None
        self.start_time = None
        self.moves = 0
        self.show_full_map = False
        self.game_over = False
        self.visited = set()
        self.fullscreen = False
        self.base_cell_size = CELL_SIZE
        self.show_dfs_paths = False  # ✅ Nouvelle variable pour afficher les chemins DFS
        self.dfs_paths = []  # ✅ Stocke les chemins trouvés par DFS
        self.show_bfs_path = False  # ✅ Nouvelle variable pour afficher le chemin BFS
        self.bfs_path = []  # ✅ Stocke le chemin trouvé par BFS
        
    def select_difficulty(self):
        temp_screen = pygame.display.set_mode((400, 300), pygame.RESIZABLE)
        pygame.display.set_caption("Sélection de la difficulté")
        
        font = pygame.font.SysFont(None, 36)
        title_font = pygame.font.SysFont(None, 48)
        
        buttons = []
        for i, difficulty in enumerate(DIFFICULTIES.keys()):
            buttons.append({
                "text": difficulty,
                "rect": pygame.Rect(100, 100 + i * 60, 200, 50),
                "difficulty": difficulty
            })
        
        running = True
        while running:
            temp_screen.fill((50, 50, 50))
            
            title = title_font.render("Sélectionnez la difficulté", True, TEXT_COLOR)
            temp_screen.blit(title, (400//2 - title.get_width()//2, 30))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        self.toggle_fullscreen()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for button in buttons:
                        if button["rect"].collidepoint(mouse_pos):
                            self.difficulty = button["difficulty"]
                            running = False
            
            for button in buttons:
                color = BUTTON_HOVER_COLOR if button["rect"].collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
                pygame.draw.rect(temp_screen, color, button["rect"], border_radius=10)
                text = font.render(button["text"], True, TEXT_COLOR)
                temp_screen.blit(text, (button["rect"].centerx - text.get_width()//2, 
                                       button["rect"].centery - text.get_height()//2))
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            config = DIFFICULTIES[self.difficulty]
            window_width = min(config["width"] * self.base_cell_size, 1200)
            window_height = min(config["height"] * self.base_cell_size, 800) + 80
            self.screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
        
        pygame.display.set_caption(f"Labyrinthe - {self.difficulty}")
    
    def calculate_cell_size(self):
        if not self.screen or not self.maze:
            return self.base_cell_size
            
        config = DIFFICULTIES[self.difficulty]
        maze_width = config["width"]
        maze_height = config["height"]
        
        available_width = self.screen.get_width()
        available_height = self.screen.get_height() - 80
        
        max_cell_width = available_width // maze_width
        max_cell_height = available_height // maze_height
        
        cell_size = min(max_cell_width, max_cell_height, self.base_cell_size)
        return max(cell_size, 10)
    
    def generate_maze(self):
        config = DIFFICULTIES[self.difficulty]
        generator = MazeGenerator(config["width"], config["height"], self.difficulty)
        self.maze = generator.generate()
        self.player_pos = [1, 1]
        self.start_time = time.time()
        self.moves = 0
        self.show_full_map = False
        self.game_over = False
        self.visited = set()
        self.visited.add((self.player_pos[1], self.player_pos[0]))
        self.show_dfs_paths = False  # ✅ Réinitialiser l'affichage DFS
        self.dfs_paths = []  # ✅ Réinitialiser les chemins DFS
        self.show_bfs_path = False  # ✅ Réinitialiser l'affichage BFS
        self.bfs_path = []  # ✅ Réinitialiser le chemin BFS
        
        self.view_range = config["view_range"]
        window_width = min(config["width"] * self.base_cell_size, 1200)
        window_height = min(config["height"] * self.base_cell_size, 800) + 80
        
        self.screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
        pygame.display.set_caption(f"Labyrinthe - {self.difficulty}")
    
    def find_all_paths_dfs(self):
        """✅ Trouve tous les chemins possibles de la position actuelle à la sortie en utilisant DFS"""
        config = DIFFICULTIES[self.difficulty]
        start = (self.player_pos[1], self.player_pos[0])  # (y, x)
        goal = (config["height"] - 2, config["width"] - 1)  # Position de la sortie
        
        all_paths = []
        visited = set()
        
        def dfs(current, path):
            if current == goal:
                all_paths.append(path[:])
                return
            
            visited.add(current)
            y, x = current
            
            # Directions: haut, droite, bas, gauche
            for dy, dx in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                ny, nx = y + dy, x + dx
                next_pos = (ny, nx)
                
                if (0 <= ny < config["height"] and 0 <= nx < config["width"] and 
                    self.maze[ny][nx] == 0 and next_pos not in visited):
                    path.append(next_pos)
                    dfs(next_pos, path)
                    path.pop()
            
            visited.remove(current)
        
        dfs(start, [start])
        return all_paths
    
    def find_shortest_path_bfs(self):
        """✅ Trouve le chemin le plus court de la position actuelle à la sortie en utilisant BFS"""
        config = DIFFICULTIES[self.difficulty]
        start = (self.player_pos[1], self.player_pos[0])  # (y, x)
        goal = (config["height"] - 2, config["width"] - 1)  # Position de la sortie
        
        # Si on est déjà à la sortie
        if start == goal:
            return [start]
        
        queue = deque([start])
        visited = {start}
        parent = {start: None}
        
        while queue:
            current = queue.popleft()
            y, x = current
            
            if current == goal:
                # Reconstruire le chemin à partir du goal
                path = []
                while current is not None:
                    path.append(current)
                    current = parent[current]
                return path[::-1]  # Inverser pour avoir start -> goal
            
            # Explorer les voisins
            for dy, dx in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                ny, nx = y + dy, x + dx
                neighbor = (ny, nx)
                
                if (0 <= ny < config["height"] and 0 <= nx < config["width"] and 
                    self.maze[ny][nx] == 0 and neighbor not in visited):
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
        
        return []  # Aucun chemin trouvé
    
    def draw_maze(self):
        config = DIFFICULTIES[self.difficulty]
        width, height = config["width"], config["height"]
        
        cell_size = self.calculate_cell_size()
        player_radius = max(cell_size // 3, 5)
        
        self.screen.fill((50, 50, 50))
        
        game_area_top = 40
        game_area_height = self.screen.get_height() - 80
        
        if self.show_full_map:
            total_maze_width = width * cell_size
            total_maze_height = height * cell_size
            
            offset_x = (self.screen.get_width() - total_maze_width) // 2
            offset_y = game_area_top + (game_area_height - total_maze_height) // 2
            
            for y in range(height):
                for x in range(width):
                    rect = pygame.Rect(
                        x * cell_size + offset_x,
                        y * cell_size + offset_y,
                        cell_size,
                        cell_size
                    )
                    if self.maze[y][x] == 1:
                        pygame.draw.rect(self.screen, WALL_COLOR, rect)
                    else:
                        pygame.draw.rect(self.screen, PATH_COLOR, rect)
                        
                    if (y, x) in self.visited:
                        pygame.draw.rect(self.screen, VISITED_COLOR, rect)
            
            # ✅ Dessiner la position de départ en vert
            start_rect = pygame.Rect(
                1 * cell_size + offset_x,
                1 * cell_size + offset_y,
                cell_size,
                cell_size
            )
            pygame.draw.rect(self.screen, START_COLOR, start_rect)
            
            # ✅ Dessiner les chemins DFS en rouge
            if self.show_dfs_paths and self.dfs_paths:
                for path in self.dfs_paths:
                    for y, x in path:
                        # Ne pas redessiner la position de départ
                        if not (y == 1 and x == 1):
                            rect = pygame.Rect(
                                x * cell_size + offset_x,
                                y * cell_size + offset_y,
                                cell_size,
                                cell_size
                            )
                            pygame.draw.rect(self.screen, DFS_PATH_COLOR, rect)
            
            # ✅ Dessiner le chemin BFS en bleu
            if self.show_bfs_path and self.bfs_path:
                for y, x in self.bfs_path:
                    # Ne pas redessiner la position de départ
                    if not (y == 1 and x == 1):
                        rect = pygame.Rect(
                            x * cell_size + offset_x,
                            y * cell_size + offset_y,
                            cell_size,
                            cell_size
                        )
                        pygame.draw.rect(self.screen, BFS_PATH_COLOR, rect)
            
            player_rect = pygame.Rect(
                self.player_pos[0] * cell_size + offset_x + cell_size//2 - player_radius,
                self.player_pos[1] * cell_size + offset_y + cell_size//2 - player_radius,
                player_radius * 2,
                player_radius * 2
            )
            pygame.draw.ellipse(self.screen, PLAYER_COLOR, player_rect)

            exit_rect = pygame.Rect(
                (width-1) * cell_size + offset_x,
                (height-2) * cell_size + offset_y,
                cell_size,
                cell_size
            )
            pygame.draw.rect(self.screen, EXIT_COLOR, exit_rect)

        else:
            start_x = max(0, self.player_pos[0] - self.view_range)
            end_x = min(width, self.player_pos[0] + self.view_range + 1)
            start_y = max(0, self.player_pos[1] - self.view_range)
            end_y = min(height, self.player_pos[1] + self.view_range + 1)
            
            view_width = (end_x - start_x) * cell_size
            view_height = (end_y - start_y) * cell_size
            
            offset_x = (self.screen.get_width() - view_width) // 2
            offset_y = game_area_top + (game_area_height - view_height) // 2
            
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    rect = pygame.Rect(
                        (x - start_x) * cell_size + offset_x,
                        (y - start_y) * cell_size + offset_y,
                        cell_size,
                        cell_size
                    )
                    if self.maze[y][x] == 1:
                        pygame.draw.rect(self.screen, WALL_COLOR, rect)
                    else:
                        pygame.draw.rect(self.screen, PATH_COLOR, rect)
                        
                    if (y, x) in self.visited:
                        pygame.draw.rect(self.screen, VISITED_COLOR, rect)
            
            # ✅ Dessiner la position de départ en vert dans la vue réduite
            if start_y <= 1 < end_y and start_x <= 1 < end_x:
                start_rect = pygame.Rect(
                    (1 - start_x) * cell_size + offset_x,
                    (1 - start_y) * cell_size + offset_y,
                    cell_size,
                    cell_size
                )
                pygame.draw.rect(self.screen, START_COLOR, start_rect)
            
            # ✅ Dessiner les chemins DFS dans la vue réduite
            if self.show_dfs_paths and self.dfs_paths:
                for path in self.dfs_paths:
                    for y, x in path:
                        if start_y <= y < end_y and start_x <= x < end_x:
                            # Ne pas redessiner la position de départ
                            if not (y == 1 and x == 1):
                                rect = pygame.Rect(
                                    (x - start_x) * cell_size + offset_x,
                                    (y - start_y) * cell_size + offset_y,
                                    cell_size,
                                    cell_size
                                )
                                pygame.draw.rect(self.screen, DFS_PATH_COLOR, rect)
            
            # ✅ Dessiner le chemin BFS dans la vue réduite
            if self.show_bfs_path and self.bfs_path:
                for y, x in self.bfs_path:
                    if start_y <= y < end_y and start_x <= x < end_x:
                        # Ne pas redessiner la position de départ
                        if not (y == 1 and x == 1):
                            rect = pygame.Rect(
                                (x - start_x) * cell_size + offset_x,
                                (y - start_y) * cell_size + offset_y,
                                cell_size,
                                cell_size
                            )
                            pygame.draw.rect(self.screen, BFS_PATH_COLOR, rect)
            
            player_rect = pygame.Rect(
                (self.player_pos[0] - start_x) * cell_size + offset_x + cell_size//2 - player_radius,
                (self.player_pos[1] - start_y) * cell_size + offset_y + cell_size//2 - player_radius,
                player_radius * 2,
                player_radius * 2
            )
            pygame.draw.ellipse(self.screen, PLAYER_COLOR, player_rect)
            
            if start_y <= height-2 <= end_y-1 and start_x <= width-1 <= end_x-1:
                exit_rect = pygame.Rect(
                    (width-1 - start_x) * cell_size + offset_x,
                    (height-2 - start_y) * cell_size + offset_y,
                    cell_size,
                    cell_size
                )
                pygame.draw.rect(self.screen, EXIT_COLOR, exit_rect)
        
        self.draw_ui()
    
    def draw_ui(self):
        config = DIFFICULTIES[self.difficulty]
        
        top_ui_rect = pygame.Rect(0, 0, self.screen.get_width(), 40)
        pygame.draw.rect(self.screen, UI_BG_COLOR, top_ui_rect)
        
        bottom_ui_rect = pygame.Rect(0, self.screen.get_height() - 40, self.screen.get_width(), 40)
        pygame.draw.rect(self.screen, UI_BG_COLOR, bottom_ui_rect)
        
        font = pygame.font.SysFont(None, 24)
        
        elapsed_time = int(time.time() - self.start_time) if self.start_time else 0
        time_text = font.render(f"Temps: {elapsed_time}s", True, TEXT_COLOR)
        self.screen.blit(time_text, (20, 10))
        
        moves_text = font.render(f"Mouvements: {self.moves}", True, TEXT_COLOR)
        self.screen.blit(moves_text, (self.screen.get_width() - moves_text.get_width() - 20, 10))
        
        difficulty_text = font.render(f"Difficulté: {self.difficulty}", True, TEXT_COLOR)
        self.screen.blit(difficulty_text, (self.screen.get_width()//2 - difficulty_text.get_width()//2, 10))
        
        # ✅ Afficher l'état DFS et BFS
        dfs_status = "DFS: ON (D)" if self.show_dfs_paths else "DFS: OFF (D)"
        dfs_text = font.render(dfs_status, True, TEXT_COLOR)
        self.screen.blit(dfs_text, (self.screen.get_width()//2 - dfs_text.get_width()//2 - 80, self.screen.get_height() - 30))
        
        bfs_status = "BFS: ON (B)" if self.show_bfs_path else "BFS: OFF (B)"
        bfs_text = font.render(bfs_status, True, TEXT_COLOR)
        self.screen.blit(bfs_text, (self.screen.get_width()//2 - bfs_text.get_width()//2 + 80, self.screen.get_height() - 30))
        
        display_mode = "Plein écran (F)" if self.fullscreen else "Fenêtré (F)"
        display_text = font.render(display_mode, True, TEXT_COLOR)
        self.screen.blit(display_text, (self.screen.get_width() - display_text.get_width() - 20, self.screen.get_height() - 30))
        
        button_width = 150
        button_spacing = 10
        total_buttons_width = button_width * 4 + button_spacing * 3
        start_x = self.screen.get_width()//2 - total_buttons_width//2
        
        if total_buttons_width > self.screen.get_width() - 40:
            button_width = (self.screen.get_width() - 40 - button_spacing * 3) // 4
            start_x = 20
        
        map_button_rect = pygame.Rect(start_x, self.screen.get_height() - 35, button_width, 30)
        map_button_color = BUTTON_HOVER_COLOR if map_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, map_button_color, map_button_rect, border_radius=5)
        map_text = font.render("Carte complète" if not self.show_full_map else "Vue zoomée", True, TEXT_COLOR)
        self.screen.blit(map_text, (map_button_rect.centerx - map_text.get_width()//2, 
                                   map_button_rect.centery - map_text.get_height()//2))
        
        restart_button_rect = pygame.Rect(start_x + button_width + button_spacing, self.screen.get_height() - 35, button_width, 30)
        restart_button_color = BUTTON_HOVER_COLOR if restart_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, restart_button_color, restart_button_rect, border_radius=5)
        restart_text = font.render("Recommencer", True, TEXT_COLOR)
        self.screen.blit(restart_text, (restart_button_rect.centerx - restart_text.get_width()//2, 
                                       restart_button_rect.centery - restart_text.get_height()//2))
        
        difficulty_button_rect = pygame.Rect(start_x + (button_width + button_spacing) * 2, self.screen.get_height() - 35, button_width, 30)
        difficulty_button_color = BUTTON_HOVER_COLOR if difficulty_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, difficulty_button_color, difficulty_button_rect, border_radius=5)
        difficulty_button_text = font.render("Changer difficulté", True, TEXT_COLOR)
        self.screen.blit(difficulty_button_text, (difficulty_button_rect.centerx - difficulty_button_text.get_width()//2, 
                                                difficulty_button_rect.centery - difficulty_button_text.get_height()//2))
        
        quit_button_rect = pygame.Rect(start_x + (button_width + button_spacing) * 3, self.screen.get_height() - 35, button_width, 30)
        quit_button_color = BUTTON_HOVER_COLOR if quit_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, quit_button_color, quit_button_rect, border_radius=5)
        quit_text = font.render("Quitter", True, TEXT_COLOR)
        self.screen.blit(quit_text, (quit_button_rect.centerx - quit_text.get_width()//2, 
                                    quit_button_rect.centery - quit_text.get_height()//2))
        
        if self.game_over:
            game_over_font = pygame.font.SysFont(None, 48)
            game_over_text = game_over_font.render("Félicitations! Vous avez gagné!", True, (0, 255, 0))
            text_rect = game_over_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
            self.screen.blit(game_over_text, text_rect)
    
    def move_player(self, dx, dy):
        new_x, new_y = self.player_pos[0] + dx, self.player_pos[1] + dy
        
        if (0 <= new_x < DIFFICULTIES[self.difficulty]["width"] and 
            0 <= new_y < DIFFICULTIES[self.difficulty]["height"] and 
            self.maze[new_y][new_x] == 0):
            
            self.player_pos = [new_x, new_y]
            self.moves += 1
            self.visited.add((new_y, new_x))
            
            if new_x == DIFFICULTIES[self.difficulty]["width"] - 1 and new_y == DIFFICULTIES[self.difficulty]["height"] - 2:
                self.game_over = True
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if not self.game_over:
                    if event.key == pygame.K_UP:
                        self.move_player(0, -1)
                    elif event.key == pygame.K_DOWN:
                        self.move_player(0, 1)
                    elif event.key == pygame.K_LEFT:
                        self.move_player(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move_player(1, 0)
                    # ✅ Touche D pour activer/désactiver l'affichage DFS
                    elif event.key == pygame.K_d:
                        self.show_dfs_paths = not self.show_dfs_paths
                        if self.show_dfs_paths:
                            # Calculer les chemins seulement quand on active DFS
                            self.dfs_paths = self.find_all_paths_dfs()
                        else:
                            self.dfs_paths = []
                    # ✅ Touche B pour activer/désactiver l'affichage BFS
                    elif event.key == pygame.K_b:
                        self.show_bfs_path = not self.show_bfs_path
                        if self.show_bfs_path:
                            # Calculer le chemin seulement quand on active BFS
                            self.bfs_path = self.find_shortest_path_bfs()
                        else:
                            self.bfs_path = []
                
                if event.key == pygame.K_f:
                    self.toggle_fullscreen()
            
            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                button_width = 150
                button_spacing = 10
                total_buttons_width = button_width * 4 + button_spacing * 3
                start_x = self.screen.get_width()//2 - total_buttons_width//2
                
                if total_buttons_width > self.screen.get_width() - 40:
                    button_width = (self.screen.get_width() - 40 - button_spacing * 3) // 4
                    start_x = 20
                
                map_button_rect = pygame.Rect(start_x, self.screen.get_height() - 35, button_width, 30)
                if map_button_rect.collidepoint(mouse_pos):
                    self.show_full_map = not self.show_full_map
                
                restart_button_rect = pygame.Rect(start_x + button_width + button_spacing, self.screen.get_height() - 35, button_width, 30)
                if restart_button_rect.collidepoint(mouse_pos):
                    self.generate_maze()
                
                difficulty_button_rect = pygame.Rect(start_x + (button_width + button_spacing) * 2, self.screen.get_height() - 35, button_width, 30)
                if difficulty_button_rect.collidepoint(mouse_pos):
                    return "change_difficulty"
                
                quit_button_rect = pygame.Rect(start_x + (button_width + button_spacing) * 3, self.screen.get_height() - 35, button_width, 30)
                if quit_button_rect.collidepoint(mouse_pos):
                    return False
        
        return True
    
    def run(self):
        running = True
        while running:
            self.select_difficulty()
            self.generate_maze()
            
            game_running = True
            while game_running:
                result = self.handle_events()
                
                if result == False:
                    game_running = False
                    running = False
                elif result == "change_difficulty":
                    game_running = False
                else:
                    self.draw_maze()
                    pygame.display.flip()
                    self.clock.tick(60)
        
        pygame.quit()

# Lancer le jeu
if __name__ == "__main__":
    game = MazeGame()
    game.run()
