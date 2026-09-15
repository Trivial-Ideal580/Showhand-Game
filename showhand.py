import random
from collections import Counter
from itertools import combinations

# -------------------- 牌型定义 --------------------
RANK_MAP = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}
RANK_DISPLAY = {v: k for k, v in RANK_MAP.items()}
SUITS = ['♠', '♥', '♦', '♣']

HAND_RANKS = {
    '皇家同花顺': 10,
    '同花顺': 9,
    '四条': 8,
    '葫芦': 7,
    '同花': 6,
    '顺子': 5,
    '三条': 4,
    '两对': 3,
    '一对': 2,
    '高牌': 1
}

# -------------------- 牌与牌堆 --------------------
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{RANK_DISPLAY[self.rank]}{self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        for suit in SUITS:
            for rank in range(2, 15):
                self.cards.append(Card(rank, suit))
        random.shuffle(self.cards)

    def deal(self, n=1):
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt if n > 1 else dealt[0]

# -------------------- 牌型评估 --------------------
def evaluate_5cards(cards):
    """评估5张牌的牌型，返回 (名称, 等级, 关键值列表)"""
    ranks = sorted([c.rank for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    rank_counts = Counter(ranks)
    count_items = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    counts = [item[1] for item in count_items]
    values = [item[0] for item in count_items]

    is_flush = len(set(suits)) == 1
    is_straight = False
    straight_high = None
    if len(rank_counts) == 5:
        if ranks[0] - ranks[4] == 4:
            is_straight = True
            straight_high = ranks[0]
        elif ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5

    if is_flush and is_straight and straight_high == 14:
        return ('皇家同花顺', HAND_RANKS['皇家同花顺'], [14])
    if is_flush and is_straight:
        return ('同花顺', HAND_RANKS['同花顺'], [straight_high])
    if counts == [4, 1]:
        return ('四条', HAND_RANKS['四条'], [values[0], values[1]])
    if counts == [3, 2]:
        return ('葫芦', HAND_RANKS['葫芦'], [values[0], values[1]])
    if is_flush:
        return ('同花', HAND_RANKS['同花'], ranks)
    if is_straight:
        return ('顺子', HAND_RANKS['顺子'], [straight_high])
    if counts == [3, 1, 1]:
        return ('三条', HAND_RANKS['三条'], [values[0], values[1], values[2]])
    if counts == [2, 2, 1]:
        return ('两对', HAND_RANKS['两对'], [values[0], values[1], values[2]])
    if counts == [2, 1, 1, 1]:
        return ('一对', HAND_RANKS['一对'], [values[0], values[1], values[2], values[3]])
    return ('高牌', HAND_RANKS['高牌'], ranks)

def evaluate_5cards_from_5(cards):
    """直接评估5张牌（正好5张）"""
    return evaluate_5cards(cards)

def compare_hands(hand1, hand2):
    """比较两手5张牌，返回 1: hand1赢, -1: hand2赢, 0: 平局"""
    name1, rank1, key1 = evaluate_5cards(hand1)
    name2, rank2, key2 = evaluate_5cards(hand2)
    if rank1 != rank2:
        return 1 if rank1 > rank2 else -1
    for k1, k2 in zip(key1, key2):
        if k1 != k2:
            return 1 if k1 > k2 else -1
    return 0

# -------------------- 游戏逻辑 --------------------
class StudGame:
    def __init__(self):
        self.player_chips = 500
        self.computer_chips = 500
        self.pot = 0
        self.round_num = 0

    def new_deck(self):
        self.deck = Deck()

    def display_cards(self, cards):
        return " ".join(str(c) for c in cards)

    def show_state(self):
        """显示当前游戏状态"""
        print("\n" + "-"*50)
        print(f"筹码: 你 {self.player_chips} | 电脑 {self.computer_chips} | 底池 {self.pot}")
        print(f"你的明牌: {self.display_cards(self.player_up)}")
        print(f"你的底牌: {self.display_cards(self.player_down)}")
        print(f"电脑明牌: {self.display_cards(self.computer_up)}")
        print(f"电脑底牌: ?? (未开)")
        print("-"*50)

    def get_player_bet(self, min_bet=0, max_bet=None):
        """获取玩家下注金额，支持弃牌"""
        if max_bet is None:
            max_bet = self.player_chips
        if min_bet > max_bet:
            min_bet = max_bet
        while True:
            try:
                prompt = f"请输入下注金额 (当前筹码 {self.player_chips}, 最少 {min_bet}, 最多 {max_bet})，或输入 'f' 弃牌: "
                user_input = input(prompt).strip().lower()
                if user_input == 'f':
                    return 'fold'
                amount = int(user_input)
                if amount < min_bet:
                    print(f"下注不能少于 {min_bet}。")
                elif amount > max_bet:
                    print(f"下注不能超过 {max_bet}。")
                elif amount > self.player_chips:
                    print("筹码不足。")
                else:
                    return amount
            except ValueError:
                print("请输入有效数字或 'f' 弃牌。")

    def computer_bet(self, min_bet, max_bet):
        """电脑简单AI下注，可能弃牌"""
        # 根据明牌强度简单决策
        strength = self.evaluate_up_strength(self.computer_up)
        # 如果明牌很弱且当前下注较大，有概率弃牌
        if strength <= 1 and min_bet > 50 and random.random() < 0.3:
            return 'fold'
        if strength >= 3:
            bet = min(max_bet, max(min_bet, int(self.computer_chips * 0.2)))
        elif strength >= 2:
            bet = min(max_bet, max(min_bet, int(self.computer_chips * 0.1)))
        else:
            bet = min(max_bet, min_bet)
        bet = min(bet, self.computer_chips)
        return bet

    def evaluate_up_strength(self, up_cards):
        """评估明牌强度（简单版，用于电脑决策）"""
        if len(up_cards) < 2:
            return 1
        ranks = [c.rank for c in up_cards]
        rank_counts = Counter(ranks)
        max_count = max(rank_counts.values())
        if max_count >= 3:
            return 4
        elif max_count == 2:
            return 3
        elif len(set(c.suit for c in up_cards)) == len(up_cards):
            return 2
        return 1

    def get_up_card_value(self, cards):
        """获取明牌中最大的牌值，用于决定下注顺序"""
        if not cards:
            return 0
        return max(c.rank for c in cards)

    def play_round(self):
        """进行一局游戏"""
        if self.player_chips <= 0 or self.computer_chips <= 0:
            print("筹码不足，游戏结束。")
            return False

        self.round_num += 1
        print(f"\n{'='*20} 第 {self.round_num} 局 {'='*20}")
        self.new_deck()
        self.pot = 0

        # 发前两张牌：一张明牌一张底牌
        self.player_up = [self.deck.deal()]
        self.player_down = [self.deck.deal()]
        self.computer_up = [self.deck.deal()]
        self.computer_down = [self.deck.deal()]

        print("发牌阶段：每人一张明牌一张底牌")
        self.show_state()

        # 决定谁先下注：明牌大的先下注
        player_up_val = self.player_up[0].rank
        computer_up_val = self.computer_up[0].rank
        if player_up_val >= computer_up_val:
            first = 'player'
            print(f"你的明牌 {self.player_up[0]} 大于等于电脑明牌 {self.computer_up[0]}，你先下注。")
        else:
            first = 'computer'
            print(f"电脑明牌 {self.computer_up[0]} 大于你的明牌 {self.player_up[0]}，电脑先下注。")

        # 第一轮下注
        print("\n--- 第一轮下注 ---")
        if first == 'player':
            bet = self.get_player_bet(min_bet=10)
            if bet == 'fold':
                print("你选择了弃牌，本局结束。")
                self.computer_chips += self.pot
                self.pot = 0
                return True
            self.player_chips -= bet
            self.pot += bet
            print(f"你下注 {bet}")
            comp_bet = self.computer_bet(min_bet=bet, max_bet=min(100, self.computer_chips))
            if comp_bet == 'fold':
                print("电脑选择了弃牌，你赢得底池！")
                self.player_chips += self.pot
                self.pot = 0
                return True
            comp_bet = min(self.computer_chips, bet)
            self.computer_chips -= comp_bet
            self.pot += comp_bet
            print(f"电脑跟注 {comp_bet}")
        else:
            comp_bet = self.computer_bet(min_bet=10, max_bet=min(100, self.computer_chips))
            if comp_bet == 'fold':
                print("电脑选择了弃牌，你赢得底池！")
                self.player_chips += self.pot
                self.pot = 0
                return True
            self.computer_chips -= comp_bet
            self.pot += comp_bet
            print(f"电脑下注 {comp_bet}")
            bet = self.get_player_bet(min_bet=comp_bet)
            if bet == 'fold':
                print("你选择了弃牌，本局结束。")
                self.computer_chips += self.pot
                self.pot = 0
                return True
            self.player_chips -= bet
            self.pot += bet
            print(f"你下注 {bet}")

        # 后续发牌和下注（每轮发一张明牌）
        for round_idx in range(2, 5):
            print(f"\n--- 第 {round_idx} 轮发牌 ---")
            # 发一张明牌给双方
            self.player_up.append(self.deck.deal())
            self.computer_up.append(self.deck.deal())
            self.show_state()

            # 决定谁先下注：新牌大的先下注
            player_new = self.player_up[-1].rank
            computer_new = self.computer_up[-1].rank
            if player_new >= computer_new:
                first = 'player'
                print(f"你的新明牌 {self.player_up[-1]} 大于等于电脑新明牌 {self.computer_up[-1]}，你先下注。")
            else:
                first = 'computer'
                print(f"电脑新明牌 {self.computer_up[-1]} 大于你的新明牌 {self.player_up[-1]}，电脑先下注。")

            # 下注
            if first == 'player':
                bet = self.get_player_bet(min_bet=10)
                if bet == 'fold':
                    print("你选择了弃牌，本局结束。")
                    self.computer_chips += self.pot
                    self.pot = 0
                    return True
                self.player_chips -= bet
                self.pot += bet
                print(f"你下注 {bet}")
                comp_bet = self.computer_bet(min_bet=bet, max_bet=min(200, self.computer_chips))
                if comp_bet == 'fold':
                    print("电脑选择了弃牌，你赢得底池！")
                    self.player_chips += self.pot
                    self.pot = 0
                    return True
                comp_bet = min(self.computer_chips, bet)
                self.computer_chips -= comp_bet
                self.pot += comp_bet
                print(f"电脑跟注 {comp_bet}")
            else:
                comp_bet = self.computer_bet(min_bet=10, max_bet=min(200, self.computer_chips))
                if comp_bet == 'fold':
                    print("电脑选择了弃牌，你赢得底池！")
                    self.player_chips += self.pot
                    self.pot = 0
                    return True
                self.computer_chips -= comp_bet
                self.pot += comp_bet
                print(f"电脑下注 {comp_bet}")
                bet = self.get_player_bet(min_bet=comp_bet)
                if bet == 'fold':
                    print("你选择了弃牌，本局结束。")
                    self.computer_chips += self.pot
                    self.pot = 0
                    return True
                self.player_chips -= bet
                self.pot += bet
                print(f"你下注 {bet}")

        # 开牌比大小
        print("\n" + "="*50)
        print("开牌阶段")
        all_player = self.player_up + self.player_down
        all_computer = self.computer_up + self.computer_down
        print(f"你的5张牌: {self.display_cards(all_player)}")
        print(f"电脑的5张牌: {self.display_cards(all_computer)}")

        p_name, p_rank, p_key = evaluate_5cards(all_player)
        c_name, c_rank, c_key = evaluate_5cards(all_computer)
        print(f"你的牌型: {p_name}")
        print(f"电脑牌型: {c_name}")

        result = compare_hands(all_player, all_computer)
        if result == 1:
            print("你赢了！")
            self.player_chips += self.pot
        elif result == -1:
            print("电脑赢了！")
            self.computer_chips += self.pot
        else:
            print("平局，筹码返还。")
            half = self.pot // 2
            self.player_chips += half
            self.computer_chips += self.pot - half
        self.pot = 0
        print(f"当前筹码: 你 {self.player_chips} | 电脑 {self.computer_chips}")
        return True

    def start(self):
        print("欢迎来到梭哈游戏！每人初始筹码500。")
        print("规则：开局发两张牌（一明一底），明牌大的先下注。")
        print("之后每轮发一张明牌，新牌大的先下注，共四张明牌，然后开牌比大小。")
        print("每人最终5张牌（4明+1底）。下注金额可自定义。")
        print("任何时候都可以输入 'f' 弃牌。\n")
        while self.player_chips > 0 and self.computer_chips > 0:
            if not self.play_round():
                break
            cont = input("按回车继续下一局，输入 q 退出: ").strip().lower()
            if cont == 'q':
                break
        print(f"\n游戏结束！最终筹码: 你 {self.player_chips} | 电脑 {self.computer_chips}")
        if self.player_chips > self.computer_chips:
            print("恭喜你成为最终赢家！")
        elif self.player_chips < self.computer_chips:
            print("电脑赢了，再接再厉！")
        else:
            print("平局！")

# -------------------- 启动游戏 --------------------
if __name__ == "__main__":
    game = StudGame()
    game.start()