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
LARGEUR, HAUTEUR = 1024, 768  # Augmentation de la résolution
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
    def __init__(self, x, y, taille, score, vies, direction=1):
        self.x = x
        self.y = max(y, HAUTEUR_BANDE)  # Empêche le spawn au-dessus de la bande noire
        self.taille = taille
        self.score = score
        self.vies = vies
        self.direction = direction
        self.image = random.choice(images_poissons_gauche if direction == 1 else images_poissons_droite)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.invincibilite_duree = 5
        self.dernier_bonus_coeur = None  # Aucun cœur ramassé au départ
        self.dernier_bonus_bouclier = None
        self.dernier_bonus_buff = None
        self.dernier_bonus_nerf = None
        self.invincibilite_duree_defaut = 5  # Durée d'invincibilité par défaut
        self.invincibilite_duree = self.invincibilite_duree_defaut  # Durée actuelle (modifiable)


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
        bonus_timer = time.time()
    
    elif objet_bonus.type_bonus == "coeur":
        joueur.vies += 1
        joueur.dernier_bonus_coeur = time.time()  # Enregistre l'heure de collecte du cœur
        bonus_timer = time.time()

    elif objet_bonus.type_bonus == "bouclier":
        joueur.invulnerable = True
        joueur.invulnerable_timer = time.time()
        joueur.invincibilite_duree = 20  # Durée temporaire pour le bouclier
    
    elif objet_bonus.type_bonus == "buff":
        vitesse_poisson += 3
        bonus_timer = time.time()
        joueur.dernier_bonus_buff = time.time()
        # La réduction de vitesse sera gérée dans la boucle principale
    
    elif objet_bonus.type_bonus == "nerf":
        vitesse_poisson_autre -= 1
        bonus_timer = time.time()
        joueur.dernier_bonus_nerf = time.time()
        # Le retour à la vitesse normale sera géré dans la boucle principale


def calculer_gain(joueur_score, poisson_score, joueur_taille):
    gain = int(1 + (poisson_score / joueur_score) * (joueur_taille / 10))
    return gain * 2 if bonus_actif else gain

