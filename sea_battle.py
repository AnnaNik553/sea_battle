import random
import sys
import time


class BoardOutException(Exception):
    pass


class UsedPointException(Exception):
    pass


class DotIsAShipException(Exception):
    pass


class PointIsContourException(Exception):
    pass


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.ship = False
        self.may_exist = True
        self.value = '\u25CC'  # '\u25CC' - 0 - закрытая клетка, Т - промах, Х - попадание

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Ship:
    def __init__(self, length, stpoint, orientation='horizontal'):
        self.length = length
        self.stpoint = stpoint
        self.orientation = orientation
        self.quantity_of_life = length
        if self.orientation == 'horizontal':
            self.dots = [(self.stpoint[0] + i, self.stpoint[1]) for i in range(self.length)]
        if self.orientation == 'vertical':
            self.dots = [(self.stpoint[0], self.stpoint[1] + i) for i in range(self.length)]

    def get_dots(self):
        return self.dots


class Board:
    N = 6

    def __init__(self, hid=False):
        self.field = [[Dot(j, i) for j in range(1, self.N + 1)] for i in range(1, self.N + 1)]
        self.ships = []
        self.hid = hid
        self.live_ships = 0

    def add_ship(self, ship):
        if self.out(ship.get_dots()):
            raise BoardOutException("Координаты корабля выходят за поле")

        for dot in ship.get_dots():
            if self.field[dot[1] - 1][dot[0] - 1].ship:
                raise DotIsAShipException('Нельзя поставить корабль, т.к. точка уже явлется кораблем')

        for dot in ship.get_dots():
            if not self.field[dot[1] - 1][dot[0] - 1].may_exist:
                raise PointIsContourException('Нельзя поставить корабль, т.к. точка является контуром другого корабля')

        self.ships.append(ship)
        self.live_ships += 1
        for dot in ship.get_dots():
            self.field[dot[1] - 1][dot[0] - 1].ship = True
        self.contour(ship)

    def contour(self, ship):
        cont = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        cont_dots = []
        for dot in ship.get_dots():
            x, y = dot
            cont_dots.extend([(i[0] + x, i[1] + y) for i in cont if 0 < i[0] + x < 7 and 0 < i[1] + y < 7 and not self.field[i[1] + y - 1][i[0] + x - 1].ship])
        cont_dots = list(set(cont_dots))
        for dot in cont_dots:
            x, y = dot
            self.field[y - 1][x - 1].may_exist = False

    def show(self):
        if self.hid:
            print(' |' + "|".join(map(str, range(1, self.N + 1))) + '|')
            for i, row in enumerate(self.field):
                print(i + 1, end='|')
                for cell in row:
                    print(cell.value, end='|')
                print()
            print('-' * 10)
        else:
            print(' |' + "|".join(map(str, range(1, self.N + 1))) + '|')
            for i, row in enumerate(self.field):
                print(i + 1, end='|')
                for cell in row:
                    if cell.ship and cell.value not in ('T', 'X'):
                        print('\u29C8', end='|')
                    else:
                        print(cell.value, end='|')
                print()
            print('-' * 10)

    def out(self, dots):
        if isinstance(dots, Dot):
            return not 0 < dots.x < 7 or not 0 < dots.y < 7
        if isinstance(dots, tuple):
            return not 0 < dots[0] < 7 or not 0 < dots[1] < 7
        for dot in dots:
            if not 0 < dot[0] < 7 or not 0 < dot[1] < 7:
                return True
        return False

    def shot(self, target):
        if self.out(target):
            raise BoardOutException("Координаты выстрела выходят за поле")
        dot = self.field[target[1] - 1][target[0] - 1]
        if dot.value in ('T', 'X'):
            raise UsedPointException('Повторный выстрел в точку')
        if not dot.ship:
            dot.value = 'T'
            return False
        else:
            dot.value = 'X'
            for ship in self.ships:
                if (dot.x, dot.y) in ship.get_dots():
                    ship.quantity_of_life -= 1
            return True


