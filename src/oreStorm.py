"""
Ore Storm
Two Player Arcade Survival
(elements of sopwith and lode runner)
"""

from enum import Enum, IntEnum
import os, pygame, random

# --- Global constants ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Ore Storm"

BACKGROUNDCOLOR = WHITE

FPS = 60

# --- Game Resources ---
SOUND_DATAPATH = 'data'
SOUNDS = IntEnum("SOUNDS", "PLANE_FIRE PICKUP_AMMO")
#SOUNDS = IntEnum("SOUNDS", "PLANE_FIRE PLANE_COLLIDE PLAYER_JUMP PLAYER_DIE BLOCK_CRASH BLOCK_DIE")


# --- Classes ---

# Audio System
class StandardAudio(object):
    # TODO -- improve soundfile loading and playing using LocatorService to allow in-game muting/unmuting --

    def __init__(self):
        self.loadAudioFiles()

    def play(self, audioID):
        try:
            index = int(audioID) - 1 # offset index as Enum starts at 1
            self.sounds[index].play()
        except:
            print("failed to play sound: %s." % str(audioID.name))

    def loadAudioFiles(self):
        self.sounds = []
        for item in SOUNDS:
            try:
                sound = pygame.mixer.Sound(os.path.join(SOUND_DATAPATH, str(item.name)+'.wav'))
                self.sounds.append(sound)

            except:
                print(str(item.name)+'.wav')
                raise UserWarning("Failed to load sound file in %s folder." % SOUND_DATAPATH)


class NullAudio(object):
    def __init__(self):
        # Debug print
        print("INFO: NullAudio initialized -- sound's muted!")

    def play(self, audioID):
        pass

# Spritesheet handling class from pygame cookbook
# modified -- added transforming loop
class Spritesheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error as message:
            print('Unable to load spritesheet image:', filename)
            raise SystemExit(message)
    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey = None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image
    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey = None):
        "Loads multiple images, supply a list of coordinates"
        return [self.image_at(rect, colorkey) for rect in rects]
    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey = None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)
    # Scale images images in a list
    def scale_images(self, images_list, width, height):
        "Returns a list of scaled images"
        scaled_images = []
        for i in range(len(images_list)):
            scaled_images.append(pygame.transform.scale(images_list[i], (width, height)))
        return scaled_images

    def mirror_images(self, images_list, flipX, flipY):
        "Returns a list of mirrored images"
        mirrored_images = []
        for i in range(len(images_list)):
            mirrored_images.append(pygame.transform.flip(images_list[i], flipX, flipY))
        return mirrored_images

class GravitySprite(pygame.sprite.Sprite):
    """ Abstract class that implements basic gravity.
    Note: hack implementation -- currently requires rect to be updated by change_y variable"""
    def __init__(self):
        super().__init__()

        # speed vector
        self.change_y = 0

    def calc_gravity(self):
        """ Calculate gravity """
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += .35

class AmmoBox(GravitySprite):
    """ Ammobox item that adds ammo to planePlayer """

    # --- AmmoBox constants ---
    AMMOBOX_COLOR = GREEN
    AMMOBOX_WIDTH = 20
    AMMOBOX_HEIGHT = 8

    def __init__(self, pos, platform_list):
        """Constructor, create ammobox image."""
        super().__init__()
        self.image = pygame.Surface([self.AMMOBOX_WIDTH, self.AMMOBOX_HEIGHT])
        self.image.fill(self.AMMOBOX_COLOR)
        self.rect = self.image.get_rect()

        self.rect.center = pos
        self.platform_list = platform_list

        #speed vectors
        self.change_x = 0

    def activate(self, player):
        print("bonus ammo!")
        audioSystem.play(SOUNDS.PICKUP_AMMO)
        player.addAmmo(10)

    def update(self):
        """move the box"""
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
            # debug
            print("box is gone and this should only appear once")


        self.calc_gravity()

                # move up/down
        self.rect.y += self.change_y

        # vertical collision check
        block_hit_list = pygame.sprite.spritecollide(self, self.platform_list, False)
        for block in block_hit_list:
            # Reset position based on the top/bottom of object
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom

            self.change_y = 0


