import random
import sys
import os
import time
import pygame


""" 
Pour maximiser la résolution : Ne pas toucher

os.environ['SDL_VIDEO_CENTERED'] = '1' # Vous devez appeler ceci avant pygame.init()

pygame.init()

info = pygame.display.Info() # Vous devez appeler ceci avant pygame.display.set_mode()


# Dimensions de l'écran

LARGEUR, HAUTEUR = info.current_w, info.current_h  # Augmentation de la résolution
HAUTEUR_BANDE = 60  # Hauteur de la bande noire
screen = pygame.display.set_mode((LARGEUR, HAUTEUR))

window_width, window_height = LARGEUR - 10, HAUTEUR - 50
window = pygame.display.set_mode((window_width, window_height))
"""


pygame.init()

# Dimensions de l'écran
LARGEUR, HAUTEUR = 1280, 800  # Augmentation de la résolution
HAUTEUR_BANDE = 60  # Hauteur de la bande noire
screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Le Jeu du Poisson")

# Couleurs
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)


# Couleurs
gold_light = (255, 215, 0)  # Or clair
gold_dark = (218, 165, 32)  # Or foncé


# Charger les images de fond
dossier_fond = r"img\fond"
fonds_frames = [pygame.transform.scale(pygame.image.load(os.path.join(dossier_fond, f"frame_({i}).png")), 
                                     (LARGEUR, HAUTEUR - HAUTEUR_BANDE)) for i in range(96)]

# Reste des imports d'images inchangé
dossier_images_gauche = r"img\GtoD"  
dossier_images_droite = r"img\DtoG" 

def charger_images_poisson(dossier, taille=(40, 40)):
    return [pygame.transform.scale(pygame.image.load(os.path.join(dossier, img)), taille) 
            for img in os.listdir(dossier) if img.endswith(".png")]

images_poissons_gauche = charger_images_poisson(dossier_images_gauche)
images_poissons_droite = charger_images_poisson(dossier_images_droite)

requin_image = pygame.image.load(r"img\inmeangeable\requin.png")
requin_image = pygame.transform.scale(requin_image, (100, 100))  # Taille du requin

objet_bonus_image = pygame.image.load(r"img\tres\tresor.png")
bonus_emoji_image = pygame.transform.scale(pygame.image.load(r"img\tres\X2.png"), (43, 33))

fond_frame_index = 0
largeur_poisson = 40
hauteur_poisson = 40
vitesse_poisson = 5
vitesse_poisson_autre = 3

poissons = []
score = 10
bonus_actif = False
bonus_timer = 0

police = pygame.font.SysFont("Arial", 24)

def afficher_ecran_fin(victoire):
    """Affiche l'écran de fin de partie"""
    screen.fill(NOIR)
    message = "VICTOIRE !" if victoire else "DÉFAITE..."
    couleur = BLANC if victoire else ROUGE
    police_fin = pygame.font.SysFont("Arial", 74, bold=True)
    texte = police_fin.render(message, True, couleur)
    text_rect = texte.get_rect(center=(LARGEUR/2, HAUTEUR/2))
    screen.blit(texte, text_rect)
    
    # Instructions pour quitter
    police_instructions = pygame.font.SysFont("Arial", 24)
    instructions = police_instructions.render("Appuyez sur ESPACE pour quitter", True, BLANC)
    inst_rect = instructions.get_rect(center=(LARGEUR/2, HAUTEUR/2 + 100))
    screen.blit(instructions, inst_rect)
    pygame.display.flip()

    # Attendre que le joueur appuie sur ESPACE
    attente = True
    while attente:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    attente = False
                    return