class Player:
    def __init__(self, board, enemy_board):
        self.board = board
        self.enemy_board = enemy_board

    def ask(self):
        pass

    def move(self):
        coords = self.ask()
        try:
            hit = self.enemy_board.shot(coords)
            if hit:
                print('\n---Попадание!---\n')
            else:
                print('\n---Промах (---\n')
            return hit
        except BoardOutException:
            print('\nПовторите попытку. Координаты точки выстрела могут быть от 1 до 6 включительно\n')
            return True
        except UsedPointException:
            print('\nПовторите попытку. Укажите другие координаты.\n')
            return True


class AI(Player):
    def __init__(self, board, enemy_board):
        super().__init__(board, enemy_board)
        self.used_points = []

    def ask(self):
        while True:
            x = random.randint(1, 6)
            y = random.randint(1, 6)
            if (x, y) in self.used_points:
                continue
            self.used_points.append((x, y))
            return x, y


class User(Player):
    def ask(self):
        while True:
            try:
                coord = tuple(map(int, input('Введите координаты выстрела x и y через пробел, например "1 2": ').split()))
                if len(coord) != 2:
                    print('Введите два числа от 1 до 6')
                    continue
                return coord
            except ValueError:
                print('Координаты должны быть числами')


class Game:
    MAX_TRY_COUNT = 5_000

    def __init__(self):
        self.user = None
        self.user_board = None
        self.comp = None
        self.comp_board = None

    def random_board(self):
        len_ships = (3, 2, 2, 1, 1, 1, 1)
        while True:
            board = Board()
            for l in len_ships:
                count = 0
                while True:
                    count += 1
                    ship = Ship(l, (random.randint(1, 6), random.randint(1, 6)), orientation=random.choice(['horizontal', 'vertical']))
                    try:
                        board.add_ship(ship)
                        break
                    except PointIsContourException:
                        continue
                    except BoardOutException:
                        continue
                    except DotIsAShipException:
                        continue
                    finally:
                        if count > self.MAX_TRY_COUNT:
                            break
            if len(board.ships) < len(len_ships):
                continue
            return board

    def greet(self):
        print('Добро пожаловать в игру "Морской бой"!\n'
              'У игрока и компьютера есть доска с расставленными кораблями:\n'
              '1 корабль на 3 клетки, 2 корабля на 2 клетки и 4 корабля на одну клетку.\n'
              'Игрок и компьютер поочередно делаю выстрел по доске соперника.\n'
              'Координаты выстрела должны быть в пределах доски от 1 до 6 включительно.\n'
              'Выигрывает тот, кто первым поразит все корабли соперника.\nУдачи!\n')

    def loop(self):
        self.user_board = self.random_board()
        self.comp_board = self.random_board()
        self.comp_board.hid = True
        self.user = User(self.user_board, self.comp_board)
        self.comp = AI(self.comp_board, self.user_board)

        whose_move = 1  # 1 - игрок, 2 - компьютер
        while True:
            while whose_move == 1:
                print('Ваша доска')
                self.user_board.show()
                print('Доска противника')
                self.comp_board.show()
                self.check_win()
                if self.user.move():
                    continue
                else:
                    whose_move = 2
                    break
            while whose_move == 2:
                print('\nХод компьютера\n')
                time.sleep(1)
                print('Ваша доска')
                self.user_board.show()
                print('Доска противника')
                self.comp_board.show()
                self.check_win()
                if self.comp.move():
                    continue
                else:
                    whose_move = 1
                    break

    def check_win(self):
        if len([ship for ship in self.comp_board.ships if ship.quantity_of_life > 0]) == 0:
            print('\n-------------\nВы выйграли!\n-------------\n')
            sys.exit(0)
        if len([ship for ship in self.user_board.ships if ship.quantity_of_life > 0]) == 0:
            print('\n-------------\nВы проиграли\n-------------\n')
            sys.exit(0)

    def start(self):
        self.greet()
        self.loop()


game = Game()
game.start()