class Bullet(pygame.sprite.Sprite):
    """ Bullets fired by players to destroy blocks."""

    # --- Bullet constants ---
    BULLET_COLOR = GREEN
    BULLET_WIDTH = 5
    BULLET_HEIGHT = 10
    BULLET_SPEED = 8


    def __init__(self, pos):
        """Constructor, create image of bullet. """
        super().__init__()
        self.image = pygame.Surface([self.BULLET_WIDTH, self.BULLET_HEIGHT])
        self.image.fill(self.BULLET_COLOR)
        self.rect = self.image.get_rect()

        self.rect.center = pos

        # debug message
        print("new bullet at " + str(self.rect.center))


    def update(self):
        if self.rect.bottom < 0:
            self.kill()
            # debug message
            print("gone and you should only see this once per shot")
        else:
            self.rect.y -= self.BULLET_SPEED




class Block(GravitySprite):
    """ This class represents a falling block. """
    # --- Block constants ---
    PAYLOADS = ['bomb', 'fuel']
    BLOCK_WIDTH = 20
    BLOCK_HEIGHT = 20

    def __init__(self):
        """ Constructor, create the image of the block. """
        super().__init__()
        self.image = pygame.Surface([self.BLOCK_WIDTH, self.BLOCK_HEIGHT])
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()

        self.set_payload()
        self.set_fallBehavior()

        #speed vectors
        self.change_x = 0

    def set_fallBehavior(self):
        # assigns fall() to a fallBehavior
        self.fall = self.linearFallBehavior

        #### TESTING ####
        ## mixed fall types ##
        if random.randint(1,100) > 95:
            self.fall = self.basicGravityFallBehavior
        ### END TEST ####

    # fallBehavior strategies
    def linearFallBehavior(self):
        self.rect.y += 1
        if self.rect.y > SCREEN_HEIGHT + self.rect.height:
            self.reset_pos()

    def basicGravityFallBehavior(self):
        self.calc_gravity()

        # reset box and timeFallen if it clears screen
        if self.rect.y > SCREEN_HEIGHT + self.rect.height:
            self.change_y = 0
            self.reset_pos()

        # move rect
        self.rect.y += self.change_y


    def set_payload(self):
        "determine what the box contains"
        if random.randint(1,100) > 50:
            self.payload = random.choice(self.PAYLOADS)
            if self.payload == 'bomb':
                self.image.fill(RED)
            if self.payload == 'fuel':
                self.image.fill(GREEN)
        else:
            self.payload = None
            self.image.fill(BLACK)

    def reset_pos(self):
        """ Called when the block is 'collected' or falls off
        the screen. """
        self.rect.y = random.randrange(-300, -20)
        self.rect.x = random.randrange(SCREEN_WIDTH)
        self.set_payload()

    def drop(self, groups, platform_list):
        if self.payload == 'fuel':
            print("pickup dropped")
            p = AmmoBox(self.rect.center, platform_list)
            for group in groups:
                group.add(p)

    def update(self):
        """ Automatically called when we need to move the block. """
        self.fall() # calls the fall strategy selected on creation

class PlanePlayer(pygame.sprite.Sprite):
    """ This class represents the player in control of the aircraft. """

    # --- Class Constants ---
    PLANE_WIDTH = 20
    PLANE_HEIGHT = 20
    PLANE_AMMO = 20

    RECOIL_DISTANCE = 10

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([self.PLANE_WIDTH, self.PLANE_HEIGHT])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.ammo = self.PLANE_AMMO

        self.offset_x = 0;
        self.offset_y = 0;

    def fire(self, groups):

        if self.ammo > 0:
            # play sfx
            # TODO -- configure AudioLocator to play sound
            audioSystem.play(SOUNDS.PLANE_FIRE)
            # expend ammo
            self.ammo -= 1
            print("fire! bullets remaining: " + str(self.ammo))
            # create a new bullet and add to appropriate Sprite groups
            b = Bullet(pygame.mouse.get_pos())
            for group in groups:
                group.add(b)
            # recoil from shot
            self.recoil()
        else:
            print("out of ammo!")

    def addAmmo(self, num):
        self.ammo += num

    def recoil(self):
        self.offset_y += self.RECOIL_DISTANCE

    def update(self):
        """ Update the player location. """
        pos = pygame.mouse.get_pos()
        adjustedPos = (pos[0], pos[1] + self.offset_y)
        self.rect.center = adjustedPos

        if self.offset_y > 0:
            self.offset_y -= 1
        else:
            self.offset_y = 0


