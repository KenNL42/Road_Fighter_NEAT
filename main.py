#try to make similar to classic NES Road Fighter
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
PLAYER_SOBER_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "player.png")), (100,100))
BG_IMG = pygame.image.load(os.path.join("imgs", "Road_Background.jpg"))
OBSTACLE_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "car.png")), (100,100))
STAT_FONT = pygame.font.SysFont("comicsans", 50)
GENERATION = 0

class Player:
    IMG = PLAYER_SOBER_IMG
    VELOCITY = 5

    #initialize player's position to center
    def __init__(self):
        self.x = 200
        self.y = 600

    def moveLeft(self):
        self.x -= self.VELOCITY

    def moveRight(self):
        self.x += self.VELOCITY

    def draw(self, window):
        window.blit(self.IMG, (self.x, self.y))

    # retrieve only the image of the player by ignoring blank area
    def get_mask(self):
        return pygame.mask.from_surface(self.IMG)

    def checkAround(self, obstacle):
        # return 1 when there is an obstacle in a specific area
        left = self.checkLeft(obstacle)
        right = self.checkRight(obstacle)
        middle = self.checkMiddle(obstacle)
        farLeft = self.checkFarLeft(obstacle)
        farRight = self.checkFarRight(obstacle)
        return farLeft, left, middle, right, farRight

    # check left side of the player
    def checkLeft(self, obstacle):
        if obstacle.x >= self.x - 100 and obstacle.x <= self.x:
            return 1
        if self.x - 100 <= 0:
            return 1
        return 0

    # check right side of the player
    def checkRight(self, obstacle):
        if obstacle.x >= self.x + 100 and obstacle.x <= self.x + 200:
            return 1
        if self.x + 100 >= WIN_WIDTH:
            return 1
        return 0

    # check above of the player
    def checkMiddle(self, obstacle):
        if obstacle.x > self.x  and obstacle.x < self.x + 100:
            return 1
        return 0

    # check far left side of the player
    def checkFarLeft(self, obstacle):
        if obstacle.x > self.x - 200 and obstacle.x < self.x - 100:
            return 1
        if self.x - 200 <= 0:
            return 1
        return 0

    # check far right side of the player
    def checkFarRight(self, obstacle):
        if obstacle.x > self.x + 200 and obstacle.x < self.x + 300:
            return 1
        if self.x + 200 <= WIN_WIDTH:
            return 1
        return 0

class Obstacle:
    IMG = OBSTACLE_IMG
    VEL = 20

    # initialize position to the top of the window
    def __init__(self):
        self.x = 0
        self.y = -100
        self.passed = False
        self.set_position()

    # randomly assign obstacle's position
    def set_position(self):
        self.y -= random.randrange(0, 1000)
        self.x += random.randrange(0, 500)

    # move the obstacle down
    def move(self):
        self.y += self.VEL

    def draw(self, win):
        win.blit(self.IMG, (self.x, self.y))

    # check for collision
    def collide(self, player, win):
        player_mask = player.get_mask()
        obstacle_mask = pygame.mask.from_surface(self.IMG)
        offset = (self.x - player.x, self.y - player.y)
        if player_mask.overlap(obstacle_mask, offset):
            return True
        return False

def draw_window(window, players, obstacle, score, generation):
    window.blit(BG_IMG, (0, 0))
    if generation == 0:
        generation = 1
    for player in players:
        player.draw(window)
    obstacle.draw(window)

    # display score
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(score_label, (WIN_WIDTH - 150, 10))

    # display generation
    score_label = STAT_FONT.render("Gens: " + str(generation - 1), 1, (255, 255, 255))
    window.blit(score_label, (WIN_WIDTH - 180, 40))

    pygame.display.update()

def main(genomes, config):
    nets = []
    ge = []
    players = []
    global GENERATION
    GENERATION += 1

    # generate players
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

        # move obstacle and check for collision
        for obstacle in obstacles:
            for x, player in enumerate(players):
                # check if collide
                if obstacle.collide(player, WINDOW):
                    ge[x].fitness -= 1
                    # remove collided player
                    nets.pop(players.index(player))
                    ge.pop(players.index(player))
                    players.pop(players.index(player))

                # if the player dodge the obstacle
                if not obstacle.passed and obstacle.y > player.y:
                    obstacle.passed = True
                    add_obstacle = True

            # if obstacle passes the screen
            if obstacle.y + obstacle.IMG.get_height() > WIN_HEIGTH:
                removed_obstacle.append(obstacle)

            obstacle.move()

        # increment score
        if add_obstacle:
            score += 1
            # increase fitness for players that make through each obstacle
            for g in ge:
                g.fitness += 5
            obstacles.append(Obstacle()) # generate a new obstacle

        # remove an out of screen obstacle from the set
        for r in removed_obstacle:
            obstacles.remove(r)

        # call NEAT to find the best way to survive
        for x, player in enumerate(players):
            ge[x].fitness += 0.01
            around_environment = player.checkAround(obstacle) # get data about area around player
            output = nets[x].activate((
                                        player.x,
                                        around_environment[0],
                                        around_environment[1],
                                        around_environment[2],
                                        around_environment[3],
                                        around_environment[4],
                                       ))
            if output[0] > 0.5:
                player.moveLeft()
            if output[2] > 0.5:
                player.moveRight()

            # remove a player if they are out of the map
            if player.x <= 5 or player.x + player.IMG.get_width() >= 495:
                ge[x].fitness -= 1
            if player.x <= 0 or player.x + player.IMG.get_width() >= WIN_WIDTH:
                ge[x].fitness -= 3
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

    winner = population.run(main, 100)



if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)