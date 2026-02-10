#!/usr/bin/python

import json
import datetime
import time
import sys
import os

import requests
import yaml

with open('config.yaml', encoding='UTF-8') as g:
    _cfg = yaml.load(g, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
DISCORD_WEBHOOK_LOG_URL = _cfg['DISCORD_WEBHOOK_LOG_URL']
URL_BASE = _cfg['URL_BASE']
CHARGE = _cfg['CHARGE']
USER = _cfg['USER']

# LOG_PICE는 마지막 매수 금액보다 현재 금액이 얼마만큼 낮을 경우 추가 매수할 것인가를 지정함
# 설정한 가격보다 차이나는 경우는 판단과 매수 사이에 지연이 있어 주식 가격이 변경되어 발생함
# (매수 가격근 지정하지 않음, 매수 시점에 거래 가능 금액으로 바로 매수함)
LOW_PICE = int(_cfg['LOW_PICE'])
HIGH_PICE = int(_cfg['HIGH_PICE'])
MAX_BUY_CNT = int(_cfg['BUY_CNT'])
DAY_MAX_BUY_CNT = int(_cfg['DAY_MAX_BUY_CNT'])
STOP_FLAG = int(_cfg['STOP_FLAG'])


msg_low_price = 0

TOKEN_FILE = "access_token.txt" #토큰을 저장할 파일명

if HIGH_PICE < 50:
    HIGH_PICE = 50


def send_message_log(msg):
    now = datetime.datetime.now()
    log_file = "AutoStock_"+now.strftime("%Y%m%d")+".log"

    with open(log_file, "a") as f:
        f.write(f"[{now.strftime('%H:%M:%S')}] {str(msg)}\n")

def send_message_log_sale(msg):
    now = datetime.datetime.now()
    log_file = "sel_AutoStock_"+now.strftime("%Y%m%d")+".log"

    with open(log_file, "a") as f:
        f.write(f"[{now.strftime('%H:%M:%S')}] {str(msg)}\n")

def send_message_log_current(msg):
    now = datetime.datetime.now()
    log_file = "sel_AutoStock_"+now.strftime("%Y%m%d")+"_current.log"

    with open(log_file, "a") as f:
        f.write(f"[{now.strftime('%H:%M:%S')}] {str(msg)}\n")


def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"{now.strftime('%H:%M:%S')}[{USER}]{str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    time.sleep(0.1)
    print(message)
    send_message_log (message)

def send_message_monitor(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"{now.strftime('%H:%M:%S')}[{USER}]{str(msg)}"}
    requests.post(DISCORD_WEBHOOK_LOG_URL, data=message)
    time.sleep(0.1)
    #print(message)
    send_message_log (message)

def get_access_token():
    """토큰 발급 및 파일 저장"""
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    time.sleep(0.1)
    ACCESS_TOKEN = res.json()["access_token"]

    # 토큰을 파일에 저장
    with open(TOKEN_FILE, "w") as f:
        f.write(ACCESS_TOKEN)

    return ACCESS_TOKEN


def load_access_token():
    """파일에서 토큰 로드"""
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()  # 앞뒤 공백 제거
    except FileNotFoundError:
        return None

def is_token_valid(token):
    """토큰 유효성 검사 (예시, 실제 API에 따라 다름)"""
    # 토큰의 만료 시간을 확인하거나, API를 호출하여 유효성을 검사하는 로직을 추가합니다.
    # 예시: 토큰 만료 시간이 현재 시간보다 이후인지 확인
    # 만약 토큰이 유효하지 않다면 False를 반환
    # 여기서는 단순하게 항상 True를 반환하도록 구현 (실제로는 API를 호출하여 검증해야 함)

    #실제 API 호출 예시 (유효성 검증 API가 있다면)


    """현재가 조회"""
    code="069500"
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"FHKST01010100"}
    params = {
        "fid_cond_mrkt_div_code":"J",
        "fid_input_iscd":code,
    }
    res = requests.get(URL, headers=headers, params=params)
    time.sleep(0.1)
    if res.status_code == 200: # 성공적인 응답
        return True
    else:
        if os.path.isfile(TOKEN_FILE):
            send_message_log(f"os.remove({TOKEN_FILE})")
            os.remove(TOKEN_FILE)
        return False


def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
    'content-Type' : 'application/json',
    'appKey' : APP_KEY,
    'appSecret' : APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    time.sleep(0.1)
    hashkey = res.json()["HASH"]
    return hashkey

def get_current_price(code="005930"):
    """현재가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"FHKST01010100"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    }
    res = requests.get(URL, headers=headers, params=params)

    time.sleep(0.1)
    return int(res.json()['output']['stck_prpr'])

def get_target_price(code="005930"):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST01010400"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    "fid_org_adj_prc":"1",
    "fid_period_div_code":"D"
    }
    res = requests.get(URL, headers=headers, params=params)
    time.sleep(0.1)
    stck_oprc = int(res.json()['output'][0]['stck_oprc']) #오늘 시가
    send_message(f"{code} = 오늘 시가: {stck_oprc}원")
    stck_hgpr = int(res.json()['output'][1]['stck_hgpr']) #전일 고가
    send_message(f"{code} = 전일 고가: {stck_hgpr}원")
    stck_lwpr = int(res.json()['output'][1]['stck_lwpr']) #전일 저가
    send_message(f"{code} = 전일 저가: {stck_lwpr}원")

def get_stock_balance_now_struct(code):
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8434R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    time.sleep(0.1)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']

    return stock_list, evaluation

def get_stock_balance_now(code):
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8434R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    time.sleep(0.1)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message_log("====주식 보유잔고====")
    stock_qty = 0

    stock_current = 0
    for stock in stock_list:
        send_message_log (f"stock['prdt_name'] = {stock['prdt_name']} : 상품명")
        send_message_log (f"stock['trad_dvsn_name'] = {stock['trad_dvsn_name']} : 매매구분명")
        send_message_log (f"stock['bfdy_buy_qty']   = {stock['bfdy_buy_qty']} : 전일매수수량")
        send_message_log (f"stock['bfdy_sll_qty']   = {stock['bfdy_sll_qty']} : 전일매도수량")
        send_message_log (f"stock['thdt_buyqty']    = {stock['thdt_buyqty']} : 금일매수수량")
        send_message_log (f"stock['thdt_sll_qty']   = {stock['thdt_sll_qty']} : 금일매도수량")
        send_message_log (f"stock['hldg_qty']       = {stock['hldg_qty']} : 보유수량")
        send_message_log (f"stock['ord_psbl_qty']   = {stock['ord_psbl_qty']} : 주문가능수량")
        send_message_log (f"stock['pchs_avg_pric']  = {stock['pchs_avg_pric']} : 매입평균가격")
        send_message_log (f"stock['pchs_amt']       = {stock['pchs_amt']} : 매입금액")
        send_message_log (f"stock['prpr'] = {stock['prpr']} : 현재가")
        send_message_log (f"stock['evlu_amt']       = {stock['evlu_amt']} : 평가금액")
        send_message_log (f"stock['evlu_pfls_amt']  = {stock['evlu_pfls_amt']} : 평가손익금액= 평가금액 - 매입금액")
        send_message_log (f"stock['evlu_pfls_rt']   = {stock['evlu_pfls_rt']} : 평가손익율")
        send_message_log (f"stock['fltt_rt']        = {stock['fltt_rt']} : 등락율")
        send_message_log (f"stock['bfdy_cprs_icdc'] = {stock['bfdy_cprs_icdc']} : 전일대비증감")
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            send_message_log (f"{stock['prdt_name']} ({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
            if stock['pdno'] == code:
                stock_qty = int(stock['hldg_qty'])
                stock_current = int(stock['prpr'])
                break

    send_message_log (f"evaluation['dnca_tot_amt'] = {evaluation[0]['dnca_tot_amt']} : 예수금총금액")
    send_message_log (f"evaluation['nxdy_excc_amt'] = {evaluation[0]['nxdy_excc_amt']} : 익일정산금액")
    send_message_log (f"evaluation['scts_evlu_amt'] = {evaluation[0]['scts_evlu_amt']} : 유가평가금액")
    send_message_log (f"evaluation['evlu_amt_smtl_amt'] = {evaluation[0]['evlu_amt_smtl_amt']} : 평가금액합계금액")
    send_message_log(f"주식 현재가 : {stock_current}원")
    send_message_log(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    send_message_log(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    stock_cash = int(evaluation[0]['scts_evlu_amt']) - int(evaluation[0]['evlu_pfls_smtl_amt'])
    evaluation_cash = int(evaluation[0]['scts_evlu_amt'])
    time.sleep(0.1)
    send_message_log(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    tot_evlu_amt = int(evaluation[0]['tot_evlu_amt'])
    time.sleep(0.1)
    send_message_log("=================")
    return stock_cash, evaluation_cash, stock_qty, tot_evlu_amt

def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8434R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    time.sleep(0.1)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message_log("====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            send_message_log (f"{stock['prdt_name']} ({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
    send_message_log(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    #time.sleep(0.1)
    send_message_log(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    #time.sleep(0.1)
    send_message_log(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    #time.sleep(0.1)
    send_message_log("=================")
    return stock_dict

def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8908R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    time.sleep(0.1)
    cash = res.json()['output']['ord_psbl_cash']
    send_message_log(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)

def buy(code="005930", qty="1"):
    """주식 시장가 매수"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json",
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0802U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    time.sleep(0.1)
    if res.json()['rt_cd'] == '0':
        send_message_log (f"[매수 성공]{str(res.json())}")

        return True

    send_message(f"[매수 실패]{str(res.json())}")
    if "장운영일자가 주문일과 상이합니다" in str(res.json()):
        send_message_log("장운영일자가 주문일과 상이합니다")
        sys.exit()
    return False

