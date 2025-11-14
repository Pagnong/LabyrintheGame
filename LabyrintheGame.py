import pygame
import random
import time
import sys

# Initialisation de Pygame
pygame.init()

# Constantes
CELL_SIZE = 40
MINI_MAP_CELL_SIZE = 5
PLAYER_RADIUS = 15
WALL_COLOR = (0, 0, 0)
PATH_COLOR = (255, 255, 255)
PLAYER_COLOR = (255, 0, 0)
EXIT_COLOR = (0, 255, 0)
VISITED_COLOR = (200, 200, 255)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER_COLOR = (120, 120, 220)
TEXT_COLOR = (255, 255, 255)
UI_BG_COLOR = (70, 70, 70)

# Difficultés - Moyen et Difficile rendus plus difficiles
DIFFICULTIES = {
    "Facile": {"width": 15, "height": 15, "view_range": 5},
    "Moyen": {"width": 35, "height": 35, "view_range": 3},
    "Difficile": {"width": 55, "height": 55, "view_range": 2}
}

class MazeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maze = [[1 for _ in range(width)] for _ in range(height)]
        
    def generate(self):
        # Point de départ
        start_x, start_y = 1, 1
        self.maze[start_y][start_x] = 0
        
        # Génération avec algorithme de backtracking
        stack = [(start_x, start_y)]
        
        while stack:
            current_x, current_y = stack[-1]
            
            # Trouver les voisins non visités
            neighbors = []
            for dx, dy in [(0, -2), (2, 0), (0, 2), (-2, 0)]:
                nx, ny = current_x + dx, current_y + dy
                if 0 < nx < self.width - 1 and 0 < ny < self.height - 1 and self.maze[ny][nx] == 1:
                    neighbors.append((nx, ny, dx, dy))
            
            if neighbors:
                # Choisir un voisin aléatoire
                nx, ny, dx, dy = random.choice(neighbors)
                
                # Casser le mur entre la cellule courante et le voisin
                self.maze[current_y + dy//2][current_x + dx//2] = 0
                self.maze[ny][nx] = 0
                
                stack.append((nx, ny))
            else:
                stack.pop()
        
        # Définir l'entrée et la sortie
        self.maze[1][0] = 0  # Entrée
        self.maze[self.height-2][self.width-1] = 0  # Sortie
        
        return self.maze

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
        
    def select_difficulty(self):
        # Créer une fenêtre pour la sélection de difficulté
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
            
            # Afficher le titre
            title = title_font.render("Sélectionnez la difficulté", True, TEXT_COLOR)
            temp_screen.blit(title, (400//2 - title.get_width()//2, 30))
            
            # Gérer les événements
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
            
            # Afficher les boutons
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
            # Mode plein écran
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            # Mode fenêtré avec taille par défaut
            config = DIFFICULTIES[self.difficulty]
            window_width = min(config["width"] * self.base_cell_size, 1200)
            window_height = min(config["height"] * self.base_cell_size, 800) + 80
            self.screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
        
        pygame.display.set_caption(f"Labyrinthe - {self.difficulty}")
    
    def calculate_cell_size(self):
        """Calcule la taille des cellules en fonction de la taille de la fenêtre"""
        if not self.screen or not self.maze:
            return self.base_cell_size
            
        config = DIFFICULTIES[self.difficulty]
        maze_width = config["width"]
        maze_height = config["height"]
        
        # Calculer la taille disponible pour le labyrinthe
        available_width = self.screen.get_width()
        available_height = self.screen.get_height() - 80  # Réserver de l'espace pour l'interface
        
        # Calculer la taille maximale des cellules pour que le labyrinthe tienne dans l'écran
        max_cell_width = available_width // maze_width
        max_cell_height = available_height // maze_height
        
        # Utiliser la plus petite taille pour garder les proportions
        cell_size = min(max_cell_width, max_cell_height, self.base_cell_size)
        
        # Assurer une taille minimale
        return max(cell_size, 10)
    
    def generate_maze(self):
        config = DIFFICULTIES[self.difficulty]
        generator = MazeGenerator(config["width"], config["height"])
        self.maze = generator.generate()
        self.player_pos = [1, 1]  # Position de départ
        self.start_time = time.time()
        self.moves = 0
        self.show_full_map = False
        self.game_over = False
        self.visited = set()
        self.visited.add((self.player_pos[1], self.player_pos[0]))
        
        # Calculer la taille initiale de la fenêtre
        self.view_range = config["view_range"]
        window_width = min(config["width"] * self.base_cell_size, 1200)
        window_height = min(config["height"] * self.base_cell_size, 800) + 80
        
        # Créer la fenêtre redimensionnable
        self.screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
        pygame.display.set_caption(f"Labyrinthe - {self.difficulty}")
    
    def draw_maze(self):
        config = DIFFICULTIES[self.difficulty]
        width, height = config["width"], config["height"]
        
        # Calculer la taille des cellules adaptée à la fenêtre
        cell_size = self.calculate_cell_size()
        player_radius = max(cell_size // 3, 5)
        
        # Effacer l'écran
        self.screen.fill((50, 50, 50))
        
        # Zone de jeu (entre les interfaces haut et bas)
        game_area_top = 40
        game_area_height = self.screen.get_height() - 80
        
        if self.show_full_map:
            # Calculer le décalage pour centrer le labyrinthe
            total_maze_width = width * cell_size
            total_maze_height = height * cell_size
            
            offset_x = (self.screen.get_width() - total_maze_width) // 2
            offset_y = game_area_top + (game_area_height - total_maze_height) // 2
            
            # Afficher la carte complète
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
                        
                    # Marquer les cellules visitées
                    if (y, x) in self.visited:
                        pygame.draw.rect(self.screen, VISITED_COLOR, rect)
            
            # Dessiner le joueur
            player_rect = pygame.Rect(
                self.player_pos[0] * cell_size + offset_x + cell_size//2 - player_radius,
                self.player_pos[1] * cell_size + offset_y + cell_size//2 - player_radius,
                player_radius * 2,
                player_radius * 2
            )
            pygame.draw.ellipse(self.screen, PLAYER_COLOR, player_rect)
            
            # Dessiner la sortie
            exit_rect = pygame.Rect(
                (width-1) * cell_size + offset_x,
                (height-2) * cell_size + offset_y,
                cell_size,
                cell_size
            )
            pygame.draw.rect(self.screen, EXIT_COLOR, exit_rect)
        else:
            # Afficher la vue zoomée autour du joueur
            start_x = max(0, self.player_pos[0] - self.view_range)
            end_x = min(width, self.player_pos[0] + self.view_range + 1)
            start_y = max(0, self.player_pos[1] - self.view_range)
            end_y = min(height, self.player_pos[1] + self.view_range + 1)
            
            # Calculer le décalage pour centrer la vue
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
                        
                    # Marquer les cellules visitées
                    if (y, x) in self.visited:
                        pygame.draw.rect(self.screen, VISITED_COLOR, rect)
            
            # Dessiner le joueur
            player_rect = pygame.Rect(
                (self.player_pos[0] - start_x) * cell_size + offset_x + cell_size//2 - player_radius,
                (self.player_pos[1] - start_y) * cell_size + offset_y + cell_size//2 - player_radius,
                player_radius * 2,
                player_radius * 2
            )
            pygame.draw.ellipse(self.screen, PLAYER_COLOR, player_rect)
            
            # Dessiner la sortie si elle est dans la vue
            if start_y <= height-2 <= end_y-1 and start_x <= width-1 <= end_x-1:
                exit_rect = pygame.Rect(
                    (width-1 - start_x) * cell_size + offset_x,
                    (height-2 - start_y) * cell_size + offset_y,
                    cell_size,
                    cell_size
                )
                pygame.draw.rect(self.screen, EXIT_COLOR, exit_rect)
        
        # Dessiner l'interface utilisateur
        self.draw_ui()
    
    def draw_ui(self):
        config = DIFFICULTIES[self.difficulty]
        
        # Zone pour l'interface du haut (informations)
        top_ui_rect = pygame.Rect(0, 0, self.screen.get_width(), 40)
        pygame.draw.rect(self.screen, UI_BG_COLOR, top_ui_rect)
        
        # Zone pour l'interface du bas (boutons)
        bottom_ui_rect = pygame.Rect(0, self.screen.get_height() - 40, self.screen.get_width(), 40)
        pygame.draw.rect(self.screen, UI_BG_COLOR, bottom_ui_rect)
        
        font = pygame.font.SysFont(None, 24)
        
        # Afficher le temps écoulé en haut à gauche
        elapsed_time = int(time.time() - self.start_time) if self.start_time else 0
        time_text = font.render(f"Temps: {elapsed_time}s", True, TEXT_COLOR)
        self.screen.blit(time_text, (20, 10))
        
        # Afficher le nombre de mouvements en haut à droite
        moves_text = font.render(f"Mouvements: {self.moves}", True, TEXT_COLOR)
        self.screen.blit(moves_text, (self.screen.get_width() - moves_text.get_width() - 20, 10))
        
        # Afficher la difficulté au centre en haut
        difficulty_text = font.render(f"Difficulté: {self.difficulty}", True, TEXT_COLOR)
        self.screen.blit(difficulty_text, (self.screen.get_width()//2 - difficulty_text.get_width()//2, 10))
        
        # Afficher le mode d'affichage en haut
        display_mode = "Plein écran (F)" if self.fullscreen else "Fenêtré (F)"
        display_text = font.render(display_mode, True, TEXT_COLOR)
        self.screen.blit(display_text, (self.screen.get_width() - display_text.get_width() - 20, self.screen.get_height() - 30))
        
        # Calculer les positions des boutons en bas
        button_width = 150
        button_spacing = 10
        total_buttons_width = button_width * 4 + button_spacing * 3
        start_x = self.screen.get_width()//2 - total_buttons_width//2
        
        # Ajuster la taille des boutons si l'écran est trop petit
        if total_buttons_width > self.screen.get_width() - 40:
            button_width = (self.screen.get_width() - 40 - button_spacing * 3) // 4
            total_buttons_width = button_width * 4 + button_spacing * 3
            start_x = 20
        
        # Bouton pour afficher/masquer la carte complète
        map_button_rect = pygame.Rect(start_x, self.screen.get_height() - 35, button_width, 30)
        map_button_color = BUTTON_HOVER_COLOR if map_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, map_button_color, map_button_rect, border_radius=5)
        map_text = font.render("Carte complète" if not self.show_full_map else "Vue zoomée", True, TEXT_COLOR)
        self.screen.blit(map_text, (map_button_rect.centerx - map_text.get_width()//2, 
                                   map_button_rect.centery - map_text.get_height()//2))
        
        # Bouton pour recommencer
        restart_button_rect = pygame.Rect(start_x + button_width + button_spacing, self.screen.get_height() - 35, button_width, 30)
        restart_button_color = BUTTON_HOVER_COLOR if restart_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, restart_button_color, restart_button_rect, border_radius=5)
        restart_text = font.render("Recommencer", True, TEXT_COLOR)
        self.screen.blit(restart_text, (restart_button_rect.centerx - restart_text.get_width()//2, 
                                       restart_button_rect.centery - restart_text.get_height()//2))
        
        # Bouton pour retourner à la sélection de difficulté
        difficulty_button_rect = pygame.Rect(start_x + (button_width + button_spacing) * 2, self.screen.get_height() - 35, button_width, 30)
        difficulty_button_color = BUTTON_HOVER_COLOR if difficulty_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, difficulty_button_color, difficulty_button_rect, border_radius=5)
        difficulty_button_text = font.render("Changer difficulté", True, TEXT_COLOR)
        self.screen.blit(difficulty_button_text, (difficulty_button_rect.centerx - difficulty_button_text.get_width()//2, 
                                                difficulty_button_rect.centery - difficulty_button_text.get_height()//2))
        
        # Bouton pour quitter
        quit_button_rect = pygame.Rect(start_x + (button_width + button_spacing) * 3, self.screen.get_height() - 35, button_width, 30)
        quit_button_color = BUTTON_HOVER_COLOR if quit_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, quit_button_color, quit_button_rect, border_radius=5)
        quit_text = font.render("Quitter", True, TEXT_COLOR)
        self.screen.blit(quit_text, (quit_button_rect.centerx - quit_text.get_width()//2, 
                                    quit_button_rect.centery - quit_text.get_height()//2))
        
        # Afficher un message si le jeu est terminé
        if self.game_over:
            game_over_font = pygame.font.SysFont(None, 48)
            game_over_text = game_over_font.render("Félicitations! Vous avez gagné!", True, (0, 255, 0))
            text_rect = game_over_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
            self.screen.blit(game_over_text, text_rect)
    
    def move_player(self, dx, dy):
        new_x, new_y = self.player_pos[0] + dx, self.player_pos[1] + dy
        
        # Vérifier si le mouvement est valide
        if (0 <= new_x < DIFFICULTIES[self.difficulty]["width"] and 
            0 <= new_y < DIFFICULTIES[self.difficulty]["height"] and 
            self.maze[new_y][new_x] == 0):
            
            self.player_pos = [new_x, new_y]
            self.moves += 1
            self.visited.add((new_y, new_x))
            
            # Vérifier si le joueur a atteint la sortie
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
                
                # Touche F pour basculer le plein écran
                if event.key == pygame.K_f:
                    self.toggle_fullscreen()
            
            elif event.type == pygame.VIDEORESIZE:
                # Redimensionner la fenêtre (sauf en mode plein écran)
                if not self.fullscreen:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Calculer les positions des boutons en bas
                button_width = 150
                button_spacing = 10
                total_buttons_width = button_width * 4 + button_spacing * 3
                start_x = self.screen.get_width()//2 - total_buttons_width//2
                
                # Ajuster la taille des boutons si l'écran est trop petit
                if total_buttons_width > self.screen.get_width() - 40:
                    button_width = (self.screen.get_width() - 40 - button_spacing * 3) // 4
                    start_x = 20
                
                # Bouton carte complète
                map_button_rect = pygame.Rect(start_x, self.screen.get_height() - 35, button_width, 30)
                if map_button_rect.collidepoint(mouse_pos):
                    self.show_full_map = not self.show_full_map
                
                # Bouton recommencer
                restart_button_rect = pygame.Rect(start_x + button_width + button_spacing, self.screen.get_height() - 35, button_width, 30)
                if restart_button_rect.collidepoint(mouse_pos):
                    self.generate_maze()
                
                # Bouton changer difficulté
                difficulty_button_rect = pygame.Rect(start_x + (button_width + button_spacing) * 2, self.screen.get_height() - 35, button_width, 30)
                if difficulty_button_rect.collidepoint(mouse_pos):
                    return "change_difficulty"
                
                # Bouton quitter
                quit_button_rect = pygame.Rect(start_x + (button_width + button_spacing) * 3, self.screen.get_height() - 35, button_width, 30)
                if quit_button_rect.collidepoint(mouse_pos):
                    return False
        
        return True
    
    def run(self):
        # Boucle principale du jeu
        running = True
        while running:
            # Sélectionner la difficulté
            self.select_difficulty()
            
            # Générer le labyrinthe
            self.generate_maze()
            
            # Boucle de jeu
            game_running = True
            while game_running:
                result = self.handle_events()
                
                if result == False:
                    game_running = False
                    running = False
                elif result == "change_difficulty":
                    game_running = False
                else:
                    # Dessiner le jeu
                    self.draw_maze()
                    
                    # Mettre à jour l'affichage
                    pygame.display.flip()
                    self.clock.tick(60)
        
        pygame.quit()

# Lancer le jeu
if __name__ == "__main__":
    game = MazeGame()
    game.run()
