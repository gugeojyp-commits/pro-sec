import random
import requests
import json
import threading
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="국어 소리의 변동 평가 (2차시)",
    page_icon="✏️",
    layout="centered"
)

# -----------------------------------------------------------------------------
# ⚠️ 세션 강제 초기화 루틴 (버전 변경 시 캐시 리셋)
# -----------------------------------------------------------------------------
APP_VERSION = "v5_add_complex_coda_37q"
if st.session_state.get("app_version") != APP_VERSION:
    st.session_state.clear()
    st.session_state.app_version = APP_VERSION

# -----------------------------------------------------------------------------
# 🔗 [설정] 구글 시트 배포 URL 및 교사용 테스트 비밀번호
# -----------------------------------------------------------------------------
GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbymuGKCOqviCjqn3PEab4ubtf_m5cf1Gj184kGTgFqm0nBrOSKX7_oc9V_Wjv73AbGTAA/exec"
TEACHER_PASSWORD = "01063052122"
SHEET_TAB_NAME = "2차시"  # 📌 구글 스프레드시트 탭 이름

# 🚀 백그라운드 실시간 전송 함수 (화면 멈춤 방지)
def send_to_google_sheet_async(url, payload):
    if "여기에_배포_URL" in url or not url.startswith("https://script.google.com"):
        return
    try:
        requests.post(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=8
        )
    except Exception:
        pass

