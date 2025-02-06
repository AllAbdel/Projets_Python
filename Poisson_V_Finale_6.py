import random
import sys
import os
import time
import pygame
import math


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
HAUTEUR_BANDE = 80  # Hauteur de la bande noire
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
VAGUE_GTOD_IMAGE = r"img\event\vagueGtoD.png"
VAGUE_DTOG_IMAGE = r"img\event\vagueDtoG.png"
HAMECON_IMAGE = r"img\event\hamecon.png"

def charger_images_poisson(dossier, taille=(40, 40)):
    return [pygame.transform.scale(pygame.image.load(os.path.join(dossier, img)), taille) 
            for img in os.listdir(dossier) if img.endswith(".png")]

images_poissons_gauche = charger_images_poisson(dossier_images_gauche)
images_poissons_droite = charger_images_poisson(dossier_images_droite)

requin_image = pygame.image.load(r"img\event\requin.png")
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


class Poisson:
    def __init__(self, x, y, taille, score, vies, direction=1, est_joueur=False):
        self.x = x
        self.y = max(y, HAUTEUR_BANDE)
        self.taille = taille
        self.score = score
        self.vies = vies
        self.direction = direction
        self.est_joueur = est_joueur
        self.freeze = False
        self.freeze_timer = None
        self.freeze_duration = 20  # durée du freeze en secondes

        if est_joueur:
            # Si c'est un joueur, on initialise l'image du joueur
            self.vitesse = 3  # Vitesse fixe pour le joueur, par exemple
            self.image_droite = pygame.transform.scale(
                pygame.image.load(r"img\perso\evolution1toD.png"), 
                (self.taille, self.taille)
            )
            self.image_gauche = pygame.transform.scale(
                pygame.image.load(r"img\perso\evolution1toG.png"), 
                (self.taille, self.taille)
            )
            self.image = self.image_droite  # Image par défaut pour le joueur
        else:
            # Si c'est un poisson ennemi, on choisit une image aléatoire
            self.vitesse = random.randint(1, 3)  # vitesse aléatoire entre 1 et 3 pour chaque poisson
            self.vitesse_initiale = self.vitesse  # Sauvegarde la vitesse initiale
            self.image = random.choice(images_poissons_gauche if direction == 1 else images_poissons_droite)
            
        # Création du rectangle autour de l'image
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Autres attributs
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.invincibilite_duree = 5
        self.dernier_bonus_coeur = None
        self.dernier_bonus_bouclier = None
        self.dernier_bonus_buff = None
        self.dernier_bonus_nerf = None
        self.dernier_bonus_freeze = None
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
        # Effet rougâtre et clignotement lors de l'invincibilité
        if self.invulnerable:
            if (time.time() - self.invulnerable_timer) % 1 < 0.75:
                surface_rougeatre = pygame.Surface((self.taille, self.taille), pygame.SRCALPHA)
                surface_rougeatre.blit(self.image, (0, 0))
                surface_rougeatre.fill((255, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(pygame.transform.scale(surface_rougeatre, (int(self.taille * 1.2), int(self.taille * 1.2))), 
                        (self.x - self.taille * 0.1, self.y - self.taille * 0.1))
        else:
            screen.blit(self.image, (self.x, self.y))
        
        # Affichage du score au-dessus du poisson en noir
        if not isinstance(self, (Requin, PoissonVague)):  # Ne pas afficher le score pour les requins et les vagues
            texte = police.render(str(self.score), True, NOIR)
            text_rect = texte.get_rect(center=(self.rect.centerx, self.rect.top - 10))
            screen.blit(texte, text_rect)

    def deplacer(self):
        if not self.freeze:  # Ne déplace le poisson que s'il n'est pas gelé
            self.x += self.direction * vitesse_poisson_autre
        # Le reste de la méthode reste inchangé
        self.y = max(HAUTEUR_BANDE, min(self.y, HAUTEUR - self.taille))
        self.rect.x, self.rect.y = self.x, self.y
        if self.rect.left > LARGEUR or self.rect.right < 0:
            if self in poissons:
                poissons.remove(self)
        self.gerer_invincibilite()

class MenuPause:
    def __init__(self, largeur, hauteur):
        self.largeur = largeur
        self.hauteur = hauteur
        
        # Création des boutons
        bouton_largeur = 300
        bouton_hauteur = 60
        espace_entre_boutons = 30
        y_depart = hauteur // 2 - (bouton_hauteur * 2 + espace_entre_boutons * 1.5)
        x_centre = largeur // 2 - bouton_largeur // 2

        self.boutons = {
            'reprendre': MenuBouton(x_centre, y_depart, 
                            bouton_largeur, bouton_hauteur, "Reprendre"),
            'options': MenuBouton(x_centre, y_depart + bouton_hauteur + espace_entre_boutons,
                            bouton_largeur, bouton_hauteur, "Options"),
            'menu_principal': MenuBouton(x_centre, y_depart + (bouton_hauteur + espace_entre_boutons) * 2,
                            bouton_largeur, bouton_hauteur, "Menu Principal"),
            'quitter': MenuBouton(x_centre, y_depart + (bouton_hauteur + espace_entre_boutons) * 3,
                            bouton_largeur, bouton_hauteur, "Quitter")
        }

    def afficher(self, screen):
        # Créer un fond semi-transparent gris
        surface_pause = pygame.Surface((self.largeur, self.hauteur), pygame.SRCALPHA)
        surface_pause.fill((128, 128, 128, 2))  # Gris transparent
        screen.blit(surface_pause, (0, 0))

        # Titre Pause
        police_titre = pygame.font.SysFont("impact", 72)
        titre = police_titre.render("PAUSE", True, (255, 215, 0))
        titre_rect = titre.get_rect(center=(self.largeur // 2, 150))
        screen.blit(titre, titre_rect)

        # Affichage et gestion des boutons
        pos_souris = pygame.mouse.get_pos()
        for bouton in self.boutons.values():
            bouton.gerer_survol(pos_souris)
            bouton.dessiner(screen)

    def gerer_clic(self, pos_souris):
        for nom, bouton in self.boutons.items():
            if bouton.est_clique(pos_souris):
                return nom
        return None

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
            "nerf": pygame.transform.scale(pygame.image.load(r"img\tres\nerf.png"), (30, 30)),
            "freeze": pygame.transform.scale(pygame.image.load(r"img\tres\freeze.png"), (30, 30)) # Ajoutez cette ligne
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
        
    elif objet_bonus.type_bonus == "freeze":
        temps_actuel = time.time()
        # Applique le freeze à tous les poissons
        for poisson in poissons:
            if not isinstance(poisson, (Requin, PoissonVague)):  # Exclure requins et vagues
                poisson.freeze = True
                poisson.freeze_timer = temps_actuel
        joueur.dernier_bonus_freeze = temps_actuel


def calculer_gain(joueur_score, poisson_score, joueur_taille):
    gain = int(1 + (poisson_score / joueur_score) * (joueur_taille / 10))
    return gain * 2 if bonus_actif else gain

def afficher_score_et_taille(joueur, score, vies, temps_debut, nb_poissons_max):
    global bonus_actif, bonus_timer  # Déclaration des variables globales
    
    # Dessiner la bande gold dark en haut
    pygame.draw.rect(screen, gold_dark, (0, 0, LARGEUR, HAUTEUR_BANDE))
    pygame.draw.rect(screen, NOIR, (0, 0, LARGEUR, HAUTEUR_BANDE), 3)  # Contour Noir autour de la bande

    # Chargement et redimensionnement de l'image du cœur
    coeur_image = pygame.transform.scale(pygame.image.load(r"img\tres\coeur.png"), (25, 25))
    # Chargement et redimensionnement de l'emoji poisson
    poisson_emoji = pygame.transform.scale(pygame.image.load(r"img\tres\poisson.png"), (25, 25))
    # Chargement et redimensionnement de l'emoji score
    score_emoji = pygame.transform.scale(pygame.image.load(r"img\tres\score.png"), (250, 155))
    # Chargement et redimensionnement de l'emoji score
    bouclier_emoji = pygame.transform.scale(pygame.image.load(r"img\tres\bouclier.png"), (35, 35))

    
    screen.blit(score_emoji, (-25, -42))  # Position de l'emoji score
    # Affichage du score, vies et nombre de poissons
    police = pygame.font.SysFont("impact", 20, bold=False)
    screen.blit(police.render(f"{score}", True, gold_light), (85, 33))
    police = pygame.font.SysFont("arial", 20, bold=True)


    # Affichage des vies avec l'emoji cœur (décalé vers la droite)
    vies_x = LARGEUR // 5  # Position X de départ pour les cœurs (augmentée)
    for i in range(vies):
        screen.blit(coeur_image, (vies_x + (i * 20), HAUTEUR_BANDE // 2.1))  # 30 pixels d'espacement entre chaque cœur
    
    # Affichage du nombre de poissons avec l'emoji
    screen.blit(poisson_emoji, (LARGEUR // 4, HAUTEUR_BANDE // 8))  # Position de l'emoji
    screen.blit(police.render(f": {nb_poissons_max}", True, BLANC), (LARGEUR // 3.65, HAUTEUR_BANDE // 7))  # Texte après l'emoji
  
  
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
            inv_texte = police.render(f"Invincibilité durant ({temps_restant}s)", True, ROUGE)
            screen.blit(bouclier_emoji, (LARGEUR // 1.87, HAUTEUR_BANDE // 9.5))  # Position de l'emoji
            text_rect = inv_texte.get_rect(center=(LARGEUR // 1.85, HAUTEUR_BANDE // 1.6))
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
        screen.blit(plus_text, (int(LARGEUR // 6.3), HAUTEUR_BANDE // 2))
        screen.blit(coeur_image, (int(LARGEUR // 6), HAUTEUR_BANDE // 2.1))

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

class Goldfish(Poisson):
    def __init__(self, x, y, score_joueur, direction=1):
        super().__init__(x, y, taille=40, score=score_joueur, vies=0, direction=direction)
        self.image = pygame.image.load(r"img\event\goldfishGtoD.png" if direction == 1 else r"img\event\goldfishDtoG.png")
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.vitesse = 6

    def deplacer(self):
        self.x += self.direction * self.vitesse
        self.y = max(HAUTEUR_BANDE, min(self.y, HAUTEUR - self.taille))
        self.rect.x, self.rect.y = self.x, self.y
        if self.rect.left > LARGEUR or self.rect.right < 0:
            if self in poissons:
                poissons.remove(self)
                

class Meduse:
    def __init__(self):
        self.images = [
            pygame.transform.scale(pygame.image.load(f"img/event/meduse{i}.png"), (40, 40)) 
            for i in range(1, 6)
        ]
        self.image_courante = random.choice(self.images)
        self.x = random.randint(0, LARGEUR - 40)
        self.y = HAUTEUR
        self.vitesse = 2
        self.rect = self.image_courante.get_rect(topleft=(self.x, self.y))
        
    def deplacer(self):
        self.y -= self.vitesse
        self.rect.y = self.y
        
    def dessiner(self, screen):
        screen.blit(self.image_courante, (self.x, self.y))
    
    def verifier_collision(self, joueur):
        if self.rect.colliderect(joueur.rect):
            joueur.freeze = True
            joueur.freeze_timer = time.time()
            joueur.vies -= 1
            return True
        return False


class AlerteVague:
    def __init__(self):
        self.alerte_image = pygame.transform.scale(pygame.image.load(r"img\event\alerte.png"), (40, 40))
        self.vague_gtod = pygame.transform.scale(pygame.image.load(VAGUE_GTOD_IMAGE), (45,45))
        self.vague_dtog = pygame.transform.scale(pygame.image.load(VAGUE_DTOG_IMAGE), (45,45))
        self.timer = 5
        self.temps_debut = time.time()
        self.scale_factor = 1.0
        self.scale_direction = 0.05
        
        # Définir la zone sûre
        self.zone_sure = random.randint(HAUTEUR_BANDE + 90, HAUTEUR - 90)
        self.epaisseur_zone = 90
        
        # Décider de la direction de la vague dès l'initialisation
        self.direction_vague = 1 if random.choice([True, False]) else -1
        
        self.vague_active = False
        self.vague_terminee = False
        self.duree_vague = 5
        self.poissons_vague = []
        self.temps_debut_vague = None
        
    def update(self):
        temps_actuel = time.time()
        temps_ecoule = temps_actuel - self.temps_debut

        # Animation de l'icône d'alerte
        self.scale_factor += self.scale_direction
        if self.scale_factor >= 1.3 or self.scale_factor <= 0.7:
            self.scale_direction *= -1

        # Vérifier si la vague doit commencer
        if temps_ecoule >= self.timer and not self.vague_active:
            self.vague_active = True
            self.temps_debut_vague = temps_actuel

        # Vérifier si la vague est terminée
        if self.vague_active and temps_actuel - self.temps_debut_vague >= self.duree_vague:
            self.vague_terminee = True

        return self.vague_terminee

    def dessiner(self, screen, joueur_x, joueur_y):
        if not self.vague_active:
            taille_actuelle = int(40 * self.scale_factor)
            alerte_scalee = pygame.transform.scale(self.alerte_image, (taille_actuelle, taille_actuelle))
            screen.blit(alerte_scalee, (joueur_x, joueur_y - 50))
        else:
            # Suppression du dessin de la zone verte
            surface_zones = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            
            # Zones rouges là où il y a des poissons
            for poisson in self.poissons_vague:
                pygame.draw.rect(surface_zones, (255, 0, 0, 50), 
                                (0, poisson.y, LARGEUR, 45))
            
            screen.blit(surface_zones, (0, 0))
            


class PoissonVague(Poisson):
    def __init__(self, x, y, direction):
        super().__init__(x, y, taille=45, score=0, vies=0, direction=direction)
        self.vitesse = 10  # On définit la vitesse à 10
        image_path = r"img\event\vagueGtoD.png" if direction == 1 else r"img\event\vagueDtoG.png"
        self.image = pygame.transform.scale(pygame.image.load(image_path), (45, 45))

    def deplacer(self):
        self.x += self.direction * self.vitesse  # Utilisation de self.vitesse au lieu de vitesse_poisson_autre
        self.rect.x = self.x
        self.rect.y = self.y
        
        if self.rect.left > LARGEUR or self.rect.right < 0:
            if self in poissons:
                poissons.remove(self)


def generer_poissons_vague(alerte_vague):
    poissons_vague = []
    espacement = 45

    zone_sure_bas = alerte_vague.zone_sure - 45
    zone_sure_haut = alerte_vague.zone_sure + 45
    
    # Position de départ selon la direction
    x_depart = -40 if alerte_vague.direction_vague > 0 else LARGEUR

    for y in range(HAUTEUR_BANDE, HAUTEUR - 45, espacement):
        if zone_sure_bas <= y <= zone_sure_haut:
            continue
        
        # Tous les poissons vont dans la même direction
        poissons_vague.append(PoissonVague(x_depart, y, alerte_vague.direction_vague))

    return poissons_vague

class Requin(Poisson):
    def __init__(self, x, y, direction=1):
        super().__init__(x, y, taille=120, score=0, vies=0, direction=direction)
        self.image = requin_image
        self.vitesse = 1
        # Agrandir la hitbox
        self.rect = self.image.get_rect(topleft=(x, y))
        self.rect = self.rect.inflate(20, 20)  # Augmenter la taille du rectangle de collision


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
        self.intervalle_bonus = 1  # Nouveau paramètre : intervalle entre les bonus
        self.dernier_bonus = 0  # Nouveau paramètre : temps du dernier bonus
        
        # Paramètres d'apparition des poissons
        self.taux_apparition_poisson = 0.05  # Augmenté à 3% de chance par frame
        self.max_poissons = 50
        
        # Paramètres d'apparition des requins
        self.intervalle_requin_min = 10  # secondes
        self.intervalle_requin_max = 20  # secondes
        
        # Paramètres du joueur
        self.vies_initiales = 5
        self.taille_initiale = 40
        self.score_initial = 10
        
        # Paramètres d'invincibilité
        self.duree_invincibilite = 5  # secondes
        self.duree_invincibilite_bouclier = 20  # secondes


class MenuBouton:
    def __init__(self, x, y, largeur, hauteur, texte):
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.texte = texte
        self.survol = False
        
    def dessiner(self, surface):
        couleur = (255, 215, 0)  if self.survol else (218, 165, 32) 
        pygame.draw.rect(surface, couleur, self.rect, border_radius=12)
        pygame.draw.rect(surface, NOIR, self.rect, 3, border_radius=12)
        
        police = pygame.font.SysFont("impact", 36)
        texte_surface = police.render(self.texte, True, NOIR)
        texte_rect = texte_surface.get_rect(center=self.rect.center)
        surface.blit(texte_surface, texte_rect)
        
    def gerer_survol(self, pos_souris):
        self.survol = self.rect.collidepoint(pos_souris)
        
    def est_clique(self, pos_souris):
        return self.rect.collidepoint(pos_souris)

class Menu:
    global gold_dark, gold_light

    def __init__(self, largeur, hauteur):
        self.largeur = largeur
        self.hauteur = hauteur
        self.musique_choisie = None
        self.musiques_disponibles = [
            "0001.ogg", "0002.ogg", "0003.ogg", "0004.ogg"
        ]  # Liste des musiques disponibles
        self.musique_par_defaut = "menu.ogg"  # Musique par défaut
        self.chemin_musique = "sons/"  # Dossier où sont stockées les musiques
        self.ecran = pygame.display.set_mode((largeur, hauteur))
        pygame.display.set_caption("Le Jeu du Poisson - Menu")

        # Chargement du fond animé
        self.dossier_fond = r"img\fond"
        self.fonds_frames = [pygame.transform.scale(
                            pygame.image.load(os.path.join(self.dossier_fond, f"frame_({i}).png")),
                            (largeur, hauteur)) for i in range(96)]
        self.fond_frame_index = 0

        # Création des boutons
        bouton_largeur = 300
        bouton_hauteur = 60
        espace_entre_boutons = 30
        y_depart = hauteur // 2 - (bouton_hauteur * 2 + espace_entre_boutons * 1.5)
        x_centre = largeur // 2 - bouton_largeur // 2

        self.boutons = {
            'jouer': MenuBouton(x_centre, y_depart, 
                                bouton_largeur, bouton_hauteur, "Jouer"),
            'comment_jouer': MenuBouton(x_centre, y_depart + bouton_hauteur + espace_entre_boutons,
                                bouton_largeur, bouton_hauteur, "Comment Jouer"),
            'options': MenuBouton(x_centre, y_depart + (bouton_hauteur + espace_entre_boutons) * 2,
                                bouton_largeur, bouton_hauteur, "Options"),
            'quitter': MenuBouton(x_centre, y_depart + (bouton_hauteur + espace_entre_boutons) * 3,
                                bouton_largeur, bouton_hauteur, "Quitter")
        }

        # Lancer la musique dès le début
        self.jouer_musique()


    def jouer_musique(self):
        """Joue la musique choisie ou la musique par défaut si aucune n'est sélectionnée."""
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.stop()
        musique_a_jouer = os.path.join(
            self.chemin_musique,
            self.musique_choisie if self.musique_choisie else self.musique_par_defaut
        )
        pygame.mixer.music.load(musique_a_jouer)
        pygame.mixer.music.play(-1)  # Lecture en boucle
        
    def afficher_texte_comment_jouer(self):
        running = True
        offset_y = 0  # Variable de défilement

        # Taille pour les images réduites
        image_width, image_height = 50, 50

        # Chargement de la police et redimensionnement des images
        police_texte = pygame.font.SysFont("arial", 24)
        img_poisson = pygame.transform.scale(pygame.image.load("img/GtoD/GtoD_(1).png"), (image_width, image_height))
        img_bonus_buff = pygame.transform.scale(pygame.image.load("img/tres/buff.png"), (image_width, image_height))
        img_bonus_nerf = pygame.transform.scale(pygame.image.load("img/tres/nerf.png"), (image_width, image_height))
        img_bonus_bouclier = pygame.transform.scale(pygame.image.load("img/tres/bouclier.png"), (image_width, image_height))
        img_requin = pygame.transform.scale(pygame.image.load("img/event/requin.png"), (image_width, image_height))
        img_bonus_attraction = pygame.transform.scale(pygame.image.load("img/tres/aimant.png"), (image_width, image_height))
        img_bonus_Sattraction = pygame.transform.scale(pygame.image.load("img/tres/superaimant.png"), (image_width, image_height))
        img_bonus_freeze = pygame.transform.scale(pygame.image.load("img/tres/freeze.png"), (image_width, image_height))
        img_bonus_x2 = pygame.transform.scale(pygame.image.load("img/tres/X2.png"), (image_width, image_height))
        img_bonus_x4 = pygame.transform.scale(pygame.image.load("img/tres/X4.png"), (image_width, image_height))
        img_poisson_dore = pygame.transform.scale(pygame.image.load("img/event/goldfishGtoD.png"), (image_width, image_height))
        img_bombe = pygame.transform.scale(pygame.image.load("img/event/bombe.png"), (image_width, image_height))
        img_canne_peche = pygame.transform.scale(pygame.image.load("img/event/hamecon.png"), (image_width, image_height))
        img_vague = pygame.transform.scale(pygame.image.load("img/event/vagueGtoD.png"), (70, 70))

        # Instructions avec texte et images
        textes = [
            "Bienvenue dans Le Jeu du Poisson !",
            "",
            "- Utilisez les flèches directionnelles pour vous déplacer",
            "- Ou utilisez la molette pour vous déplacer",
            "",
            "- Mangez les poissons plus petits que vous pour grandir",
            "- Évitez les poissons plus gros comme", img_poisson, "et surtout les", img_requin, "!",
            "- Attrapez les bonus pour obtenir des avantages",
            "",
            "Voici les bonus disponibles dans le jeu :",
            "",
            "- Bonus Buff (Vitesse) :", img_bonus_buff,
            "  Augmente temporairement votre vitesse pendant 20 secondes.",
            "",
            "- Bonus Nerf :", img_bonus_nerf,
            "  Ralentit tous les ennemis pendant 20 secondes.",
            "",
            "- Bonus Bouclier :", img_bonus_bouclier,
            "  Vous rend invincible pendant 20 secondes,",
            "  mais vous ne pouvez pas manger de poissons durant cette période.",
            "",
            "- Bonus Attraction :", img_bonus_attraction,
            "  Attire les poissons plus petits vers vous dans un certain rayon.",
            "",
            "- Super Attraction :", img_bonus_Sattraction,
            "  Attire tous les petits poissons, même éloignés.",
            "",
            "- Bonus Freeze :", img_bonus_freeze,
            "  Gèle tous les ennemis et les empêche de bouger pendant 15 secondes.",
            "",
            "- Multiplicateur de score x2 :", img_bonus_x2,
            "  Double votre score pendant un certain temps.",
            "",
            "- Multiplicateur de score x4 :", img_bonus_x4,
            "  Multiplie votre score par 4 pendant la même durée que le x2.",
            "",
            "Événements spéciaux pendant le jeu :",
            "",
            "- Poisson doré :", img_poisson_dore,
            "  Un poisson rapide qui peut venir de gauche ou de droite.",
            "  Attrapez-le pour obtenir un bonus aléatoire.",
            "",
            "- Vague de poissons :", img_vague,
            "  Apparition en masse de poissons avec 25% de chance d'apparition pendant 5 secondes.",
            "",
            "- Bombe :", img_bombe,
            "  Une bombe descend dans l'eau et explose. Si elle est touchée, vous perdez une vie.",
            "  Si vous êtes à une distance moyenne de l'explosion, vous serez repoussé en arrière.",
            "",
            "- Canne à pêche :", img_canne_peche,
            "  La canne apparaît et tourne en cercle pendant 10 secondes.",
            "  Évitez-la pour ne pas perdre une vie.",
            "",
            "Objectif :",
            "- Atteignez un score de 300 pour gagner !",
            "",
            "Appuyez sur ÉCHAP pour revenir au menu"
        ]

        while running:
            # Gérer l'arrière-plan et le fond semi-transparent
            self.ecran.blit(self.fonds_frames[self.fond_frame_index], (0, 0))
            self.fond_frame_index = (self.fond_frame_index + 1) % len(self.fonds_frames)
            surface = pygame.Surface((self.largeur - 100, self.hauteur - 100), pygame.SRCALPHA)
            pygame.draw.rect(surface, (0, 0, 0, 180), surface.get_rect(), border_radius=15)
            self.ecran.blit(surface, (50, 50))

            # Affichage du titre
            police_titre = pygame.font.SysFont("impact", 48)
            titre = police_titre.render("Comment Jouer", True, (255, 215, 0))
            titre_rect = titre.get_rect(center=(self.largeur // 2, 100))
            self.ecran.blit(titre, titre_rect)

            # Définir la zone de découpage pour limiter l'affichage du texte
            clip_rect = pygame.Rect(75, 150, self.largeur - 150, self.hauteur - 200)
            self.ecran.set_clip(clip_rect)  # Activer le découpage

            # Affichage des textes et images avec défilement
            y_texte = 200 + offset_y
            for ligne in textes:
                if isinstance(ligne, pygame.Surface):
                    # Affichage de l'image
                    image_rect = ligne.get_rect(center=(self.largeur // 2, y_texte))
                    self.ecran.blit(ligne, image_rect)
                    y_texte += image_rect.height + 10
                else:
                    # Affichage du texte
                    texte_surface = police_texte.render(ligne, True, (255, 255, 255))
                    texte_rect = texte_surface.get_rect(center=(self.largeur // 2, y_texte))
                    self.ecran.blit(texte_surface, texte_rect)
                    y_texte += 30  # Espacement entre les lignes de texte

            # Désactiver le découpage après avoir dessiné le contenu défilable
            self.ecran.set_clip(None)

            # Gérer les événements de défilement avec la molette de la souris et les touches
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_DOWN:
                        offset_y -= 20
                    elif event.key == pygame.K_UP:
                        offset_y += 20
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # Molette vers le haut
                        offset_y += 20
                    elif event.button == 5:  # Molette vers le bas
                        offset_y -= 20

            pygame.display.flip()



    def afficher_options(self):
        """Affiche le menu Options et permet de choisir une musique et ajuster le volume."""
        self.jouer_musique()  # Jouer la musique au début du menu Options
        selection_index = 0  # Index de la musique sélectionnée
        volume = pygame.mixer.music.get_volume()  # Récupérer le volume actuel
        volume_bar_x = self.largeur // 2 - 150
        volume_bar_y = self.hauteur - 200
        volume_bar_width = 300
        volume_bar_height = 20

        running = True

        while running:
            self.ecran.blit(self.fonds_frames[self.fond_frame_index], (0, 0))
            self.fond_frame_index = (self.fond_frame_index + 1) % len(self.fonds_frames)

            # Rectangle semi-transparent
            surface = pygame.Surface((self.largeur - 100, self.hauteur - 100), pygame.SRCALPHA)
            pygame.draw.rect(surface, (0, 0, 0, 180), surface.get_rect(), border_radius=15)
            self.ecran.blit(surface, (50, 50))

            # Titre
            police_titre = pygame.font.SysFont("impact", 48)
            titre = police_titre.render("Options - Choix de musique", True, (255, 215, 0))
            titre_rect = titre.get_rect(center=(self.largeur // 2, 100))
            self.ecran.blit(titre, titre_rect)

            # Afficher la liste des musiques
            police_musique = pygame.font.SysFont("arial", 30)
            for i, musique in enumerate(self.musiques_disponibles):
                couleur = (255, 255, 255) if i != selection_index else (255, 215, 0)  # Highlight sélection
                texte = police_musique.render(musique, True, couleur)
                texte_rect = texte.get_rect(center=(self.largeur // 2, 200 + i * 50))
                self.ecran.blit(texte, texte_rect)

            # Barre de volume
            # Barre de fond
            pygame.draw.rect(self.ecran, (100, 100, 100), (volume_bar_x, volume_bar_y, volume_bar_width, volume_bar_height))
            # Barre de volume ajustable
            pygame.draw.rect(
                self.ecran, 
                (255, 215, 0), 
                (volume_bar_x, volume_bar_y, int(volume_bar_width * volume), volume_bar_height)
            )
            # Curseur
            pygame.draw.circle(
                self.ecran, 
                (255, 255, 255), 
                (volume_bar_x + int(volume_bar_width * volume), volume_bar_y + volume_bar_height // 2), 
                10
            )
            
            # Instructions pour volume
            instructions_volume = police_musique.render("Ajustez le volume avec la souris", True, gold_dark)
            self.ecran.blit(instructions_volume, (self.largeur // 2 - 200, self.hauteur - 250))

            # Instructions générales
            instructions = police_musique.render(
                "Flèches pour naviguer | Entrée pour sélectionner | Échap pour revenir",
                True, gold_dark
            )
            instructions_rect = instructions.get_rect(center=(self.largeur // 2, self.hauteur - 100))
            self.ecran.blit(instructions, instructions_rect)

            # Gérer les événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_DOWN:
                        selection_index = (selection_index + 1) % len(self.musiques_disponibles)
                    elif event.key == pygame.K_UP:
                        selection_index = (selection_index - 1) % len(self.musiques_disponibles)
                    elif event.key == pygame.K_RETURN:
                        self.musique_choisie = self.musiques_disponibles[selection_index]
                        self.jouer_musique()  # Changer immédiatement la musique
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        mouse_x, mouse_y = event.pos
                        if volume_bar_x <= mouse_x <= volume_bar_x + volume_bar_width and \
                            volume_bar_y <= mouse_y <= volume_bar_y + volume_bar_height:
                            # Ajuster le volume en fonction de la position de la souris
                            volume = (mouse_x - volume_bar_x) / volume_bar_width
                            pygame.mixer.music.set_volume(volume)

            pygame.display.flip()

            
    def executer(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Affichage du fond animé
            self.ecran.blit(self.fonds_frames[self.fond_frame_index], (0, 0))
            self.fond_frame_index = (self.fond_frame_index + 1) % len(self.fonds_frames)
            
            # Titre du jeu
            police_titre = pygame.font.SysFont("impact", 72)
            titre = police_titre.render("Le Jeu du Poisson", True, (250,215,0))
            titre_rect = titre.get_rect(center=(self.largeur // 2, 150))
            self.ecran.blit(titre, titre_rect)
            
            # Mise à jour des boutons
            pos_souris = pygame.mouse.get_pos()
            for bouton in self.boutons.values():
                bouton.gerer_survol(pos_souris)
                bouton.dessiner(self.ecran)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        if self.boutons['jouer'].est_clique(pos_souris):
                            return "jouer"
                        elif self.boutons['comment_jouer'].est_clique(pos_souris):
                            self.afficher_texte_comment_jouer()
                        elif self.boutons['options'].est_clique(pos_souris):
                            self.afficher_options()
                        elif self.boutons['quitter'].est_clique(pos_souris):
                            pygame.quit()
                            sys.exit()
            
            pygame.display.flip()
            clock.tick(60)
            
class CannePeche:
    def __init__(self, centre_x, centre_y):
        self.image = pygame.transform.scale(pygame.image.load(r"img\event\hamecon.png"),(30,30))
        self.taille = 40
        self.angle = 0
        self.vitesse_rotation = 3
        self.rayon_rotation = 25
        self.centre_x = centre_x
        self.centre_y = centre_y
        self.x = self.centre_x + self.rayon_rotation
        self.y = self.centre_y
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.duree = 10
        self.temps_creation = time.time()
        self.en_rotation = True
        self.a_touche_joueur = False
        self.particules_disparition = []

        
        # Particules d'éclaboussure
        self.particules_debut = []
        self.particules_fin = []
        
    def creer_eclaboussure(self, x, y, liste_particules):
        for _ in range(20):  # Nombre de particules
            liste_particules.append(EclaboussureParticule(x, y))
    
    def update(self):
        temps_ecoule = time.time() - self.temps_creation

        if self.a_touche_joueur:
            # Créer des particules de disparition si ce n'est pas déjà fait
            if not self.particules_disparition:
                self.creer_eclaboussure(self.x, self.y, self.particules_disparition)
            
            # Mettre à jour les particules de disparition
            self.particules_disparition = [p for p in self.particules_disparition if p.update()]
            return len(self.particules_disparition) > 0

        # Vérifier si l'événement doit se terminer
        if temps_ecoule >= self.duree + 1:
            return False

        # Si la durée totale de l'événement n'est pas encore écoulée
        if temps_ecoule >= self.duree:
            self.en_rotation = False
            
            # Éclaboussure de fin
            if not self.particules_fin:
                self.creer_eclaboussure(self.x, self.y, self.particules_fin)
            
            # Mettre à jour les particules de fin
            self.particules_fin = [p for p in self.particules_fin if p.update()]

        if self.en_rotation:
            # Rotation de l'hameçon autour du centre
            self.angle += self.vitesse_rotation
            self.x = self.centre_x + math.cos(math.radians(self.angle)) * self.rayon_rotation
            self.y = self.centre_y + math.sin(math.radians(self.angle)) * self.rayon_rotation
            self.rect.topleft = (self.x, self.y)

        return True

    def dessiner(self, screen):
        if not self.a_touche_joueur:
            # Dessiner le fil et l'hameçon normalement
            pygame.draw.line(screen, (100, 100, 100), (self.centre_x, HAUTEUR_BANDE), 
                           (self.x + self.taille//2, self.y), 2)
            screen.blit(self.image, (self.x, self.y))
        
        # Dessiner les particules
        for particule in self.particules_debut:
            particule.dessiner(screen)
        for particule in self.particules_fin:
            particule.dessiner(screen)
        for particule in self.particules_disparition:
            particule.dessiner(screen)
            



class Bombe:
    def __init__(self, x):
        self.image = pygame.transform.scale(pygame.image.load(r"img\event\bombe.png"), (40, 40))
        self.x = x
        self.y = HAUTEUR_BANDE
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.vitesse_descente = 3
        self.timer = 8
        self.temps_creation = time.time()
        self.hauteur_cible = HAUTEUR - 200
        self.en_descente = True
        self.a_explose = False
        self.rayon_mortel = 120  # Rayon multiplié par 4
        self.rayon_repulsion = 200  # Rayon multiplié par 4
        self.explosion = None
        self.afficher_zones = True  # Pour l'affichage des zones de danger
        self.animation_repulsion = None


    def update(self, joueur):
        temps_actuel = time.time()
        temps_ecoule = temps_actuel - self.temps_creation

        if self.en_descente and self.y < self.hauteur_cible:
            self.y += self.vitesse_descente
            self.rect.y = self.y
        else:
            self.en_descente = False

        if temps_ecoule >= self.timer and not self.a_explose:
            self.explosion = Explosion(self.x + 20, self.y + 20)
            self.exploser(joueur)
            self.a_explose = True

        if hasattr(self, 'onde_choc'):
            if not self.onde_choc.update():
                delattr(self, 'onde_choc')

        if self.animation_repulsion:
            if not self.animation_repulsion.update():
                self.animation_repulsion = None

        # Collision avec la bombe
        if not self.a_explose and joueur.rect.colliderect(self.rect):
            if not joueur.invulnerable:
                joueur.vies -= 1
                joueur.invulnerable = True
                joueur.invulnerable_timer = time.time()
            self.explosion = Explosion(self.x + 20, self.y + 20)
            self.exploser(joueur)
            self.a_explose = True
            return True

        return False

    def exploser(self, joueur):
        centre_bombe = (self.x + 20, self.y + 20)
        centre_joueur = (joueur.x + joueur.taille/2, joueur.y + joueur.taille/2)
        
        distance = ((centre_joueur[0] - centre_bombe[0])**2 + 
                (centre_joueur[1] - centre_bombe[1])**2)**0.5

        # Création de l'onde de choc dans tous les cas
        onde_choc = OndeChoc(centre_bombe[0], centre_bombe[1])
        self.onde_choc = onde_choc

        if not joueur.invulnerable:
            if distance <= self.rayon_mortel:
                joueur.vies -= 1
                joueur.invulnerable = True
                joueur.invulnerable_timer = time.time()
                dx = centre_joueur[0] - centre_bombe[0]
                dy = centre_joueur[1] - centre_bombe[1]
                norme = (dx**2 + dy**2)**0.5
                if norme > 0:
                    dx = dx/norme * 240
                    dy = dy/norme * 240
                    self.animation_repulsion = AnimationRepulsion(joueur, dx, dy, 240)
            elif distance <= self.rayon_repulsion:
                dx = centre_joueur[0] - centre_bombe[0]
                dy = centre_joueur[1] - centre_bombe[1]
                norme = (dx**2 + dy**2)**0.5
                if norme > 0:
                    dx = dx/norme * 200
                    dy = dy/norme * 200
                    self.animation_repulsion = AnimationRepulsion(joueur, dx, dy, 200)

    def dessiner(self, screen):
        if not self.a_explose:
            # Dessiner les zones de danger avec transparence
            surface_zones = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            
            # Zone de répulsion (jaune transparent)
            pygame.draw.circle(surface_zones, (255, 255, 0, 50), 
                             (self.x + 20, self.y + 20), 
                             self.rayon_repulsion)
            
            # Zone mortelle (rouge transparent)
            pygame.draw.circle(surface_zones, (255, 0, 0, 50), 
                             (self.x + 20, self.y + 20), 
                             self.rayon_mortel)
            
            screen.blit(surface_zones, (0, 0))
            screen.blit(self.image, self.rect)
            
            # Timer
            temps_restant = max(0, int(self.timer - (time.time() - self.temps_creation)))
            police = pygame.font.SysFont("Arial", 20)
            texte = police.render(str(temps_restant), True, (255, 0, 0))
            screen.blit(texte, (self.x + 15, self.y - 20))
        
        if hasattr(self, 'onde_choc'):
            self.onde_choc.dessiner(screen)
        if self.animation_repulsion:
            self.animation_repulsion.dessiner(screen)
            
        
class Particule:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.vie = random.randint(20, 40)
        self.couleur = random.choice([(255, 165, 0), (255, 69, 0), (255, 0, 0)])  # Orange, Rouge-Orange, Rouge
        self.taille = random.randint(2, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vie -= 1
        self.taille = max(0, self.taille - 0.1)
        return self.vie > 0

    def dessiner(self, screen):
        pygame.draw.circle(screen, self.couleur, (int(self.x), int(self.y)), int(self.taille))

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.particules = [Particule(x, y) for _ in range(50)]
        self.duree = 40  # Durée de l'animation en frames
        self.frame_actuelle = 0

    def update(self):
        self.particules = [p for p in self.particules if p.update()]
        self.frame_actuelle += 1
        return self.frame_actuelle < self.duree

    def dessiner(self, screen):
        for p in self.particules:
            p.dessiner(screen)
            
class EclaboussureParticule:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rayon = random.uniform(2, 5)
        self.vitesse_x = random.uniform(-2, 2)
        self.vitesse_y = random.uniform(-3, 0)
        self.couleur = (135, 206, 235)  # Bleu clair de l'eau
        self.vie = random.randint(10, 20)
        self.vie_initiale = self.vie
        
    def update(self):
        self.x += self.vitesse_x
        self.y += self.vitesse_y
        self.vie -= 1
        self.rayon = max(0, self.rayon * 0.95)  # Réduction progressive du rayon
        return self.vie > 0
    
    def dessiner(self, screen):
        # Transparence basée sur la durée de vie
        alpha = int(255 * (self.vie / self.vie_initiale))
        surface_particule = pygame.Surface((self.rayon*2, self.rayon*2), pygame.SRCALPHA)
        pygame.draw.circle(surface_particule, self.couleur + (alpha,), (int(self.rayon), int(self.rayon)), int(self.rayon))
        screen.blit(surface_particule, (int(self.x - self.rayon), int(self.y - self.rayon)))


class OndeChoc:
    def __init__(self, x, y, duree=20):
        self.x = x
        self.y = y
        self.rayon = 0
        self.rayon_max = 200
        self.duree = duree
        self.frame = 0
        self.alpha = 255
        
    def update(self):
        self.frame += 1
        self.rayon = (self.rayon_max * self.frame) / self.duree
        self.alpha = max(0, 255 * (1 - self.frame / self.duree))
        return self.frame < self.duree
        
    def dessiner(self, screen):
        if self.alpha > 0:
            surface = pygame.Surface((self.rayon * 2, self.rayon * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (135, 206, 235, self.alpha), 
                                        (self.rayon, self.rayon), self.rayon)
            screen.blit(surface, (self.x - self.rayon, self.y - self.rayon))

class AnimationRepulsion:
    def __init__(self, joueur, dx, dy, force, duree=20):
        self.joueur = joueur
        self.dx = dx
        self.dy = dy
        self.force = force
        self.frame = 0
        self.duree = duree
        self.x_initial = joueur.x
        self.y_initial = joueur.y
        self.x_final = min(max(joueur.x + dx, 0), LARGEUR - joueur.taille)
        self.y_final = min(max(joueur.y + dy, HAUTEUR_BANDE), HAUTEUR - joueur.taille)
        # Suppression de l'onde de choc autour du joueur
        
    def update(self):
        if self.frame < self.duree:
            progress = self.frame / self.duree
            # Utilisation d'une fonction easeOut pour un mouvement plus naturel
            ease = 1 - (1 - progress) * (1 - progress)
            
            self.joueur.x = self.x_initial + (self.x_final - self.x_initial) * ease
            self.joueur.y = self.y_initial + (self.y_final - self.y_initial) * ease
            
            self.joueur.rect.x = self.joueur.x
            self.joueur.rect.y = self.joueur.y
            
            self.frame += 1
            return True
        return False
        
    def dessiner(self, screen):
        # Suppression du dessin de l'onde
        pass

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
        self.but = 50
        self.canne_peche = None
        self.dernier_event_peche = time.time()
        self.intervalle_peche = 10  # Par exemple, un événement canne à pêche toutes les 20 secondes
        self.dernier_goldfish = time.time()
        self.intervalle_goldfish = 250  # 15 secondes entre chaque apparition
        self.bombes = []
        self.dernier_spawn_bombe = time.time()
        self.intervalle_bombe = 500  # Une bombe toutes les 20 secondes
        self.alerte_vague = None
        self.dernier_event_vague = time.time()
        self.intervalle_vague = 100  # Une vague toutes les 30 secondes
        self.taux_apparition_normal = self.parametres.taux_apparition_poisson
        self.meduses = []
        self.dernier_spawn_meduse = time.time()
        self.intervalle_meduse = 10  # Une méduse toutes les 10 secondes

        # Initialisation des variables globales
        bonus_actif = False
        bonus_timer = 0

    def afficher_ecran_fin(self, victoire):
        running = True
        
        # Création des boutons
        bouton_largeur = 230
        bouton_hauteur = 50
        espace_entre_boutons = 20
        y_depart = HAUTEUR // 2 + 50
        x_centre = LARGEUR // 2 - bouton_largeur // 2
        
        boutons = {
            'rejouer': MenuBouton(x_centre, y_depart, 
                            bouton_largeur, bouton_hauteur, "Rejouer"),
            'menu': MenuBouton(x_centre, y_depart + bouton_hauteur + espace_entre_boutons,
                            bouton_largeur, bouton_hauteur, "Menu Principal"),
            'quitter': MenuBouton(x_centre, y_depart + (bouton_hauteur + espace_entre_boutons) * 2,
                            bouton_largeur, bouton_hauteur, "Quitter")
        }
        
        while running:
            # Fond semi-transparent gris
            surface_fond = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            surface_fond.fill((128, 128, 128, 180))  # Gris transparent
            screen.blit(surface_fond, (0, 0))

            # Affichage du message de victoire/défaite
            message = "VICTOIRE !" if victoire else "DÉFAITE..."
            couleur = BLANC if victoire else ROUGE
            police_fin = pygame.font.SysFont("Arial", 74, bold=True)
            texte = police_fin.render(message, True, couleur)
            text_rect = texte.get_rect(center=(LARGEUR/2, HAUTEUR/3))
            screen.blit(texte, text_rect)
            
            # Affichage du score final
            police_score = pygame.font.SysFont("Arial", 36)
            score_text = f"Score final : {self.joueur.score}"
            score_surface = police_score.render(score_text, True, gold_light)
            score_rect = score_surface.get_rect(center=(LARGEUR/2, HAUTEUR/3 + 60))
            screen.blit(score_surface, score_rect)
            
            # Mise à jour et affichage des boutons
            pos_souris = pygame.mouse.get_pos()
            for bouton in boutons.values():
                bouton.gerer_survol(pos_souris)
                bouton.dessiner(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        if boutons['rejouer'].est_clique(pos_souris):
                            return "rejouer"
                        elif boutons['menu'].est_clique(pos_souris):
                            return "menu"
                        elif boutons['quitter'].est_clique(pos_souris):
                            pygame.quit()
                            sys.exit()
            
            pygame.display.flip()

            
        
    @staticmethod
    def main():
        pygame.init()
        while True:
            # On ne crée et exécute le menu que si on n'est pas en train de rejouer
            menu = Menu(LARGEUR, HAUTEUR)
            action = menu.executer()
            
            while action == "jouer":  # Boucle de jeu qui permet de relancer directement
                partie = Partie()
                resultat = partie.boucle_principale()
                
                if resultat == "menu":
                    action = "menu"  # Sort de la boucle de jeu pour retourner au menu
                    break
                elif resultat == "rejouer":
                    action = "jouer"  # Maintient la boucle de jeu pour relancer directement
                    continue
                elif resultat == "quitter":
                    pygame.quit()
                    sys.exit()
            
            # Si on sort de la boucle de jeu et qu'on n'est pas sur "menu", c'est qu'on veut quitter
            if action != "menu":
                break
            
            # Gestion des événements pour quitter
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        
        pygame.quit()
        sys.exit()

    def initialiser_partie(self):
        self.temps_debut = time.time()
        self.dernier_requin = time.time()
        self.intervalle_requin = random.uniform(
            self.parametres.intervalle_requin_min,
            self.parametres.intervalle_requin_max
        )
        
        # Création du joueur avec est_joueur=True
        self.joueur = Poisson( LARGEUR //2, HAUTEUR //2,
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
            
            # Vérification spéciale pour les poissons de vague
            if isinstance(poisson, PoissonVague):
                # Collision avec la vague fait perdre 1 PV
                if self.joueur.rect.colliderect(poisson.rect):
                    if not self.joueur.invulnerable:
                        self.joueur.vies -= 1
                        self.joueur.invulnerable = True
                        self.joueur.invulnerable_timer = time.time()
                continue  # Ignorer les autres interactions avec les poissons de vague
            
            if self.joueur.rect.colliderect(poisson.rect):
                # Si une vague est active, vérifier si le poisson est dans une zone interdite
                if self.alerte_vague and self.alerte_vague.vague_active:
                    y_poisson = poisson.y
                    if (y_poisson < self.alerte_vague.zone_sure - self.alerte_vague.epaisseur_zone//2 or 
                        y_poisson > self.alerte_vague.zone_sure + self.alerte_vague.epaisseur_zone//2):
                        continue  # Ne pas autoriser les interactions dans les zones interdites
                
                if self.joueur.invulnerable:
                    # Si invincible, peut seulement manger les poissons plus petits ou le Goldfish
                    if poisson.score <= self.joueur.score and not isinstance(poisson, Requin):
                        if isinstance(poisson, Goldfish):
                            self.manger_goldfish(poisson)
                        else:
                            self.manger_poisson(poisson)
                else:  # Si pas invincible
                    if isinstance(poisson, Requin):
                        self.joueur.vies -= 1
                        self.joueur.invulnerable = True
                        self.joueur.invulnerable_timer = time.time()
                        break  # Sort de la boucle après avoir perdu une vie
                    elif isinstance(poisson, Goldfish):
                        self.manger_goldfish(poisson)
                    elif poisson.score <= self.joueur.score:
                        self.manger_poisson(poisson)
                    else:
                        self.joueur.vies -= 1
                        self.joueur.invulnerable = True
                        self.joueur.invulnerable_timer = time.time()
                        break  # Sort de la boucle après avoir perdu une vie
                        
    def generer_bombe(self, temps_actuel):
        if temps_actuel - self.dernier_spawn_bombe >= self.intervalle_bombe:
            x = random.randint(50, LARGEUR - 50)
            self.bombes.append(Bombe(x))
            self.dernier_spawn_bombe = temps_actuel

    def gerer_bombes(self):
        for bombe in self.bombes[:]:
            if bombe.update(self.joueur):
                self.bombes.remove(bombe)
            else:
                bombe.dessiner(screen)
                
    def generer_meduse(self, temps_actuel):
        if temps_actuel - self.dernier_spawn_meduse >= self.intervalle_meduse:
            self.meduses.append(Meduse())
            self.dernier_spawn_meduse = temps_actuel
                
    def gerer_event_vague(self, temps_actuel):
        if not self.alerte_vague and temps_actuel - self.dernier_event_vague >= self.intervalle_vague:
            self.alerte_vague = AlerteVague()
            self.parametres.taux_apparition_poisson = 0

        if self.alerte_vague:
            # Si la vague devient active et qu'on n'a pas encore généré les poissons
            if self.alerte_vague.vague_active and not self.alerte_vague.poissons_vague:
                self.alerte_vague.poissons_vague = generer_poissons_vague(self.alerte_vague)
                for poisson in self.alerte_vague.poissons_vague:
                    self.poissons.append(poisson)

            if self.alerte_vague.update():
                self.alerte_vague = None
                self.dernier_event_vague = temps_actuel
                self.parametres.taux_apparition_poisson = self.taux_apparition_normal
            else:
                self.alerte_vague.dessiner(screen, self.joueur.x, self.joueur.y)
                        
                    
    def manger_poisson(self, poisson):
        gain = calculer_gain(self.joueur.score, poisson.score, self.joueur.taille)
        self.joueur.score += gain
        
        # Calcul de la nouvelle taille
        nouvelle_taille = min(self.joueur.taille + gain // 2, 70)  # Limite à 70
        if nouvelle_taille != self.joueur.taille:  # Si la taille a changé
            self.joueur.taille = nouvelle_taille
            # Mise à jour de l'image selon la direction
            if self.joueur.derniere_direction >= 0:
                self.joueur.image = pygame.transform.scale(self.joueur.image_droite, (nouvelle_taille, nouvelle_taille))
            else:
                self.joueur.image = pygame.transform.scale(self.joueur.image_gauche, (nouvelle_taille, nouvelle_taille))
            # Mise à jour du rectangle de collision
            ancien_centre = self.joueur.rect.center
            self.joueur.rect = self.joueur.image.get_rect()
            self.joueur.rect.center = ancien_centre
        
        if poisson in self.poissons:
            self.poissons.remove(poisson)
            
    def manger_goldfish(self, goldfish):
        if goldfish in self.poissons:
            bonus_type = random.choice(["score_x2", "coeur", "bouclier", "buff", "nerf", "freeze"])
            
            # Affichage du bonus obtenu
            police_bonus = pygame.font.SysFont("Arial", 36)
            texte_bonus = f"Bonus obtenu : {bonus_type}"
            surface_texte_bonus = police_bonus.render(texte_bonus, True, (255, 215, 0))  # Or doré
            rect_texte_bonus = surface_texte_bonus.get_rect(center=(LARGEUR // 2, HAUTEUR // 2))
            
            # Créer une surface temporaire pour afficher le texte
            surface_temporaire = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            surface_temporaire.fill((0, 0, 0, 128))  # Fond semi-transparent
            surface_temporaire.blit(surface_texte_bonus, rect_texte_bonus)
            
            # Afficher le texte pendant 2 secondes
            screen.blit(surface_temporaire, (0, 0))
            pygame.display.update()
            pygame.time.delay(2000)  # Attendre 2 secondes

            self.objet_bonus = ObjetBonusAvance()
            self.objet_bonus.type_bonus = bonus_type
            gestion_bonus_avance(self.joueur, self.objet_bonus)
            self.poissons.remove(goldfish)
            
    def gerer_event_canne_peche(self, temps_actuel):
        if not self.canne_peche and temps_actuel - self.dernier_event_peche >= self.intervalle_peche:
            centre_x = random.randint(100, LARGEUR - 100)
            centre_y = random.randint(HAUTEUR_BANDE + 100, HAUTEUR - 100)
            self.canne_peche = CannePeche(centre_x, centre_y)
            self.dernier_event_peche = temps_actuel
        
        if self.canne_peche:
            if not self.canne_peche.update():
                self.canne_peche = None
            else:
                self.canne_peche.dessiner(screen)
                if not self.canne_peche.a_touche_joueur and self.joueur.rect.colliderect(self.canne_peche.rect):
                    if not self.joueur.invulnerable:
                        self.joueur.vies -= 1
                        self.joueur.invulnerable = True
                        self.joueur.invulnerable_timer = time.time()
                        self.canne_peche.a_touche_joueur = True


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
    def generer_goldfish(self, temps_actuel):
        if temps_actuel - self.dernier_goldfish >= self.intervalle_goldfish:
            x = -40 if random.choice([True, False]) else LARGEUR
            y = random.randint(HAUTEUR_BANDE, HAUTEUR - 40)
            goldfish = Goldfish(x, y, self.joueur.score, direction=1 if x == -40 else -1)
            self.poissons.append(goldfish)
            self.dernier_goldfish = temps_actuel
            
    
            
            
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
        # Vérification des vies
        if self.joueur.vies <= 0:
            return True
        
        # Vérification du score et des poissons
        poissons_totaux = self.poissons_sortis + len(self.poissons)
        if poissons_totaux >= self.parametres.max_poissons and self.joueur.score < self.but:
            # Vérifie si tous les poissons restants sont hors écran
            poissons_visibles = sum(1 for p in self.poissons if 0 <= p.x <= LARGEUR)
            return poissons_visibles == 0
        
        return False
                    

    def gerer_bonus(self, temps_actuel):
        # Gestion du freeze
        for poisson in self.poissons:
            if poisson.freeze and poisson.freeze_timer:
                if temps_actuel - poisson.freeze_timer >= 20:  # Durée du freeze à 20 secondes
                    poisson.freeze = False
                    poisson.freeze_timer = None
        
        # Gestion de bonus buff
        if self.joueur.dernier_bonus_buff and temps_actuel - self.joueur.dernier_bonus_buff <= self.parametres.duree_bonus:
            self.parametres.vitesse_actuelle_joueur = self.parametres.vitesse_base_joueur + 3
        else:
            self.parametres.vitesse_actuelle_joueur = self.parametres.vitesse_base_joueur
            if self.joueur.dernier_bonus_buff and temps_actuel - self.joueur.dernier_bonus_buff > self.parametres.duree_bonus:
                self.joueur.dernier_bonus_buff = None

        # Gestion de bonus nerf
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
    
    def dessiner(self):
        if self.freeze:
            # Ajouter un effet bleuté pour les poissons gelés
            surface_gelee = self.image.copy()
            surface_gelee.fill((100, 100, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(surface_gelee, (self.x, self.y))
        else:
            # Code de dessin normal
            if self.invulnerable and (time.time() * 2) % 1 < 0.5:
                screen.blit(pygame.transform.scale(self.image, (int(self.taille * 1.2), int(self.taille * 1.2))), 
                        (self.x - self.taille * 0.1, self.y - self.taille * 0.1))
            else:
                screen.blit(self.image, (self.x, self.y))
    
    
    def boucle_principale(self):
        global vitesse_poisson_autre
        self.initialiser_partie()
        vitesse_initiale_poisson = self.parametres.vitesse_poisson_autre
        running = True
        pause = False
        menu_pause = MenuPause(LARGEUR, HAUTEUR)
        
        while running:
            temps_actuel = time.time()
            
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # ALT+F4 ou croix de la fenêtre
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pause = not pause
                    elif event.key == pygame.K_r and not pause:  # Touche R pour recommencer
                        return "rejouer"
            
            if pause:
                menu_pause.afficher(screen)
                pygame.display.update()
                
                # Gestion des événements pendant la pause
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Clic gauche
                            action = menu_pause.gerer_clic(event.pos)
                            if action == 'reprendre':
                                pause = False
                            elif action == 'options':
                                # Créez une instance de Menu pour gérer les options
                                menu = Menu(LARGEUR, HAUTEUR)
                                menu.afficher_options()
                            elif action == 'menu_principal':
                                return "menu"
                            elif action == 'quitter':
                                pygame.quit()
                                sys.exit()
                continue
                
            # Affichage du fond
            screen.blit(fonds_frames[self.fond_frame_index], (0, HAUTEUR_BANDE))
            self.fond_frame_index = (self.fond_frame_index + 1) % len(fonds_frames)
            


            # Initialisation de la vitesse de base si elle n'est pas encore définie
            if 'vitesse_initiale_poisson' not in locals():
                vitesse_initiale_poisson = self.parametres.vitesse_poisson_autre

            # Réinitialisation des vitesses après la fin des bonus
            if self.joueur.dernier_bonus_nerf and temps_actuel - self.joueur.dernier_bonus_nerf <= self.parametres.duree_bonus:
                vitesse_poisson_autre = vitesse_initiale_poisson * 0.5  # Réduction de 50% pendant le nerf
            else:
                vitesse_poisson_autre = vitesse_initiale_poisson  # Retour à la vitesse normale
                if self.joueur.dernier_bonus_nerf and temps_actuel - self.joueur.dernier_bonus_nerf > self.parametres.duree_bonus:
                    self.joueur.dernier_bonus_nerf = None

            # Gestion des méduses
            for meduse in self.meduses[:]:
                meduse.deplacer()
                meduse.dessiner(screen)
                if meduse.verifier_collision(self.joueur):
                    self.meduses.remove(meduse)
                elif meduse.y < HAUTEUR_BANDE:
                    self.meduses.remove(meduse)

            # Gestion des événements
            if not self.gerer_evenements():
                return
            
            # Mise à jour du jeu
            self.generer_bombe(temps_actuel)
            self.gerer_bombes()
            self.gerer_mouvements_joueur()
            self.generer_poissons()
            self.gerer_event_canne_peche(temps_actuel)
            self.generer_requin(temps_actuel)
            self.gerer_event_vague(temps_actuel)
            self.generer_goldfish(temps_actuel)
            self.gerer_collisions()
            self.gerer_bonus(temps_actuel)
            self.generer_meduse(temps_actuel)


            # Mise à jour des états
            self.joueur.gerer_invincibilite()
            
            # Affichage
            self.joueur.dessiner()
            for poisson in self.poissons:
                poisson.dessiner()
                
            afficher_score_et_taille(self.joueur, self.joueur.score, self.joueur.vies, self.temps_debut,
                                    f"{len(self.poissons)}/{self.parametres.max_poissons}")
            
            
            
            # Dans la boucle principale, après les autres mises à jour
            if self.verifier_defaite():
                return "menu"  # Écran de défaite

            if self.joueur.score >= self.but:
                return self.afficher_ecran_fin(True)  # Écran de victoire
            
            pygame.display.update()
            self.clock.tick(60)

        
# Au début du fichier, après les imports
bonus_actif = False
bonus_timer = 0
    
if __name__ == "__main__":
    Partie.main()
