# jarvis_display.py
# Advanced JARVIS HUD - Mark II Style
import pygame
import math
import time
import random
import threading

# --- INITIALIZATION ---
pygame.init()
pygame.font.init()

# --- CONSTANTS & SETTINGS ---
WIDTH, HEIGHT = 800, 600
CENTER = (WIDTH // 2, HEIGHT // 2)
FPS = 60

# --- COLORS (Iron Man Palette) ---
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)       # Main Color (Idle)
BLUE_DARK = (0, 100, 150)  # Background detail
WHITE = (255, 255, 255)    # Text
ORANGE = (255, 165, 0)     # Listening Mode
RED = (255, 50, 50)        # Speaking/Processing Mode

# Global Control Variables
current_state = 0  # 0=Idle, 1=Listening, 2=Speaking
jarvis_display_instance = None
running = True

# --- HELPER FUNCTIONS ---

def draw_arc(surface, color, center, radius, start_angle, end_angle, width=1):
    """Pygame mein clean arcs draw karne ke liye helper function."""
    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = center
    # Angles ko radians mein convert karna padta hai
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    pygame.draw.arc(surface, color, rect, -end_rad, -start_rad, width)

def rotate_surface(surface, angle):
    """Ek surface ko center ke around rotate karta hai bina wobble ke."""
    rotated_surface = pygame.transform.rotate(surface, angle)
    new_rect = rotated_surface.get_rect(center=surface.get_rect().center)
    return rotated_surface, new_rect

# --- CLASS: ROTATING RINGS (The core of the UI) ---

class HUDElement:
    def __init__(self, radius, speed, color, width=2, direction=1):
        self.radius = radius
        self.angle = 0
        self.speed = speed
        self.color = color
        self.width = width
        self.direction = direction # 1 for Clockwise, -1 for Anti-Clockwise
        
        # Ek transparent surface banate hain har ring ke liye
        self.surface_size = radius * 2 + 10
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=CENTER)
        
        self.draw_structure() # Initial drawing

    def draw_structure(self):
        """Is function ko subclass mein override karenge alag designs ke liye."""
        pass

    def update(self):
        self.angle += self.speed * self.direction
        if self.angle >= 360: self.angle -= 360
        if self.angle < 0: self.angle += 360

    def draw(self, screen):
        # Image ko rotate karke screen par blit karte hain
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        new_rect = rotated_image.get_rect(center=CENTER)
        screen.blit(rotated_image, new_rect)
        
    def set_color(self, new_color):
        self.color = new_color
        # Color change hone par structure dubara draw karna padega
        self.image.fill((0,0,0,0)) # Clear
        self.draw_structure() # Redraw

# --- SPECIFIC RING DESIGNS (Matching the Image) ---

