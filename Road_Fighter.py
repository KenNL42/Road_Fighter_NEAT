#try to make similar to classic NES Road Fighter
import pygame
import random
import os
import neat
import pickle
import matplotlib.pyplot as plt

pygame.font.init()

# constant variables
WIN_WIDTH = 600
WIN_HEIGHT = 800
IMG_WIDTH = 50
IMG_HEIGHT = 100
ROAD_LEFTWALL = 140
ROAD_RIGHTWALL = 420
WINDOW = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Road Fighter")
PLAYER_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "player.png")), (IMG_WIDTH,IMG_HEIGHT))
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "Road_Background.jpg")), (600,800))
OBSTACLE_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "car.png")), (IMG_WIDTH,IMG_HEIGHT))
STAT_FONT = pygame.font.SysFont("comicsans", 50)
GENERATION = 0
x_data = []
y_data = []


class Player:
    IMG = PLAYER_IMG
    VELOCITY = 5

    #initialize player's position to center
    def __init__(self):
        self.x = 300
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
        if obstacle.x >= self.x - self.IMG.get_width() and obstacle.x <= self.x:
            return 1
        if obstacle.x + obstacle.IMG.get_width() >= self.x - self.IMG.get_width() and obstacle.x + obstacle.IMG.get_width() <= self.x:
            return 1
        if self.x - self.IMG.get_width() <= ROAD_LEFTWALL:
            return 1
        return 0

    # check right side of the player
    def checkRight(self, obstacle):
        if obstacle.x >= self.x + self.IMG.get_width() and obstacle.x <= self.x + self.IMG.get_width() * 2:
            return 1
        if obstacle.x + obstacle.IMG.get_width() >= self.x + self.IMG.get_width() and obstacle.x + obstacle.IMG.get_width() <= self.x + self.IMG.get_width() * 2:
            return 1
        if self.x + self.IMG.get_width() >= ROAD_RIGHTWALL:
            return 1
        return 0

    # check above of the player
    def checkMiddle(self, obstacle):
        if obstacle.x > self.x  and obstacle.x < self.x + self.IMG.get_width():
            return 1
        if obstacle.x + obstacle.IMG.get_width() > self.x  and obstacle.x + obstacle.IMG.get_width() < self.x + self.IMG.get_width():
            return 1
        return 0

    # check far left side of the player
    def checkFarLeft(self, obstacle):
        if obstacle.x > self.x - 2 * self.IMG.get_width() and obstacle.x < self.x - self.IMG.get_width():
            return 1
        if self.x - 2 * self.IMG.get_width() <= ROAD_LEFTWALL:
            return 1
        return 0

    # check far right side of the player
    def checkFarRight(self, obstacle):
        if obstacle.x > self.x + 2 * self.IMG.get_width() and obstacle.x < self.x + 3 * self.IMG.get_width():
            return 1
        if self.x + 2 * self.IMG.get_width() >= ROAD_RIGHTWALL:
            return 1
        return 0

class Obstacle:
    IMG = OBSTACLE_IMG
    VEL = 15

    # initialize position to the top of the window
    def __init__(self):
        self.x = 140
        self.y = -100
        self.passed = False
        self.set_position()

    # randomly assign obstacle's position
    def set_position(self):
        self.y -= random.randrange(0, 1000)
        self.x += random.randrange(0, 380 - self.IMG.get_width())

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

class Road:
    IMG = BG_IMG
    VEL = 5

    def __init__(self):
        self.x = 0
        self.y1 = 0
        self.y2 = -1 * self.IMG.get_height()

    def move(self):
        self.y1 += self.VEL
        self.y2 += self.VEL
        if self.y1 >= WIN_HEIGHT:
            self.y1 = -1 * self.IMG.get_height()
        if self.y2 >= WIN_HEIGHT:
            self.y2 = -1 * self.IMG.get_height()

    def draw(self, win):
        win.blit(self.IMG, (self.x, self.y1))
        win.blit(self.IMG, (self.x, self.y2))


def draw_window(window, players, obstacle, score, generation, road):
    road.draw(window)
    if generation == 0:
        generation = 1
    for player in players:
        player.draw(window)
    obstacle.draw(window)

    # display score
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(score_label, (WIN_WIDTH - 160, 10))

    # display generation
    score_label = STAT_FONT.render("Gens: " + str(generation - 1), 1, (255, 255, 255))
    window.blit(score_label, (WIN_WIDTH - 160, 40))

    pygame.display.update()

def main(genomes, config):
    nets = []
    ge = []
    players = []
    road = Road()
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

    clock = pygame.time.Clock()

    run = True



    while run:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                plt.bar(x_data, y_data, align='center')
                plt.xlabel('generation')
                plt.ylabel('score')
                plt.show()
                run = False
                pygame.quit()
                quit()

        if len(players) <= 0:
            run = False
            break

        add_obstacle = False
        removed_obstacle = []

        road.move()

        # move obstacle and check for collision
        for obstacle in obstacles:
            for x, player in enumerate(players):
                # check if collide
                if obstacle.collide(player, WINDOW):
                    ge[x].fitness -= 5
                    # remove collided player
                    nets.pop(players.index(player))
                    ge.pop(players.index(player))
                    players.pop(players.index(player))

                # if the player dodge the obstacle
                if not obstacle.passed and obstacle.y > player.y:
                    obstacle.passed = True
                    add_obstacle = True

            # if obstacle passes the screen
            if obstacle.y + obstacle.IMG.get_height() > WIN_HEIGHT:
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
            ge[x].fitness += 0.05
            for obstacle in obstacles:
                around_environment = player.checkAround(obstacle) # get data about area around player
                output = nets[x].activate((
                                            player.x,
                                            around_environment[0],
                                            around_environment[1],
                                            around_environment[2],
                                            around_environment[3],
                                            around_environment[4],
                ))
                #print(around_environment)
                if output[0] > 0.5:
                    player.moveLeft()
                if output[2] > 0.5:
                    player.moveRight()

            # discourage NEAT to have player stay at the side of the screen
            if player.x <= 160 or player.x + player.IMG.get_width() >= WIN_WIDTH - 100:
                ge[x].fitness -= 0.1

            if player.x >= 250 and player.x <= 300:
                ge[x].fitness += 0.1

            # remove a player if they are out of the map
            if player.x <= 140 or player.x + player.IMG.get_width() >= WIN_WIDTH - 80:
                ge[x].fitness -= 10
                nets.pop(players.index(player))
                ge.pop(players.index(player))
                players.pop(players.index(player))

        draw_window(WINDOW, players, obstacle, score, GENERATION, road)

        # stop if score is large enough
        if score > 100:
            with open("best.pickle", "wb") as f:
                pickle.dump(nets[0], f)
            run = False
            raise SystemExit()
            break



        x_data.append(GENERATION)
        y_data.append(score)

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
