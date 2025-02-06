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

def charger_images_poisson(dossier, taille=(40, 40)):
    return [pygame.transform.scale(pygame.image.load(os.path.join(dossier, img)), taille) 
            for img in os.listdir(dossier) if img.endswith(".png")]

images_poissons_gauche = charger_images_poisson(dossier_images_gauche)
images_poissons_droite = charger_images_poisson(dossier_images_droite)

requin_image = pygame.image.load(r"img\event\requin.png")
requin_image = pygame.transform.scale(requin_image, (100, 100))  # Taille du requin


goldfish_image = pygame.image.load(r"img\event\goldfishDtoG.png")
goldfish_image = pygame.transform.scale(goldfish_image, (40, 40))  # Taille du goldfish

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
        # Ajout de l'image freeze aux bonus existants
        self.bonus_images = {
            "score_x2": pygame.transform.scale(pygame.image.load(r"img\tres\X2.png"), (32, 32)),
            "coeur": pygame.transform.scale(pygame.image.load(r"img\tres\coeur.png"), (30, 30)),
            "bouclier": pygame.transform.scale(pygame.image.load(r"img\tres\bouclier.png"), (30, 30)),
            "buff": pygame.transform.scale(pygame.image.load(r"img\tres\buff.png"), (30, 30)),
            "nerf": pygame.transform.scale(pygame.image.load(r"img\tres\nerf.png"), (30, 30)),
            "freeze": pygame.transform.scale(pygame.image.load(r"img\tres\freeze.png"), (30, 30))  # Ajoutez une image pour le freeze
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
        

# Modification de la fonction gestion_bonus_avance
def gestion_bonus_avance(joueur, objet_bonus):
    global bonus_actif, bonus_timer, vitesse_poisson, vitesse_poisson_autre
    
    if objet_bonus.type_bonus == "score_x2":
        bonus_actif = True
        bonus_timer = time.time()
    
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
        joueur.dernier_bonus_freeze = time.time()


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
    
    # Position pour l'icône freeze (ajustez selon vos besoins)
    x_freeze, y_freeze = int(LARGEUR * 0.80), int(HAUTEUR_BANDE * 0.3)
    
    # Affichage du bonus freeze
    if joueur.dernier_bonus_freeze and time.time() - joueur.dernier_bonus_freeze < 20:
        freeze_image = pygame.transform.scale(pygame.image.load(r"img\tres\freeze.png"), (32, 32))
        screen.blit(freeze_image, (x_freeze, y_freeze))
    
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
        # Score supérieur : entre 100% et 150% du score du joueur
        return random.randint(score_joueur, score_joueur * 1.5)
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
                



class Goldfish(Poisson):
    def __init__(self, x, y, direction=1):
        super().__init__(x, y, taille=120, score=10, vies=0, direction=direction)
        self.image = goldfish_image  # Image spécifique du goldfish
        self.vitesse = 6  # Le goldfish est rapide

    def deplacer(self):
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
        self.vitesse_goldfish = 6

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
        self.taux_apparition_poisson = 0.03  # Augmenté à 3% de chance par frame
        self.max_poissons = 250
        
        # Paramètres d'apparition des requins
        self.intervalle_requin_min = 1  # secondes
        self.intervalle_requin_max = 15  # secondes
        
        # Paramètres d'apparition des goldfish
        self.intervalle_goldfish_min = 1  # secondes
        self.intervalle_goldfish_max = 10  # secondes
        
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
        img_requin = pygame.transform.scale(pygame.image.load("img/event/requin.png"), (image_width, image_height))
        img_bonus_attraction = pygame.transform.scale(pygame.image.load("img/tres/aimant.png"), (image_width, image_height))
        img_bonus_Sattraction = pygame.transform.scale(pygame.image.load("img/tres/superaimant.png"), (image_width, image_height))
        img_bonus_freeze = pygame.transform.scale(pygame.image.load("img/tres/freeze.png"), (image_width, image_height))
        img_bonus_x2 = pygame.transform.scale(pygame.image.load("img/tres/X2.png"), (image_width, image_height))
        img_bonus_x4 = pygame.transform.scale(pygame.image.load("img/tres/X4.png"), (image_width, image_height))
        img_poisson_dore = pygame.transform.scale(pygame.image.load("img/event/goldfishGtoD.png"), (image_width, image_height))
        img_bombe = pygame.transform.scale(pygame.image.load("img/event/bombe.png"), (image_width, image_height))
        img_canne_peche = pygame.transform.scale(pygame.image.load("img/event/hamcon.png"), (image_width, image_height))
        img_vague = pygame.transform.scale(pygame.image.load("img/event/vague.png"), (image_width, image_height))

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


class Partie:
    def __init__(self, parametres=None):
        global bonus_actif, bonus_timer
        self.parametres = parametres or ParametresPartie()
        self.clock = pygame.time.Clock()
        self.temps_debut = None
        self.dernier_requin = None
        self.dernier_goldfish = None
        self.intervalle_requin = None
        self.intervalle_goldfish = None
        self.bonus_actif = False
        self.bonus_timer = 0
        self.fond_frame_index = 0
        self.dernier_bonus_freeze = None
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
        """Affiche l'écran de fin de partie avec des boutons interactifs"""
        running = True
        
        # Création des boutons
        bouton_largeur = 235
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
            pygame.draw.rect(screen, (0, 0, 0, 90), (400, 200, 500, 500))
            pygame.draw.rect(screen, (gold_dark), (400, 200, 500, 500), 10)

            

            
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
        self.temps_debut = time.time()
        self.dernier_goldfish = time.time()
        self.intervalle_goldfish = random.uniform(
            self.parametres.intervalle_goldfish_min,
            self.parametres.intervalle_goldfish_max
        )
        
        # Création du joueur avec est_joueur=True
        self.joueur = Poisson(
            LARGEUR//2, HAUTEUR //2,
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
    def generer_goldfish(self, temps_actuel):
        if temps_actuel - self.dernier_goldfish >= self.intervalle_goldfish:
            x = LARGEUR
            y = random.randint(HAUTEUR_BANDE, HAUTEUR - 100)
            goldfish = Goldfish(x, y, direction=-1)
            goldfish.vitesse = self.parametres.vitesse_goldfish
            self.poissons.append(goldfish)
            self.dernier_goldfish = temps_actuel
            self.intervalle_goldfish = random.uniform(
                self.parametres.intervalle_goldfish_min,
                self.parametres.intervalle_goldfish_max
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
        # On commence par la vitesse de base
        self.parametres.vitesse_actuelle_poisson = self.parametres.vitesse_base_poisson

        # Gestion de bonus buff
        if self.joueur.dernier_bonus_buff and temps_actuel - self.joueur.dernier_bonus_buff <= self.parametres.duree_bonus:
            self.parametres.vitesse_actuelle_joueur = self.parametres.vitesse_base_joueur + 3
        else:
            self.parametres.vitesse_actuelle_joueur = self.parametres.vitesse_base_joueur
            if self.joueur.dernier_bonus_buff and temps_actuel - self.joueur.dernier_bonus_buff > self.parametres.duree_bonus:
                self.joueur.dernier_bonus_buff = None

        # Gestion de bonus nerf (seulement si freeze n'est pas actif)
        if not (self.joueur.dernier_bonus_freeze and temps_actuel - self.joueur.dernier_bonus_freeze <= self.parametres.duree_bonus):
            if self.joueur.dernier_bonus_nerf and temps_actuel - self.joueur.dernier_bonus_nerf <= self.parametres.duree_bonus:
                self.parametres.vitesse_actuelle_poisson = self.parametres.vitesse_base_poisson - 1
            elif self.joueur.dernier_bonus_nerf and temps_actuel - self.joueur.dernier_bonus_nerf > self.parametres.duree_bonus:
                self.joueur.dernier_bonus_nerf = None
                
        # Gestion de bonus freeze (prioritaire)
        if self.joueur.dernier_bonus_freeze and temps_actuel - self.joueur.dernier_bonus_freeze <= self.parametres.duree_bonus:
            self.parametres.vitesse_base_poisson = 0
            self.parametres.vitesse_actuelle_poisson = 0
        elif self.joueur.dernier_bonus_freeze and temps_actuel - self.joueur.dernier_bonus_freeze > self.parametres.duree_bonus:
            self.joueur.dernier_bonus_freeze = None
            # Ne pas remettre la vitesse ici car elle sera gérée par nerf ou la vitesse de base

        

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
        vitesse_initiale_poisson = self.parametres.vitesse_poisson_autre
        running = True
        
        while running:
            temps_actuel = time.time()
            
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # ALT+F4 ou croix de la fenêtre
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Touche R pour recommencer
                        return "rejouer"
                    # Ajouter ici d'autres touches si nécessaire
            
            # Vérification des conditions de victoire/défaite
            if self.joueur.score >= 270:
                action = self.afficher_ecran_fin(victoire=True)
                if action == "rejouer":
                    return "rejouer"
                elif action == "menu":
                    return "menu"
                return action
            elif self.verifier_defaite():
                action = self.afficher_ecran_fin(victoire=False)
                if action == "rejouer":
                    return "rejouer"
                elif action == "menu":
                    return "menu"
                return action
            
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



            # Gestion des événements
            if not self.gerer_evenements():
                return
            
            # Mise à jour du jeu
            self.gerer_mouvements_joueur()
            self.generer_poissons()
            self.generer_requin(temps_actuel)
            self.generer_goldfish(temps_actuel)
            self.gerer_collisions()
            self.gerer_bonus(temps_actuel)


            # Mise à jour des états
            self.joueur.gerer_invincibilite()
            
            # Affichage
            self.joueur.dessiner()
            for poisson in self.poissons:
                poisson.dessiner()
                
            afficher_score_et_taille(self.joueur, self.joueur.score, self.joueur.vies, self.temps_debut,
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
    params.vitesse_poisson_autre = 3
    params.max_poissons = 20
    params.intervalle_bonus = 0
    partie = Partie(params)    # Création et lancement de la partie
    partie.boucle_principale()
    
if __name__ == "__main__":
    Partie.main()
    jeu()
