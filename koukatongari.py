import math
import os
import random
import sys
import time
import pygame as pg



WIDTH = 480  # ゲームウィンドウの幅
HEIGHT = 720  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))

#global変数の追加
gameround = 0


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：飛行機や爆弾，ビームなどのRect
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
    引数2 dst：飛行機SurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（飛行機）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        飛行機画像Surfaceを生成する
        引数1 num：飛行機画像ファイル名の番号
        引数2 xy：飛行機画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/hikoki.png"), 0, 0.15)
        img = pg.transform.flip(img0, True, False)  # デフォルトの飛行機
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
        self.hp = 5
        self.dire = (0, -1)
        self.image = img0
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"
        self.is_invincible = False
        
    def blink(self, screen):
        """
        飛行機が攻撃を受けた時に一瞬だけ戦败时の图片に変え、その後元の画像に戻る
        """
        self.is_invincible = True
        original_image = self.image
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/8.png"), 0, 2.0)  # 戦败时的图片
        screen.blit(self.image, self.rect)
        pg.display.update()
        time.sleep(0.1)
        self.image = original_image
        self.is_invincible = False


    def change_img(self, num: int, screen: pg.Surface):
        """
        飛行機画像を切り替え，画面に転送する
        引数1 num：飛行機画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じて飛行機を移動させる
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
        self.image = self.imgs[self.dire]
        
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    bossbeam_image=pg.transform.rotozoom(pg.image.load(f"fig/beam2.png"), 0, 0.03)  # ボスの攻撃の弾画像読み込み
    bossscull_image = pg.transform.rotozoom(pg.image.load(f"fig/bone.png"), 0, 0.03)  # ボスの攻撃の弾の画像読み込み

    def __init__(self, emy: "Enemy", bird: Bird, mode=0):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象の飛行機
        """
        super().__init__()
        self.mode = mode
        if self.mode==2:
            self.hit = "nohit"  # ボムとビームの当たり判定なし
            self.image=__class__.bossscull_image  
        else:
            self.hit = "hit"
            if self.mode == 0:
                rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
            
                self.image = pg.Surface((2*rad, 2*rad))
                color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
                pg.draw.circle(self.image, color, (rad, rad), rad)
                self.image.set_colorkey((0, 0, 0))
            else:
                self.image = __class__.bossbeam_image
            
        vlst = [(0, 1), (1, 1), (1, 0), (-1, 0), (-1, 1)]
        
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        if self.mode == 3:
            self.vx, self.vy =  random.choice(vlst)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        if gameround == 0:  #爆弾の速度をroundごとに早くする
            self.speed = 6
        elif gameround == 1:
            self.speed = 9
        elif gameround == 2:
            self.speed = 12
        elif gameround == 3:
            self.speed = 18
        else:
            self.speed = 10
        self.state = "active"
        self.count = 0
        
        

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if self.mode != 0:
            if self.rect.left < 0:
                self.vx *= -1
                self.rect.left = 0
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH
                self.vx *= -1
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        self.count += 1
        if check_bound(self.rect) != (True, True) and check_bound(self.rect) != (False, True) or self.count >= 300:
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つ飛行機
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
        if gameround == 0:
            self.vx, self.vy = 0, +6
            self.bound = random.randint(50, HEIGHT//2)  # 停止位置
            self.state = "down"  # 降下状態or停止状態
            self.interval = random.randint(50, 300)
        elif gameround == 1:
            self.vx, self.vy = 0, +12
            self.bound = random.randint(50, HEIGHT//2)  # 停止位置
            self.state = "down"  # 降下状態or停止状態
            self.interval = random.randint(50, 250)
        elif gameround == 2:
            self.vx, self.vy = 0, +18
            self.bound = random.randint(50, HEIGHT//2)  # 停止位置
            self.state = "down"  # 降下状態or停止状態
            self.interval = random.randint(50, 200)
        else:
            self.vx, self.vy = 0, +24
            self.bound = random.randint(50, HEIGHT//2)  # 停止位置
            self.state = "down"  # 降下状態or停止状態
            self.interval = random.randint(50, 150)

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
        
        if gameround >= 2:
            self.vx += 1.5 if random.choice([True,False]) else -2
            self.rect.move_ip(self.vx, self.vy)
            if self.rect.left < 0:
                self.rect.left = 0
                self.vx = 1
            if self.rect.right > WIDTH :
                self.rect.right = WIDTH
                self.vx = 1
            if self.rect.centery > self.bound:
                self.vy = 0
                self.state = "stop"


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


# 各ラウンドの背景と移動   
class Round:
    def __init__(self):
        self.current_round = 0 # 現在のラウンド番号
        self.backgrounds = [pg.image.load(f"fig/round{i}.jpg") for i in range(1, 6)]
        self.bg_pos = -HEIGHT # 背景画像の位置(画面外)
        self.transition_time = 120 # トランジションの時間
        self.is_transitioning = True
        self.required_scores = [0, 50, 70, 80, 100]  # 各ラウンドに必要なスコア

    def update(self, screen, score, items):
        if self.is_transitioning:
            if self.transition_time > 60:  # 最初の1秒間は黒画面にテキスト表示
                self.transition_time -= 1
                screen.fill((0, 0, 0)) # 画面を黒で塗りつぶす
                font = pg.font.Font(None, 64)
                if self.current_round == 4: # 最終ラウンド
                    text = font.render("Final Round", True, (255, 255, 255))
                else: # 1～4ラウンド
                    text = font.render(f"Round{self.current_round + 1}", True, (255, 255, 255))
                text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
                screen.blit(text, text_rect)
            elif self.transition_time > 0:  # 次の1秒間で背景をスライドイン
                self.transition_time -= 1
                self.bg_pos += HEIGHT / 60  # 1秒(60フレーム)かけて画面を下に移動
                screen.blit(self.backgrounds[self.current_round], (0, self.bg_pos))
            else:
                self.is_transitioning = False
                self.bg_pos = 0
        else:
            screen.blit(self.backgrounds[self.current_round], (0, 0))

        # スコアに基づいてラウンドを更新
        if self.current_round < 4 and score.value >= self.required_scores[self.current_round + 1]:
            self.next_round(items)

    def next_round(self, items):
        global gameround
        if self.current_round < 4:
            if self.current_round == 0:
                items.add(GetItem("fig/boomerang.png", downsize=100, angle=0, xy=(WIDTH/4, 100), item_name="boomerang"))
                items.add(GetItem("fig/slash_effect.png", downsize=100, angle=0, xy=(WIDTH-WIDTH/4, 100), item_name="slash"))
            elif self.current_round == 1:
                items.add(GetItem("fig/satellite_shield.png", downsize=100, angle=0, xy=(WIDTH/2, 100), item_name="satellite"))
            elif self.current_round == 2:
                 items.add(GetItem("fig/shootingsatellite.png", downsize=100, angle=0, xy=(WIDTH-WIDTH/4, 100), item_name="satellite"))
                 items.add(GetItem("fig/penet_bullet.png", downsize=100, angle=90, xy=(WIDTH/4, 100), item_name="weapon_mode"))
            elif self.current_round == 3:
                items.add(GetItem("fig/weapon_up.png", downsize=100, angle=0, xy=(WIDTH/2, 100), item_name="rate_up"))
            gameround += 1
            self.current_round += 1
            self.is_transitioning = True
            self.transition_time = 120  # 2秒間のトランジション（1秒テキスト表示 + 1秒背景スライド）
            self.bg_pos = -HEIGHT  # 背景位置をリセット
        
 
def show_title_screen(screen):
    """
    タイトル画面を表示する関数
    引数 screen：画面Surface
    """
    font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 50)
    title = font.render("鳥の悪魔討伐", True, (255, 255, 255))
    instruction = font.render("Press S to Start", True, (255, 255, 255))
    
    screen.fill((0, 0, 0))  # 画面を黒で塗りつぶす
    title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
    instruction_rect = instruction.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
    screen.blit(title, title_rect)
    screen.blit(instruction, instruction_rect)
    pg.display.update()



 #ボスクラス
class Boss(pg.sprite.Sprite):
    img = pg.transform.rotozoom(pg.image.load(f"fig/bosstoka.png"), 0, 2.0)
    img2 = pg.transform.rotozoom(pg.image.load(f"fig/boss2.png"), 0, 2.0)

    def __init__(self, hp: int):
        super().__init__()
        self.image = __class__.img
        self.rect = self.image.get_rect() 
        self.rect.center = WIDTH//2, 0
        self.vx, self.vy = 0, +6
        self.bound = 100  # 停止位置
        self.state = "down"  # 降下状態or停止状態 
        self.interval = 30  # 爆弾投下初期インターバル
        self.interval2 = 50  # ビーム当てても消えない爆弾投下インターバル
        self.hp = hp  # ボスのHPを5に設定
        self.boss_mode = "yowayowa"   
        
    def update(self, hp: int):
        # ボスの動き（例えば左右に移動）
        self.vx += 5 if random.choice([True, False]) else -5
        self.rect.move_ip(self.vx, self.vy)
        # 画面の端を超えないように
        if self.boss_mode == "yowayowa":  # ボスの第一段階動き範囲指定
            if self.rect.left < 0:
                self.rect.left = 0
                self.vx = 10
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH
                self.vx = -10
            if self.rect.centery > self.bound:
                self.vy = 0
                self.state = "stop"
        else:  # ボスの第二、三段階動き範囲指定、速度指定兼制限
            self.vy += 5 if random.choice([True, False]) else -5  # 速度をランダムで増減させる
            # 画面外出ないようにする
            if self.rect.left < 0:
                self.vx = 10
                self.rect.left = 0
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH
                self.vx = -10
            if self.rect.top < 0:
                self.rect.top = 0
                self.vy = 10
            if self.rect.bottom> HEIGHT//4:
                self.rect.bottom = HEIGHT//4
                self.vy = -10
            # 速度制限
            if self.vx > 30:
                self.vx = 30
            if self.vx < -30:
                self.vx = -30
            if self.vy > 30:
                self.vy = 30
            if self.vy < -30:
                self.vy = -30
        
        if self.hp <= hp//2:
            if self.hp <= hp//4:
                self.boss_mode = "tuyotuyotuyo"  # ボスの行動パターン変える
                self.interval = 1
                self.image = __class__.img2  # ボスの画像を変える
            else:
                self.boss_mode = "tuyotuyo"  # ボスの行動パターンを変える
                self.interval = 15
            
        if self.hp <= 0:  # ボスHPなくなったらキル
            self.kill()

class Weapon(pg.sprite.Sprite): 
    """
    武器の親クラス
    """
    def __init__(self, bird: Bird, speed:int = 10):
        super().__init__()
        self.bird = bird
        self.speed = speed
        self.damage = 1
        self.life = 1000

    def update(self):
        self.life -= 1
        if check_bound(self.rect) != (True, True):
            self.kill()

class NormalWeapon(Weapon):
    """
    通常弾に関するクラス
    """
    img = pg.image.load(f"fig/beam.png")
    small_image = pg.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
    image = pg.transform.rotozoom(small_image, 90, 1)
    def __init__(self, bird: Bird, beam_x: int = 0, speed: int = 10):
        """
        武器画像Surfaceを生成する
        引数1 bird：武器を発射する飛行機
        引数2 ビームのX位置のオフセット
        引数3 ビームのスピード
        """
        super().__init__(bird, speed)
        self.rect = __class__.image.get_rect()
        self.rect.centerx = bird.rect.centerx + beam_x
        self.rect.bottom = bird.rect.top
        self.vx = 0
        self.vy = -self.speed  # デフォルトで上方向に移動

    def update(self):
        self.rect.move_ip(0, -self.speed)  # 常に上方向に移動
        super().update()

class PenetWeapon(NormalWeapon):
    """
    敵と衝突しても消えない弾に関するクラス
    """
    def __init__(self, bird: Bird, beam_x: int = 0, speed: int = 10):
        """
        武器画像Surfaceを生成する
        引数1 bird：武器を発射する飛行機
        引数2 ビームのX位置のオフセット
        引数3 ビームのスピード
        """
        super().__init__(bird, beam_x, speed)
        self.image = pg.transform.laplacian(self.image)  # 区別をつける
  
    def update(self):
        """
        武器を上方向に移動させる
        """
        super().update()

class SatelliteWeapon(Weapon):
    """
    飛行機の周りを周回する衛星に関するクラス
    """
    img = pg.image.load(f"fig/satellite_shield.png")
    image = pg.transform.rotozoom(img, 0, 0.05)
    def __init__(self, bird: Bird, radius: int = 200, angle : int = 0, angular_speed: float = 0.05):
        """
        武器画像Surfaceを生成する
        引数1 bird：武器を発射する飛行機
        引数2 周回する半径
        引数3 周回する初期角度
        引数4 周回速度
        """
        super().__init__(bird)
        self.radius = radius
        self.angle = math.radians(angle)       
        self.angular_speed = angular_speed
        self.rect = __class__.image.get_rect()

    def update(self):
        """
        武器を周回させる
        """
        x = self.bird.rect.centerx + math.cos(self.angle) * self.radius
        y = self.bird.rect.centery + math.sin(self.angle) * self.radius
        self.rect.center = (x, y)
        self.angle += self.angular_speed
        if self.angle > 2 * math.pi:
            self.angle -= 2 * math.pi # 角度を0~360度の範囲に収める

class ShootingSatelliteWeapon(SatelliteWeapon):
    bullets = pg.sprite.Group()
    img = pg.image.load(f"fig/shootingsatellite.png")
    image = pg.transform.rotozoom(img, 0, 0.5)
    def __init__(self, bird: Bird, radius: int = 200, angle: int = 0, angular_speed: float = 0.05, shoot_cooldown: int = 50):
        super().__init__(bird, radius, angle, angular_speed)
        self.shoot_cooldown = shoot_cooldown  # 発射間隔（フレーム数）
        self.shoot_timer = 0

    def update(self):
        """
        武器を周回させると弾の発射
        """
        # 衛星の位置を更新
        super().update()

        # 弾の発射と管理
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cooldown:
            self.shoot_timer = 0
            # 新しい弾を生成
            bullet = NormalWeapon(self.bird, 0, 1)
            bullet.rect.center = self.rect.center
            ShootingSatelliteWeapon.bullets.add(bullet)
        # 弾の更新
        self.bullets.update()


class SlashWeapon(Weapon):
    """
    斬撃に関するクラス
    """
    img = pg.image.load(f"fig/slash_effect.png")
    image = pg.transform.flip(img, True, False)
    def __init__(self, bird: Bird, hp: int = 10):
        """
        武器画像Surfaceを生成する
        引数1 bird：武器を発射する飛行機
        引数2 斬撃の残留時間
        """
        super().__init__(bird)
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.image = pg.transform.rotozoom(__class__.image, angle, 0.1)
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.hp = hp
    
    def update(self):
        """
        斬撃の残留管理
        """
        self.hp -= 1
        if self.hp <= 0:
            self.kill()

class BoomerangWeapon(Weapon):
    """
    ブーメランに関するクラス
    """
    img = pg.image.load(f"fig/boomerang.png")
    original_image = pg.transform.rotozoom(img, 0, 0.05)
    def __init__(self, bird: Bird, speed: int = 5, max_distance: int = 300, rotation_speed: int = 10):
        """
        武器画像Surfaceを生成する
        引数1 bird：武器を発射する飛行機
        引数2 ブーメランのスピード
        引数3 ブーメランの最大距離
        引数4 ブーメランの回転速度
        """
        super().__init__(bird, speed)
        self.image = __class__.original_image
        self.rect = self.image.get_rect()
        self.rect.center = bird.rect.center
        self.max_distance = max_distance
        self.distance = 0
        self.returning = False
        self.angle = 0
        self.rotation_speed = rotation_speed

    def update(self):
        """
        ブーメランの移動
        """
        # ブーメランを回転させる
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pg.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        if not self.returning:
            # 前進するときの処理
            self.rect.move_ip(0, -self.speed)
            self.distance += self.speed
            if self.distance >= self.max_distance:
                self.returning = True
        else:
            # 戻るときの処理
            dx = self.bird.rect.centerx - self.rect.centerx
            dy = self.bird.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                dx, dy = dx / dist, dy / dist
                self.rect.move_ip(dx * self.speed, dy * self.speed)

            # 飛行機に当たったら消滅
            if self.rect.colliderect(self.bird.rect):
                self.kill()
    
class GetItem(pg.sprite.Sprite):
    """
    アイテムに関するクラス
    """
    def __init__(self, img_name: str, downsize: int, angle: int, xy: tuple, item_name: str):
        """
        アイテム画像Surfaceを生成する
        引数1 アイテムの画像の保存場所と名前
        引数2 アイテムの縮小具合
        引数3 アイテムの角度
        引数4 アイテムの生成位置
        引数5 アイテムの名前
        """
        super().__init__()
        img = pg.image.load(img_name)
        small_image = self.scale_image(img, downsize)
        self.small_image = pg.transform.rotozoom(small_image, angle, 1)
        self.rect = self.small_image.get_rect()
        self.rect.center = xy
        self.item_name = item_name

    def scale_image(self, image: pg.Surface, size: int):
        """
        アスペクト比を保ちながら画像を指定サイズの正方形内に収める
        """
        width, height = image.get_size()
        aspect_ratio = width / height
        
        if aspect_ratio > 1:  # 横長の画像
            new_width = size
            new_height = int(size / aspect_ratio)
        else:  # 縦長または正方形の画像
            new_height = size
            new_width = int(size * aspect_ratio)
        
        scaled_image = pg.transform.smoothscale(image, (new_width, new_height))
        
        # 正方形の背景を作成
        square_surface = pg.Surface((size, size), pg.SRCALPHA)
        
        # 縮小した画像を正方形の中央に配置
        x = (size - new_width) // 2
        y = (size - new_height) // 2
        square_surface.blit(scaled_image, (x, y))
        
        return square_surface
    def update(self, screen: pg.Surface):
        """
        画像の描画
        """
        screen.blit(self.small_image, self.rect)
        


def main():
    bosshp = 100
    pg.display.set_caption("真！飛行機無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (WIDTH//2, HEIGHT-100))
    bombs = pg.sprite.Group()
    bombs2 = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()
    gvys = pg.sprite.Group()

    round_manager = Round()
    weapons = pg.sprite.Group()
    items = pg.sprite.Group()    
    bosses = pg.sprite.Group()
    

    tmr = 0
    num_barriers = 3
    angle = 360 / num_barriers
    weapon_cooldown ={"bullet":14, "satellite":70, "slash":20, "boomerang":20}
    weapon_timer = {"bullet":14, "satellite":70, "slash":20, "boomerang":20}
    weapon_dict = {"weapon_mode":0, "satellite":0, "slash":0, "boomerang":0}
    clock = pg.time.Clock()

    show_title_screen(screen)
    title_screen = True
    while title_screen:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                title_screen = False

    count = 0
    boss_count = 0
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))

            if not bird.is_invincible and pg.sprite.spritecollide(bird, bombs, True):
                bird.hp -= 1
                # bird.blink(screen)  # 飛行機が攻撃を受けたらフラッシュする
                if bird.hp <= 0:
                    bird.change_img(8, screen)  # 飛行機悲しみエフェクト
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return
        """武器の発射処理"""
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
        # 弾丸
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
            elif weapon_dict["satellite"] == 2:
                # 既存のSatelliteWeaponの数をカウント
                current_satellite_count = sum(isinstance(weapon, ShootingSatelliteWeapon) for weapon in weapons)
                # 既存のSatelliteWeaponの数がバリア数より少なくなっていたら再生成
                if current_satellite_count < num_barriers:
                    for weapon in list(weapons):
                        if isinstance(weapon, ShootingSatelliteWeapon):
                            weapons.remove(weapon)
                    for i in range(num_barriers):
                        ten = angle * i
                        weapons.add(ShootingSatelliteWeapon(bird, 75, ten))
            weapon_timer["satellite"] = 0
        # 衛星弾
        if weapon_timer["slash"] >= weapon_cooldown["slash"]:
            if weapon_dict["slash"] == 1:
                weapons.add(SlashWeapon(bird))
            weapon_timer["slash"] = 0
        # 斬撃
        if weapon_timer["boomerang"] >= weapon_cooldown["boomerang"]:
            if weapon_dict["boomerang"] == 1:
                weapons.add(BoomerangWeapon(bird))
            weapon_timer["boomerang"] = 0
        # ブーメラン            
        

        screen.blit(bg_img, [0, 0])

        if round_manager.is_transitioning:
            screen.fill((0, 0, 0))  # 黒い背景を描画
        else:
            screen.blit(bg_img, [0, 0])  # 通常の背景を描画
        round_manager.update(screen, score, items)

        if not round_manager.is_transitioning:
            if len(items) == 0:
                if gameround == 0:
                    if tmr%250 == 0:  # 200フレーム，敵機を出現させる
                        for _ in range(1):
                            emys.add(Enemy())
                elif gameround == 1:
                    if tmr%200 == 0:  # 200フレーム，敵機を出現させる
                        for _ in range(2):  # 敵機の数
                            emys.add(Enemy())
                elif gameround == 2:
                    if tmr%170 == 0:  # 200フレーム，敵機を出現させる
                        for _ in range(4):  # 敵機の数
                            emys.add(Enemy())
                elif gameround == 3:
                    if tmr%80 == 0:  # 200フレーム，敵機を出現させる
                        for _ in range(5):  # 敵機の数
                            emys.add(Enemy())
                elif gameround == 4:
                    if boss_count == 0:
                        bosses.add(Boss(bosshp))
                        boss_count += 1
                for emy in emys:
                    if tmr%emy.interval == 0:
                        # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                        bombs.add(Bomb(emy, bird))

                for boss in bosses:
                    if tmr%boss.interval == 0:
                    # intervalに応じて爆弾投下
                        if boss.boss_mode == "yowayowa" or boss.boss_mode =="tuyotuyo":
                            bombs.add(Bomb(boss, bird, 1))  # 自分に向けてボム投下
                        else:
                            bombs.add(Bomb(boss, bird, 3))  # ランダム5パターンのうち1つの方向にボムを投下
                    if boss.boss_mode=="tuyotuyo" or boss.boss_mode == "tuyotuyotuyo":
                        if tmr%boss.interval2 == 0:
                            bombs2.add(Bomb(boss, bird, 2))  # 消えないボム投下

            """武器の衝突処理"""
            if weapon_dict["weapon_mode"] == 0:
                """weaponmodeがnormal(ノーマル)のときの衝突処理"""
                
                for emy in pg.sprite.groupcollide(emys, weapons, True, True).keys():
                            exps.add(Explosion(emy, 100))  # 爆発エフェクト
                            score.value += 10  # 10点アップ
                            bird.change_img(6, screen)  # 飛行機喜びエフェクト
                for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                    exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                    score.value += 1  # 1点アップ
                for boss in pg.sprite.groupcollide(bosses, weapons, False, True).keys():
                    boss.hp -= 1  # ボスに攻撃が当たったらボスのHPを1減らす
                for bomb in pg.sprite.groupcollide(bombs2, weapons, False, True).keys():  # 消せないボムとビームがぶつかったらビームのみを消す
                    pass
            
            elif weapon_dict["weapon_mode"] == 1:
                """weaponmodeがpanet(貫通モード)のときの衝突処理"""
                for emy in pg.sprite.groupcollide(emys, weapons, True, False).keys():
                    exps.add(Explosion(emy, 100))  # 爆発エフェクト
                    score.value += 10  # 10点アップ
                    bird.change_img(6, screen)  # 飛行機喜びエフェクト
                for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                    exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                    score.value += 1  # 1点アップ
                for boss in pg.sprite.groupcollide(bosses, weapons, False, True).keys():
                    boss.hp -= 1  # ボスに攻撃が当たったらボスのHPを1減らす
                for bomb in pg.sprite.groupcollide(bombs2, weapons, False, True).keys():  # 消せないボムとビームがぶつかったらビームのみを消す
                    pass

            if weapon_dict["satellite"] == 1:
                for emy in pg.sprite.groupcollide(emys, weapons, True, False).keys():
                    exps.add(Explosion(emy, 100))
                    score.value += 10
                    bird.change_img(6, screen)
                for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                    exps.add(Explosion(bomb, 50))
                    score.value += 1
                for boss in pg.sprite.groupcollide(bosses, weapons, False, False).keys():
                    boss.hp -= 1  # ボスに攻撃が当たったらボスのHPを1減らす
                for bomb in pg.sprite.groupcollide(bombs2, weapons, True, True).keys():  # 消せないボムとビームがぶつかったらビームのみを消す
                    pass

            elif weapon_dict["satellite"] == 2:
                for emy in pg.sprite.groupcollide(emys, weapons, True, True).keys():
                    exps.add(Explosion(emy, 100))
                    score.value += 10
                    bird.change_img(6, screen)
                for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                    exps.add(Explosion(bomb, 50))
                    score.value += 1
                for emy in pg.sprite.groupcollide(emys, ShootingSatelliteWeapon.bullets, True, True).keys():
                    exps.add(Explosion(emy, 100))
                    score.value += 10
                    bird.change_img(6, screen)
                for bomb in pg.sprite.groupcollide(bombs, ShootingSatelliteWeapon.bullets, True, True).keys():
                    exps.add(Explosion(bomb, 50))
                    score.value += 1
                for boss in pg.sprite.groupcollide(bosses, weapons, False, False).keys():
                    boss.hp -= 1  # ボスに攻撃が当たったらボスのHPを1減らす
                for boss in pg.sprite.groupcollide(bosses, ShootingSatelliteWeapon.bullets, False, True).keys():
                    boss.hp -= 1  # ボスに攻撃が当たったらボスのHPを1減らす
                for bomb in pg.sprite.groupcollide(bombs2, weapons, False, True).keys():  # 消せないボムとビームがぶつかったらビームのみを消す
                    pass
                for bomb in pg.sprite.groupcollide(bombs2, ShootingSatelliteWeapon.bullets, False, True).keys():  # 消せないボムとビームがぶつかったらビームのみを消す
                    pass

            if weapon_dict["slash"] == 1:
                for emy in pg.sprite.groupcollide(emys, weapons, True, False).keys():
                    exps.add(Explosion(emy, 100))
                    score.value += 10
                    bird.change_img(6, screen)
                for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                    exps.add(Explosion(bomb, 50))
                    score.value += 1
                for boss in pg.sprite.groupcollide(bosses, weapons, False, False).keys():
                    boss.hp -= 1  # ボスに攻撃が当たったらボスのHPを1減らす
                # for bomb in pg.sprite.groupcollide(bombs2, weapons, False, False).keys():  # 消せないボムとビームがぶつかったらビームのみを消す
                #     pass

            if weapon_dict["boomerang"] == 1:
                for emy in pg.sprite.groupcollide(emys, weapons, True, False).keys():
                    exps.add(Explosion(emy, 100))
                    score.value += 10
                    bird.change_img(6, screen)
                for bomb in pg.sprite.groupcollide(bombs, weapons, True, False).keys():
                    exps.add(Explosion(bomb, 50))
                    score.value += 1
                for boss in pg.sprite.groupcollide(bosses, weapons, False, False).keys():
                    boss.hp -= 1  # ボスに攻撃が当たったらボスのHPを1減らす
                for bomb in pg.sprite.groupcollide(bombs2, weapons, False, True).keys():  # 消せないボムとビームがぶつかったらビームのみを消す
                    pass
                """追加武器の衝突処理終了"""
                for bomb in pg.sprite.groupcollide(bombs, shields, True, True).keys():
                    exps.add(Explosion(bomb, 50))

                for emy in pg.sprite.groupcollide(emys, gvys, True, False).keys():
                    gvys.add(Explosion(emy, 100))  # 爆発エフェクト
                    score.value += 10

                for bomb in pg.sprite.groupcollide(bombs, gvys, True, False).keys():
                    gvys.add(Explosion(bomb, 50))
                    score.value += 1

                if len(pg.sprite.spritecollide(bird, bombs, True)) != 0 or len(pg.sprite.spritecollide(bird, bombs2, True)) != 0 or len(pg.sprite.spritecollide(bird, bosses, True)) != 0:
                    bird.hp -= 1
                    if bird.hp <= 0:
                        font = pg.font.Font(None, 50)
                        img = font.render(f"GAME OVER", 0, (0, 0, 0))
                        rect = img.get_rect()
                        rect.center = WIDTH//2, HEIGHT//2
                        screen.blit(img, rect)
                        pg.display.update()
                        time.sleep(2)
                        return


            if bosses.sprites() == [] and boss_count == 1:  # boss召喚後にbossが存在しない時
                img2 = pg.transform.rotozoom(pg.image.load(f"fig/explosion.png"), 0, 5.0)
                rect2 = img2.get_rect()
                rect2.center = WIDTH//2, HEIGHT//2
                screen.blit(img2, rect2)
                font = pg.font.Font(None, 50)
                color = (0, 0, 0)
                img = font.render(f"GAME CLEAR", 0, color)
                rect = img.get_rect()
                rect.center = WIDTH//2, HEIGHT//2
                screen.blit(img, rect)
                
                pg.display.update()
                time.sleep(5)
                return
            for item in pg.sprite.spritecollide(bird, items, True): #アイテムの取得処理
                if item.item_name == "rate_up":
                        weapon_cooldown["bullet"] = 7
                        weapon_timer["bullet"] = 7
                else:
                    weapon_dict[item.item_name] += 1
                items.empty()
        else:
            emys.empty()
            bombs.empty()
        items.update(screen)
        exps.update()
        exps.draw(screen)
        bird.update(key_lst, screen)
        # beams.update()
        # beams.draw(screen)
        weapons.update()
        weapons.draw(screen)
        weapons.update()
        for weapon in weapons:
            if isinstance(weapon, ShootingSatelliteWeapon):
                weapon.bullets.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        bombs2.update()
        bombs2.draw(screen)
        score.update(screen)
        gvys.update()
        gvys.draw(screen)
        shields.draw(screen)
        shields.update()
        weapons.update()
        bosses.draw(screen)
        bosses.update(bosshp)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()