class GroundPlayer(GravitySprite):
    """ Player in control of ground character."""

    # -- Class Constants ---
    PLAYER_WIDTH = 32
    PLAYER_HEIGHT = 32
    PLAYER_SPEED = 3
    PLAYER_JUMP_HEIGHT = 6

    PLAYER_SPRITESHEET_FILENAME = 'groundPlayer.png'
    PLAYER_SPRITESHEET_PATH = 'data'
    PLAYER_COLORKEY = (157, 142, 135)
    ANIMATION_FRAMEDELAY = 10
    ANIM_STATES = Enum('ANIM_STATES', 'ONGROUND JUMPING FALLING STANDING')
    ANIM_DIRECTIONS = Enum('ANIM_DIRECTIONS', 'LEFT RIGHT')

    # list of sprites that block movement
    level = None

    def __init__(self):
        super().__init__()

        self.loadPlayerImages(Spritesheet(os.path.join(self.PLAYER_SPRITESHEET_PATH, self.PLAYER_SPRITESHEET_FILENAME)))
        self.image = self.images_standing_right[0] # initial image for height/width (arbitrary)
        self.rect = self.image.get_rect()

        # set speed vectors
        self.change_x = 0
        self.change_y = 0


    def loadPlayerImages(self, spritesheet):
        # initialize animation variables
        self.playerAnimationState = None
        self.playerDirectionState = None
        self.current_images_list = None
        self.animation_index = 0
        self.animation_delay = 0

        # load Running images
        self.images_right = spritesheet.images_at([(17, 32, 16, 16), (33, 32, 16, 16), (49, 32, 16, 16), (65, 32, 16, 16), (81, 32, 16, 16), (97, 32, 16, 16)], colorkey=self.PLAYER_COLORKEY)
        self.images_right = spritesheet.scale_images(self.images_right, self.PLAYER_WIDTH, self.PLAYER_HEIGHT)
        self.images_left = spritesheet.mirror_images(self.images_right, True, False)

        # load Standing images
        self.images_standing_right = spritesheet.images_at([(17, 16, 16, 16), (33, 16, 16, 16), (49, 16, 16, 16), (65, 16, 16, 16)], colorkey=self.PLAYER_COLORKEY)
        self.images_standing_right = spritesheet.scale_images(self.images_standing_right, self.PLAYER_WIDTH, self.PLAYER_HEIGHT)
        # arrange the Standing images to include an occasional blinking frame
        self.blink_image = self.images_standing_right[3]
        self.images_standing_right = (self.images_standing_right[:3] + self.images_standing_right[1:2]) * 3
        self.images_standing_right.append(self.blink_image)
        # copy to left facing strip
        self.images_standing_left = spritesheet.mirror_images(self.images_standing_right, True, False)

        # load Jumping images
        self.images_jumping_right = spritesheet.images_at([(17, 48, 16, 16)], colorkey=self.PLAYER_COLORKEY)
        self.images_jumping_right = spritesheet.scale_images(self.images_jumping_right, self.PLAYER_WIDTH, self.PLAYER_HEIGHT)
        self.images_jumping_left = spritesheet.mirror_images(self.images_jumping_right, True, False)

        # load Falling images
        self.images_falling_right = spritesheet.images_at([(33, 48, 16, 16)], colorkey=self.PLAYER_COLORKEY)
        self.images_falling_right = spritesheet.scale_images(self.images_falling_right, self.PLAYER_WIDTH, self.PLAYER_HEIGHT)
        self.images_falling_left = spritesheet.mirror_images(self.images_falling_right, True, False)

    def updatePlayerImage(self):
        # display image and advance index
        # expects animation index to be reset to zero when  current_images_list changes
        self.image = self.current_images_list[self.animation_index]
        self.animation_delay += 1
        if self.animation_delay > self.ANIMATION_FRAMEDELAY:
            self.animation_index += 1
            self.animation_delay = 0
            if self.animation_index >= len(self.current_images_list):
                self.animation_index = 0


    def setPlayerAnimationState(self, playerAnimationState, playerDirectionState):
        """update the player state if it's new"""
        #assert(playerAnimationState
        if self.playerAnimationState != playerAnimationState:
            print("DEBUG: state mismatch! " + str(self.playerAnimationState) + " does not equal " + str(playerAnimationState))
            self.playerAnimationState = playerAnimationState
            self.setCurrentImagesList(playerAnimationState, playerDirectionState)

        if self.playerDirectionState != playerDirectionState:
            print("DEBUG: direction mismatch! " + str(self.playerDirectionState) + " does not equal " + str(playerDirectionState))
            self.playerDirectionState = playerDirectionState
            self.setCurrentImagesList(playerAnimationState, playerDirectionState)

    def setCurrentImagesList(self, playerAnimationState, playerDirectionState):
        """ Also resets the animation index when changing current_images_list
        """
        if playerAnimationState == self.ANIM_STATES.ONGROUND:
            if self.playerDirectionState == self.ANIM_DIRECTIONS.LEFT:
                self.current_images_list = self.images_left
            else:
                self.current_images_list = self.images_right

        elif playerAnimationState == self.ANIM_STATES.STANDING:
            if self.playerDirectionState == self.ANIM_DIRECTIONS.LEFT:
                self.current_images_list = self.images_standing_left
            else:
                self.current_images_list = self.images_standing_right

        elif playerAnimationState == self.ANIM_STATES.JUMPING:
            if self.playerDirectionState == self.ANIM_DIRECTIONS.LEFT:
                self.current_images_list = self.images_jumping_left
            else:
                self.current_images_list = self.images_jumping_right


        elif playerAnimationState == self.ANIM_STATES.FALLING:
            if self.playerDirectionState == self.ANIM_DIRECTIONS.LEFT:
                self.current_images_list = self.images_falling_left
            else:
                self.current_images_list = self.images_falling_right
        else:
            self.current_images_list = self.images_standing_right
        # reset the animation index to start new action from beginning
        self.animation_index = 0


    def update(self):
        """move the player """

        self.calc_gravity()
        self.boundary_check()

        # move left/right
        self.rect.x += self.change_x

        # collision check
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:
            # If moving right, set right side to the left side of item
            if self.change_x > 0:
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                self.rect.left = block.rect.right

        # move up/down
        self.rect.y += self.change_y

        # vertical collision check
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:
            # Reset position based on the top/bottom of object
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom

            self.change_y = 0

        # check if falling for animation state
        self.checkAnimationState()
        self.updatePlayerImage()

    def boundary_check(self):
        # check if on the ground
        if self.rect.y >= SCREEN_HEIGHT and self.change_y >= 0:
        #if self.rect.y >= SCREEN_HEIGHT - self.rect.height and self.change_y >= 0:
            self.change_y = 0
            self.rect.y = SCREEN_HEIGHT

    def jump(self):
        """ Called when user hits 'jump' button """

        # temporarily move down to check if there is a platform to jump from (no air jumps)
        self.rect.y += 2 # works better with two pixels
        platform_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        self.rect.y -= 2

        if len(platform_hit_list) > 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.change_y = -self.PLAYER_JUMP_HEIGHT

    def go_left(self):
        """ move left """
        self.change_x = -self.PLAYER_SPEED

    def go_right(self):
        """ move right """
        self.change_x = self.PLAYER_SPEED

    def stop(self):
        """ called when no input from movement keys """
        self.change_x = 0

    def checkAnimationState(self):
        """ Called to set current AnimationState """
        animationState = self.playerAnimationState
        directionState = self.playerDirectionState




        # Animation state
        if self.change_y > 0:
            animationState = self.ANIM_STATES.FALLING
        elif self.change_y < 0:
            animationState = self.ANIM_STATES.JUMPING
        else:
            animationState = self.ANIM_STATES.ONGROUND

        # Directional State
        if self.change_x > 0:
            directionState = self.ANIM_DIRECTIONS.RIGHT
        elif self.change_x < 0:
            directionState = self.ANIM_DIRECTIONS.LEFT

        # Check if standing still
        if self.change_x == 0 and animationState == self.ANIM_STATES.ONGROUND:
            animationState = self.ANIM_STATES.STANDING

        # set the states
        self.setPlayerAnimationState(animationState, directionState)