# -----------------------------------------------------------------------------
# 📚 2차시 퀴즈 데이터 (총 37문항 고정)
# -----------------------------------------------------------------------------
RAW_QUIZ_DATA = {
    "1. 소리의 동화 (구개음화, 비음화, 유음화)": [
        {
            "id": 1,
            "type": "short",
            "question": "음운과 음운이 만날 때, 한 음운이 다른 음운의 영향을 받아 그와 같거나 비슷하게 소리 나는 현상을 [     ]라 한다. 빈칸에 들어갈 올바른 개념을 쓰시오.",
            "answer": "동화",
            "explanation": "한 음운이 인접한 다른 음운의 영향을 받아 비슷하거나 동일하게 바뀌는 음운 변동 현상을 '동화'라고 합니다."
        },
        {
            "id": 2,
            "type": "choice",
            "question": "'구개음화'에 대한 설명으로 올바른 것을 고르시오.",
            "options": [
                "1. 'ㄷ, ㅌ'이 조사나 접미사의 모음 'ㅣ'를 만나 각각 [ㅈ, ㅊ]으로 바뀌는 현상이다.",
                "2. 'ㄷ, ㅌ'이 실질 형태소의 모음 'ㅣ'를 만날 때 일어난다."
            ],
            "answer": "1. 'ㄷ, ㅌ'이 조사나 접미사의 모음 'ㅣ'를 만나 각각 [ㅈ, ㅊ]으로 바뀌는 현상이다.",
            "explanation": "구개음화는 받침 'ㄷ, ㅌ'이 모음 'ㅣ'나 반모음 'j'로 시작하는 '형식 형태소(조사, 접미사)'를 만날 때 [ㅈ, ㅊ]으로 바뀌어 뒤 음절 첫소리로 옮겨 발음되는 현상입니다."
        },
        {
            "id": 3,
            "type": "short",
            "question": "'밭이'의 올바른 표준 발음을 쓰시오.",
            "answer": ["바치", "[바치]"],
            "explanation": "받침 'ㅌ' 뒤에 모음 'ㅣ'로 시작하는 조사(형식 형태소) '-이'가 결합하였으므로, 구개음화가 적용되어 [바치]로 발음합니다."
        },
        {
            "id": 4,
            "type": "choice",
            "question": "'닫히다'의 표준 발음 과정을 바르게 설명한 것을 고르시오.",
            "options": [
                "1. 'ㄷ'과 'ㅎ'이 만나 거센소리 [ㅌ]이 된 후, 모음 'ㅣ'를 만나 구개음화 [치]로 발음된다.",
                "2. 'ㄷ'이 먼저 구개음화가 일어나 [지]가 된 후 'ㅎ'과 합쳐진다."
            ],
            "answer": "1. 'ㄷ'과 'ㅎ'이 만나 거센소리 [ㅌ]이 된 후, 모음 'ㅣ'를 만나 구개음화 [치]로 발음된다.",
            "explanation": "'닫히다'는 거센소리되기(축약)로 [다티다]가 된 후, 'ㅌ'이 'ㅣ'를 만나 구개음화가 일어나 최종 [다치다]로 발음됩니다."
        },
        {
            "id": 5,
            "type": "choice",
            "question": "다음 중 '비음화'가 일어난 예시로만 짝지어진 것은?",
            "options": [
                "1. 굳이[구지], 신라[실라]",
                "2. 국물[궁물], 닫는[단는], 밥만[밤만]"
            ],
            "answer": "2. 국물[궁물], 닫는[단는], 밥만[밤만]",
            "explanation": "받침 'ㄱ, ㄷ, ㅂ'이 비음 'ㄴ, ㅁ' 앞에서 각각 비음인 [ㅇ, ㄴ, ㅁ]으로 바뀌어 소리 나는 현상을 '비음화'라고 합니다."
        },
        {
            "id": 6,
            "type": "choice",
            "question": "'ㄹ의 비음화'에 대한 설명으로 알맞은 것을 고르시오.",
            "options": [
                "1. 받침 'ㅁ, ㅇ' 뒤에 연결되는 'ㄹ'은 [ㄹ] 소리를 유지한다.",
                "2. 받침 'ㅁ, ㅇ' 또는 'ㄱ, ㅂ' 뒤에 연결되는 'ㄹ'은 [ㄴ]으로 발음된다."
            ],
            "answer": "2. 받침 'ㅁ, ㅇ' 또는 'ㄱ, ㅂ' 뒤에 연결되는 'ㄹ'은 [ㄴ]으로 발음된다.",
            "explanation": "받침 'ㅁ, ㅇ' 뒤 또는 'ㄱ, ㅂ' 뒤에 오는 'ㄹ'은 비음 [ㄴ]으로 바뀝니다. (예: 담력[담녁], 강릉[강능], 협력[협녁→혐녁])"
        },
        {
            "id": 7,
            "type": "choice",
            "question": "'유음화'의 원리로 올바른 것을 고르시오.",
            "options": [
                "1. 'ㄴ'은 'ㄹ'의 앞이나 뒤에서 [ㄹ]로 발음된다.",
                "2. 'ㄹ'은 'ㄴ'의 앞이나 뒤에서 [ㄴ]으로 발음된다."
            ],
            "answer": "1. 'ㄴ'은 'ㄹ'의 앞이나 뒤에서 [ㄹ]로 발음된다.",
            "explanation": "'ㄴ'이 유음 'ㄹ'을 앞이나 뒤에서 만나 [ㄹ]로 바뀌어 발음되는 현상을 '유음화'라고 합니다. (예: 신라[실라], 칼날[칼날])"
        },
        {
            "id": 8,
            "type": "short",
            "question": "예외 규정: 한자어 중 '생산량'과 '결단력'의 올바른 표준 발음을 순서대로 적으시오. (쉼표로 구분)",
            "answer": ["생산냥, 결딴녁", "생산냥,결딴녁", "[생산냥], [결딴녁]", "[생산냥],[결딴녁]"],
            "explanation": "일반적으로 'ㄴ+ㄹ'은 유음화되지만, 일부 한자어 합성어에서는 뒤의 'ㄹ'이 [ㄴ]으로 발음되는 예외가 있습니다."
        },
        {
            "id": 9,
            "type": "short",
            "question": "[바탕다지기] 문장의 밑줄 친 부분의 표준 발음을 순서대로 적으시오: '이 발은([ 1 ]) 누가 관리([ 2 ])해야 하는 것인지([ 3 ]) 협상했다.'",
            "answer": ["바른, 관리, 거신지", "바른,관리,거신지", "[바른], [관리], [거신지]", "바른관리거신지"],
            "explanation": "'발은'은 연음되어 [바른], '관리'는 유음화로 [관리], '것인지'는 연음되어 [거신지]로 발음합니다."
        },
        {
            "id": 10,
            "type": "short",
            "question": "[바탕다지기] 다음 문장 빈칸의 표준 발음을 적으시오: '이번에 제정된 대통령령([     ])을 발표하겠습니다.'",
            "answer": ["대통녕령", "대통녕녕", "[대통녕령]", "[대통녕녕]"],
            "explanation": "'대통령'에서 'ㅇ+ㄹ' 비음화로 [대통녕]이 되며, 뒤의 '령' 역시 비음화되어 최종적으로 [대통녕령](또는 관습상 [대통녕녕])으로 발음됩니다."
        },
        {
            "id": 11,
            "type": "short",
            "question": "[바탕다지기] 다음 문장 빈칸의 표준 발음을 적으시오: '층간 소음을 방지하기 위해 실내화([     ])를 신어야 합니다.'",
            "answer": ["실래화", "[실래화]"],
            "explanation": "'ㄹ+ㄴ' 유음화 조건에 따라 [실래화]로 발음하는 것이 올바른 표준 발음입니다."
        },
        {
            "id": 12,
            "type": "short",
            "question": "[바탕다지기] 다음 문장 빈칸의 표준 발음을 적으시오: '하고 싶은 말이 있으면 의견란([     ])에 자유롭게 남겨 주세요.'",
            "answer": ["의견난", "[의견난]"],
            "explanation": "한자어 '의견란'은 유음화가 일어나지 않고 뒤의 'ㄹ'이 비음 [ㄴ]으로 소리 나는 예외 단어로 [의견난]이 맞습니다."
        },
        {
            "id": 33,
            "type": "short",
            "question": "다음 단어의 표준 발음을 순서대로 적으시오: '닳는', '핥네' (쉼표로 구분)",
            "answer": ["달른, 할레", "달른,할레", "[달른], [할레]", "[달른],[할레]", "달른할레"],
            "explanation": "‘닳는’은 ‘ㅎ’이 탈락하고 앞의 유음 ‘ㄹ’에 의해 뒤의 비음 ‘ㄴ’이 유음화되어 [달른]으로 발음합니다. ‘핥네’ 역시 겹받침 단순화 및 유음화 과정을 거쳐 최종 [할레]로 발음합니다."
        },
        {
            "id": 34,
            "type": "short",
            "question": "‘ㄹ의 비음화’와 관련된 단어입니다. 다음 단어들의 표준 발음을 순서대로 적으시오: '담력', '석류', '협력' (쉼표로 구분)",
            "answer": [
                "담녁, 성뉴, 혐녁", "담녁,성뉴,혐녁", 
                "[담녁], [성뉴], [혐녁]", "[담녁],[성뉴],[혐녁]", 
                "담녁성뉴혐녁"
            ],
            "explanation": "'담력'은 받침 'ㅁ' 뒤의 'ㄹ'이 비음화되어 [담녁], '석류'와 '협력'은 뒤의 'ㄹ'이 먼저 [ㄴ]으로 바뀐 후 앞의 자음이 영향을 받아 상호 비음화되어 각각 [성뉴], [혐녁]으로 발음됩니다."
        }
    ],
    "2. 된소리되기 (경음화)": [
        {
            "id": 13,
            "type": "choice",
            "question": "'된소리되기'의 기본 원칙으로 알맞지 않은 것을 고르시오.",
            "options": [
                "1. 받침 'ㄱ, ㄷ, ㅂ' 뒤에 연결되는 'ㄱ, ㄷ, ㅂ, ㅅ, ㅈ'은 된소리로 발음한다.",
                "2. 어간 받침 'ㄴ, ㅁ' 뒤에 결합하는 어미의 첫소리는 된소리로 발음한다.",
                "3. 어간 받침 'ㄴ, ㅁ' 뒤에 피동, 사동 접미사 '-기-'가 오면 된소리로 발음한다."
            ],
            "answer": "3. 어간 받침 'ㄴ, ㅁ' 뒤에 피동, 사동 접미사 '-기-'가 오면 된소리로 발음한다.",
            "explanation": "어간 받침 'ㄴ, ㅁ' 뒤에 피동, 사동 접미사 '-기-'가 올 때는 된소리되기가 일어나지 않고 예사소리 그대로 발음합니다. (예: 안기다[안기다], 신기다[신기다])"
        },
        {
            "id": 14,
            "type": "short",
            "question": "한자어에서 'ㄹ' 받침 뒤에 올 때 된소리로 발음되는 자음 3개를 쓰시오. (쉼표로 구분, 예: ㄱ, ㄴ, ㄷ)",
            "answer": ["ㄷ, ㅅ, ㅈ", "ㄷ,ㅅ,ㅈ", "ㄷ, ㅈ, ㅅ", "ㄷ,ㅈ,ㅅ", "ㅅ, ㄷ, ㅈ", "ㅅ,ㄷ,ㅈ", "ㅈ, ㅅ, ㄷ", "ㅈ,ㅅ,ㄷ", "ㅈ, ㄷ, ㅅ", "ㅈ,ㄷ,ㅅ"],
            "explanation": "한자어에서 'ㄹ' 받침 뒤에 결합하는 'ㄷ, ㅅ, ㅈ'은 된소리 [ㄸ, ㅆ, ㅉ]으로 발음합니다. (예: 갈등[갈뜨], 일시[일씨], 발전[발쩐])"
        },
        {
            "id": 15,
            "type": "choice",
            "question": "다음 중 된소리되기가 적용되지 않는 단어는?",
            "options": [
                "1. 허허실실",
                "2. 갈등",
                "3. 할 것을"
            ],
            "answer": "1. 허허실실",
            "explanation": "같은 한자가 겹쳐진 단어(허허실실, 절절하다 등)는 된소리로 발음하지 않고 예사소리로 발음합니다."
        },
        {
            "id": 16,
            "type": "choice",
            "question": "관형사형 어미 '-(으)ㄹ' 뒤에 오는 'ㄱ, ㄷ, ㅂ, ㅅ, ㅈ'의 발음 규칙으로 올바른 것은?",
            "options": [
                "1. 예사소리로 발음한다.",
                "2. 된소리로 발음한다."
            ],
            "answer": "2. 된소리로 발음한다.",
            "explanation": "관형사형 어미 '-(으)ㄹ' 뒤에 연결되는 예사소리는 된소리로 발음합니다. (예: 할 것을[할꺼슬], 만날 사람[만날싸람])"
        },
        {
            "id": 17,
            "type": "short",
            "question": "[바탕다지기] 밑줄 친 단어의 발음을 순서대로 적으시오: '주민 신고([ 1 ])가 들어와서 신발을 신고([ 2 ]) 출동([ 3 ])했다.'",
            "answer": ["신고, 신꼬, 출똥", "신고,신꼬,출똥", "[신고], [신꼬], [출똥]", "신고신꼬출똥"],
            "explanation": "명사 '신고'는 [신고], 동사 어간 뒤 어미 '신-+-고'는 [신꼬], 한자어 'ㄹ' 받침 뒤 'ㄷ'은 [출똥]으로 발음합니다."
        },
        {
            "id": 18,
            "type": "short",
            "question": "[바탕다지기] 밑줄 친 단어의 발음을 순서대로 적으시오: '내가 집에 남기로([ 1 ]) 해서 가족들은 나를 남기고([ 2 ]) 집을 떠났다.'",
            "answer": ["남끼로, 남기고", "남끼로,남기고", "[남끼로], [남기고]", "남끼로남기고"],
            "explanation": "'남다' 어간 받침 뒤 어미 '-기-'는 된소리 [남끼로], 사동 접미사 '-기-'가 결합한 '남기다'는 예사소리 [남기고]로 발음합니다."
        },
        {
            "id": 19,
            "type": "choice",
            "question": "다음 단어의 올바른 발음을 고르시오: ‘덮개’",
            "options": [
                "1. [덥개]",
                "2. [덥깨]"
            ],
            "answer": "2. [덥깨]",
            "explanation": "받침 'ㅍ'이 음절 끝소리 규칙으로 [ㅂ]이 되고, 'ㅂ' 뒤 예사소리 'ㄱ'이 된소리가 되어 최종 [덥깨]로 발음합니다."
        },
        {
            "id": 20,
            "type": "choice",
            "question": "다음 단어의 올바른 발음을 고르시오: ‘핥다’",
            "options": [
                "1. [할따]",
                "2. [할타]"
            ],
            "answer": "1. [할따]",
            "explanation": "겹받침 'ㄾ'에서 대표음 [ㄹ]이 남고, 뒤의 어미 'ㄷ'이 된소리로 변동되어 [할따]로 발음합니다."
        },
        {
            "id": 37,
            "type": "short",
            "question": "다음 겹받침 단어들의 올바른 표준 발음을 순서대로 적으시오: '넓게', '핥다', '훑소', '떫지' (쉼표로 구분)",
            "answer": [
                "널께, 할따, 훌쏘, 떨찌", "널께,할따,훌쏘,떨찌",
                "[널께], [할따], [훌쏘], [떨찌]", "[널께],[할따],[훌쏘],[떨찌]",
                "널께할따훌쏘떨찌"
            ],
            "explanation": "용언 어간의 겹받침 ‘ㄼ, ㄾ’은 자음 앞에서 원칙적으로 [ㄹ]로 발음됩니다(탈락). 이어지는 어미의 첫소리 ‘ㄱ, ㄷ, ㅅ, ㅈ’은 된소리로 바뀌므로 각각 [널께], [할따], [훌쏘], [떨찌]로 발음합니다."
        }
    ],
    "3. 소리의 첨가 & 반모음 관련 발음": [
        {
            "id": 21,
            "type": "choice",
            "question": "'ㄴ 첨가'가 일어나는 환경 조건으로 올바른 것을 고르시오.",
            "options": [
                "1. 합성어나 파생어에서 앞 단어 끝이 자음이고 뒤 단어가 '이, 야, 여, 요, 유'로 시작할 때",
                "2. 모든 단어에서 모음 뒤에 '이, 야, 여, 요, 유'가 올 때"
            ],
            "answer": "1. 합성어나 파생어에서 앞 단어 끝이 자음이고 뒤 단어가 '이, 야, 여, 요, 유'로 시작할 때",
            "explanation": "ㄴ 첨가는 합성어나 파생어에서 앞 말의 끝이 자음(받침)이고, 뒷말의 첫음절이 '이, 야, 여, 요, 유'일 때 발생합니다."
        },
        {
            "id": 22,
            "type": "choice",
            "question": "'솜이불'의 음운 변동 과정과 최종 발음이 바르게 연결된 것을 고르시오.",
            "options": [
                "1. ㄴ 첨가 → [솜니불]",
                "2. 연음 현상 → [소미불]"
            ],
            "answer": "1. ㄴ 첨가 → [솜니불]",
            "explanation": "합성어 '솜+이불'에서 자음 받침 뒤 모음 '이'가 왔으므로 'ㄴ'이 첨가되어 [솜니불]로 발음합니다."
        },
        {
            "id": 23,
            "type": "choice",
            "question": "'막일'의 발음 변화 과정을 순서대로 바르게 설명한 것은?",
            "options": [
                "1. ㄴ 첨가 [막닐] → 비음화 [망닐]",
                "2. 비음화 [망일] → ㄴ 첨가 [망닐]"
            ],
            "answer": "1. ㄴ 첨가 [막닐] → 비음화 [망닐]",
            "explanation": "'막+일'에서 먼저 ㄴ 첨가가 일어나 [막닐]이 되고, 'ㄱ'이 비음 'ㄴ'을 만나 비음화되어 최종 [망닐]이 됩니다."
        },
        {
            "id": 24,
            "type": "short",
            "question": "'알약'의 최종 표준 발음을 쓰시오.",
            "answer": ["알략", "[알략]"],
            "explanation": "'알+약'에서 ㄴ 첨가로 [알냑]이 된 후, 앞의 유음 'ㄹ'로 인해 유음화가 일어나 최종 [알략]이 됩니다."
        },
        {
            "id": 25,
            "type": "choice",
            "question": "다음 중 'ㄴ 첨가' 환경이지만 ㄴ을 첨가하여 발음하지 않는 예외 단어는?",
            "options": [
                "1. 맨입",
                "2. 송별연"
            ],
            "answer": "2. 송별연",
            "explanation": "'송별연[송별연]', '등용문[등용문]' 등은 ㄴ 첨가 환경이지만 표기대로 연음하여 발음하는 관습적 예외입니다."
        },
        {
            "id": 26,
            "type": "choice",
            "question": "용언의 어간 끝 'ㅣ, ㅚ, ㅟ' 뒤에 어미 '-어/-오'가 올 때의 발음 허용 규정으로 알맞은 것은?",
            "options": [
                "1. [어], [오]로 발음하는 것이 원칙이나, 반모음 'j'가 첨가된 [여], [요] 발음도 허용한다.",
                "2. 오직 [여], [요]로만 발음해야 한다."
            ],
            "answer": "1. [어], [오]로 발음하는 것이 원칙이나, 반모음 'j'가 첨가된 [여], [요] 발음도 허용한다.",
            "explanation": "'피어' -> [피어](원칙)/[피여](허용), '되어' -> [되어](원칙)/[되여](허용)처럼 반모음 'j' 첨가 발음도 표준으로 허용합니다."
        },
        {
            "id": 27,
            "type": "choice",
            "question": "다음 중 반모음 'j' 첨가를 표준 발음으로 인정하지 않는 경우는?",
            "options": [
                "1. 'ㅐ, ㅔ'로 끝나는 어간 뒤 (예: 세어, 깨어)",
                "2. 'ㅣ, ㅚ'로 끝나는 어간 뒤 (예: 피어, 되어)"
            ],
            "answer": "1. 'ㅐ, ㅔ'로 끝나는 어간 뒤 (예: 세어, 깨어)",
            "explanation": "'ㅐ, ㅔ' 뒤에 반모음 'j'가 첨가되어 [세여], [깨여]로 발음하는 것은 표준 발음으로 인정하지 않습니다."
        },
        {
            "id": 28,
            "type": "choice",
            "question": "용언 활용형에 나타나는 '져, 쪄, 처'의 발음 규칙에 대한 설명으로 올바른 것은?",
            "options": [
                "1. 반모음 'j'를 탈락시켜 단모음인 [저, 쩌, 처]로 발음한다.",
                "2. 이중 모음 그대로 [져, 쪄, 쳐]로만 발음해야 한다."
            ],
            "answer": "1. 반모음 'j'를 탈락시켜 단모음인 [저, 쩌, 처]로 발음한다.",
            "explanation": "용언의 활용형에서 '져, 쪄, 처'는 이중 모음이 아닌 단모음 [저, 쩌, 처]로 발음합니다. (예: 가져[가저], 쪄[쩌], 다쳐[다처])"
        },
        {
            "id": 29,
            "type": "short",
            "question": "[바탕다지기] 문장의 괄호 안 알맞은 발음을 순서대로 적으시오: '색연필([ 1 ])로 꽃잎([ 2 ])도 그렸다.'",
            "answer": ["생년필, 꼰닙", "생년필,꼰닙", "[생년필], [꼰닙]", "[생년필],[꼰닙]"],
            "explanation": "'색연필'은 ㄴ첨가 및 비음화로 [생년필], '꽃잎'은 끝소리/ㄴ첨가 및 비음화로 [꼰닙]이 됩니다."
        },
        {
            "id": 30,
            "type": "choice",
            "question": "[바탕다지기] 다음 문장의 밑줄 친 부분의 올바른 발음 규정은? '정원에 피어 있는 꽃에 벌이 기어다닌다.'",
            "options": [
                "1. [피어], [기어다닌다]만 표준 발음이다.",
                "2. 원칙 발음 [피어]/[기어다닌다]와 반모음이 첨가된 [피여]/[기여다닌다] 둘 다 표준 발음이다."
            ],
            "answer": "2. 원칙 발음 [피어]/[기어다닌다]와 반모음이 첨가된 [피여]/[기여다닌다] 둘 다 표준 발음이다.",
            "explanation": "어간 모음 'ㅣ' 뒤에 어미 '-어'가 결합할 때는 [어]가 원칙이나 반모음 'j'가 첨가된 [여] 발음도 표준 발음으로 허용됩니다."
        },
        {
            "id": 31,
            "type": "short",
            "question": "[바탕다지기] 문장의 밑줄 친 단어의 올바른 발음을 순서대로 적으시오: '친구네 만두를 가져가서([ 1 ]) 맛있게 쪄([ 2 ]) 먹었다.'",
            "answer": ["가저가서, 쩌", "가저가서,쩌", "[가저가서], [쩌]", "[가저가서],[쩌]"],
            "explanation": "'져, 쪄, 처'는 단모음화되어 각각 [가저가서], [쩌]로 발음합니다."
        },
        {
            "id": 32,
            "type": "choice",
            "question": "'한여름'의 표준 발음으로 올바른 것을 고르시오.",
            "options": [
                "1. [하녀름]",
                "2. [한녀름]"
            ],
            "answer": "2. [한녀름]",
            "explanation": "접두사 '한-'과 '여름'이 결합한 파생어로, 자음 뒤 '여' 앞에서 'ㄴ'이 첨가되어 [한녀름]으로 발음합니다."
        },
        {
            "id": 35,
            "type": "short",
            "question": "다음 단어의 표준 발음을 순서대로 적으시오: '내복약', '식용유' (쉼표로 구분)",
            "answer": [
                "내봉냑, 시굥유", "내봉냑,시굥유", 
                "[내봉냑], [시굥유]", "[내봉냑],[시굥유]", 
                "내봉냑시굥유"
            ],
            "explanation": "'내복약'은 '내복+약'의 합성어로 'ㄴ 첨가' 후 비음화가 일어나 [내봉냑]이 됩니다. 반면 '식용유'는 ㄴ 첨가가 일어나지 않고 앞 자음이 그대로 연음되어 [시굥유]로 발음하는 것이 표준입니다."
        },
        {
            "id": 36,
            "type": "choice",
            "question": "'물엿'의 표준 발음 도출 과정을 순서대로 바르게 나타낸 것은?",
            "options": [
                "1. ㄴ 첨가 [물녯] → 유음화 및 음절 끝소리 규칙 [물렫]",
                "2. 연음 현상 [무렷] → 음절 끝소리 규칙 [무렫]"
            ],
            "answer": "1. ㄴ 첨가 [물녯] → 유음화 및 음절 끝소리 규칙 [물렫]",
            "explanation": "'물+엿'은 복합어로 앞말이 자음이고 뒷말이 '여'로 시작하여 먼저 'ㄴ'이 첨가([물녯])된 후, 앞말의 유음 'ㄹ' 영향으로 유음화가 일어나 최종 [물렫]으로 발음됩니다."
        }
    ]
}

