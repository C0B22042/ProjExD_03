import random
import sys
import time
import math

import pygame as pg


WIDTH = 900  # ゲームウィンドウの幅
HEIGHT = 600  # ゲームウィンドウの高さ


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとん，または，爆弾SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }

    ang = list()
    for i in range(8):
        ang.append([-i*45+90, i>4])

    angles = dict(zip(
        [(0, -5), (5, -5), (5, 0), (5, 5), (0, 5), (-5, 5), (-5, 0), (-5, -5)], 
        ang
    ))

    angle = 0

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        self.original_img = pg.transform.flip(  # 左右反転
            pg.transform.rotozoom(  # 2倍に拡大
                pg.image.load(f"ex03/fig/{num}.png"), 
                0, 
                2.0), 
            True, 
            False
        )
        self.img = self.original_img
        self.rct = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface, ):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"ex03/fig/{num}.png"), 0, 2.0)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface, invaldation_angle = False):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not invaldation_angle and sum_mv != [0, 0]:
            self.angle, flip = __class__.angles[tuple(sum_mv)]
            sub_img = self.original_img
            if flip:
                sub_img = pg.transform.flip(self.original_img, False, True)
            self.img = pg.transform.rotozoom(sub_img, self.angle, 1.0)
        screen.blit(self.img, self.rct)

    def get_Angle(self):
        return self.angle


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int, bird: Bird):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """

        def gen_rec_rand_xy():
            """
                bird周辺のボム生成を制限する
            """
            prohibited_range = bird.rct[:]
            for i in range(2):
                prohibited_range[i] -= prohibited_range[i+2]//2
                prohibited_range[i+2] = prohibited_range[i] + prohibited_range[i+2]*2
            while True:
                xy = random.randint(0+rad, WIDTH-rad), random.randint(0+rad, HEIGHT-rad)
                if not (prohibited_range[0] < xy[0] < prohibited_range[2]):
                    if not (prohibited_range[1] < xy[1] < prohibited_range[3]):
                        break
            return xy
        
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()

        color = list(color)
        self.notice_img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.notice_img, color, (rad, rad), rad)
        self.notice_img.set_colorkey((0, 0, 0))
        self.notice_img.set_alpha(127)

        self.rct.center = gen_rec_rand_xy()

        self.notice = -50
            
            
        random.randint(0, 360)
        angle = math.radians(random.randint(0, 360))
        self.vx, self.vy = math.cos(angle)*5, math.sin(angle)*5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if self.notice < 0:
            screen.blit(self.notice_img, self.rct)

        else:
            yoko, tate = check_bound(self.rct)
            if not yoko:
                self.vx *= -1
            if not tate:
                self.vy *= -1
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)

        self.notice += 1

class Beam: 
    """
     beam に関するクラス
    """
    __beam_count = 0
    
    def __init__(self):
        """
         beam surfaceを生成
        """
        self.beam_surface = pg.image.load("ex03/fig/beam.png")
        self.sur_beams = dict()

        self.cool_time = 1
    
    """
     beam surfaceをSurfaces classに渡し、初期化
     bird_rctに依存したbeamの始点を代入
    """
    def MakeBeam(self, bird: Bird):
        if self.cool_time > 0:
            angle = bird.get_Angle()
            new_beam_surface = pg.transform.rotozoom(self.beam_surface, angle, 1.0)
            rad_angle = math.radians(angle)
            xy_for_angle = [math.cos(rad_angle)*5, -math.sin(rad_angle)*5]
            self.sur_beams[self.__beam_count] = Surfaces([new_beam_surface], [xy_for_angle])
            beam_rct = self.sur_beams[self.__beam_count].rects[0]
            beam_rct[:2] = [bird.rct[i] + bird.rct[i+2]//2 - beam_rct[i+2]//2 + f3*12 for i,f3 in enumerate(xy_for_angle)]
            self.sur_beams[self.__beam_count].set_rects([beam_rct])
            self.__beam_count += 1
            self.cool_time = -30
        return

    """
     screenに表示、また画面外のbeam surfaceを削除
    """    
    def Load(self, screen: pg.Surface):
        del_key = list()
        for key in self.sur_beams:
            rect = self.sur_beams[key].rects[0]
            if rect[0] > WIDTH:
                del_key.append(key)
                continue
            self.sur_beams[key].LoadRect()
            screen.blit(*self.sur_beams[key].get_blit(0))
        for key in del_key:
            del self.sur_beams[key]
        self.cool_time += 1
        return
    
    def explosion(self, bombs):
        del_key = list()
        for key in self.sur_beams:
            if bombs.colliderect(self.sur_beams[key].rects[0]):
                del_key.append(key)
        for key in del_key:
            del self.sur_beams[key]
        return len(del_key) > 0
    
class explosion:
    """
        爆裂！
    """

    def __init__(self) -> None:
        """
            setup variables and surface
        """
        self.explosion_img = [pg.image.load("ex03/fig/explosion.gif")]
        self.explosion_img.append(pg.transform.flip(self.explosion_img[0], True, True))
        self.explosions = list()
        self.explosions_count = list()
    
    def Make(self, rect: pg.Rect):
        """
            make new beam
        """
        self.explosions.append(Surfaces(self.explosion_img))
        self.explosions[-1].set_rects([rect for i in range(2)]) 
        self.explosions_count.append(0)
        return
    
    def Update(self, screen: pg.Surface):
        """
            meam updata and del surface
        """
        del_index = list()
        for i in range(len(self.explosions)):
            self.explosions_count[i] += 1
            if self.explosions_count[i] > 40:
                del_index.append(i)
                continue
            screen.blit(*self.explosions[i].get_blit(self.explosions_count[i]%2))
        for i in range(len(del_index)):
            del self.explosions[i]
            del self.explosions_count[i]
        return
    
    def HitJudge(self, bird: Bird) -> bool:
        """
            explosion に当たり判定を追加
        """
        explosion: Surfaces = None
        for explosion in self.explosions:
            explosion.UpdateRect()
            if bird.rct.colliderect(explosion.rects[0]):
                return True
        return False
        
class Score:
    """
        点数表示
    """

    def __init__(self):
        """
            setup font, color and score 
        """
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = -1

        self.count_up()
        
    def count_up(self):
        """
            score count up
        """
        self.score += 1
        self.sco_img = self.font.render(f"スコア:{self.score}", 0, self.color)
        return
    
    def draw_score(self, screen: pg.Surface):
        """
            draw score surface
        """
        screen.blit(self.sco_img, self.sco_img.get_rect())
        return

"""
 Surfaces class is surface objects management module
  surface objectをlist型、またはdict型で一括管理することが可能です。
