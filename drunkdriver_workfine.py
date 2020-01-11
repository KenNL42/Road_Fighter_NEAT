#*****************************************************************



import pygame
import random
import os
import time
import neat

pygame.font.init()

# constant variables
WIN_WIDTH = 600
WIN_HEIGTH = 800
WINDOW = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGTH))
pygame.display.set_caption("Drunk Driver")
PLAYER_SOBER_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "player-sober.png")), (200,200))
BG_IMG = pygame.image.load(os.path.join("imgs", "Road_Background.png"))
OBSTACLE_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "car.png")), (200,200))
STAT_FONT = pygame.font.SysFont("comicsans", 50)
GENERATION = 0

DRAW_LINES = True


class Player:
    IMG = PLAYER_SOBER_IMG
    VELOCITY = 10

    #initialize player's position to center
    def __init__(self):
        self.x = 200
        self.y = 600
        self.lane = 2

    def moveLeft(self):
        #if self.x > 0:
            #self.x -= self.VELOCITY
            self.x -= 200
            self.lane -= 1

    def moveRight(self):
        #if self.x < WIN_WIDTH - self.IMG.get_width():
            #self.x += self.VELOCITY
            self.x += 200
            self.lane += 1
            print("moveRight is called")

    def draw(self, window):
        window.blit(self.IMG, (self.x, self.y))

    def get_mask(self):
        return pygame.mask.from_surface(self.IMG)

    def moveTo(self, lane):
        if lane == 0:
            self.x = 0
        elif lane == 1:
            self.x = 200
        else:
            self.x = 400


class Obstacle:
    IMG = OBSTACLE_IMG
    GAP = 200
    VEL = 10

    def __init__(self):
        self.x1 = 0
        self.x2 = 0
        self.y = 0
        self.passed = False
        self.lane1 = 0
        self.lane2 = 0
        self.set_position()


    def set_position(self):
        self.y = -100
        lane = random.randrange(1, 4)
        if lane == 1:
            self.x1 = 0
        elif lane == 2:
            self.x1 = 200
        else:
            self.x1 = 400

        self.lane1 = lane

        lane = random.randrange(1, 4)
        if lane == 1:
            self.x2 = 0
        elif lane == 2:
            self.x2 = 200
        else:
            self.x2 = 400

        self.lane2 = lane

    def move(self):
        self.y += self.VEL

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

    def collide(self, player, win):
        player_mask = player.get_mask()
        obstacle_mask = pygame.mask.from_surface(self.IMG)
        # may need to change y to get the "bottom" part of image
        offset1 = (self.x1 - player.x, self.y - player.y)
        offset2 = (self.x2 - player.x, self.y - player.y)
        if player_mask.overlap(obstacle_mask, offset1) or player_mask.overlap(obstacle_mask, offset2):
            return True
        return False

def draw_window(window, players, obstacle, score, generation):
    if generation == 0:
        generation = 1
    window.blit(BG_IMG, (0, 0))
    for player in players:
        if DRAW_LINES:
            try:
                pygame.draw.line(window, (255, 0, 0),
                                 (player.x + player.IMG.get_width() / 2, player.y + player.IMG.get_height() / 2),
                                 (obstacle.x1 + obstacle.IMG.get_width() / 2, obstacle.y + obstacle.IMG.get_height() / 2),
                                 5)
                pygame.draw.line(window, (0, 0, 255),
                                 (player.x + player.IMG.get_width() / 2, player.y + player.IMG.get_height() / 2),
                                 (obstacle.x2 + obstacle.IMG.get_width() / 2, obstacle.y + obstacle.IMG.get_height() / 2),
                                 5)
            except:
                pass
        player.draw(window)
    obstacle.draw(window)
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(score_label, (WIN_WIDTH - 180, 10))

    score_label = STAT_FONT.render("Gens: " + str(generation - 1), 1, (255, 255, 255))
    window.blit(score_label, (WIN_WIDTH - 180, 40))

    pygame.display.update()

def main(genomes, config):
    #player = Player()
    nets = []
    ge = []
    players = []

    global GENERATION
    GENERATION += 1

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        players.append(Player())
        g.fitness = 0
        ge.append(g)

    obstacles = [Obstacle()]
    score = 0
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # in case there are more than one line of obstacles
        obstacle_index = 0
        if len(players) > 0:
            if len(obstacles) > 1 and players[0].y < obstacles[0].y + obstacles[0].IMG.get_height():
                obstacle_index = 1
        else:
            run = False
            break



        add_obstacle = False
        removed_obstacle = []
        for obstacle in obstacles:
            for x, player in enumerate(players):
                # check if collide
                if obstacle.collide(player, WINDOW):
                    ge[x].fitness -= 10
                    # remove collided player
                    nets.pop(players.index(player))
                    ge.pop(players.index(player))
                    players.pop(players.index(player))

                # if the player dodge the obstacle
                if not obstacle.passed and obstacle.y > player.y:
                    obstacle.passed = True
                    add_obstacle = True

            # if obstacle passes the screen
            if obstacle.y + obstacle.IMG.get_width() > WIN_HEIGTH:
                removed_obstacle.append(obstacle)

            obstacle.move()

        if add_obstacle:
            score += 1
            # increase fitness for players that make through each obstacle
            for g in ge:
                g.fitness += 5
            obstacles.append(Obstacle())

        for r in removed_obstacle:
            obstacles.remove(r)



        array_obs = [0, 0, 0]
        array_obs[obstacle.lane1 - 1] = 1
        array_obs[obstacle.lane2 - 1] = 1

        array_player = [0, 0, 0]
        array_player[player.lane - 1] = 1
        max = -1

        for x, player in enumerate(players):
            ge[x].fitness += 0.01
            output = nets[x].activate((array_player[0],
                                       array_player[1],
                                       array_player[2],
                                       array_obs[0],
                                       array_obs[1],
                                       array_obs[2],
                                       ))
            # -----------------------------------
            #print(array_player[0], array_player[1], array_player[2], array_obs[0], array_obs[1], array_obs[2])
            # if output[0] > 0.5:
            #     player.moveRight()
            # elif output[1] > 0.5:
            #     player.moveLeft()
            #print(output[0], output[1], output[2])

            if output[0] > output[1] and output[0] > output[2]:
                max = 0
            elif output[1] > output[2] and output[1] > output[0]:
                max = 1
            elif output[2] > output[1] and output[2] > output[0]:
                max = 2

        #print("Max: ", max)
        player.moveTo(max)


        # keys = pygame.key.get_pressed()
        #
        # #test moving
        # if keys[pygame.K_LEFT]:
        #     player.moveLeft()
        # if keys[pygame.K_RIGHT]:
        #     player.moveRight()
        # if obstacle.collide(player, WINDOW):
        #     collision_label = STAT_FONT.render("COLLIDED", 1, (255, 255, 255))
        #     WINDOW.blit(collision_label, (10, 50))
        # pygame.display.update()

        for player in players:
            if player.x <= -50 or player.x + player.IMG.get_width() >= WIN_WIDTH + 50:
                nets.pop(players.index(player))
                ge.pop(players.index(player))
                players.pop(players.index(player))

        draw_window(WINDOW, players, obstacle, score, GENERATION)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(main, 50)



if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)