def clean_text(text):
    if isinstance(text, list):
        return [t.replace(" ", "").replace("[", "").replace("]", "").replace(".", ",").replace("/", ",") for t in text]
    return text.replace(" ", "").replace("[", "").replace("]", "").replace(".", ",").replace("/", ",")

# -----------------------------------------------------------------------------
# 1. 초기 퀴즈 세팅
# -----------------------------------------------------------------------------
def reset_full_quiz():
    shuffled_list = []
    for category_name, items in RAW_QUIZ_DATA.items():
        category_items = items.copy()
        random.shuffle(category_items)
        for item in category_items:
            item_copy = item.copy()
            item_copy["category"] = category_name
            shuffled_list.append(item_copy)
            
    st.session_state.quiz_list = shuffled_list
    st.session_state.current_index = 0
    st.session_state.user_answers = {}
    st.session_state.passed_status = {}
    st.session_state.checked_status = {}
    st.session_state.first_attempt_status = {}
    st.session_state.quiz_finished = False
    st.session_state.sheet_submitted = False

if "student_id" not in st.session_state:
    st.session_state.student_id = ""
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "user_info_submitted" not in st.session_state:
    st.session_state.user_info_submitted = False

# 총 문항 수(37개) 반영
if "quiz_list" not in st.session_state or len(st.session_state.quiz_list) != 37:
    reset_full_quiz()

