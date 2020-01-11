import pygame
import random
import os
import time
import neat
from pygame.locals import *

import math
from time import sleep

pygame.font.init()

WIN_WIDTH = 800
WIN_HEIGHT = 600
GROUND_LEVEL = 500
PLAYER_SOBER_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "player-sober.png")), (100,100))
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "Road_Background.png")), (WIN_WIDTH,WIN_HEIGHT))
OBSTACLE_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "car.png")), (100,100))
STAT_FONT = pygame.font.SysFont("comicsans", 50)

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

clock = pygame.time.Clock()

# class Player:
#     IMG = PLAYER_SOBER_IMG
#     isjump = False
#     # y = v0*t - 0.5*g*t^2
#     # v = v0 - g*t
#
#     #initialize player's position to center
#     def __init__(self):
#         self.x = 50
#         self.y = GROUND_LEVEL
#         self.v0 = -40
#         self.g = 10
#         self.time_counter = 0
#         self.velocity = 0
#
#     def jump(self):
#         self.isjump = True
#         self.velocity = 30
#
#     def update(self):
#         if self.isjump:
#             #self.time_counter += 0.1
#
#             # Change position
#             #displacement = (self.v0 * self.time_counter) - (.5 * self.g * self.time_counter**2)
#             #self.y = (self.v0 * self.time_counter) - (.5 * self.g * self.time_counter**2)
#             self.velocity -= self.g * .1
#
#             self.y -= self.velocity
#
#         # If ground is reached, reset variables.
#         if self.y > GROUND_LEVEL:
#             self.y = GROUND_LEVEL
#             self.isjump = 0
#             self.time_counter = 0
#             self.v0 = -30
#             self.velocity = 0
#
#     def draw(self, window):
#         window.blit(self.IMG, (self.x, self.y))
#
#     def get_mask(self):
#         return pygame.mask.from_surface(self.IMG)

class Player:
    IMG = PLAYER_SOBER_IMG
    def __init__(self):
        self.x = 50
        self.y = GROUND_LEVEL
        # isJump and jumpCount should be attributes of Mario.
        self.isJump = False
        self.jumpCount = 10

    def jump(self):
        # Check if mario is jumping and then execute the
        # jumping code.
        if self.isJump:
            if self.jumpCount >= -10:
                neg = 1
                if self.jumpCount < 0:
                    neg = -1
                self.y -= self.jumpCount**2 * .5 * neg
                self.jumpCount -= .5
            else:
                self.isJump = False
                self.jumpCount = 10

    def draw(self, window):
        window.blit(self.IMG, (self.x, self.y))

    def get_mask(self):
        return pygame.mask.from_surface(self.IMG)


class Obstacle:
    IMG = OBSTACLE_IMG
    GAP = 200
    VEL = 10

    def __init__(self):

        self.x = WIN_WIDTH + 100
        self.y = GROUND_LEVEL
        self.passed = False
        self.set_position()

    def set_position(self):
        position = random.randrange(0, 400)
        self.x += position

    def move(self):
        self.x -= self.VEL

    def draw(self, window):
        window.blit(self.IMG, (self.x, self.y))

    def collide(self, player, win):
        player_mask = player.get_mask()
        obstacle_mask = pygame.mask.from_surface(self.IMG)
        offset = (self.x - player.x, self.y - round(player.y))
        if player_mask.overlap(obstacle_mask, offset):
            return True
        return False


def draw_window(players, window, obstacle):
    window.blit(BG_IMG, (0, 0))
    for player in players:
        player.draw(window)
    obstacle.draw(window)
    pygame.display.update()

def main(genomes, config):

    nets = []
    ge = []
    players = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        players.append(Player())
        g.fitness = 0
        ge.append(g)

    #player = Player()
    obstacles = [Obstacle()]

    clock.tick(60)

    score = 0

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        # in case there are more than one line of obstacles
        obstacle_index = 0
        if len(players) > 0:
            if len(obstacles) > 1 and players[0].y < obstacles[0].y + obstacles[0].IMG.get_height():
                obstacle_index = 1
        else:
            run = False
            break

        for x, player in enumerate(players):
            ge[x].fitness += 0.1
            output = nets[x].activate((player.x,
                                       obstacles[obstacle_index].x
                                       ))
            print(obstacles[obstacle_index].x)
            if output[0] > 0.5:
                player.isJump = True

        add_obstacle = False
        removed_obstacle = []
        for obstacle in obstacles:
            for x, player in enumerate(players):
                # check if collide
                if obstacle.collide(player, WIN):
                    ge[x].fitness -= 10
                    # remove collided player
                    nets.pop(players.index(player))
                    ge.pop(players.index(player))
                    players.pop(players.index(player))

                # if the player dodge the obstacle
                if not obstacle.passed and obstacle.x < player.x:
                    obstacle.passed = True
                    add_obstacle = True

                obstacle.move()

            # if obstacle passes the screen
            if obstacle.x + obstacle.IMG.get_width() < 0:
                removed_obstacle.append(obstacle)

        if add_obstacle:
            score += 1
            # increase fitness for players that make through each obstacle
            for g in ge:
                g.fitness += 5
            obstacles.append(Obstacle())

        for r in removed_obstacle:
            obstacles.remove(r)

        player.jump()
        pygame.display.update()
        draw_window(players, WIN, obstacle)

#main()

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