import math
import os
import random
import sys
import time
import pygame as pg



WIDTH = 480  # ゲームウィンドウの幅
HEIGHT = 720  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"
        self.hyper_life = 500

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        if  key_lst[pg.K_LSHIFT]:
                self.speed = 20
        else:
                self.speed = 10
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]

        if self.state == "hyper":
            # self.image = pg.transform.laplacian(self.imgs[self.dire])
            self.image = pg.transform.laplacian(self.image)
            if self.hyper_life < 0:
                self.state = "normal"
                # print(f"state:{self.state}")
            self.hyper_life -= 1
        else:
            self.image = self.imgs[self.dire]
            # print(self.hyper_life)
        
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)

class Gravity(pg.sprite.Sprite):
    """
    追加機能2
    """
    def __init__(self, life: int):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, WIDTH, HEIGHT))
        self.image.set_alpha(200)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH/2, HEIGHT/2
        self.life = life

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 10000
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class EMP:
    """
    機体を無力化
    enemyクラスからintervalを呼び出し、無限(inf)にする
    爆弾を無力化
    透明な黄色を表示
    0.05秒で更新する
    """
    def __init__(self,  enemies: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.surface):
        for enemy in enemies:
            enemy.interval = math.inf
            enemy.image = pg.transform.laplacian(enemy.image)
            enemy.image.set_colorkey((0, 0, 0))
        for bomb in bombs:
            bomb.speed /=2
            bomb.state = "inactive"
        img = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(img, (255, 255, 0),(0, 0, WIDTH, HEIGHT))
        img.set_alpha(100)
        screen.blit(img, [0, 0])
        pg.display.update()
        time.sleep(0.05)


        
class Shield(pg.sprite.Sprite):
    def __init__(self, bird, life):
        super().__init__()
        bx,by = bird.rect.center
        bw = bird.image.get_width()
        bh = bird.image.get_height()

        self.life = life

        self.shild = pg.Surface((20, bh*2))
        self.image = pg.draw.rect(self.shild, (0, 0, 255), (0, 0, 20, bh*2))
        self.shild.set_colorkey((0, 0, 0))

        vx, vy = bird.dire
        self.imageagree = math.degrees(math.atan2(-vy, vx))
        self.image = pg.transform.rotate(self.shild, self.imageagree)
        
        self.rect = self.image.get_rect()
        if bird.dire == (1, 0):
            self.rect.center = bx+bw, by
        elif bird.dire == (1, -1):
            self.rect.center = bx+bw//2, by-bw//2
        elif bird.dire == (0, -1):
            self.rect.center = bx, by-bw
        elif bird.dire == (-1, -1):
            self.rect.center = bx-bw//2, by-bw//2
        elif bird.dire == (-1, 0):
            self.rect.center = bx-bw, by
        elif bird.dire == (-1, 1):
            self.rect.center = bx-bw//2, by+bw//2
        elif bird.dire == (0, 1):
            self.rect.center = bx, by+bw
        elif bird.dire == (1, 1):
            self.rect.center = bx+bw//2, by+bw//2
    
    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()

class Weapon(pg.sprite.Sprite):
    def __init__(self, bird):
        super().__init__()
        self.bird = bird
        self.speed = 10
        self.damage = 1
        self.life = 1000

    def update(self):
        self.life -= 1
        if check_bound(self.rect) != (True, True):
            self.kill()