def afficher_score_et_taille(joueur, score, vies, temps_debut):
    # Dessiner la bande gold dark en haut
    pygame.draw.rect(screen, gold_dark, (0, 0, LARGEUR, HAUTEUR_BANDE))
    pygame.draw.rect(screen, NOIR, (0, 0, LARGEUR, HAUTEUR_BANDE), 3)  # Contour Noir autour de la bande
    
 
    
    # Affichage du score et des vies
    screen.blit(police.render(f"Score: {score}", True, BLANC), (10, 20))
    screen.blit(police.render(f"Vies: {vies}", True, ROUGE), (150, 20))
    
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
            text_rect = inv_texte.get_rect(center=(LARGEUR // 2, HAUTEUR_BANDE // 2))
            screen.blit(inv_texte, text_rect)
    
    # Position en pourcentage pour les bonus
    x_nerf, y_nerf = int(LARGEUR * 0.65), int(HAUTEUR_BANDE * 0.25)
    x_buff, y_buff = int(LARGEUR * 0.70), int(HAUTEUR_BANDE * 0.25)
    x_score_x2, y_score_x2 = int(LARGEUR * 0.75), int(HAUTEUR_BANDE * 0.32)
    
    # Affichage des bonus
    if joueur.dernier_bonus_nerf and time.time() - joueur.dernier_bonus_nerf < 10:
        nerf_image = pygame.transform.scale(pygame.image.load(r"img\tres\nerf.png"), (32, 32))
        screen.blit(nerf_image, (x_nerf, y_nerf))
    
    if joueur.dernier_bonus_buff and time.time() - joueur.dernier_bonus_buff < 10:
        buff_image = pygame.transform.scale(pygame.image.load(r"img/tres/buff.png"), (32, 32))
        screen.blit(buff_image, (x_buff, y_buff))
    
    # Affichage du bonus de score x2 si actif
    if bonus_actif:
        screen.blit(bonus_emoji_image, (x_score_x2, y_score_x2))
    
    # Affichage de "+1 vie" près de "Vies" pendant 3 secondes après collecte
    if joueur.dernier_bonus_coeur and time.time() - joueur.dernier_bonus_coeur < 3:
        screen.blit(police.render("+1 vie", True, ROUGE), (int(LARGEUR * 0.22), 20))

    
        # Ajout du cadre transparent en pourcentage autour de trois bonus
    cadre_largeur = int(LARGEUR * 0.15)
    cadre_hauteur = int(HAUTEUR_BANDE * 0.8)
    cadre_x = x_nerf - int(cadre_largeur * 0.05)
    cadre_y = int(HAUTEUR_BANDE * 0.1)



        # Ajout du cadre transparent en pourcentage autour de trois bonus
    cadre_largeur = int(LARGEUR * 0.15)
    cadre_hauteur = int(HAUTEUR_BANDE * 0.8)
    cadre_x = x_nerf - int(cadre_largeur * 0.05)
    cadre_y = int(HAUTEUR_BANDE * 0.1)

    # Épaisseur du contour
    epaisseur_contour = 3  # Ajuste la valeur selon la taille que tu souhaites

    # Dessin du cadre transparent avec un contour OR
    pygame.draw.rect(screen, (0, 0, 0, 90), (cadre_x, cadre_y, cadre_largeur, cadre_hauteur), epaisseur_contour)

    
    surface_cadre = pygame.Surface((cadre_largeur, cadre_hauteur), pygame.SRCALPHA)
    surface_cadre.fill((0, 0, 255, 100))  # Transparence bleu à 100%
    surface_cadre.fill((0, 255, 0, 100))  # Transparence vert à 100%
    screen.blit(surface_cadre, (cadre_x, cadre_y))

    pygame.draw.line(screen, (0, 0, 0), (0, 0), (LARGEUR, 0), 2)  # Ligne sombre en haut
    pygame.draw.line(screen, (50, 50, 50), (0, HAUTEUR_BANDE), (LARGEUR, HAUTEUR_BANDE), 2)  # Ligne claire en bas





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

def jeu():
    global score, fond_frame_index, bonus_actif, bonus_timer, vitesse_poisson, vitesse_poisson_autre, clignotement
    joueur = Poisson(50, HAUTEUR - 50, largeur_poisson, score, 3)
    poissons.clear()
    objet_bonus_avance = None
    clock = pygame.time.Clock()
    temps_debut = time.time()
    
    # Variables pour la génération des requins
    dernier_requin = time.time()
    intervalle_requin = random.uniform(10, 25)



    while True:
        temps_actuel = time.time()
        screen.blit(fonds_frames[fond_frame_index], (0, HAUTEUR_BANDE))
        fond_frame_index = (fond_frame_index + 1) % len(fonds_frames)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        touches = pygame.key.get_pressed()
        if touches[pygame.K_LEFT] and joueur.x > 0:
            joueur.x -= vitesse_poisson
        if touches[pygame.K_RIGHT] and joueur.x < LARGEUR - joueur.taille:
            joueur.x += vitesse_poisson
        if touches[pygame.K_UP] and joueur.y > HAUTEUR_BANDE:
            joueur.y -= vitesse_poisson
        if touches[pygame.K_DOWN] and joueur.y < HAUTEUR - joueur.taille:
            joueur.y += vitesse_poisson
        joueur.rect.x, joueur.rect.y = joueur.x, joueur.y

        # Génération des nouveaux poissons
        if random.randint(1, 100) > 95 and len(poissons) < 10:
            taille = random.randint(20, 100)
            score_poisson = generer_score_poisson(joueur.score)
            x = -taille if random.choice([True, False]) else LARGEUR
            y = random.randint(HAUTEUR_BANDE, HAUTEUR - taille)
            poissons.append(Poisson(x, y, taille, score_poisson, random.randint(1, 3), direction=1 if x == -taille else -1))

        # Génération du requin
        if temps_actuel - dernier_requin >= intervalle_requin:
            x = -100 if random.choice([True, False]) else LARGEUR
            y = random.randint(HAUTEUR_BANDE, HAUTEUR - 100)
            poissons.append(Requin(x, y, direction=1 if x == -100 else -1))
            dernier_requin = temps_actuel
            intervalle_requin = random.uniform(20, 30)

        # Gestion des collisions avec les poissons
        for poisson in poissons[:]:
            poisson.deplacer()
            if joueur.rect.colliderect(poisson.rect):
                if isinstance(poisson, Requin):
                    if joueur.vies > 1 and not joueur.invulnerable:
                        joueur.vies -= 1
                        joueur.invulnerable = True
                        joueur.invulnerable_timer = time.time()
                elif not joueur.invulnerable:
                    if poisson.score < joueur.score:
                        gain = calculer_gain(joueur.score, poisson.score, joueur.taille)
                        joueur.score += gain
                        joueur.taille += gain // 2
                        joueur.image = pygame.transform.scale(joueur.image, (joueur.taille, joueur.taille))
                        joueur.rect = joueur.image.get_rect(topleft=(joueur.x, joueur.y))
                        if poisson in poissons:
                            poissons.remove(poisson)
                    else:
                        if joueur.vies > 1:
                            joueur.vies -= 1
                            joueur.invulnerable = True
                            joueur.invulnerable_timer = time.time()

        # Gestion des bonus actifs
        if bonus_timer:
            temps_ecoule = temps_actuel - bonus_timer
            if temps_ecoule > 20:  # Durée de 20 secondes pour tous les bonus
                # Réinitialiser les effets
                bonus_actif = False
                vitesse_poisson = 5  # Valeur par défaut
                vitesse_poisson_autre = 2  # Valeur par défaut
                bonus_timer = None

        # Génération des bonus
        if objet_bonus_avance is None:
            if random.random() < 0.02:  # 2% de chance à chaque frame
                objet_bonus_avance = ObjetBonusAvance()

        # Mise à jour et affichage du bonus
        if objet_bonus_avance:
            objet_bonus_avance.deplacer()
            objet_bonus_avance.dessiner()
            
            # Collision avec le joueur
            if objet_bonus_avance.rect.colliderect(joueur.rect):
                gestion_bonus_avance(joueur, objet_bonus_avance)
                objet_bonus_avance = None
            
            # Bonus sort de l'écran
            elif objet_bonus_avance.rect.top > HAUTEUR:
                objet_bonus_avance = None

        joueur.gerer_invincibilite()
        joueur.dessiner()
        for poisson in poissons:
            poisson.dessiner()
        
        afficher_score_et_taille(joueur, joueur.score, joueur.vies, temps_debut)
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    jeu()