class Poisson:
    def __init__(self, x, y, taille, score, vies, direction=1, est_joueur=False):
        self.x = x
        self.y = max(y, HAUTEUR_BANDE)
        self.taille = taille
        self.score = score
        self.vies = vies
        self.direction = direction
        self.est_joueur = est_joueur
        
        if est_joueur:
            # Charge les images du joueur et les redimensionne
            self.image_droite = pygame.transform.scale(
                pygame.image.load(r"img\perso\evolution1toD.png"), 
                (self.taille, self.taille)
            )
            self.image_gauche = pygame.transform.scale(
                pygame.image.load(r"img\perso\evolution1toG.png"), 
                (self.taille, self.taille)
            )
            self.image = self.image_droite  # Image par défaut
        else:
            self.image = random.choice(images_poissons_gauche if direction == 1 else images_poissons_droite)
            
        self.rect = self.image.get_rect(topleft=(x, y))
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.invincibilite_duree = 5
        self.dernier_bonus_coeur = None
        self.dernier_bonus_bouclier = None
        self.dernier_bonus_buff = None
        self.dernier_bonus_nerf = None
        self.invincibilite_duree_defaut = 5
        self.invincibilite_duree = self.invincibilite_duree_defaut
        self.derniere_direction = 0  # Pour suivre la dernière direction du joueur

    def gerer_invincibilite(self):
        if self.invulnerable:
            temps_ecoule = time.time() - self.invulnerable_timer
            if temps_ecoule >= self.invincibilite_duree:
                self.invulnerable = False
                self.invulnerable_timer = 0
                # Réinitialise la durée d'invincibilité à sa valeur par défaut
                self.invincibilite_duree = self.invincibilite_duree_defaut

    def dessiner(self):
        if self.invulnerable and (time.time() * 2) % 1 < 0.5:
            screen.blit(pygame.transform.scale(self.image, (int(self.taille * 1.2), int(self.taille * 1.2))), 
                       (self.x - self.taille * 0.1, self.y - self.taille * 0.1))
        else:
            screen.blit(self.image, (self.x, self.y))
        texte = police.render(str(self.score), True, NOIR)
        text_rect = texte.get_rect(center=self.rect.center)
        screen.blit(texte, text_rect)

    def deplacer(self):
        self.x += self.direction * vitesse_poisson_autre
        # Limite le déplacement vertical à la zone sous la bande noire
        self.y = max(HAUTEUR_BANDE, min(self.y, HAUTEUR - self.taille))
        self.rect.x, self.rect.y = self.x, self.y
        if self.rect.left > LARGEUR or self.rect.right < 0:
            if self in poissons:
                poissons.remove(self)
        self.gerer_invincibilite()



class ObjetBonusAvance:
    def __init__(self):
        self.x = random.randint(0, LARGEUR - 30)
        self.y = HAUTEUR_BANDE
        # Chargement des différentes images selon le type de bonus
        self.bonus_images = {
            "score_x2": pygame.transform.scale(pygame.image.load(r"img\tres\X2.png"), (32, 32)),
            "coeur": pygame.transform.scale(pygame.image.load(r"img\tres\coeur.png"), (30, 30)),
            "bouclier": pygame.transform.scale(pygame.image.load(r"img\tres\bouclier.png"), (30, 30)),
            "buff": pygame.transform.scale(pygame.image.load(r"img\tres\buff.png"), (30, 30)),
            "nerf": pygame.transform.scale(pygame.image.load(r"img\tres\nerf.png"), (30, 30))
        }
        self.type_bonus = random.choice(list(self.bonus_images.keys()))
        self.image = self.bonus_images[self.type_bonus]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.vitesse = 3

    def deplacer(self):
        # Fait tomber le bonus vers le bas
        self.y += self.vitesse
        self.rect.y = self.y
    
    def dessiner(self):
        # Affiche le bonus à l'écran
        screen.blit(self.image, (self.x, self.y))

def gestion_bonus_avance(joueur, objet_bonus):
    global bonus_actif, bonus_timer, bonus_emoji_image, vitesse_poisson, vitesse_poisson_autre
    
    if objet_bonus.type_bonus == "score_x2":
        bonus_actif = True
        bonus_timer = time.time()  # Enregistre le moment où le bonus est activé
    
    elif objet_bonus.type_bonus == "coeur":
        joueur.vies += 1
        joueur.dernier_bonus_coeur = time.time()
    
    elif objet_bonus.type_bonus == "bouclier":
        joueur.invulnerable = True
        joueur.invulnerable_timer = time.time()
        joueur.invincibilite_duree = 20
    
    elif objet_bonus.type_bonus == "buff":
        vitesse_poisson += 3
        bonus_timer = time.time()
        joueur.dernier_bonus_buff = time.time()
    
    elif objet_bonus.type_bonus == "nerf":
        vitesse_poisson_autre -= 1
        bonus_timer = time.time()
        joueur.dernier_bonus_nerf = time.time()