st.title("✏️ [국어] 소리의 변동 형성평가 (2차시), 90~93쪽")

# -----------------------------------------------------------------------------
# 2. 학생 정보 입력 화면
# -----------------------------------------------------------------------------
if not st.session_state.user_info_submitted:
    st.subheader("👤 감일고 학생 정보 입력 (2차시)")
    st.write("학번과 이름을 정확히 입력하세요. 잘못 기재하면 참여하지 않은 것으로 처리됩니다. (총 37문항)")
    
    with st.form(key="student_info_form"):
        s_id = st.text_input("학번을 입력하세요. (예: 20101)", key="input_s_id")
        s_name = st.text_input("이름을 입력하세요.", key="input_s_name")
        start_button = st.form_submit_button("🚀 2차시 평가 시작하기 (Enter)", use_container_width=True)
        
        if start_button:
            if s_id.strip() and s_name.strip():
                st.session_state.student_id = s_id.strip()
                st.session_state.student_name = s_name.strip()
                st.session_state.user_info_submitted = True
                st.rerun()
            else:
                st.warning("⚠️ 학번과 이름을 모두 입력해 주세요!")

# -----------------------------------------------------------------------------
# 3. 개별 문제 풀이 화면 (st.form으로 엔터키 자동 제출 활성화)
# -----------------------------------------------------------------------------
elif not st.session_state.quiz_finished:
    quiz_list = st.session_state.quiz_list
    total_q = len(quiz_list)
    curr_idx = st.session_state.current_index
    curr_q = quiz_list[curr_idx]

    col_info, col_prog = st.columns([1, 1])
    with col_info:
        st.write(f"👤 **학생:** {st.session_state.student_name} ({st.session_state.student_id})")
    with col_prog:
        st.write(f"🎯 **진행:** {curr_idx + 1} / {total_q} 문항")
    
    st.progress((curr_idx + 1) / total_q)
    st.write("")

    # 1번 문제에서 바로 교사용 점프 기능 제공
    if curr_idx == 0:
        c1, c2 = st.columns([3, 1])
        with c1:
            pw_input = st.text_input("확인", type="password", key="quick_admin_pw", label_visibility="collapsed", placeholder="교사 비번")
        with c2:
            if st.button("결과확인", key="quick_jump_btn", use_container_width=True):
                if pw_input == TEACHER_PASSWORD:
                    st.session_state.quiz_finished = True
                    st.rerun()
                else:
                    st.error("비밀번호 불일치")
        st.write("---")

    st.caption(f"📌 {curr_q['category']}")
    st.subheader(f"Q{curr_idx + 1}. {curr_q['question']}")

    saved_ans = st.session_state.user_answers.get(curr_q["id"], "")
    
    # ── [엔터키 지원] Form 블록으로 묶기 ──
    with st.form(key=f"quiz_form_{curr_q['id']}"):
        if curr_q["type"] == "short":
            user_input = st.text_input(
                "정답 입력:", 
                value=saved_ans, 
                placeholder="답안을 입력하고 Enter를 누르세요...", 
                key=f"q_input_{curr_q['id']}"
            )
        else:
            opts = curr_q["options"]
            default_idx = opts.index(saved_ans) if saved_ans in opts else None
            user_input = st.radio(
                "알맞은 답 선택:", 
                opts, 
                index=default_idx, 
                key=f"q_input_{curr_q['id']}", 
                label_visibility="collapsed"
            )

        st.write("")
        form_submitted = st.form_submit_button("🔍 정답 확인 (Enter)", use_container_width=True)

    # 채점 로직 (Enter를 치거나 확인 버튼 클릭 시 실행)
    if form_submitted:
        if user_input:
            st.session_state.user_answers[curr_q["id"]] = user_input
            st.session_state.checked_status[curr_q["id"]] = True
            
            correct = curr_q["answer"]
            if curr_q["type"] == "short":
                cleaned_user = clean_text(user_input)
                cleaned_correct = clean_text(correct)
                is_correct = (cleaned_user in cleaned_correct) if isinstance(cleaned_correct, list) else (cleaned_user == cleaned_correct)
            else:
                is_correct = (user_input == correct)
            
            if curr_q["id"] not in st.session_state.first_attempt_status:
                st.session_state.first_attempt_status[curr_q["id"]] = is_correct

            st.session_state.passed_status[curr_q["id"]] = is_correct
            st.rerun()
        else:
            st.warning("⚠️ 먼저 정답을 입력하거나 선택해 주세요.")

    # 해설 및 다음 문제 이동 버튼 출력부
    if st.session_state.checked_status.get(curr_q["id"], False):
        ans = st.session_state.user_answers.get(curr_q["id"], "")
        is_passed = st.session_state.passed_status.get(curr_q["id"], False)
        
        if is_passed:
            st.success("🎉 **정답입니다! 통과하셨습니다.**")
        else:
            st.error(f"❌ **오답입니다. 해설을 확인하고 정답을 맞춰 다음으로 이동하세요.** (입력한 답: {ans})")
        
        st.info(f"💡 **교과서 원리 해설:**\n\n{curr_q['explanation']}")

        st.write("")
        if is_passed:
            if curr_idx < total_q - 1:
                if st.button("➡️ 다음 문제로 이동", use_container_width=True):
                    st.session_state.current_index += 1
                    st.rerun()
            else:
                if st.button("🏁 모든 문제 완료! 최종 결과 확인하기", use_container_width=True):
                    st.session_state.quiz_finished = True
                    st.rerun()
        else:
            st.caption("🔒 **정답을 맞혀야 다음 문제로 넘어갈 수 있습니다.**")