def sale(code="005930", qty="1"):
    """주식 시장가 매도"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json",
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0801U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    time.sleep(0.1)
    if res.json()['rt_cd'] == '0':
        send_message_log (f"[매도 성공]{str(res.json())}")
        return True

    send_message(f"[매도 실패]{str(res.json())}")
    if "장운영일자가 주문일과 상이합니다" in str(res.json()):
        send_message_log("장운영일자가 주문일과 상이합니다")
        sys.exit()
    return False

def get_my_oder_bak(code):
    send_message_log ("--------------------------")
    send_message_log(f"get_my_oder_bak ({code})")

    file_name = f"my_{code}.txt"
    file_name_bak = f"my_{code}_"+now.strftime("%Y%m%d")+".txt"
    send_message_log(f"file_name    ={file_name}")
    send_message_log(f"file_name_bak={file_name_bak}")

    if not os.path.exists(file_name_bak):
        my_price_bak = []
        send_message_log("파일이 존재하지 않습니다.")
        with open(file_name, 'r') as f:
            for line in f:
                tmp_line=line.strip()
                if len(tmp_line) <= 0:
                    continue
                if int(tmp_line) <= 50:
                    continue
                my_price_bak.append(int(tmp_line))

        my_price_bak.sort(reverse=True)
        with open(file_name_bak, 'w') as f:
            for i in my_price_bak:
                f.write(str(i)+"\n")


    my_price = []
    with open(file_name_bak, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            my_price.append(int(tmp_line))

    if len(my_price) <= 0:
        send_message_log("my_price no item")
        send_message_log ("- 2 return get_my_oder_bak ------")
        return 0, 0
    send_message_log ("- 1 return get_my_oder_bak ------")
    return my_price[-1], len(my_price)

def zero_set_my_oder(code):
    send_message_log ("--------------------------")
    send_message_log(f"zero_set_my_oder ({code})")

    file_name = f"my_{code}.txt"
    send_message_log(f"file_name={file_name}")
    if not os.path.exists(file_name):
        send_message_log("파일이 존재하지 않습니다.")
        send_message_log ("- 1 return get_my_oder ------")
        with open(file_name, 'w') as f:
            f.write("\n")
        return 0, 0

    with open(file_name, 'w') as f:
        f.write("\n")
    return 0, 0

def get_my_oder(code):
    send_message_log ("--------------------------")
    send_message_log(f"get_my_oder ({code})")

    file_name = f"my_{code}.txt"
    send_message_log(f"file_name={file_name}")
    if not os.path.exists(file_name):
        send_message_log("파일이 존재하지 않습니다.")
        send_message_log ("- 1 return get_my_oder ------")
        with open(file_name, 'w') as f:
            f.write("\n")
        return 0, 0

    cnt = 0
    my_price = []
    #send_message_log(f"file_name={file_name}")
    # 파일을 읽기 모드('r')로 엽니다.
    with open(file_name, 'r') as f:
        # 파일의 내용을 읽어옵니다.
        for line in f:
            tmp_line=line.strip()
            #send_message_log(f"{cnt} line={tmp_line}")
            if len(tmp_line) <= 0:
                send_message_log(f"E1: {cnt} line={tmp_line}")
                continue
            if int(tmp_line) <= 50:
                send_message_log(f"E2: {cnt} line={tmp_line}")
                continue
            cnt = cnt + 1
            my_price.append(int(tmp_line))

    if len(my_price) <= 0:
        send_message_log("my_price no item")
        send_message_log ("- 2 return get_my_oder ------")
        return 0, 0

    #send_message_log(f"file_name={file_name}")
    my_price.sort(reverse=True)

    send_message_log(f"0 my_price[0] = {my_price[0]}")
    send_message_log(f"return {my_price[-1]}, {cnt}")
    send_message_log ("- 3 return get_my_oder ------")
    return my_price[-1], len(my_price)


def get_list_my_oder(code):
    send_message_log ("--------------------------")
    send_message_log(f"get_list_my_oder ({code})")

    file_name = f"my_{code}.txt"
    send_message_log(f"file_name={file_name}")
    if not os.path.exists(file_name):
        send_message_log("파일이 존재하지 않습니다.")
        send_message_log ("- 1 return get_list_my_oder ------")
        with open(file_name, 'w') as f:
            f.write("\n")
        return []

    my_price = []
    #send_message_log(f"file_name={file_name}")
    # 파일을 읽기 모드('r')로 엽니다.
    with open(file_name, 'r') as f:
        # 파일의 내용을 읽어옵니다.
        for line in f:
            tmp_line=line.strip()
            #send_message_log(f" line={tmp_line}")
            if len(tmp_line) <= 0:
                send_message_log(f"E1: line={tmp_line}")
                continue
            if int(tmp_line) <= 50:
                send_message_log(f"E2: line={tmp_line}")
                continue
            my_price.append(int(tmp_line))

    if len(my_price) <= 0:
        send_message_log("my_price no item")
        send_message_log ("- 2 return get_list_my_oder ------")
        return []

    my_price.sort(reverse=True)

    send_message_log ("- 3 return get_list_my_oder ------")
    return my_price

##############################################################
##############################################################
##############################################################
def buy_Offsetting_Processing_v1 (code, current_price):
    send_message_log ("------------------------")
    send_message_log (f"buy_Offsetting_Processing_v1 ({code}, {current_price})")
    file_name = f"my_{code}.txt"

    if not os.path.exists(file_name):
        send_message_log (f"{file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(file_name, 'w') as f:
            f.write("\n")
        return 0

    my_price = []
    with open(file_name, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            my_price.append(int(tmp_line))
    if len(my_price) < 20:
# 보유 주식수가 10보다 작을 경우 매수한다.
        return 0

    my_price.sort(reverse=True)

    if current_price < my_price[-1]:
    # current_price보다 낮은 금액이 없어 매수가 필요함
        send_message_log ("- 1 return buy_Offsetting_Processing_v1 ------")
        return 0

    if int(current_price) in my_price:
    # my_price에 current_price 값이 이미 존재하여 매수가 불필요함
        current_price_count = my_price.count(int(current_price))
        if current_price_count >= MAX_BUY_CNT:
# 다만 매수한 current_price 가격이 MAX_BUY_CNT보다 많을 경우 매수하지 않는다.
            send_message_log(f"{sym} : current_price : {current_price}")
            send_message_log(f"{sym} : current_price_count : {current_price_count}")
            send_message_log ("- 2 return buy_Offsetting_Processing_v1 ------")
            return 1


    for idx in range(0, int(len(my_price)-5)):
        if current_price > my_price[idx]:
            # current_price가 my_price[idx] 보다 크다면
            # my_price[idx]이 current_price 보다 작을 경우 차이를 tmp_price에 저장하고
            # my_price[idx]를 current_price로 바꾼다.
            # 구매하려는 current_price 보다 낮은 가격이 있을 경우 해당 주식을 current_price 가격으로 대체한다.
            # 이는 구매하려 하는 주식 보다 낮은 가격을 올려 매수한 것처럼 처리한다.
            # current_price 보다 낮은 가격이 없을 경우에는 매수를 수행한다.
            # 0을 return 하면 매수를 수행하고
            # 0보다 큰수를 반환하면 매수를 하지 않는다.
            # current_price와 낮은 가격 차이는 my_price[0] 차감한다.
            tmp_price = current_price - my_price[idx]
            if tmp_price > 100:
                # 매수 상계 처리할 때 상계할 금액과 가격차이가 100이상이 나면 상계 매수하지 않고 직접 매수한다.
                send_message_log(f"{sym} : current_price : {current_price}")
                send_message_log ("- 3 return buy_Offsetting_Processing_v1 ------")
                return 0

            send_message_log (f"tmp_price={tmp_price}")
            send_message_log (f"my_price[{idx}]={my_price[idx]}")
            my_price[idx] = current_price
            send_message_log (f"my_price[{idx}]={my_price[idx]}")
            send_message_log (f"my_price[{idx}+1]={my_price[idx+1]}")
            my_price[idx+1] = my_price[idx+1] - tmp_price
            send_message_log (f"my_price[{idx}+1]={my_price[idx+1]}")
            send_message_log ( f"buy:1 ({current_price}): [{idx}+1]={my_price[idx+1]}")
            send_message_log_sale ( f"buy:1 ({current_price}): [{idx}+1]={my_price[idx+1]}")
            send_message_log_current ( f"buy:1 ({current_price}): [{idx}+1]={my_price[idx+1]}")
            my_price.sort(reverse=True)
            with open(file_name, 'w') as f:
                for i in my_price:
                    send_message_log (f"{code} = {i}")
                    f.write(str(i)+"\n")

            send_message_log ("- 4 return buy_Offsetting_Processing_v1 ------")
            return 1


    # 모든 조건에서 상계처리가 되지 않은 경우 매수한다.
    return 0


##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
# 최고점에 있을 경우 최고가를 조정하면 계속 최고가를 매수하는 문제가 발생
# 최저점에 있을 경우 최저가를 조정하면 계속 최저가를 매수하는 문제가 발생
# 최고가, 최저가는 조정하지 않는다.
##############################################################
def organize_v1 (code):
    send_message_log ("------------------------")
    send_message_log (f"organize_v1 ({code})")
    file_name = f"my_{code}.txt"

    if not os.path.exists(file_name):
        send_message_log (f"{file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(file_name, 'w') as f:
            f.write("\n")
        return

    my_price = []
    with open(file_name, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            my_price.append(int(tmp_line))

    if len (my_price) < 30:
        send_message_log (f"len (my_price) = {len(my_price)}")
        send_message_log ("- 1 return organize_v1 ------")
        return

    sum_result = sum(my_price)
    send_message_log ( f"장부총금액 : {sum_result}원")


    my_price.sort(reverse=True)


    for idx in range(0, int(len(my_price)-2)):
        #print (f"{idx}: {my_price[idx]}")
        tmp_digit = abs(my_price[idx]) % 10
        #print(f"tmp_digit = {tmp_digit}")
        if not (tmp_digit == 5 or tmp_digit == 0):
            send_message_log("끝의 숫자가 5 또는 0으로 끝나지 않습니다.")
            send_message_log (f"{idx}: {my_price[idx]}")
            send_message_log(f"tmp_digit = {tmp_digit}")
            my_price[idx] = my_price[idx] - tmp_digit
            send_message_log (f"{idx}: {my_price[idx]}")
            my_price[-1] = my_price[-1] + tmp_digit
            send_message_log (f"{len(my_price)}: {my_price[-1]}")



    my_price.sort()
    loop_cnt = 0
    send_message_log("==============================")
    while True:
        #send_message_log(f" LOOP loop_cnt = {loop_cnt}")
        loop_cnt = loop_cnt + 1
        if loop_cnt > 100:
            break

        result = 0
        #send_message_log (f"my_price[0]:{my_price[0]}")
        split_cnt = 0
        for idx in range(5, int(len(my_price)-(MAX_BUY_CNT+4))):
            #if (my_price[idx]+20) > my_price[0]:
            #    continue

            #send_message_log (f"my_price[{idx}]:{my_price[idx]}")

            if my_price[idx] == my_price[-1]:
                continue

            my_price_count = my_price.count(int(my_price[idx]))
            max_count = MAX_BUY_CNT
            if my_price_count <= max_count:
                continue
            if my_price[idx] == my_price[idx+max_count]:
                send_message_log (f"organize_v1 my_price[{idx}]:{my_price[idx]} ({my_price_count})")
## 같 같은 가격의 수가 4개 이상일 경우 하나는 5를 더하고 다른 하나는 5를 뺀다
                send_message_log (f"organize_v1 my_price[{idx}]:{my_price[idx]} == my_price[{idx+max_count}]:{my_price[idx+max_count]}")
                my_price[idx] = my_price[idx] - 5
                my_price[idx+max_count] = my_price[idx+max_count] + 5
                send_message_log (f"            my_price[{idx}]:{my_price[idx]} == my_price[{idx+max_count}]:{my_price[idx+max_count]}")
                result = 1
                split_cnt = split_cnt + 1
                break

        send_message_log(f"LOOP Cnt [{loop_cnt}] : split_cnt = {split_cnt}")


        my_price.sort()

        if result == 0:
            break

    my_price.sort(reverse=True)
    index = 0
    for idx in range(0, int(len(my_price)-1)):
        if my_price[idx] != my_price[idx+1]:
            my_price_count = my_price.count(int(my_price[idx]))
            max_count = MAX_BUY_CNT
            if my_price_count > (max_count):
                index = index + 1
                send_message_log(f"organize_v1 ({index}) {idx} {my_price[idx]} : CNT = {my_price_count}")

    #send_message_log (f"organize_v1 LOOP loop_cnt = {loop_cnt}")
    #send_message_log (f"organize_v1 my_price[ 0]={my_price[0]} High")
    #send_message_log (f"organize_v1 my_price[-1]={my_price[-1]} Low")
    #send_message_log (f"organize_v1 my_price High-Low ={my_price[0] - my_price[-1]}")
    #send_message_log (f"organize_v1 my_price len ={len(my_price)}")

    cnt = 0
    bak_i = 0
    with open(file_name, 'w') as f:
        for i in my_price:
            if (bak_i - i) > 5:
                send_message_log (f"{cnt} {code} = {i} ({bak_i - i})")
            f.write(str(i)+"\n")
            cnt = cnt + 1
            bak_i = i

    send_message_log (f"organize_v1 LOOP loop_cnt = {loop_cnt}")
    send_message_log (f"organize_v1 my_price[ 0]={my_price[0]} High")
    send_message_log (f"organize_v1 my_price[-1]={my_price[-1]} Low")
    send_message_log (f"organize_v1 my_price High-Low ={my_price[0] - my_price[-1]}")
    send_message_log (f"organize_v1 my_price len ={len(my_price)}")
    send_message_log ("- 3 return organize_v1 ------")
    return
##############################################################
##############################################################
##############################################################
##############################################################
def organize (code):
    send_message_log ("------------------------")
    send_message_log (f"organize ({code})")
    file_name = f"my_{code}.txt"

    if not os.path.exists(file_name):
        send_message_log (f"{file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(file_name, 'w') as f:
            f.write("\n")
        return

    my_price = []
    with open(file_name, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            my_price.append(int(tmp_line))


    if len (my_price) < 200:
        send_message_log ("- 1 return organize ------")
        return

    my_price.sort(reverse=True)


    for idx in range(1, int(len(my_price)-100)):
        send_message_log (f"my_price[{idx}]:{my_price[idx]}")
        if (my_price[idx]+10) > my_price[0]:
            continue

        if my_price[idx] == my_price[idx+1]:
            send_message_log (f"my_price[{idx}]:{my_price[idx]} == my_price[{idx}+1]:{my_price[idx+1]}")
            send_message_log (f"my_price[{idx}]={my_price[idx]} + 5")
            my_price[idx] = my_price[idx] + 5
            send_message_log (f"my_price[{idx}]={my_price[idx]}")

            send_message_log (f"my_price[0]={my_price[0]} - 5")
            my_price[0] = my_price[0] - 5
            send_message_log (f"my_price[0]={my_price[0]}")
            break


    my_price.sort(reverse=True)


    cnt = 0
    with open(file_name, 'w') as f:
        for i in my_price:
            send_message_log (f"{cnt} {code} = {i}")
            f.write(str(i)+"\n")
            cnt = cnt + 1

    send_message_log ("- 3 return organize ------")
    return
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
def organize_bak (code):
    send_message_log ("------------------------")
    send_message_log (f"organize_bak ({code})")
    file_name = f"my_{code}.txt"

    if not os.path.exists(file_name):
        send_message_log (f"{file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(file_name, 'w') as f:
            f.write("\n")
        return

    my_price = []
    with open(file_name, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            my_price.append(int(tmp_line))


    if len (my_price) < 20:
        send_message_log ("- 1 return organize_bak ------")
        return

    my_price.sort(reverse=True)


    center_cnt=int(len(my_price)/2)

    if (my_price[center_cnt]+10) >= my_price[0]:
        send_message_log (f"my_price[0]={my_price[0]}")
        send_message_log (f"my_price[{center_cnt}]={my_price[center_cnt]}")
        send_message_log ("- 2 return organize_bak ------")
        return


    send_message_log (f"my_price[0]={my_price[0]} - 5")
    send_message_log (f"my_price[{center_cnt-1}]={my_price[center_cnt-1]} - 5")
    send_message_log (f"my_price[{center_cnt}]={my_price[center_cnt]} + 10")

    my_price[center_cnt] = my_price[center_cnt] + 10
    my_price[0] = my_price[0] - 5
    my_price[center_cnt-1] = my_price[center_cnt-1] - 5

    send_message_log (f"my_price[0]={my_price[0]}")
    send_message_log (f"my_price[{center_cnt-1}]={my_price[center_cnt-1]}")
    send_message_log (f"my_price[{center_cnt}]={my_price[center_cnt]}")


    my_price.sort(reverse=True)


    cnt = 0
    with open(file_name, 'w') as f:
        for i in my_price:
            send_message_log (f"{cnt} {code} = {i}")
            f.write(str(i)+"\n")
            cnt = cnt + 1

    send_message_log ("- 3 return organize_bak ------")
    return
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
def organize_low (code):
    send_message_log ("------------------------")
    send_message_log (f"organize_low ({code})")
    file_name = f"my_{code}.txt"

    if not os.path.exists(file_name):
        send_message_log (f"{file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(file_name, 'w') as f:
            f.write("\n")
        return

    my_price = []
    with open(file_name, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            my_price.append(int(tmp_line))


    if len (my_price) < 20:
        send_message_log ("------------------------")
        return

    my_price.sort(reverse=True)

    for idx in range(len(my_price)-1, int(len(my_price)/2), -1):
        send_message_log (f"my_price[{idx}]:{my_price[idx]}")
        if my_price[idx] == my_price[0]:
            return

        if my_price[idx] == my_price[idx-1]:
            send_message_log (f"my_price[{idx}]:{my_price[idx]} == my_price[{idx}-1]:{my_price[idx-1]}")
            send_message_log (f"my_price[{idx}]={my_price[idx]} - 5")
            my_price[idx] = my_price[idx] - 5
            send_message_log (f"my_price[{idx}]={my_price[idx]}")

            send_message_log (f"my_price[{idx}-1]={my_price[idx-1]} + 5")
            my_price[idx-1] = my_price[idx-1] + 5
            send_message_log (f"my_price[{idx}-1]={my_price[idx-1]}")
            break

    my_price.sort(reverse=True)


    with open(file_name, 'w') as f:
        for i in my_price:
            send_message_log (f"{code} = {i}")
            f.write(str(i)+"\n")

    send_message_log ("------------------------")
    return
##############################################################
##############################################################
##############################################################
##############################################################
def organize_low_100 (code):
    send_message_log ("------------------------")
    send_message_log (f"organize_low_100 ({code})")
    file_name = f"my_{code}.txt"

    if not os.path.exists(file_name):
        send_message_log (f"{file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(file_name, 'w') as f:
            f.write("\n")
        return

    my_price = []
    with open(file_name, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            my_price.append(int(tmp_line))


    if len (my_price) < 20:
        send_message_log ("------------------------")
        return

    my_price.sort(reverse=True)
    gap = 5

    for gap in range(0, 10, 5):
        send_message_log (f"gap = {gap}")
        for idx in range(len(my_price)-1, int(len(my_price)/2), -1):
            send_message_log (f"my_price[{idx}]:{my_price[idx]}")
            if my_price[idx] == my_price[0]:
                return

            if not my_price[idx]+gap < my_price[idx-1]:
                send_message_log (f"my_price[{idx}]:{my_price[idx]} == my_price[{idx}-1]:{my_price[idx-1]}")
                send_message_log (f"my_price[{idx}]={my_price[idx]} - 5")
                my_price[idx] = my_price[idx] - 5
                send_message_log (f"my_price[{idx}]={my_price[idx]}")

                send_message_log (f"my_price[{idx}-1]={my_price[idx-1]} + 5")
                my_price[idx-1] = my_price[idx-1] + 5
                send_message_log (f"my_price[{idx}-1]={my_price[idx-1]}")
                break

    my_price.sort(reverse=True)


    with open(file_name, 'w') as f:
        for i in my_price:
            send_message_log (f"{code} = {i}")
            f.write(str(i)+"\n")

    send_message_log ("------------------------")
    return
##############################################################
##############################################################
##############################################################
##############################################################
# 재투자 reinvest 만큼 my_price에서 가장 높은 매수 종목에서 차감한다.
def my_oder_reinvest(code, reinvest=10):
    send_message_log (f"my_oder_reinvest ({code}, {reinvest})")

    # 매수 가격 정보를 기록하는 파일
    file_name = f"my_{code}.txt"

    if not os.path.exists(file_name):
        send_message_log (f"{file_name} 파일이 존재하지 않습니다.")
        return 0


    my_price = []
    # 파일을 읽기 모드('r')로 엽니다.
    # 파일을 읽어 my_price에 추가한다.
    # 50보다 작은 경우 무시한다.
    with open(file_name, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            #send_message_log (f"({code}) line={tmp_line}")
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            my_price.append(int(tmp_line))

# 수익 투자 금액을 5원씩 나눴을때 개수 가 전체 주식 수보다 작을 경우 재투자 하지 않는다.
    if len(my_price) < ((reinvest // 5)+10):
        return 0

    my_price.sort(reverse=True)

    if my_price[10] <= (my_price[-1] + reinvest):
        return 0

# 수익 재투자는 가장 높은 가격 부터 5원씩 금액이 소진될때까지 순차적으로 차감한다.
    bak_reivenst = reinvest
    for idx in range(0, int(len(my_price)-1)):
        if (bak_reivenst > 5):
            bak_price = my_price[idx]
            my_price[idx] = my_price[idx] - 5
            send_message_log(f"reinvest my_price[{idx}] = {bak_price} => {my_price[idx]}")
            bak_reivenst = bak_reivenst - 5
        else:
            bak_price = my_price[idx]
            my_price[idx] = my_price[idx] - bak_reivenst
            send_message_log(f"reinvest my_price[{idx}] = {bak_price} => {my_price[idx]}")
            bak_reivenst = 0
            break



    my_price.sort(reverse=True)

    # 파일에 매수 가격을 내림 차순으로 기록한다.
    with open(file_name, 'w') as f:
        cnt_price = 0
        for i in my_price:
            send_message_log (f"{cnt_price} = {i}")
            cnt_price = cnt_price + 1
            f.write(str(i)+"\n")

    # backup 파일에 가록
    with open(file_name+".bak", 'w') as f:
        for i in my_price:
            #send_message_log (f"{code} = {i}")
            f.write(str(i)+"\n")

    # 재투자 금액
    return reinvest




##############################################################
##############################################################
##############################################################
##############################################################
def set_my_oder(code, price, ctrl):
    send_message_log (f"set_my_oder ({code}, {price}, {ctrl})")

    #organize (code)

    # 매수 가격 정보를 기록하는 파일
    file_name = f"my_{code}.txt"
    buy_top_max_cnt = f"buy_{code}_max_cnt.txt"

    if not os.path.exists(file_name):
        send_message_log (f"{file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(file_name, 'w') as f:
            f.write("\n")

    if not os.path.exists(buy_top_max_cnt):
        send_message_log (f"{buy_top_max_cnt} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(buy_top_max_cnt, 'w') as f:
            f.write("1:0\n")

    cnt=0
    my_price = []
    # 파일을 읽기 모드('r')로 엽니다.
    # 파일을 읽어 my_price에 추가한다.
    # 50보다 작은 경우 무시한다.
    with open(file_name, 'r') as f:
        for line in f:
            tmp_line=line.strip()
            #send_message_log (f"{cnt} ({code}) line={tmp_line}")
            if len(tmp_line) <= 0:
                continue
            if int(tmp_line) <= 50:
                continue
            cnt = cnt + 1
            my_price.append(int(tmp_line))

    send_message_log (f"ctrl = {ctrl}")
    if ctrl == "add":
        # 매수의 경우 금액을 추갛낟.
        send_message_log (f"ctrl = {ctrl}")

        my_price.append(price)
        my_price.sort(reverse=True)

        top_my_price_count = my_price.count(int(my_price[0]))
        send_message ( f"가장높은가격:{my_price[0]}원 ({top_my_price_count}개)")
        send_message ( f"가장낮은가격:{my_price[-1]}원")
        # 파일에 매수 가격을 내림 차순으로 기록한다.
        with open(file_name, 'w') as f:
            for i in my_price:
                send_message_log (f"{code} = {i}")
                f.write(str(i)+"\n")

        # backup 파일에 가록
        with open(file_name+".bak", 'w') as f:
            for i in my_price:
                #send_message_log (f"{code} = {i}")
                f.write(str(i)+"\n")

        tmp_buy_top_max_cnt = 0
        with open(buy_top_max_cnt, 'r') as f:
            for line in f:
                tmp_line=line.strip()
                send_message_log (f"{code} buy_max_cnt={tmp_line}")
                tmp_buy_top_max_cnt = int(tmp_line.split(":")[0])
                tmp_buy_top_max_price = int(tmp_line.split(":")[1])
                send_message_log (f"{code} tmp_buy_top_max_cnt={tmp_buy_top_max_cnt}")
                break

        if len(my_price) > tmp_buy_top_max_cnt:
            tmp_buy_top_max_cnt = len(my_price)
            if tmp_buy_top_max_price > my_price[-1]:
                tmp_buy_top_max_price = my_price[-1]

            send_message_log (f"{code} len(my_price)={tmp_buy_top_max_cnt}")
            with open(buy_top_max_cnt, 'w') as f:
                f.write(str(tmp_buy_top_max_cnt)+":"+str(tmp_buy_top_max_price)+"\n")
                send_message_log (f"buy_top_max_cnt = {buy_top_max_cnt} 파일.")
                send_message_log (f"{code} buy_top_max_cnt={tmp_buy_top_max_cnt}:{tmp_buy_top_max_price}")

        # 가장 마지막 항목 (가작 낮은 가격)을 반환한다.
        return my_price[-1]

    # 매도의 경우 항목 중 가장 낮은 가격을 제거한다.
    send_message_log (f"ctrl = {ctrl}")
    if len(my_price) > 0:
        if ctrl == "del":
            my_price.sort(reverse=True)
            send_message_log (f"del my_price pop = {my_price[-1]}")
            my_price.pop()

    if len(my_price) <= 0:
        # 항목이 없을 경우 0을 추가혀여 오류를 막는다.
        my_price.append(0)

    # 파일에 매수 가격을 내림 차순으로 기록한다.
    cnt = 0
    with open(file_name, 'w') as f:
        for i in my_price:
            send_message_log (f"{cnt} {code} = {i}")
            f.write(str(i)+"\n")
            cnt = cnt + 1

    # backup 파일에 기록
    with open(file_name+".bak", 'w') as f:
        for i in my_price:
            #send_message_log (f"{code} = {i}")
            f.write(str(i)+"\n")

    # 가장 마지막 항목 (가작 낮은 가격)을 반환한다.
    return my_price[-1]


##############################################################
##############################################################
##############################################################
##############################################################
def buy_inverse_stocks ():
    # 114800 ETF : KODEX 인버스
    ###################################
    sym = "114800"
    send_message_log(f"buy_inverse_stocks = {sym}")
    current_price = get_current_price(sym)
    send_message(f"{sym} : current_price : {current_price}")

    inverse_stock_cash, inverse_evl_amount, inverse_stock_qty, inverse_tot_evlu_amt = get_stock_balance_now (sym)

    send_message_log( f"{sym} = inverse_stock_cash   : {inverse_stock_cash}")
    send_message_log( f"{sym} = inverse_evl_amount   : {inverse_evl_amount}")
    send_message_log( f"{sym} = inverse_stock_qty    : {inverse_stock_qty}")
    send_message_log( f"{sym} = inverse_tot_evlu_amt : {inverse_tot_evlu_amt}")


##############################################################
def buy_stocks (sym):

    #####################################
    # 매수
    send_message_log("buy_stocks")

    if STOP_FLAG == 1:
        return 0


    my_price = get_list_my_oder(sym)

    current_price = get_current_price(sym)
    if not (current_price % 5 == 0):
# 주식 가격이 5원 단위가 아닐 경우 매수하지 않는다.
        print("false")
        return 0
    #current_price_tmp = (current_price // 10) * 10  # 1의 자리 버림


    #if current_price != current_price_tmp:
    #    return 0

    my_price_cnt = len(my_price)
    send_message_log(f"{sym} : current_price : {current_price} : my_cnt({my_price_cnt}) ")
    current_price_count = 0
    if my_price_cnt > 0:
        is_exist = int(current_price) in my_price
        send_message_log(f"{sym} : is_exist : {is_exist}")
        if is_exist:
            # current_price 가격이 이미 my_price에 존재할 경우 매수를 하지 않는다.
            current_price_count = my_price.count(int(current_price))
            send_message_log(f"{sym} : current_price_count 1 : {current_price_count}: MAX({MAX_BUY_CNT})")
            send_message_log_current(f"buy1 : {current_price} ({current_price_count}): MAX({MAX_BUY_CNT})")
            if current_price_count >= MAX_BUY_CNT:
                # 다만 매수한 current_price 가격이 MAX_BUY_CNT보다 많을 경우 매수하지 않는다.
                return 0
 
        buy_result = buy_Offsetting_Processing_v1 (sym, current_price)
## 매 매수 금액을 기준으로 기존 주식으로 상계 처리가 가능한지 확인한다.
        if buy_result > 0:
## bu buy_result 가 0보다 클 경우 상계 처리하여 current_price 가격을 장부에 생성하였으므로
## 주 주식 매수를 중지한다.
            send_message_log(f"{sym} : current_price_count 2 : {current_price}")
            return 0


    send_message_log(f"{sym} : current_price_count 3 : {current_price_count}: MAX({MAX_BUY_CNT})")
    send_message_log_current(f"buy3 : {current_price} ({current_price_count}): MAX({MAX_BUY_CNT})")

    total_cash = get_balance() # 보유 현금 조회

    if total_cash < current_price+700000:
        #organize_low (sym)
        send_message( f"{sym})잔액부족:{current_price}원 :잔액 {total_cash}")
        send_message_log( f"{sym})잔액부족:{current_price}원 :잔액 {total_cash}")
        send_message_log_current( f"{sym})잔액부족:{current_price}원 :잔액 {total_cash}")

        send_message_log ("- 2 return buy_stocks ------")
        time.sleep(10)
        return 0

    stock_cash, evl_amount, stock_qty, tot_evlu_amt = get_stock_balance_now (sym)
    send_message_log( f"{sym} = 보유현금 : {total_cash}원 (매수전)")
    send_message_log( f"{sym} = stock_cash:{stock_cash}, 주식 평가 금액 - 평가 손익 합계")
    send_message_log( f"{sym} = evl_amount:{evl_amount}, 주식 평가 금액")
    send_message_log( f"{sym} = stock_qty:{stock_qty}, 주식 수량")
    send_message_log( f"{sym} = tot_evlu_amt:{tot_evlu_amt}, 총 평가 금액")

    time.sleep(0.1)

    send_message_log ( f"{sym} = 매수1: {current_price}원")

    RESULT = buy(sym, "1")
    if RESULT is False:
        send_message( f"{sym}) 매수실폐: {current_price}원 ")
        return 0

    send_message_log( f"{sym} = 매수성공: ")
    while True:
        time.sleep(0.1)
        tmp_stock_cash, tmp_evl_amount, tmp_stock_qty, tmp_tot_evlu_amt = get_stock_balance_now (sym)
        send_message_log ( f"{sym} = tmp_stock_cash = {tmp_stock_cash}원 : tmp_stock_qty = {tmp_stock_qty}")
        if stock_qty < tmp_stock_qty:
            break

    stock_cash_1 = tmp_stock_cash - stock_cash
    time.sleep(0.1)
    if stock_cash_1 < 1:
        send_message_log ( f"stock_cash_1:{stock_cash_1} < 1")
        send_message_log ("- 3 return buy_stocks ------")
        return 0

    send_message_log ( "set_my_oder 1")
    tmp_current = set_my_oder(sym, stock_cash_1, "add")
    send_message( f"tmp_current: {tmp_current}")
    send_message_log_sale( f"{sym})매수:{stock_cash_1}원 ({tmp_stock_qty}) ")
    send_message_log ( f"stock_cash_1:{stock_cash_1}")
    send_message( f"{sym})매수:{stock_cash_1}원 ({tmp_stock_qty})")


    send_message_log ("- 5 return buy_stocks ------")
    time.sleep(10)
    return 1


##############################################################
##############################################################
def sell_Offsetting_Processing (sym):
    ###################################
    # 매도
    send_message_log("sell_Offsetting_Processing")
    send_message_log(f"HIGH_PICE={HIGH_PICE}-10")

    my_price = get_list_my_oder(sym)
    if len(my_price) <= 0:
        send_message_log(f"len(my_price) = {len(my_price)}")
        send_message_log ("- 0 return sell_Offsetting_Processing ------")
        return 0
# tmp_current 는 주식의 가장 낮은 가격을 구함
    tmp_current = my_price[-1]
# tmp_current_cnt는 매수한 주식의 총 수를 구함
    tmp_current_cnt = len(my_price)
    send_message_log(f"get_my_oder : tmp_current : {tmp_current}")
    send_message_log(f"get_my_oder : tmp_current_cnt : {tmp_current_cnt}")

    if tmp_current_cnt < 50:
# 보유 주식수가 50개 보다 작을 경우 상계 정상을 할 수 없다.
        send_message_log ("- 1 return sell_Offsetting_Processing ------")
        return 0


    current_price = get_current_price(sym)
# current_price는 현재 주식 가격을 구함
    send_message_log(f"{sym} : current_price : {current_price}")

    sumprice = tmp_current+HIGH_PICE
# sumprice는 최저가에 수익 금액을 더해 판매 초소 금액을 구한다.
    if (tmp_current+(HIGH_PICE-10)) > current_price:
# 주식의 최저가에 수익(HIGH_PICE-10)을 더한 값이 현재 주식 가격 보다 크다면 중지한다.
# 아직 current_price가 더 올라야 매도를 시도할 수 있다.
        send_message_log ( f"sel:1 {sumprice}({current_price}): {tmp_current}+{HIGH_PICE}")
        send_message_log ("- 2 return sell_Offsetting_Processing ------")
        return 0

    send_message_log ( f"sel:2 {sumprice}({current_price}): {tmp_current}+{HIGH_PICE}")

    is_exist = int(current_price) in my_price
    if is_exist:
# 현재 주식 가격과 같은 금액에 매수한 주식이 1개 이상 존재할 경우
# 상계 정산하지 않고 직접 매도 한다.
# 이미 주식을 충분히 보유하고 있어 상계 정산하지 않고 직접 매도 한다.
        my_price_count = my_price.count(int(current_price))
        send_message_log ( f"sel:3 my_price_count = {my_price_count}")
        if my_price_count > (MAX_BUY_CNT):
            send_message_log ( f"상계 매도 중지 2 (current_price={current_price}:{my_price_count})")
            return 0

        if current_price > my_price[20]:
# 현재가격이 상위 20개 보다 크면 매도한다. 고점 수익 실현
            send_message_log ( f"상계 매도 중지 3 (current_price={current_price}:{my_price_count})")
            return 0



    send_message_log_current ( f"sel:2 상계 매도 {sumprice}({current_price}): {tmp_current}+{HIGH_PICE}")
    send_message_log ( f"상계 매도 ({tmp_current}+({HIGH_PICE}-10)) < {current_price}")

    bak_current = tmp_current
    send_message_log ( "bak_current = tmp_current")
    send_message_log ( f"{bak_current} = {tmp_current}")
    tmp_current = set_my_oder(sym, current_price, "del")

    reinvest_price = int(HIGH_PICE//5)
    reinvest = my_oder_reinvest (sym, reinvest_price)

    buy_charge = int(current_price * (float(CHARGE) / 100))
    send_message ( f"{sym})상계 매도:{current_price}원({bak_current})({tmp_current_cnt}):reinvest({reinvest}) 수수료:{buy_charge}원")

    revenue_today = 0
    revenue_month = 0
    revenue_year = 0
    revenue_total = 0

    with open(revenue_today_file_name, 'r') as revenue_today_file_f:
        for line in revenue_today_file_f:
            tmp_line=line.strip()
            send_message_log (f"revenue_today_file_f = {tmp_line}")
            revenue_today = int(tmp_line)
            break

    with open(revenue_month_file_name, 'r') as revenue_month_file_f:
        for line in revenue_month_file_f:
            tmp_line=line.strip()
            send_message_log (f"revenue_month_file_f = {tmp_line}")
            revenue_month = int(tmp_line)
            break

    with open(revenue_year_file_name, 'r') as revenue_year_file_f:
        for line in revenue_year_file_f:
            tmp_line=line.strip()
            send_message_log (f"revenue_year_file_f = {tmp_line}")
            revenue_year = int(tmp_line)
            break

    with open(REVENUE_TOTAL_FILE_NAME, 'r') as revenue_total_file_f:
        for line in revenue_total_file_f:
            tmp_line=line.strip()
            send_message_log (f"revenue_total_file_f = {tmp_line}")
            revenue_total = int(tmp_line)
            break

    revenue_once = ( current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"수익:{revenue_once}원+투자:{reinvest}+수수료:{buy_charge}")
    revenue_today = revenue_today + ( current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"오늘수익:{revenue_today}원")
    with open(revenue_today_file_name, 'w') as revenue_today_file_f:
        revenue_today_file_f.write(str(revenue_today) + "\n")

    revenue_month = revenue_month + ( current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"월누적수익:{revenue_month}원")
    with open(revenue_month_file_name, 'w') as revenue_month_file_f:
        revenue_month_file_f.write(str(revenue_month) + "\n")

    revenue_year = revenue_year + ( current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"년누적수익:{revenue_year}원")
    with open(revenue_year_file_name, 'w') as revenue_year_file_f:
        revenue_year_file_f.write(str(revenue_year) + "\n")

    revenue_total = revenue_total + ( current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"누적수익:{revenue_total}원")
    with open(REVENUE_TOTAL_FILE_NAME, 'w') as revenue_total_file_f:
        revenue_total_file_f.write(str(revenue_total) + "\n")


    send_message_log_current ( f"{sym})상계 매도:{current_price}원({bak_current})({tmp_current_cnt}):reinvest({reinvest}) 수수료:{buy_charge}원")
    send_message_log_sale ( f"{sym})상계 매도:{current_price}원({bak_current})({tmp_current_cnt}):reinvest({reinvest}) 수수료:{buy_charge}원")

    # 상계 매수
    send_message_log ( "set_my_oder 1")
    tmp_current = set_my_oder(sym, current_price, "add")
    send_message( f"tmp_current: {tmp_current}")
    send_message_log_current( f"{sym})상계 매수:{current_price}원 ({tmp_current_cnt}) ")
    send_message_log_sale( f"{sym})상계 매수:{current_price}원 ({tmp_current_cnt}) ")
    send_message_log ( f"current_price:{current_price}")
    send_message( f"{sym})상계 매수:{current_price}원 ({tmp_current_cnt})")

    send_message_log ("- 5 return sell_Offsetting_Processing ------")
    return 1

##############################################################


##############################################################
##############################################################
def sell_stocks (sym):
    ###################################
    # 매도
    send_message_log("sell_stocks")
    send_message_log(f"HIGH_PICE={HIGH_PICE}")

    my_price = get_list_my_oder(sym)
    tmp_current_cnt = len(my_price)
    if tmp_current_cnt < 1:
        send_message_log ("- 1 return sell_stocks ------")
        return 0
    tmp_current = my_price[-1]
    send_message_log(f"get_my_oder : tmp_current : {tmp_current}")
    send_message_log(f"get_my_oder : tmp_current_cnt : {tmp_current_cnt}")



    current_price = get_current_price(sym)
    send_message_log(f"{sym} : current_price : {current_price}")

    sumprice = tmp_current+HIGH_PICE
    if (tmp_current+HIGH_PICE) > current_price:
# current_price가 수익 금액이 되지 않음
        send_message_log (f"sumprice = {sumprice}, {current_price-tmp_current}")
        send_message_log ("- 2 return sell_stocks ------")
        send_message_log ( f"chk:1 {sumprice}({current_price}): {tmp_current}+{HIGH_PICE}")
        send_message_log_current ( f"chk:1 {sumprice}({current_price}): {tmp_current}+{HIGH_PICE}")
        return 0

    send_message_log ( f"sel:3 {sumprice}({current_price}): {tmp_current}+{HIGH_PICE}")
    send_message_log_sale ( f"sel:3 {sumprice}({current_price}): {tmp_current}+{HIGH_PICE}")
    send_message_log_current ( f"sel:3 {sumprice}({current_price}): {tmp_current}+{HIGH_PICE}")
    send_message_log ( f"매도 ({tmp_current}+{HIGH_PICE}) < {current_price}")

    stock_cash, evl_amount, stock_qty, tot_evlu_amt = get_stock_balance_now (sym)
    send_message_log ( f"{sym}) 주식금액     : {stock_cash}")
    send_message_log ( f"{sym}) 주식평가금액 : {evl_amount}")
    send_message_log ( f"{sym}) 보유수량     : {stock_qty}")
    send_message_log ( f"{sym}) 총평가금액   : {tot_evlu_amt}")

    if stock_qty < 1:
        ###################################
        # 매도 수량 부족
        send_message( f"{sym}) 매도수량부족 : {current_price}원 :상승 {tmp_current}")
        send_message_log ("- 3 return sell_stocks ------")
        zero_set_my_oder(sym)
        return 0

    time.sleep(0.1)
    RET = sale(sym, "1")
    time.sleep(0.1)
    if RET is False:
        send_message( f"{sym}) 매도실패: {current_price}원 > {tmp_current}+{HIGH_PICE} 원")
        send_message_log ("- 4 return sell_stocks ------")
        return 0

    tmp_current_price = get_current_price(sym)
    send_message_log ( f"({sym}) 매도성공: {tmp_current_price}")
    while True:
        time.sleep(0.5)
        tmp_stock_cash, tmp_evl_amount, tmp_stock_qty, tmp_tot_evlu_amt = get_stock_balance_now (sym)
        send_message_log ( f"{sym} = tmp_evl_amount = {tmp_evl_amount}원 : tmp_stock_qty = {tmp_stock_qty}")
        if stock_qty > tmp_stock_qty:
            break

    send_message_log ( f"{sym}) 주식금액     : {tmp_stock_cash}")
    send_message_log ( f"{sym}) 주식평가금액 : {tmp_evl_amount}")
    send_message_log ( f"{sym}) 보유수량     : {tmp_stock_qty}")
    send_message_log ( f"{sym}) 총평가금액   : {tmp_tot_evlu_amt}")

    bak_current = tmp_current
    send_message_log ( "bak_current = tmp_current")
    send_message_log ( f"{bak_current} = {tmp_current}")
    tmp_current = set_my_oder(sym, tmp_current_price, "del")

    reinvest_price = int(HIGH_PICE//5)
    reinvest = my_oder_reinvest (sym, reinvest_price)

    buy_charge = int(tmp_current_price * (float(CHARGE) / 100))
    send_message ( f"{sym})매도:{tmp_current_price}원({bak_current})({tmp_stock_qty}):reinvest({reinvest}) 수수료:{buy_charge}원")

    revenue_today = 0
    revenue_month = 0
    revenue_year = 0
    revenue_total = 0

    with open(revenue_today_file_name, 'r') as revenue_today_file_f:
        for line in revenue_today_file_f:
            tmp_line=line.strip()
            send_message_log (f"revenue_today_file_f = {tmp_line}")
            revenue_today = int(tmp_line)
            break

    with open(revenue_month_file_name, 'r') as revenue_month_file_f:
        for line in revenue_month_file_f:
            tmp_line=line.strip()
            send_message_log (f"revenue_month_file_f = {tmp_line}")
            revenue_month = int(tmp_line)
            break

    with open(revenue_year_file_name, 'r') as revenue_year_file_f:
        for line in revenue_year_file_f:
            tmp_line=line.strip()
            send_message_log (f"revenue_year_file_f = {tmp_line}")
            revenue_year = int(tmp_line)
            break

    with open(REVENUE_TOTAL_FILE_NAME, 'r') as revenue_total_file_f:
        for line in revenue_total_file_f:
            tmp_line=line.strip()
            send_message_log (f"revenue_total_file_f = {tmp_line}")
            revenue_total = int(tmp_line)
            break

    revenue_once = ( tmp_current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"수익:{revenue_once}원+투자:{reinvest}+수수료:{buy_charge}")
    revenue_today = revenue_today + ( tmp_current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"오늘수익:{revenue_today}원")
    with open(revenue_today_file_name, 'w') as revenue_today_file_f:
        revenue_today_file_f.write(str(revenue_today) + "\n")

    revenue_month = revenue_month + ( tmp_current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"월누적수익:{revenue_month}원")
    with open(revenue_month_file_name, 'w') as revenue_month_file_f:
        revenue_month_file_f.write(str(revenue_month) + "\n")

    revenue_year = revenue_year + ( tmp_current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"년누적수익:{revenue_year}원")
    with open(revenue_year_file_name, 'w') as revenue_year_file_f:
        revenue_year_file_f.write(str(revenue_year) + "\n")

    revenue_total = revenue_total + ( tmp_current_price - bak_current ) - reinvest - buy_charge
    send_message ( f"누적수익:{revenue_total}원")
    with open(REVENUE_TOTAL_FILE_NAME, 'w') as revenue_total_file_f:
        revenue_total_file_f.write(str(revenue_total) + "\n")


    send_message_log_sale ( f"{sym})매도:{tmp_current_price}원({bak_current})({tmp_stock_qty}):reinvest({reinvest}) 수수료:{buy_charge}원")


    send_message_log ("- 5 return sell_stocks ------")
    return 1

##############################################################

def do_action(code):
    send_message_monitor (f"Action triggered at {datetime.datetime.now()}")
    my_price = get_list_my_oder(code)
    send_message_monitor( f"주식 코드: {code})")
    if len(my_price) > 0:
        send_message_monitor( f"최고금액 : {my_price[0]}원")
        send_message_monitor( f"최저금액 : {my_price[-1]}원")
        send_message_monitor( "장부주식수: "+ str(len(my_price)) +"개")
        sum_result = sum(my_price)
        send_message_monitor( f"장부총금액 : {sum_result}원")

    current_price = get_current_price(code)
    send_message_monitor( f"현재주식가: {current_price}원")



    stock_list, evaluation = get_stock_balance_now_struct (code)
    stock_dict = {}

    send_message_monitor ("===========================")
    for stock in stock_list:
        send_message_monitor (f" {stock['prdt_name']} : 상품명")
        #send_message_monitor (f" {stock['trad_dvsn_name']} : 매매구분명")
        send_message_monitor (f" {stock['bfdy_buy_qty']} : 전일매수수량")
        send_message_monitor (f" {stock['bfdy_sll_qty']} : 전일매도수량")
        send_message_monitor (f" {stock['thdt_buyqty']} : 금일매수수량")
        send_message_monitor (f" {stock['thdt_sll_qty']} : 금일매도수량")
        send_message_monitor (f" {stock['hldg_qty']} : 보유수량")
        #send_message_monitor (f" {stock['ord_psbl_qty']} : 주문가능수량")
        send_message_monitor (f" {stock['pchs_avg_pric']} : 매입평균가격")
        send_message_monitor (f" {stock['pchs_amt']} : 매입금액")
        send_message_monitor (f" {stock['prpr']} : 현재가")
        send_message_monitor (f" {stock['evlu_amt']} : 평가금액")
        #send_message_monitor (f" {stock['evlu_pfls_amt']} : 평가손익금액= 평가금액 - 매입금액")
        #send_message_monitor (f" {stock['evlu_pfls_rt']} : 평가손익율")
        send_message_monitor (f" {stock['fltt_rt']} : 등락율")
        send_message_monitor (f" {stock['bfdy_cprs_icdc']} : 전일대비증감")
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            #send_message_monitor (f"{stock['prdt_name']}:{stock['pdno']}={stock['hldg_qty']}주")
            time.sleep(0.1)
            if stock['pdno'] == code:
                break

    send_message_monitor (f" {evaluation[0]['dnca_tot_amt']} : 예수금총금액")
    send_message_monitor (f" {evaluation[0]['nxdy_excc_amt']} : 익일정산금액")
    send_message_monitor (f" {evaluation[0]['scts_evlu_amt']} : 유가평가금액")
    #send_message_monitor (f" {evaluation[0]['evlu_amt_smtl_amt']} : 평가금액합계금액")
    #send_message_monitor (f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    #send_message_monitor (f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    stock_cash = int(evaluation[0]['scts_evlu_amt']) - int(evaluation[0]['evlu_pfls_smtl_amt'])
    send_message_log( f"{sym} = stock_cash:{stock_cash}, 주식 평가 금액 - 평가 손익 합계")
    evaluation_cash = int(evaluation[0]['scts_evlu_amt'])
    send_message_log ( f"{sym}) 주식평가금액 : {evaluation_cash}")
    time.sleep(0.1)
    send_message_monitor(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.1)
    send_message_monitor("=================")

##############################################################
##############################################################
##############################################################
##############################################################
# 자동매매 시작
try:

    send_message_log ("===============================")
    send_message_log ("== AutoStock.py Start =========")


    if os.path.isfile("stop"):
        send_message( "Stop : stop에의해 중지합니다.")
        sys.exit()

    tmp_current={}
    tmp_current_cnt={}

    symbol_list = ["069500"] # 매수 희망 종목 리스트
    for sym in symbol_list:
        send_message_log ("===============================")
        organize_v1 (sym)

    t_now = datetime.datetime.now()
    t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
    t_8 = t_now.replace(hour=8, minute=0, second=0, microsecond=0)
    t_exit = t_now.replace(hour=15, minute=25, second=0,microsecond=0)
    today = datetime.datetime.today().weekday()
    if today in (5, 6):  # 토요일이나 일요일이면 자동 종료
        send_message_log ("1: 주말 입니다.")
        send_message_log ("1: == AutoStock.py Exit =========")
        sys.exit()



    now = datetime.datetime.now()
    revenue_today_file_name = "revenue_"+now.strftime("%Y%m%d")+".txt"
    revenue_month_file_name = "revenue_"+now.strftime("%Y%m")+".txt"
    revenue_year_file_name = "revenue_"+now.strftime("%Y")+".txt"
    REVENUE_TOTAL_FILE_NAME = "revenue_total.txt"
    t_now = datetime.datetime.now()
    if t_now < t_9 :  # AM 09:01 이전
        send_message ("5: 개장 전  입니다.")
        send_message_log ("2 == AutoStock.py Exit =========")
        #while True:
        #    t_now = datetime.datetime.now()
        #    if t_now > t_8 :  # PM 03:20 이후 :프로그램 종료
        #        break
        #    time.sleep(60)

        sys.exit ()

    if t_exit < t_now :  # PM 03:25 이후 :프로그램 종료
        send_message_log ( "6: 폐장 입니다.")
        send_message_log ("3 == AutoStock.py Exit =========")
        sys.exit ()


    if not os.path.exists(revenue_today_file_name):
        send_message_log (f"{revenue_today_file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(revenue_today_file_name, 'w') as f:
            f.write("0\n")

    if not os.path.exists(revenue_month_file_name):
        send_message_log (f"{revenue_month_file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(revenue_month_file_name, 'w') as f:
            f.write("0\n")

    if not os.path.exists(revenue_year_file_name):
        send_message_log (f"{revenue_year_file_name} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(revenue_year_file_name, 'w') as f:
            f.write("0\n")


    if not os.path.exists(REVENUE_TOTAL_FILE_NAME):
        send_message_log (f"{REVENUE_TOTAL_FILE_NAME} 파일이 존재하지 않습니다.")
        # 파일을 쓰기 모드('w')로 엽니다.
        with open(REVENUE_TOTAL_FILE_NAME, 'w') as f:
            f.write("0\n")


    ####################################
    # 직전 거래일의 가장 낮은 거래금액
    today_date = t_now.strftime("%Y%m%d")

    send_message_log(f"today_date:{today_date}")

    current_directory = os.getcwd()
    files = os.listdir(current_directory)

    send_message_log(type(files))

    files.sort()

    ####################################

    send_message ("===============================")
    send_message ("===국내 주식 자동매매 프로그램을 시작합니다===")

    ACCESS_TOKEN = load_access_token()

    if ACCESS_TOKEN and is_token_valid(ACCESS_TOKEN):
        send_message_log(f"기존 토큰 사용: {ACCESS_TOKEN}")
    else:
        send_message_log("토큰 발급...")
        ACCESS_TOKEN = get_access_token()
        send_message_log(f"새 토큰 발급: {ACCESS_TOKEN}")





    total_cash = get_balance() # 보유 현금 조회
    send_message_log (f"주문 가능 현금 잔고: {total_cash}원")
    #stock_dict = get_stock_balance() # 보유 주식 조회

    last_minute = None  # 이전에 동작한 분 정보를 저장

    for sym in symbol_list:
        send_message_log ("===============================")
        my_price = get_list_my_oder(sym)
        send_message_log ( "장부주식수: "+ str(len(my_price)) +"개")
        tmp_stock_cash, tmp_evl_amount, tmp_stock_qty, tmp_tot_evlu_amt = get_stock_balance_now (sym)
        send_message_log ( f"{sym} = tmp_stock_cash = {tmp_stock_cash}원 : tmp_stock_qty = {tmp_stock_qty}")


    while True:
        send_message_log ("===============================")
        send_message_log ("=== while loop ================")
        t_now = datetime.datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=29, second=0,microsecond=0)

        stop_file_name = "stop_"+now.strftime("%Y%m%d")
        if os.path.isfile(stop_file_name):
            send_message(f"Day Stop : {stop_file_name}에의해 중지합니다.")
            sys.exit()

        if os.path.isfile("stop"):
            send_message( "Stop : stop에의해 중지합니다.")
            sys.exit()

        today = datetime.datetime.today().weekday()
        if today in (5, 6):  # 토요일이나 일요일이면 자동 종료
            send_message( "2: 주말 입니다.")
            break

        if t_now < t_9 :  # AM 09:00 이전
            send_message( "3: 개장 전  입니다.")
            break

        if t_exit < t_now :  # PM 03:25 이후 :프로그램 종료
            send_message( "4: 폐장 입니다.")
            break

        for sym in symbol_list:
            # 분이 0 또는 30이고, 이전에 실행한 분이 아니라면 동작 수행
            if t_now.minute in [15, 45] and last_minute != t_now.minute:
                do_action(sym)
                last_minute = t_now.minute

            organize_v1 (sym)


            result_sell_1 = sell_Offsetting_Processing(sym)
            send_message_log(f"sell_Offsetting_Processing result_sell_1 = {result_sell_1}")
            if result_sell_1 == 1:
                continue
            send_message_log ("------------------------")

            result_sell = sell_stocks(sym)
            send_message_log(f"sell_stocks result_sell = {result_sell}")
            if result_sell == 1:
                continue
            send_message_log ("------------------------")

            result_buy = buy_stocks(sym)
            send_message_log(f"buy_stocks result_buy = {result_buy}")
            send_message_log ("------------------------")


            time.sleep(0.1)

        time.sleep(0.1)

    send_message ("4 == AutoStock.py Exit =========")

except Exception as error_msg:
    send_message( f"[오류 발생]{error_msg}")
    time.sleep(1)
    #if os.path.isfile(TOKEN_FILE):
    #    send_message_log(f"os.remove({TOKEN_FILE})")
    #    os.remove(TOKEN_FILE)