"""
class Surfaces:

    """
      __init__
    　　Surfaces classの初期化、または初期データ代入
    """
    def __init__(self, surfaces: list["Surface", ...] = None,
                 move_rp: list[list[float, float], ...] = [[0.0, 0.0]]):
        self.surfaces = list()
        self.rects = list()
        self.move_rp = list()
        self.__move_result = list()

        if surfaces is not None:
            self.__AddList(surfaces, move_rp)

    """
     MakeDict methode
      surfaces, move_rp, rectsのdictionary化
    """
    def MakeDict(self, keys: list[str, ...] | list[tuple, ...]):
        temporary = self.surfaces, self.move_rp, self.__move_result, self.rects
        self.surfaces, self.move_rp, self.__move_result, self.rects = [dict() for i in range(len(temporary))]

        self.__AddDict(temporary[0], temporary[1], temporary[2], keys)

    """
     Add methode
      新しいsurface objectの追加代入
    """
    def Add(self, surfaces: list["Surface", ...], move_rp: list[list[float, float], ...] = [[0.0, 0.0]],
            keys: list[str, ...] | list[tuple, ...] = None):
        if type(self.surfaces) is list:
            self.__AddList(surfaces, move_rp)
        else:
            self.__AddDict(surfaces, move_rp, keys)

    # protected methode
    def __AddList(self, surfaces, move_rp):
        move_rp_one = self.__NumCheckMoveRP(move_rp, surfaces)

        for i, surface in enumerate(surfaces):
            self.surfaces.append(surface)
            self.rects.append(surface.get_rect())
            if move_rp_one: i = 0
            self.move_rp.append(move_rp[i])
            self.__move_result.append([float(self.rects[-1][0]), float(self.rects[-1][1])])
        return

    # protected methode
    def __AddDict(self, surfaces, move_rp, move_result, keys):
        move_rp_one = self.__NumCheckMoveRP(move_rp, surfaces)

        for i, (surface, key) in enumerate(zip(surfaces, keys)):
            self.surfaces[key] = surface
            self.rects[key] = surface.get_rect()
            if move_rp_one: i = 0
            self.move_rp[key] = move_rp[i]
            self.__move_result[key] = move_result[i]
        return

    # protected methode
    @staticmethod
    def __NumCheckMoveRP(move_rp, surfaces):
        if len(move_rp) != 1:
            if len(move_rp) != len(surfaces):
                raise TypeError(
                    "Number of data in move_rp does not match surfaces - "
                    "len(move_rp) != len(surface) and len(move_rp) != 1")
            return False
        else:
            return True

    """
     LoadRect methode
      __move_resultにmove_rpに従った数値(float)を加算
    """
    def LoadRect(self):
        if type(self.surfaces) is list:
            for i in range(len(self.rects)):
                for j in range(2):
                    self.__move_result[i][j] += self.move_rp[i][j]
            return
        else:
            for key in self.surfaces:
                for j in range(2):
                    self.__move_result[key][j] += self.move_rp[key][j]
            return

    """
     get_blit mothode
      Surface.blit()に利用する引数のlist型を出力
      (なお、__move_resultをrectsに代入して処理する)
    """
    def get_blit(self, index_or_key: int | str | tuple):
        self.UpdateRect()
        if type(self.surfaces) is list:
            return self.surfaces[index_or_key], self.rects[index_or_key]
        else:
            return [self.surfaces[index_or_key], self.rects[index_or_key]]

    """
     LoadRect methode
      __move_resultのデータを整数化し、rectsに代入
      (特異的処理以外ではLoadRectでのみデータを変更する)
    """
    def UpdateRect(self):
        if type(self.surfaces) is list:
            for i in range(len(self.__move_result)):
                self.rects[i][:2] = [int(self.__move_result[i][0]), int(self.__move_result[i][1])]
            return
        else:
            self.rects = dict()
            for key in self.surfaces:
                self.rects[key][:2] = [int(self.__move_result[key][0]), int(self.__move_result[key][1])]
            return
        
    def set_rects(self, rects: list[pg.Rect, ...]):
        """
            現在位置rectを更新する
        """
        if len(rects) != 1:
            if len(rects) != len(self.surfaces):
                raise TypeError(
                    "Number of data in move_rp does not match surfaces - "
                    "len(move_rp) != len(surface) and len(move_rp) != 1")
        for i in range(len(self.surfaces)):
            self.__move_result[i] = rects[i]

    def set_rect(self, rect: list[pg.Rect], index: int):
        """
            現在位置rectをrectに更新
        """
        self.__move_result[index][:2] = rect[:2]

    def del_surface(self, index: int):
        """
            引数indexのSurfaceを削除
        """
        del self.surfaces[index]
        del self.rects[index]
        del self.__move_result[index]
        del self.move_rp[index]


"""
 SurDicts methode
  Surface classのdictionary化までを行い、classデータを出力