class Platform(pygame.sprite.Sprite):
    """ Platform the user can jump on """
    def __init__(self, width, height):
        """ Platform constructor. Assumes constructed with user passing in
        an array of 5 numbers like what's defined at the top of this code.
        """
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()


class Level():
    """ This is a generic super-class used to define a level.
    Create a child class for each level with level-specific
    info. """
    # Lists of sprites used in all levels. Add or remove
    # lists as needed for your game.
    platform_list = None
    enemy_list = None
    # How far this world has been scrolled left/right
    world_shift = 0

    def __init__(self, player):
        """ Constructor. Pass in a handle to player. Needed for when moving
        platforms collide with the player. """
        self.platform_list = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        self.player = player
        # Update everything on this level

    def update(self):
        """ Update everything in this level."""
        self.platform_list.update()
        self.enemy_list.update()

    def draw(self, screen):
        """ Draw everything on this level. """

        # Draw the background
        screen.fill(BACKGROUNDCOLOR)
        # Draw all the sprite lists that we have
        self.platform_list.draw(screen)
        self.enemy_list.draw(screen)

    def shift_world(self, shift_x):
        """ When the user moves left/right and we need to scroll everything: """
        # Keep track of the shift amount
        self.world_shift += shift_x
        # Go through all the sprite lists and shift
        for platform in self.platform_list:
            platform.rect.x += shift_x
        for enemy in self.enemy_list:
            enemy.rect.x += shift_x

    def get_platform_list(self):
        return self.platform_list


