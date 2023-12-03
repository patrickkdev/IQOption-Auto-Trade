import json
import time
import os

from iqoptionapi.stable_api import IQ_Option
import iqoptionapi.constants as OP_code

def clear_terminal():
    os.system("cls")
    
clear_terminal()

print("IQ Option Bot")

EMAIL: str = "alinneduarte04@gmail.com"     #input("Email: ")
PASSWORD: str = "Junio020499"      #input("Senha: ")

TIMEFRAME: int = int(input("Timeframe em minutos: M"))
INITIAL_TRADE_SIZE: int = int(input("Valor da entrada inicial: "))
TRADE_SIZE = INITIAL_TRADE_SIZE

PAIRS = ["EURUSD", "EURGBP", "EURJPY", "GBPUSD"]

OTC = input("Operar em OTC? (s/n): ") == "s"

MM_STRATEGY = input("Gerenciamento soros ou martingale? (soros/gale): " )

MAOS_DE_GALE_OU_SOROS: int = int(input("Numeros de mãos de {}: ".format(MM_STRATEGY)))

if OTC:
    PAIRS = list(map(lambda pair: pair + "-OTC", PAIRS))

print("Paridades: ", PAIRS)

API = IQ_Option(EMAIL, PASSWORD)
        
def connect_to_iq():
    
    status, reason = API.connect()
    
    if reason == "2FA":
        print('##### 2FA HABILITADO #####')
        print("Um sms foi enviado com um código para seu número")

        code_sms = input("Digite o código recebido: ")
        status, reason = API.connect_2fa(code_sms)

        print('##### Segunda tentativa #####')
        print('Status:', status)
        print('Reason:', reason)
        print("Email:", API.email)
        
    if (status == True):
        print("Conectado: {}".format(API.check_connect()))
        print("Banca:", API.get_balance())
        print("\n\n")

    else:
        reason_code = json.loads(reason)["code"]

        if reason_code == "requests_limit_exceeded":
            print("Falha ao conectar: Tente novamente em 10 minutos.")
        elif reason_code == "invalid_credentials":
            print("Falha ao conectar: Login ou senha incorretos.")
        else:
            print("Falha ao conectar: {}".format(reason))
        
        print("Falha ao conectar: {}".format(reason))
    
    return status

def wait_for_trading_oportunity(pair: str):
    global TRADE_SIZE
    
    print("Looking for trading opportunity on {}".format(pair))

    candles = API.get_candles(pair, TIMEFRAME * 60, 3, time.time())
    
    current_candle = candles[-1]
    current_candle_size = current_candle["close"] - current_candle["open"]
    current_candle_is_small = current_candle_size < abs(find_least_number(current_candle_size)) * 10
    
    last_candle = candles[-2]

    trade_id: int | None = None
    
    if (current_candle_is_small):
        if (last_candle["close"] > last_candle["open"]):
            print("should buy", TRADE_SIZE, OP_code.ACTIVES[pair], TIMEFRAME)
            has_placed_trade, id = API.buy(TRADE_SIZE, OP_code.ACTIVES[pair], "call", TIMEFRAME);
            if has_placed_trade:
                trade_id = id
        
        else:
            print("should sell", TRADE_SIZE, OP_code.ACTIVES[pair], TIMEFRAME)
            has_placed_trade, id = API.buy(TRADE_SIZE, OP_code.ACTIVES[pair], "put", TIMEFRAME);
            if has_placed_trade:
                trade_id = id

    if trade_id:
        has_closed, profit = wait_for_trade_result(trade_id)
        
        GAIN = profit > 0
        LOSS = profit < 0
        
        if MM_STRATEGY == "soros":
            # SOROS MONEY MANAGEMENT
            if GAIN and TRADE_SIZE < INITIAL_TRADE_SIZE * MAOS_DE_GALE_OU_SOROS:
                TRADE_SIZE = TRADE_SIZE + profit;
            elif GAIN or LOSS:
                TRADE_SIZE = INITIAL_TRADE_SIZE

        else:
            # GALE MONEY MANAGEMENT
            if LOSS and TRADE_SIZE < INITIAL_TRADE_SIZE * MAOS_DE_GALE_OU_SOROS:
                TRADE_SIZE = TRADE_SIZE * 2;
            elif GAIN or LOSS:
                TRADE_SIZE = INITIAL_TRADE_SIZE
        
        print("Trade closed");

        print("Lucro" if profit > 0 else "Prejuizo")
        
        trade_id = None
    
def wait_for_trade_result(trade_id: int):
    print("Waiting for trade result")
    has_closed, profit = API.check_win_v4(trade_id)
    return has_closed, profit

def find_least_number(reference_value):
    # Calculate the number of decimal places in the reference value
    decimal_places = len(str(reference_value).split('.')[1])

    # Calculate the least number possible based on the number of decimal places
    least_number: float = 1 / (10 ** (decimal_places + 1))

    return least_number
    
should_exit = False

while not should_exit:
    try:     
        while not API.check_connect():
            success = connect_to_iq();
            time.sleep(0.1)
            
        for pair in PAIRS:
            wait_for_trading_oportunity(pair)
                
    except KeyboardInterrupt as e:
        should_exit = True;