class NormalWeapon(Weapon):
    def __init__(self, bird: Bird, beam_x: int = 0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__(bird)
        img = pg.image.load(f"fig/beam.png")
        small_image = pg.transform.scale(img, (img.get_width() // 3, img.get_height() // 3))
        self.image = pg.transform.rotozoom(small_image, 90, 2.0)  # 常に上向き
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + beam_x
        self.rect.bottom = bird.rect.top  # こうかとんの上端に配置

    def update(self):
        """
        ビームを移動させる
        """
        self.rect.move_ip(0, -self.speed)
        super().update()

class PenetWeapon(Weapon):
    """敵と衝突しても消えない弾"""
    def __init__(self, bird: Bird, beam_x: int = 0):
        """
        武器画像Surfaceを生成する
        引数 bird：武器を発射するこうかとん
        """
        super().__init__(bird)
        img = pg.image.load(f"fig/beam.png")
        small_image = pg.transform.scale(img, (img.get_width() // 3, img.get_height() // 3))
        self.image = pg.transform.rotozoom(small_image, 90, 2.0)  # 常に上向き
        self.image = pg.transform.laplacian(self.image)  # 区別をつける
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + beam_x
        self.rect.bottom = bird.rect.top  # こうかとんの上端に配置
  
    def update(self):
        """
        武器を上方向に移動させる
        """
        self.rect.move_ip(0, -self.speed)  # 常に上方向に移動
        super().update()

class SatelliteWeapon(Weapon):
    def __init__(self, bird: Bird, radius: int = 200, angle : int = 0, angular_speed: float = 0.1):
        super().__init__(bird)
        self.radius = radius
        self.angle = math.radians(angle)
        self.image = pg.Surface((20, 20))
        self.image.set_colorkey((0, 0, 0))
        pg.draw.circle(self.image, (0, 0, 255), (10, 10), 5)
        self.angular_speed = angular_speed
        self.rect = self.image.get_rect()

    def update(self):
        x = self.bird.rect.centerx + math.cos(self.angle) * self.radius
        y = self.bird.rect.centery + math.sin(self.angle) * self.radius
        self.rect.center = (x, y)
        self.angle += self.angular_speed
        if self.angle > 2 * math.pi:
            self.angle -= 2 * math.pi # 角度を0~360度の範囲に収める


class SlashWeapon(Weapon):
    def __init__(self, bird: Bird):
        super().__init__(bird)
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        img = pg.image.load(f"fig/slash_effect.png")
        small_image = pg.transform.scale(img, (img.get_width() // 10, img.get_height() // 25))
        small_image = pg.transform.flip(small_image, True, False)
        self.image = pg.transform.rotozoom(small_image, angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.hp = 10
    
    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        # self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        self.hp -= 1
        print(self.hp)
        if self.hp <= 0:
            self.kill()

class BoomerangWeapon(Weapon):
    def __init__(self, bird: Bird):
        super().__init__(bird)
        self.original_image = pg.Surface((30, 30), pg.SRCALPHA)
        pg.draw.circle(self.original_image, (255, 0, 0), (10, 10), 5)
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = bird.rect.center
        self.speed = 10
        self.max_distance = 300  # ブーメランが飛ぶ最大距離
        self.distance = 0
        self.returning = False
        self.angle = 0
        self.rotation_speed = 10  # 回転速度

    def update(self):
        # ブーメランを回転させる
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pg.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        if not self.returning:
            # 前進
            self.rect.move_ip(0, -self.speed)
            self.distance += self.speed
            if self.distance >= self.max_distance:
                self.returning = True
        else:
            # 戻る
            dx = self.bird.rect.centerx - self.rect.centerx
            dy = self.bird.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                dx, dy = dx / dist, dy / dist
                self.rect.move_ip(dx * self.speed, dy * self.speed)

            # こうかとんに当たったら消滅
            if self.rect.colliderect(self.bird.rect):
                self.kill()

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (WIDTH//2, HEIGHT-100))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()
    gvys = pg.sprite.Group()
    weapons = pg.sprite.Group()
    tmr = 0
    num_barriers = 3
    angle = 360 / num_barriers
    weapon_cooldown ={"bullet":7, "satellite":30, "slash":20, "boomerang":20}  # 30フレーム（約0.6秒）ごとに発射
    weapon_timer = {"bullet":0, "satellite":0, "slash":0, "boomerang":0}
    weapon_dict = {"weapon_mode":2, "satellite":0, "slash":0, "boomerang":1}
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_e: #EMPの実行
                if score.value >= 20:
                    score.value -= 20
                    EMP(emys, bombs, screen)
            if event.type == pg.KEYDOWN and event.key == pg.K_w and shields.sprites() == [] and score.value >= 50:
                shields.add(Shield(bird, 400))
                score.value -= 50
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and score.value > 200:
                gvys.add(Gravity(400))
                score.value -= 200

        for i in weapon_cooldown:
            weapon_timer[i] += 1
        if weapon_timer["bullet"] >= weapon_cooldown["bullet"] and weapon_dict["weapon_mode"] != 2:
            if weapon_dict["weapon_mode"] == 0:
                weapons.add(NormalWeapon(bird, 10))
                weapons.add(NormalWeapon(bird, -10))
            elif weapon_dict["weapon_mode"] == 1:
                weapons.add(PenetWeapon(bird, 10))
                weapons.add(PenetWeapon(bird, -10))
            weapon_timer["bullet"] = 0
        if weapon_timer["satellite"] >= weapon_cooldown["satellite"]:
            if weapon_dict["satellite"] == 1:
                # SatelliteWeaponを削除
                current_satellite_count = sum(isinstance(weapon, SatelliteWeapon) for weapon in weapons)
                if current_satellite_count < num_barriers:
                    for weapon in list(weapons):
                        if isinstance(weapon, SatelliteWeapon):
                            weapons.remove(weapon)
                    for i in range(num_barriers):
                        ten = angle * i
                        weapons.add(SatelliteWeapon(bird, 75, ten))
            weapon_timer["satellite"] = 0
        
        if weapon_timer["slash"] >= weapon_cooldown["slash"]:
            if weapon_dict["slash"] == 1:
                weapons.add(SlashWeapon(bird))
            weapon_timer["slash"] = 0

        if weapon_timer["boomerang"] >= weapon_cooldown["boomerang"]:
            if weapon_dict["boomerang"] == 1:
                weapons.add(BoomerangWeapon(bird))
            weapon_timer["boomerang"] = 0

        # 課題4main
        if event.type == pg.KEYDOWN and key_lst[pg.K_RSHIFT] == True and score.value >= 100:
            bird.state = "hyper"
            bird.hyper_life = 500
            score.value -= 100
        screen.blit(bg_img, [0, 0])


        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))
        
        if weapon_dict["weapon_mode"] == 0:
            """weaponmodeがnormal(ノーマル)のときの衝突処理"""
            for emy in pg.sprite.groupcollide(emys, weapons, True, True).keys():
                exps.add(Explosion(emy, 100))  # 爆発エフェクト
                score.value += 10  # 10点アップ
                bird.change_img(6, screen)  # こうかとん喜びエフェクト
            for bomb in pg.sprite.groupcollide(bombs, weapons, True, True).keys():
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ
        
        elif weapon_dict["weapon_mode"] == 1:
            """weaponmodeがpanet(貫通モード)のときの衝突処理"""
            for emy in pg.sprite.groupcollide(emys, weapons, True, False).keys():
                exps.add(Explosion(emy, 100))  # 爆発エフェクト
                score.value += 10  # 10点アップ
                bird.change_img(6, screen)  # こうかとん喜びエフェクト
            for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ
        
        if weapon_dict["satellite"] == 1:
            for emy in pg.sprite.groupcollide(emys, weapons, True, False).keys():
                exps.add(Explosion(emy, 100))
                score.value += 10
                bird.change_img(6, screen)
            for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                exps.add(Explosion(bomb, 50))
                score.value += 1

        if weapon_dict["slash"] == 1:
            for emy in pg.sprite.groupcollide(emys, weapons, True, False).keys():
                exps.add(Explosion(emy, 100))
                score.value += 10
                bird.change_img(6, screen)
            for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                exps.add(Explosion(bomb, 50))
                score.value += 1

        if weapon_dict["boomerang"] == 1:
            for emy in pg.sprite.groupcollide(emys, weapons, True, False).keys():
                exps.add(Explosion(emy, 100))
                score.value += 10
                bird.change_img(6, screen)
            for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                exps.add(Explosion(bomb, 50))
                score.value += 1

        for bomb in pg.sprite.groupcollide(bombs, shields, True, True).keys():
            exps.add(Explosion(bomb, 50))

        for emy in pg.sprite.groupcollide(emys, gvys, True, False).keys():
            gvys.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10

        for bomb in pg.sprite.groupcollide(bombs, gvys, True, False).keys():
            gvys.add(Explosion(bomb, 50))
            score.value += 1

        if bird.state == "hyper":
            for bomb in pg.sprite.spritecollide(bird, bombs, True):
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ
        
        else:
            if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
        

        bird.update(key_lst, screen)
        # beams.update()
        # beams.draw(screen)
        weapons.update()
        weapons.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        gvys.update()
        gvys.draw(screen)
        shields.draw(screen)
        shields.update()
        weapons.update()
        pg.display.update()
        tmr += 1
        clock.tick(50)
        


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()