"""
def SurDicts(surfaces: list["Surface", ...], keys: list[str, ...] | list[tuple, ...],
             move_rp: list[list[float, float], ...] = [[0.0, 0.0]]):
    sur = Surfaces(surfaces, move_rp)
    sur.MakeDict(keys)
    return sur

def game_over(bird: Bird, screen: pg.Surface):
    # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
    bird.change_img(8, screen)
    pg.display.update()
    time.sleep(1)
    return 


def main():
    # setup class and variables
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("ex03/fig/pg_bg.jpg")
    bird = Bird(3, (int(WIDTH*9/16), int(HEIGHT*4/9)))
    bombs = [Bomb((255, 0, 0), random.randint(1, 25), bird) for i in range(5)]
    beam = Beam()
    expl = explosion()
    sco = Score()

    clock = pg.time.Clock()
    tmr = 0
    happy_count = 1

    # main loop
    while True:
        # events
        key_lst = pg.key.get_pressed()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beam.MakeBeam(bird)

        # draw and judge

        screen.blit(bg_img, [0, 0])

        # expl 当たり判定
        if expl.HitJudge(bird):
            game_over(bird, screen)
            return

        del_index = list()
        for i in range(len(bombs)):
            if bird.rct.colliderect(bombs[i].rct) and not bombs[i].notice < 0:
                game_over(bird, screen)
                return
        # beamとbombsの衝突判定、削除
            if not bombs[i].notice < 0:
                if beam.explosion(bombs[i].rct):
                    del_index.append(i)
                    bird.change_img(9, screen)
                    happy_count = -30
                    expl.Make(bombs[i].rct)
                    sco.count_up()
                    bombs.append(Bomb((255, 0, 0), random.randint(1, 25), bird))
        for i in del_index:
            del bombs[i]
        #  更新
        for i in range(len(bombs)):
            bombs[i].update(screen)

        inv = False
        if happy_count < 1: inv = True
        bird.update(key_lst, screen, invaldation_angle=inv)
        beam.Load(screen)
        expl.Update(screen)

        sco.draw_score(screen)

        pg.display.update()

        # count process
        if happy_count == 0:
            bird.change_img(3, screen)
            bird.update(key_lst, screen)
            bird.angle = 180
        
        happy_count += 1
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()

"""
    in test4
"""