# -----------------------------------------------------------------------------
# 4. 최종 완료 화면 (2차시 시트 전송)
# -----------------------------------------------------------------------------
else:
    wrong_q_list = [q for q in st.session_state.quiz_list if not st.session_state.first_attempt_status.get(q["id"], False)]
    total_count = len(st.session_state.quiz_list)
    correct_count = total_count - len(wrong_q_list)
    wrong_ids_str = ", ".join([str(q["id"]) for q in wrong_q_list]) if wrong_q_list else "없음"

    # 🚀 백그라운드 스레드로 비동기 전송 ('2차시' 탭 식별 파라미터 포함)
    if st.session_state.student_id and not st.session_state.get("sheet_submitted", False):
        payload = {
            "sheet_name": SHEET_TAB_NAME,
            "round": SHEET_TAB_NAME,
            "student_id": st.session_state.student_id,
            "student_name": st.session_state.student_name,
            "score": correct_count,
            "total": total_count,
            "wrong_questions": wrong_ids_str
        }
        st.session_state.sheet_submitted = True
        threading.Thread(
            target=send_to_google_sheet_async,
            args=(GOOGLE_SHEET_WEBAPP_URL, payload),
            daemon=True
        ).start()

    st.header(f"🎉 {st.session_state.student_name or '선생님'} 님, 2차시 평가 완료!")
    st.subheader(f"첫 시도 정답: {total_count}문항 중 {correct_count}개")
    st.write(f"평가 결과는 **구글 시트 [{SHEET_TAB_NAME}] 기록부에 자동 저장**됩니다.")
    st.write("---")

    tab1, tab2 = st.tabs(["📊 나의 결과 & 오답노트", f"📚 전체 {total_count}문항 다시 복습하기"])

    with tab1:
        if len(wrong_q_list) > 0:
            st.warning(f"⚠️ 처음 시도에서 틀렸던 문제가 **{len(wrong_q_list)}개** 있습니다.")
            if st.button("🔥 처음 틀렸던 문제만 오답노트로 다시 풀기", use_container_width=True):
                st.session_state.quiz_list = wrong_q_list.copy()
                st.session_state.current_index = 0
                st.session_state.user_answers = {}
                st.session_state.passed_status = {}
                st.session_state.checked_status = {}
                st.session_state.first_attempt_status = {}
                st.session_state.quiz_finished = False
                st.session_state.sheet_submitted = True
                st.rerun()
        else:
            st.success("💯 첫 번째 시도에서 모든 문제를 완벽하게 맞혔습니다!")

        st.write("")
        with st.expander("🔄 처음부터 전체 문제 다시 시작하기"):
            if st.button("초기화 후 새로 시작하기", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    with tab2:
        st.info(f"💡 전체 {total_count}개 문항을 자율적으로 다시 연습하고, 아래 [정답 및 해설]을 열어 확인하세요.")
        
        all_questions = []
        for cat, items in RAW_QUIZ_DATA.items():
            for item in items:
                all_questions.append((cat, item))

        for idx, (category_name, q) in enumerate(all_questions):
            st.write(f"**[{category_name}] {idx + 1}. {q['question']}**")
            
            if q["type"] == "short":
                st.text_input("답안 연습:", placeholder="답안을 직접 적어보세요...", key=f"all_view_input_{q['id']}")
            else:
                st.radio("답안 연습:", q["options"], index=None, key=f"all_view_opt_{q['id']}", label_visibility="collapsed")
            
            with st.expander(f"Q{idx + 1} 정답 및 해설 확인"):
                ans_display = q['answer'] if isinstance(q['answer'], str) else q['answer'][0]
                st.write(f"**정답:** `{ans_display}`")
                st.write(f"**💡 해설:** {q['explanation']}")
            st.write("---")