class DashedRing(HUDElement):
    """Bahar wali choti lines wali ring."""
    def draw_structure(self):
        center_local = (self.surface_size // 2, self.surface_size // 2)
        num_dashes = 60
        for i in range(num_dashes):
            start_a = i * (360 / num_dashes)
            end_a = start_a + 2 # Short dash
            draw_arc(self.image, self.color, center_local, self.radius, start_a, end_a, self.width)

class SegmentedRing(HUDElement):
    """Moti arcs wali ring."""
    def draw_structure(self):
        center_local = (self.surface_size // 2, self.surface_size // 2)
        # 3 bade segments
        draw_arc(self.image, self.color, center_local, self.radius, 0, 90, self.width + 5)
        draw_arc(self.image, self.color, center_local, self.radius, 120, 200, self.width + 5)
        draw_arc(self.image, self.color, center_local, self.radius, 240, 330, self.width + 5)

class TechRing(HUDElement):
    """Complex tech details wali ring."""
    def draw_structure(self):
        center_local = (self.surface_size // 2, self.surface_size // 2)
        pygame.draw.circle(self.image, self.color, center_local, self.radius, 1)
        
        # Kuch random geometric shapes add karte hain
        for i in range(0, 360, 45):
            rad = math.radians(i)
            x1 = center_local[0] + (self.radius - 10) * math.cos(rad)
            y1 = center_local[1] + (self.radius - 10) * math.sin(rad)
            x2 = center_local[0] + (self.radius + 10) * math.cos(rad)
            y2 = center_local[1] + (self.radius + 10) * math.sin(rad)
            pygame.draw.line(self.image, self.color, (x1, y1), (x2, y2), 2)

class CoreReactor(HUDElement):
    """Beech ka glow karne wala hissa."""
    def update(self):
        # Ye rotate nahi karega, bas color manage karega
        pass
    
    def draw(self, screen):
        # Pulsing effect (Glow)
        pulse = math.sin(time.time() * 5) * 5
        glow_radius = int(self.radius + pulse)
        
        # Transparent glow surface
        glow_surf = pygame.Surface((glow_radius * 2 + 20, glow_radius * 2 + 20), pygame.SRCALPHA)
        glow_center = (glow_radius + 10, glow_radius + 10)
        
        # Inner solid circle
        pygame.draw.circle(screen, self.color, CENTER, self.radius - 5, 2)
        
        # Faint Glow
        pygame.draw.circle(glow_surf, (*self.color, 50), glow_center, glow_radius, 5) # Low alpha
        pygame.draw.circle(glow_surf, (*self.color, 100), glow_center, glow_radius - 10, 5) # Med alpha
        
        # Glow ko center me lagana
        glow_rect = glow_surf.get_rect(center=CENTER)
        screen.blit(glow_surf, glow_rect)


# --- MAIN DISPLAY CLASS ---

class JarvisDisplay:
    def __init__(self):
        global jarvis_display_instance
        
        # Screen Setup
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("J.A.R.V.I.S. PROTOCOL")
        self.clock = pygame.time.Clock()
        
        # Fonts
        try:
            self.font_main = pygame.font.SysFont("Impact", 30)
            self.font_small = pygame.font.SysFont("Consolas", 14)
        except:
            self.font_main = pygame.font.Font(None, 40)
            self.font_small = pygame.font.Font(None, 20)

        # --- CREATING THE RINGS (LAYERS) ---
        # Ham alag-alag radius aur speed par rings banayenge image jaisa look dene ke liye
        self.rings = []
        
        # 1. Outer Dashed Ring (Slowest)
        self.rings.append(DashedRing(radius=250, speed=0.2, color=BLUE_DARK, width=2, direction=1))
        
        # 2. Outer Segmented Ring (Slow)
        self.rings.append(SegmentedRing(radius=220, speed=0.5, color=CYAN, width=3, direction=-1))
        
        # 3. Middle Tech Ring (Medium)
        self.rings.append(TechRing(radius=180, speed=0.8, color=CYAN, width=1, direction=1))
        
        # 4. Inner Dashed (Fast)
        self.rings.append(DashedRing(radius=140, speed=1.5, color=BLUE_DARK, width=2, direction=-1))
        
        # 5. Inner Bright Segmented (Fastest)
        self.rings.append(SegmentedRing(radius=110, speed=2.0, color=CYAN, width=4, direction=1))
        
        # 6. Core (Static/Pulsing)
        self.core = CoreReactor(radius=80, speed=0, color=CYAN, width=0)

        jarvis_display_instance = self
        self.status_text = "SYSTEM INITIALIZED"

    def update_colors(self):
        """State ke hisaab se sabhi rings ka color badalta hai."""
        target_color = CYAN
        
        if current_state == 0:   # IDLE
            target_color = CYAN
            self.status_text = "SYSTEM ONLINE"
        elif current_state == 1: # LISTENING
            target_color = ORANGE
            self.status_text = "LISTENING..."
        elif current_state == 2: # SPEAKING
            target_color = RED
            self.status_text = "PROCESSING / SPEAKING"
            
        # Sabhi rings ko naya color dete hain
        for ring in self.rings:
            if ring.color != target_color and ring.color != BLUE_DARK:
                ring.set_color(target_color)
        
        # Core ka color hamesha change hoga
        self.core.color = target_color

    def draw_ui(self):
        self.screen.fill(BLACK)
        
        # 1. Draw All Rings
        for ring in self.rings:
            ring.update()
            ring.draw(self.screen)
            
        # 2. Draw Core
        self.core.draw(self.screen)
        
        # 3. Draw Text (HUD Style)
        # Center Name
        text_surf = self.font_main.render("J.A.R.V.I.S", True, WHITE)
        text_rect = text_surf.get_rect(center=CENTER)
        self.screen.blit(text_surf, text_rect)
        
        # Subtitle
        sub_text = self.font_small.render("MARK II UI", True, self.core.color)
        sub_rect = sub_text.get_rect(center=(CENTER[0], CENTER[1] + 25))
        self.screen.blit(sub_text, sub_rect)
        
        # Status at bottom
        status_surf = self.font_small.render(f"STATUS: {self.status_text}", True, WHITE)
        self.screen.blit(status_surf, (20, HEIGHT - 40))
        
        # Time
        time_str = time.strftime("%H:%M:%S")
        time_surf = self.font_small.render(f"TIME: {time_str}", True, WHITE)
        self.screen.blit(time_surf, (WIDTH - 120, HEIGHT - 40))
        
        # Fake Data Numbers (Decoration)
        for i in range(5):
            y_pos = 100 + (i * 20)
            rand_num = random.randint(1000, 9999)
            data_surf = self.font_small.render(f"DAT_{i}: {rand_num}", True, BLUE_DARK)
            self.screen.blit(data_surf, (20, y_pos))

        pygame.display.flip()

    def run(self):
        global running
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            self.update_colors()
            self.draw_ui()
            self.clock.tick(FPS)
        
        pygame.quit()

    def set_state(self, state, text=""):
        """Main.py se call karne ke liye function."""
        global current_state
        current_state = state
        # Text ko hum update loop me handle kar rahe hain status ke through
        # lekin custom text ke liye:
        if text:
            self.status_text = text.upper()
    
    def stop_loop(self):
        global running
        running = False

# --- THREADING INTERFACE ---

def start_ui():
    app = JarvisDisplay()
    app.run()

# Auto-start logic for main.py integration
ui_thread = threading.Thread(target=start_ui, daemon=True)
ui_thread.start()

# Wait for initialization
time.sleep(1)

def get_jarvis_display():
    return jarvis_display_instance

# Test run agar directly is file ko chalayein
if __name__ == "__main__":
    try:
        # Testing states
        time.sleep(2)
        current_state = 1 # Listening
        time.sleep(2)
        current_state = 2 # Speaking
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False