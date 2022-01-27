import time
import pyupbit
import datetime 
import numpy as np
import requests



access = "SCpgbjxlvohuJFt7PxSHx90ocu0hINTS2r22Dof0"          # 본인 값으로 변경
secret = "6QIwRHY5quwMHYWUyzBMYO6pL4dOVf1FQcxRpIlc"          # 본인 값으로 변경
mytoken = "xoxb-2983705535250-2978509260982-gwodX99e2QQQGfVEOnfenuac"
crypto = "KRW-BTC"


def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def print_message(msg):
    """메시지 출력및 슬랙메시지 전송"""
    strbuf = datetime.datetime.now().strftime('[%m/%d %H:%M:%S] ') + msg
    print(strbuf)
    post_message(mytoken, "#crypto", strbuf)



def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15


def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


def get_ror(k=0.5):
    df = pyupbit.get_ohlcv(crypto, count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.0032
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror

def get_bestk():
    max_k = 0
    max_ror = 0
    for k in np.arange(0.1, 1.0, 0.1):
        ror = get_ror(k)

        if max_ror < ror:
            max_ror = ror
            max_k = k

    return max_k

k = get_bestk()


# 로그인
upbit = pyupbit.Upbit(access, secret)
print_message("autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(crypto)
        end_time = start_time + datetime.timedelta(days=1)

        # 9:00 < 현재 < 8:59:50 목표가 
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price(crypto, k)
            ma15 = get_ma15(crypto)
            current_price = get_current_price(crypto)
            if target_price < current_price and ma15 < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    buy_result = upbit.buy_market_order(crypto, krw*0.9995)
                    print_message(str(buy_result))
        else:
            btc = get_balance(crypto)
            if btc > 0.00008:
                sell_result = upbit.sell_market_order(crypto, btc*0.9995)
                print_message(str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        print_message(e)
        time.sleep(1)