def calculer_gain(joueur_score, poisson_score, joueur_taille):
    gain = int(1 + (poisson_score / joueur_score) * (joueur_taille / 10))
    return gain * 2 if bonus_actif else gain

def afficher_score_et_taille(joueur, score, vies, temps_debut, nb_poissons_max):
    global bonus_actif, bonus_timer  # Déclaration des variables globales
    
    # Dessiner la bande gold dark en haut
    pygame.draw.rect(screen, gold_dark, (0, 0, LARGEUR, HAUTEUR_BANDE))
    pygame.draw.rect(screen, NOIR, (0, 0, LARGEUR, HAUTEUR_BANDE), 3)  # Contour Noir autour de la bande
    
    # Affichage du score, vies et nombre de poissons
    screen.blit(police.render(f"Score: {score}", True, BLANC), (10, 20))
    screen.blit(police.render(f"Vies: {vies}", True, ROUGE), (150, 20))
    screen.blit(police.render(f"Poissons: {nb_poissons_max}", True, BLANC), (300, 20))  # Plus besoin de formater ici
  
    # Chronomètre
    temps_ecoule = time.time() - temps_debut
    minutes = int(temps_ecoule // 60)
    secondes = int(temps_ecoule % 60)
    millisecondes = int((temps_ecoule * 100) % 100)
    temps_texte = f"{minutes:02d}:{secondes:02d}:{millisecondes:02d}"
    temps_rendu = police.render(temps_texte, True, BLANC)
    screen.blit(temps_rendu, (LARGEUR - 150, 20))
    
    # Affichage de l'invincibilité au centre
    if joueur.invulnerable:
        temps_restant = max(0, int(joueur.invincibilite_duree - (time.time() - joueur.invulnerable_timer)))
        if temps_restant > 0:
            inv_texte = police.render(f"Invincible ({temps_restant}s)", True, ROUGE)
            text_rect = inv_texte.get_rect(center=(LARGEUR // 1.8, HAUTEUR_BANDE // 1.8))
            screen.blit(inv_texte, text_rect)
    
    # Position en pourcentage pour les bonus
    x_nerf, y_nerf = int(LARGEUR * 0.65), int(HAUTEUR_BANDE * 0.3)
    x_buff, y_buff = int(LARGEUR * 0.70), int(HAUTEUR_BANDE * 0.3)
    x_score_x2, y_score_x2 = int(LARGEUR * 0.75), int(HAUTEUR_BANDE * 0.37)
    
    # Affichage des bonus avec la durée correcte (20 secondes)
    if joueur.dernier_bonus_nerf and time.time() - joueur.dernier_bonus_nerf < 20:
        nerf_image = pygame.transform.scale(pygame.image.load(r"img\tres\nerf.png"), (32, 32))
        screen.blit(nerf_image, (x_nerf, y_nerf))
    
    if joueur.dernier_bonus_buff and time.time() - joueur.dernier_bonus_buff < 20:
        buff_image = pygame.transform.scale(pygame.image.load(r"img/tres/buff.png"), (32, 32))
        screen.blit(buff_image, (x_buff, y_buff))
    
    # Affichage du bonus de score x2
    if bonus_actif and time.time() - bonus_timer < 20:  # Durée de 20 secondes pour le bonus x2
        screen.blit(bonus_emoji_image, (x_score_x2, y_score_x2))
    elif bonus_actif and time.time() - bonus_timer >= 20:
        bonus_actif = False
    
    # Remplacement du "+1 vie" par l'image du cœur
    if joueur.dernier_bonus_coeur and time.time() - joueur.dernier_bonus_coeur < 3:
        coeur_image = pygame.transform.scale(pygame.image.load(r"img\tres\coeur.png"), (25, 25))
        plus_text = police.render("+", True, ROUGE)
        screen.blit(plus_text, (int(LARGEUR * 0.21), 20))
        screen.blit(coeur_image, (int(LARGEUR * 0.23), 18))

    # Cadre des bonus
    cadre_largeur = int(LARGEUR * 0.15)
    cadre_hauteur = int(HAUTEUR_BANDE * 0.8)
    cadre_x = x_nerf - int(cadre_largeur * 0.05)
    cadre_y = int(HAUTEUR_BANDE * 0.1)
    epaisseur_contour = 3

    # Dessin du cadre transparent avec un contour OR
    pygame.draw.rect(screen, (0, 0, 0, 90), (cadre_x, cadre_y, cadre_largeur, cadre_hauteur), epaisseur_contour)
    
    surface_cadre = pygame.Surface((cadre_largeur, cadre_hauteur), pygame.SRCALPHA)
    surface_cadre.fill((0, 0, 255, 100))
    surface_cadre.fill((0, 255, 0, 100))
    screen.blit(surface_cadre, (cadre_x, cadre_y))

    pygame.draw.line(screen, (0, 0, 0), (0, 0), (LARGEUR, 0), 2)
    pygame.draw.line(screen, (50, 50, 50), (0, HAUTEUR_BANDE), (LARGEUR, HAUTEUR_BANDE), 2)


def generer_score_poisson(score_joueur):
    """
    Génère un score pour un nouveau poisson avec 50% de chance d'être supérieur
    et 50% de chance d'être inférieur au score du joueur
    """
    est_superieur = random.choice([True, False])  # 50% de chance
    
    if est_superieur:
        # Score supérieur : entre 100% et 200% du score du joueur
        return random.randint(score_joueur, score_joueur * 2)
    else:
        # Score inférieur : entre 25% et 99% du score du joueur
        return random.randint(max(1, score_joueur // 4), score_joueur - 1)


class Requin(Poisson):
    def __init__(self, x, y, direction=1):
        super().__init__(x, y, taille=120, score=float("inf"), vies=0, direction=direction)
        self.image = requin_image  # Image spécifique du requin
        self.vitesse = 1  # Le requin est lent

    def deplacer(self):
        # Le requin avance lentement mais est toujours dangereux
        self.x += self.direction * self.vitesse

        self.y = max(HAUTEUR_BANDE, min(self.y, HAUTEUR - self.taille))
        self.rect.x, self.rect.y = self.x, self.y
        if self.rect.left > LARGEUR or self.rect.right < 0:
            if self in poissons:
                poissons.remove(self)

# Variables pour l'animation
clignotement = True
clock = pygame.time.Clock()

# Boucle principale
running = True
class ParametresPartie:
    def __init__(self):
        # Paramètres des vitesses
        self.vitesse_joueur = 5
        self.vitesse_poisson_autre = 3
        self.vitesse_requin = 1

        # Paramètre doublons importants pas touche !
        self.vitesse_base_joueur = 5
        self.vitesse_base_poisson = 3
        self.vitesse_actuelle_joueur = self.vitesse_base_joueur
        self.vitesse_actuelle_poisson = self.vitesse_base_poisson
        self.duree_bonus = 20
      
        # Paramètres des bonus
        self.vitesse_bonus = 3  # vitesse de tombé attention mec
        self.duree_bonus = 20  # Réduit à 20 secondes
        self.intervalle_bonus = 5  # Nouveau paramètre : intervalle entre les bonus
        self.dernier_bonus = 0  # Nouveau paramètre : temps du dernier bonus
        
        # Paramètres d'apparition des poissons
        self.taux_apparition_poisson = 0.05  # Augmenté à 10% de chance par frame
        self.max_poissons = 250
        
        # Paramètres d'apparition des requins
        self.intervalle_requin_min = 20  # secondes
        self.intervalle_requin_max = 30  # secondes
        
        # Paramètres du joueur
        self.vies_initiales = 3
        self.taille_initiale = 40
        self.score_initial = 10
        
        # Paramètres d'invincibilité
        self.duree_invincibilite = 5  # secondes
        self.duree_invincibilite_bouclier = 20  # secondes

class Partie:
    def __init__(self, parametres=None):
        global bonus_actif, bonus_timer
        self.parametres = parametres or ParametresPartie()
        self.clock = pygame.time.Clock()
        self.temps_debut = None
        self.dernier_requin = None
        self.intervalle_requin = None
        self.bonus_actif = False
        self.bonus_timer = 0
        self.fond_frame_index = 0
        self.dernier_bonus = time.time()
        self.poissons = []
        self.objet_bonus = None
        self.joueur = None
        self.nb_poissons_max = self.parametres.max_poissons
        self.poissons_sortis = 0  # Nouveau compteur pour les poissons sortis

        # Initialisation des variables globales
        bonus_actif = False
        bonus_timer = 0

    def afficher_ecran_fin(self, victoire):
        """Affiche l'écran de fin de partie"""
        screen.fill(NOIR)
        message = "VICTOIRE !" if victoire else "DÉFAITE..."
        couleur = BLANC if victoire else ROUGE
        police_fin = pygame.font.SysFont("Arial", 74, bold=True)
        texte = police_fin.render(message, True, couleur)
        text_rect = texte.get_rect(center=(LARGEUR/2, HAUTEUR/2))
        screen.blit(texte, text_rect)
        
        # Instructions pour quitter
        police_instructions = pygame.font.SysFont("Arial", 24)
        instructions = police_instructions.render("Appuyez sur ESPACE pour quitter", True, BLANC)
        inst_rect = instructions.get_rect(center=(LARGEUR/2, HAUTEUR/2 + 100))
        screen.blit(instructions, inst_rect)
        pygame.display.flip()

        # Attendre que le joueur appuie sur ESPACE
        attente = True
        while attente:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        attente = False
                        return

    def initialiser_partie(self):
        self.temps_debut = time.time()
        self.dernier_requin = time.time()
        self.intervalle_requin = random.uniform(
            self.parametres.intervalle_requin_min,
            self.parametres.intervalle_requin_max
        )
        
        # Création du joueur avec est_joueur=True
        self.joueur = Poisson(
            50, HAUTEUR - 50,
            self.parametres.taille_initiale,
            self.parametres.score_initial,
            self.parametres.vies_initiales,
            est_joueur=True
        )
        self.poissons.clear()

    def gerer_evenements(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def gerer_mouvements_joueur(self):
        touches = pygame.key.get_pressed()
        direction_changed = False
        
        if touches[pygame.K_LEFT] and self.joueur.x > 0:
            self.joueur.x -= self.parametres.vitesse_actuelle_joueur
            if self.joueur.derniere_direction >= 0:
                self.joueur.image = self.joueur.image_gauche
                self.joueur.derniere_direction = -1
                direction_changed = True
                
        if touches[pygame.K_RIGHT] and self.joueur.x < LARGEUR - self.joueur.taille:
            self.joueur.x += self.parametres.vitesse_actuelle_joueur
            if self.joueur.derniere_direction <= 0:
                self.joueur.image = self.joueur.image_droite
                self.joueur.derniere_direction = 1
                direction_changed = True
                
        if touches[pygame.K_UP] and self.joueur.y > HAUTEUR_BANDE:
            self.joueur.y -= self.parametres.vitesse_joueur
        if touches[pygame.K_DOWN] and self.joueur.y < HAUTEUR - self.joueur.taille:
            self.joueur.y += self.parametres.vitesse_joueur
            
        self.joueur.rect.x, self.joueur.rect.y = self.joueur.x, self.joueur.y
        
        if direction_changed:
            self.joueur.image = pygame.transform.scale(
                self.joueur.image,
                (self.joueur.taille, self.joueur.taille)
            )

    def gerer_collisions(self):
        for poisson in self.poissons[:]:
            poisson.deplacer()
            if self.joueur.rect.colliderect(poisson.rect):
                if isinstance(poisson, Requin):
                    if not self.joueur.invulnerable:
                        self.joueur.vies -= 1
                        if self.joueur.vies > 0:  # Seulement activer l'invulnérabilité si encore en vie
                            self.joueur.invulnerable = True
                            self.joueur.invulnerable_timer = time.time()
                elif not self.joueur.invulnerable:
                    if poisson.score < self.joueur.score:
                        gain = calculer_gain(self.joueur.score, poisson.score, self.joueur.taille)
                        self.joueur.score += gain
                        self.joueur.taille += gain // 2
                        self.joueur.image = pygame.transform.scale(
                            self.joueur.image,
                            (self.joueur.taille, self.joueur.taille)
                        )
                        self.joueur.rect = self.joueur.image.get_rect(
                            topleft=(self.joueur.x, self.joueur.y)
                        )
                        if poisson in self.poissons:
                            self.poissons.remove(poisson)
                    else:
                        self.joueur.vies -= 1
                        if self.joueur.vies > 0:
                            self.joueur.invulnerable = True
                            self.joueur.invulnerable_timer = time.time()

    def generer_poissons(self):
        if (random.random() < self.parametres.taux_apparition_poisson 
            and len(self.poissons) < self.parametres.max_poissons):
            taille = random.randint(20, 100)
            score_poisson = generer_score_poisson(self.joueur.score)
            x = -taille if random.choice([True, False]) else LARGEUR
            y = random.randint(HAUTEUR_BANDE, HAUTEUR - taille)
            self.poissons.append(
                Poisson(x, y, taille, score_poisson, 
                random.randint(1, 3),
                direction=1 if x == -taille else -1)
            )

    def generer_requin(self, temps_actuel):
        if temps_actuel - self.dernier_requin >= self.intervalle_requin:
            x = LARGEUR
            y = random.randint(HAUTEUR_BANDE, HAUTEUR - 100)
            requin = Requin(x, y, direction=-1)
            requin.vitesse = self.parametres.vitesse_requin
            self.poissons.append(requin)
            self.dernier_requin = temps_actuel
            self.intervalle_requin = random.uniform(
                self.parametres.intervalle_requin_min,
                self.parametres.intervalle_requin_max
            )

    
    def verifier_defaite(self):
                # Nouveau système de vérification de défaite
                if self.joueur.vies <= 0:
                    return True
                
                # Vérifie si tous les poissons sont sortis ET que le score est insuffisant
                poissons_totaux = self.poissons_sortis + len(self.poissons)
                if poissons_totaux >= self.parametres.max_poissons and self.joueur.score < 300:
                    # Vérifie si tous les poissons restants sont hors écran
                    poissons_visibles = sum(1 for p in self.poissons if 0 <= p.x <= LARGEUR)
                    return poissons_visibles == 0
                    
                return False

    def gerer_bonus(self, temps_actuel):
        # Gestion des vitesses (buff/nerf)
        if self.joueur.dernier_bonus_buff and temps_actuel - self.joueur.dernier_bonus_buff <= self.parametres.duree_bonus:
            self.parametres.vitesse_actuelle_joueur = self.parametres.vitesse_base_joueur + 3
        else:
            self.parametres.vitesse_actuelle_joueur = self.parametres.vitesse_base_joueur
            if self.joueur.dernier_bonus_buff and temps_actuel - self.joueur.dernier_bonus_buff > self.parametres.duree_bonus:
                self.joueur.dernier_bonus_buff = None

        if self.joueur.dernier_bonus_nerf and temps_actuel - self.joueur.dernier_bonus_nerf <= self.parametres.duree_bonus:
            self.parametres.vitesse_actuelle_poisson = self.parametres.vitesse_base_poisson - 1
        else:
            self.parametres.vitesse_actuelle_poisson = self.parametres.vitesse_base_poisson
            if self.joueur.dernier_bonus_nerf and temps_actuel - self.joueur.dernier_bonus_nerf > self.parametres.duree_bonus:
                self.joueur.dernier_bonus_nerf = None

        # Gestion du bonus x2
        if self.bonus_timer:
            temps_ecoule = temps_actuel - self.bonus_timer
            if temps_ecoule > self.parametres.duree_bonus:
                self.bonus_actif = False
                self.bonus_timer = 0

        # Génération des bonus
        if (temps_actuel - self.dernier_bonus >= self.parametres.intervalle_bonus and 
            self.objet_bonus is None):
            self.objet_bonus = ObjetBonusAvance()
            self.objet_bonus.vitesse = self.parametres.vitesse_bonus
            self.dernier_bonus = temps_actuel + random.uniform(-5, 5)

        # Gestion des bonus existants
        if self.objet_bonus:
            self.objet_bonus.deplacer()
            self.objet_bonus.dessiner()
            
            if self.objet_bonus.rect.colliderect(self.joueur.rect):
                gestion_bonus_avance(self.joueur, self.objet_bonus)
                self.objet_bonus = None
            elif self.objet_bonus.rect.top > HAUTEUR:
                self.objet_bonus = None
    
    
    def boucle_principale(self):
        global vitesse_poisson_autre
        self.initialiser_partie()
        vitesse_initiale_poisson = self.parametres.vitesse_poisson_autre  # Sauvegarde de la vitesse initiale
    
        while True:
            temps_actuel = time.time()
            
           # Vérification des conditions de victoire/défaite
            if self.joueur.score >= 300:
                self.afficher_ecran_fin(True)
                return
            elif self.verifier_defaite():
                self.afficher_ecran_fin(False)
                return
            
            # Affichage du fond
            screen.blit(fonds_frames[self.fond_frame_index], (0, HAUTEUR_BANDE))
            self.fond_frame_index = (self.fond_frame_index + 1) % len(fonds_frames)
            


            # Initialisation de la vitesse de base si elle n'est pas encore définie
            if 'vitesse_initiale_poisson' not in locals():
                vitesse_initiale_poisson = self.parametres.vitesse_poisson_autre

            # Réinitialisation des vitesses après la fin des bonus
            print("Vitesse initiale poisson:", vitesse_initiale_poisson)
            print("Vitesse des poissons (avant bonus):", self.parametres.vitesse_poisson_autre)
            if self.joueur.dernier_bonus_nerf and temps_actuel - self.joueur.dernier_bonus_nerf <= self.parametres.duree_bonus:
                vitesse_poisson_autre = vitesse_initiale_poisson * 0.5  # Réduction de 50% pendant le nerf
            else:
                vitesse_poisson_autre = vitesse_initiale_poisson  # Retour à la vitesse normale
                if self.joueur.dernier_bonus_nerf and temps_actuel - self.joueur.dernier_bonus_nerf > self.parametres.duree_bonus:
                    self.joueur.dernier_bonus_nerf = None



            # Gestion des événements
            if not self.gerer_evenements():
                return
            
            # Mise à jour du jeu
            self.gerer_mouvements_joueur()
            self.generer_poissons()
            self.generer_requin(temps_actuel)
            self.gerer_collisions()
            self.gerer_bonus(temps_actuel)


            # Mise à jour des états
            self.joueur.gerer_invincibilite()
            
            # Affichage
            self.joueur.dessiner()
            for poisson in self.poissons:
                poisson.dessiner()
                
            afficher_score_et_taille(self.joueur, self.joueur.score, 
                               self.joueur.vies, self.temps_debut, 
                               f"{len(self.poissons)}/{self.parametres.max_poissons}")
            
            pygame.display.update()
            self.clock.tick(60)

        
# Au début du fichier, après les imports
bonus_actif = False
bonus_timer = 0
def jeu():
    global vitesse_poisson_autre
    # Configuration personnalisée (optionnelle)
    params = ParametresPartie()
    params.vitesse_joueur = 5  # Exemple de modification
    params.vies_initiales = 10  # Exemple de modification
    vitesse_poisson_autre = 3  
    partie = Partie(params)    # Création et lancement de la partie
    partie.boucle_principale()

if __name__ == "__main__":
    jeu()