class Level_01(Level):
    """ Definition for level 1.
    """
    BLOCKWIDTH = 10

    def __init__(self, player):
        """" Create Level 1. """

        # Call the parent constructor
        Level.__init__(self, player)

        self.level_limit = -1000

        # create Array with width, height, x, and y of platform
        level = []
        for i in range(int(SCREEN_WIDTH/self.BLOCKWIDTH)):
            level.append([self.BLOCKWIDTH, self.BLOCKWIDTH, self.BLOCKWIDTH*i, SCREEN_HEIGHT-self.BLOCKWIDTH])

        # remove a few random floor blocks
        for i in range(random.randint(1,10)):
            level.remove(random.choice(level))

        ## DEBUG ##
        print(level)


        # add platforms per specs in level array
        for platform in level:
            block = Platform(platform[0], platform[1])
            block.rect.x = platform[2]
            block.rect.y = platform[3]
            block.player = self.player # set to ground player
            self.platform_list.add(block)


class Game(object):
    """ This class represents an instance of the game. If we need to
    reset the game we'd just need to create a new instance of this
    class. """
    # --- Class attributes.
    # In this case, all the data we need
    # to run our game.
    # Sprite lists
    pickups_list = None
    bullet_list = None
    block_list = None
    all_sprites_list = None
    player = None
    # Other data
    game_over = False
    score = 0
    # --- Class methods
    # Set up the game

    def __init__(self):
        self.score = 0
        self.game_over = False

        # Load Sounds
        self.load_sounds()

        # Create sprite lists
        self.pickups_list = pygame.sprite.Group()
        self.bullet_list = pygame.sprite.Group()
        self.block_list = pygame.sprite.Group()
        self.all_sprites_list = pygame.sprite.Group()
        # Create the block sprites
        for i in range(5):
            block = Block()
            block.rect.x = random.randrange(SCREEN_WIDTH)
            block.rect.y = random.randrange(-300, SCREEN_HEIGHT)
            self.block_list.add(block)
            self.all_sprites_list.add(block)
        # Create the plane player
        self.player = PlanePlayer()
        self.all_sprites_list.add(self.player)

        # Create the ground player
        self.player2 = GroundPlayer()
        self.all_sprites_list.add(self.player2)

        # Create the levels
        self.level_list = []
        self.level_list.append(Level_01(self.player2))

        # set current level
        self.current_level_num = 0
        self.current_level = self.level_list[self.current_level_num]
        # associate level with player
        self.player2.level = self.current_level

    def load_sounds(self):
        global audioSystem # TODO replace direct call to audioSystem with audioLocator.provide()?
        audioSystem = StandardAudio()
        #audioSystem = NullAudio() # mute sound

    def process_events(self):
        """ Process all of the events. Return a "True" if we need
        to close the window. """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            # checking for mouse up before mouse down to prevent initial shot on game restart
            if event.type == pygame.MOUSEBUTTONUP:
                self.player.fire([self.bullet_list, self.all_sprites_list])
                if self.game_over:
                    self.__init__()
                    return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                pass



            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.player2.go_left()
                if event.key == pygame.K_RIGHT:
                    self.player2.go_right()
                if event.key == pygame.K_UP:
                    self.player2.jump()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and self.player2.change_x < 0:
                    self.player2.stop()
                if event.key == pygame.K_RIGHT and self.player2.change_x > 0:
                    self.player2.stop()

    def run_logic(self):
        """
        This method is run each time through the frame. It
        updates positions and checks for collisions.
        """
        if not self.game_over:
            # Move all the sprites
            self.all_sprites_list.update()

            ### DOES THIS WORK? ####
            self.current_level.update()

            # check if a player hit a pickup
            pickups_hit_list = pygame.sprite.spritecollide(self.player2, self.pickups_list, True)
            for pickup in pickups_hit_list:
                pickup.activate(self.player) # add effect to airplayer -- currently poorly named player
                print("pickup gathered!")

            # check if a bullet hit a falling block (kill block and bullet)
            blocks_hit_list = pygame.sprite.groupcollide(self.block_list, self.bullet_list, True, True)
            for block in blocks_hit_list:
                block.drop([self.pickups_list, self.all_sprites_list], self.current_level.get_platform_list())

            # Check if falling block hits a player (game over)
            blocks_hit_list = pygame.sprite.spritecollide(self.player2, self.block_list, False)
            for block in blocks_hit_list:
                print("Ouch!")
                self.game_over = True;

            # See if the player block has collided with anything.
            blocks_hit_list = pygame.sprite.spritecollide(self.player, self.block_list, True)
            # Check the list of collisions.
            for block in blocks_hit_list:
                self.score += 1
                print(self.score)
                # You can do something with "block" here.

            # See if block hits platform
            blocks_hit_list = pygame.sprite.groupcollide(self.current_level.get_platform_list(), self.block_list, True, False)
            # debug
            #for block in blocks_hit_list:
                # print("crash!")

        if len(self.block_list) == 0:
            self.game_over = True

    def display_frame(self, screen):
        """ Display everything to the screen for the game. """
        screen.fill(WHITE)
        if self.game_over:
            font = pygame.font.SysFont("serif", 25)
            text = font.render("Game Over, click to restart", True, BLACK)
            center_x = (SCREEN_WIDTH // 2) - (text.get_width() // 2)
            center_y = (SCREEN_HEIGHT // 2) - (text.get_height() // 2)
            screen.blit(text, [center_x, center_y])
            pygame.display.flip()
        if not self.game_over:
            self.current_level.draw(screen)
            self.all_sprites_list.draw(screen)
            pygame.display.flip()

def main():
    """ Main program function. """
    pygame.mixer.pre_init(22050, -16, 2, 1024)
    # Initialize Pygame and set up the window
    pygame.init()
    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption(SCREEN_TITLE)
    pygame.mouse.set_visible(False)
    # Create our objects and set the data
    done = False
    clock = pygame.time.Clock()
    # Create an instance of the Game class
    game = Game()
    # Main game loop
    while not done:
        # Process events (keystrokes, mouse clicks, etc)
        done = game.process_events()
        # Update object positions, check for collisions
        game.run_logic()
        # Draw the current frame
        game.display_frame(screen)
        # Pause for the next frame
        clock.tick(FPS)
    # Close window and exit
    pygame.quit()
# Call the main function, start up the game
if __name__ == "__main__":
    main()