import time
from machine import Pin, ADC
from neopixel import NeoPixel

# -------------------------------------------------------------
# 1. 하드웨어 설정 (WS2813 필수 타이밍 옵션 적용)
# -------------------------------------------------------------
TIMING = (280, 515, 515, 745)
NUM_LEDS = 10
led = NeoPixel(Pin(16), NUM_LEDS, timing=TIMING)

mq2 = ADC(Pin(26))  # A0 (GP26) 핀 연결

# -------------------------------------------------------------
# 2. 임계값 및 타이머 설정
# -------------------------------------------------------------
# TODO: 본인 환경의 MQ2 평소 수치(0~65535)를 측정한 뒤 기준값을 조절하세요.
AIR_THRESHOLD = 25000  

FOCUS_TIME_SEC = 25 * 60  # 25분 (테스트용으로 25초로 바꿔서 실험해 보세요)
REST_TIME_SEC = 5 * 60   # 5분 (테스트용으로 5초로 바꿔서 실험해 보세요)

# 색상 정의 (R, G, B)
COLOR_FOCUS = (0, 150, 0)     # 초록색 (집중 모드)
COLOR_ALERT = (255, 50, 0)    # 주황/빨간색 (공기질 악화 경고)
COLOR_REST = (0, 100, 255)    # 파란색 (휴식 모드)
COLOR_OFF = (0, 0, 0)

def set_led_gauge(count, color):
    """LED 10개 중 count개만큼 주어진 색상으로 켭니다."""
    for i in range(NUM_LEDS):
        if i < count:
            led[i] = color
        else:
            led[i] = COLOR_OFF
    led.write()

def blink_warning():
    """공기질 악화 시 주황/빨간색 경고 깜빡임"""
    for _ in range(3):
        set_led_gauge(NUM_LEDS, COLOR_ALERT)
        time.sleep(0.3)
        set_led_gauge(NUM_LEDS, COLOR_OFF)
        time.sleep(0.3)

# -------------------------------------------------------------
# 3. 메인 동작 루프 (포모도로 + 공기질 감지)
# -------------------------------------------------------------
while True:
    print("--- 25분 집중 모드 시작 ---")
    start_time = time.time()
    
    # [집중 모드 25분 진행]
    while time.time() - start_time < FOCUS_TIME_SEC:
        elapsed = time.time() - start_time
        remaining = FOCUS_TIME_SEC - elapsed
        
        # MQ2 센서 값 읽기 (16비트: 0~65535)
        air_val = mq2.read_u16()
        print(f"[집중 중] 남은 시간: {int(remaining)}초 | 공기 측정값: {air_val}")
        
        # 1. 공기질 악화 체크 (센서 수치가 기준을 넘었을 때)
        if air_val > AIR_THRESHOLD:
            print("⚠️ 경고: 공기질 악화! 환기가 필요합니다.")
            blink_warning()
            time.sleep(1)
            continue
            
        # 2. 정상 상태일 때: 시간에 따라 LED 게이지 줄어듦 (10칸 -> 0칸)
        # 25분 동안 남은 시간에 비례하여 LED 개수 계산
        gauge_count = int((remaining / FOCUS_TIME_SEC) * NUM_LEDS)
        if remaining > 0 and gauge_count == 0:
            gauge_count = 1  # 시간이 조금이라도 남았으면 최소 1칸 유지
            
        set_led_gauge(gauge_count, COLOR_FOCUS)
        time.sleep(1)

    # [휴식 모드 5분 진행]
    print("--- 5분 휴식 모드 시작 ---")
    rest_start = time.time()
    while time.time() - rest_start < REST_TIME_SEC:
        rest_elapsed = time.time() - rest_start
        rest_remaining = REST_TIME_SEC - rest_elapsed
        
        # 휴식 시간에는 파란색 게이지가 차오름
        gauge_count = int((rest_elapsed / REST_TIME_SEC) * NUM_LEDS)
        set_led_gauge(gauge_count, COLOR_REST)
        time.sleep(1)
