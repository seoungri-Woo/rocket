import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 페이지 환경 설정 ---
st.set_page_config(
    page_title="Rocket Launch & Orbit Simulator",
    page_icon="🚀",
    layout="wide"
)

# --- 물리 및 천문 기본 상수 ---
G0 = 9.81           # 중력가속도 (m/s^2)
R_EARTH = 6371000.0 # 지구 반지름 (m)
RHO_0 = 1.225       # 대기 밀도 (kg/m^3)
SCALE_HEIGHT = 8500 # 대기 밀도 감소 고도 (m)
ORBIT_ALT_TARGET = 200.0 # 목표 저궤도 고도 (km)
ORBIT_VEL_TARGET = 7.79  # 목표 궤도 속도 (km/s)

# --- 시뮬레이션 물리 연산 엔진 ---
def run_rocket_simulation(payload_kg, s1_fuel_t, s1_isp, s1_thrust_kn, s2_fuel_t, s2_isp, s2_thrust_kn):
    """
    치올콥스키 로켓 방정식 및 2단계 중력/항력 손실을 포함한 궤도 투입 시뮬레이터
    """
    try:
        # 단위 변환 (톤 -> kg, kN -> N)
        s1_fuel = s1_fuel_t * 1000.0
        s2_fuel = s2_fuel_t * 1000.0
        s1_thrust = s1_thrust_kn * 1000.0
        s2_thrust = s2_thrust_kn * 1000.0
        
        # 구조체 중량 추정 (연료 중량의 10%)
        s1_struct = s1_fuel * 0.1
        s2_struct = s2_fuel * 0.1
        m_total = payload_kg + s1_struct + s1_fuel + s2_struct + s2_fuel

        # 연소 시간 및 연료 분사율 계산
        ve1 = s1_isp * G0
        m_dot1 = s1_thrust / ve1
        t_burn1 = s1_fuel / m_dot1

        ve2 = s2_isp * G0
        m_dot2 = s2_thrust / ve2
        t_burn2 = s2_fuel / m_dot2

        # 변수 초기화
        dt = 0.5
        t = 0.0
        h = 0.0
        v = 0.0
        m_curr = m_total

        # 타임라인 데이터 저장 리스트
        t_list, h_list, v_list, m_list, g_list, stage_list = [], [], [], [], [], []

        # 물리 계산 루프 (최대 600초 또는 지표면 추락 전까지)
        while t < (t_burn1 + t_burn2 + 300) and h >= 0:
            # 고도에 따른 중력 가속도 산출
            g = G0 * (R_EARTH / (R_EARTH + h)) ** 2
            
            # 대기 밀도 및 공기저항 산출 (100km 이상은 진공)
            rho = RHO_0 * np.exp(-h / SCALE_HEIGHT) if h < 100000 else 0.0
            f_drag = 0.5 * rho * (v ** 2) * 10.0 * 0.5 # 단면적 10m^2, 항력계수 0.5

            # 단별 추력 및 중량 업데이트 (Staging)
            if t < t_burn1:
                thrust = s1_thrust
                m_curr = m_total - (m_dot1 * t)
                stage_name = "1단 연소"
            elif t < t_burn1 + 5: # 1단 분리 대기 (5초)
                thrust = 0.0
                m_curr = payload_kg + s2_struct + s2_fuel
                stage_name = "1단 분리 / 관성 비행"
            elif t < t_burn1 + 5 + t_burn2:
                t2 = t - (t_burn1 + 5)
                thrust = s2_thrust
                m_curr = (payload_kg + s2_struct + s2_fuel) - (m_dot2 * t2)
                stage_name = "2단 연소"
            else:
                thrust = 0.0
                m_curr = payload_kg + s2_struct
                stage_name = "관성 비행"

            # Gravity Turn (피치 각도 제어: 고도 증가에 따른 수평 기우림)
            if h < 1000:
                pitch = 90.0 # 수직 상승
            elif h < 80000:
                pitch = max(5.0, 90.0 - ((h - 1000) / 79000.0) * 85.0)
            else:
                pitch = 0.0 # 수평 궤도 진입

            pitch_rad = np.radians(pitch)

            # 알짜 가속도 연산
            acc = (thrust - f_drag) / m_curr - g * np.sin(pitch_rad)
            v += acc * dt
            h += (v * np.sin(pitch_rad)) * dt

            # 데이터 기록
            t_list.append(t)
            h_list.append(h / 1000.0) # km
            v_list.append(v / 1000.0) # km/s
            m_list.append(m_curr / 1000.0) # ton
            g_list.append(acc / G0)
            stage_list.append(stage_name)

            t += dt

        return {
            "t": t_list, "h": h_list, "v": v_list, "m": m_list, "g": g_list,
            "max_h": max(h_list) if h_list else 0,
            "final_v": v_list[-1] if v_list else 0,
            "final_h": h_list[-1] if h_list else 0,
            "burn1_time": t_burn1,
            "burn2_time": t_burn2
        }

    except Exception as e:
        st.error(f"물리 연산 중 예외가 발생했습니다: {e}")
        return None

# --- UI 화면 구성 ---
st.title("🚀 우주 로켓 2단계 추진 & 궤도 진입 시뮬레이터")
st.markdown("로켓의 단별 연료량, 비추력(Isp), 추력을 조절하여 **지구 저궤도(LEO, 200km/7.8km/s)** 진입을 성공시키세요!")

# 사이드바 입력 제어판
st.sidebar.header("⚙️ 로켓 파라미터 튜닝")

st.sidebar.subheader("📦 탑재 화물 (Payload)")
payload_mass = st.sidebar.slider("화물 질량 (kg)", 500, 5000, 1500, 100)

st.sidebar.subheader("🔥 1단 로켓 (부스터)")
s1_fuel = st.sidebar.slider("1단 연료 중량 (톤)", 50, 200, 110, 5)
s1_isp = st.sidebar.slider("1단 비추력 Isp (초)", 200, 350, 280, 5)
s1_thrust = st.sidebar.slider("1단 추력 (kN)", 500, 3000, 1600, 50)

st.sidebar.subheader("🌌 2단 로켓 (궤도 진입용)")
s2_fuel = st.sidebar.slider("2단 연료 중량 (톤)", 5, 50, 22, 1)
s2_isp = st.sidebar.slider("2단 비추력 Isp (초)", 280, 450, 340, 5)
s2_thrust = st.sidebar.slider("2단 추력 (kN)", 100, 1000, 350, 10)

# 시뮬레이션 수행
res = run_rocket_simulation(payload_mass, s1_fuel, s1_isp, s1_thrust, s2_fuel, s2_isp, s2_thrust)

if res:
    # 핵심 성능 지표 출력
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("최고 도달 고도", f"{res['max_h']:.1f} km", delta=f"{res['max_h'] - ORBIT_ALT_TARGET:.1f} km")
    col2.metric("최종 도달 속도", f"{res['final_v']:.2f} km/s", delta=f"{res['final_v'] - ORBIT_VEL_TARGET:.2f} km/s")
    col3.metric("1단 연소 시간", f"{res['burn1_time']:.1f} 초")
    col4.metric("2단 연소 시간", f"{res['burn2_time']:.1f} 초")

    st.divider()

    # 궤도 진입 성공 여부 판정
    if res['final_h'] >= 150 and res['final_v'] >= ORBIT_VEL_TARGET:
        st.success("🎉 **[궤도 진입 성공!]** 인공위성이 성공적으로 지구 저궤도(LEO) 안착에 성공했습니다!")
    elif res['max_h'] >= 100 and res['final_v'] < ORBIT_VEL_TARGET:
        st.warning("⚠️ **[탄도 비행 / 속도 부족]** 우주 공간(100km 이상)에는 도달했으나, 궤도 속도가 부족하여 다시 대기권으로 추락합니다. (추력을 높이거나 중량을 줄이세요)")
    else:
        st.error("🚨 **[발사 실패 / 중량 과다]** 추진력이 부족하여 궤도 고도에 도달하지 못했습니다. 연료량과 비추력을 재조정하세요.")

    # 4분할 실시간 그래프 시각화
    st.subheader("📊 궤도 비행 궤적 및 물리량 변화 분석")
    fig, axs = plt.subplots(2, 2, figsize=(12, 7))

    # 1. 고도 그래프
    axs[0, 0].plot(res['t'], res['h'], color='tab:blue', linewidth=2)
    axs[0, 0].axhline(y=ORBIT_ALT_TARGET, color='r', linestyle='--', label='목표 궤도 고도 (200km)')
    axs[0, 0].set_title("고도 변화 (Altitude vs Time)")
    axs[0, 0].set_ylabel("고도 (km)")
    axs[0, 0].grid(True, alpha=0.3)
    axs[0, 0].legend()

    # 2. 속도 그래프
    axs[0, 1].plot(res['t'], res['v'], color='tab:orange', linewidth=2)
    axs[0, 1].axhline(y=ORBIT_VEL_TARGET, color='g', linestyle='--', label='목표 궤도 속도 (7.8km/s)')
    axs[0, 1].set_title("속도 변화 (Velocity vs Time)")
    axs[0, 1].set_ylabel("속도 (km/s)")
    axs[0, 1].grid(True, alpha=0.3)
    axs[0, 1].legend()

    # 3. 로켓 중량 변화 그래프
    axs[1, 0].plot(res['t'], res['m'], color='tab:green', linewidth=2)
    axs[1, 0].set_title("총 질량 변화 (Mass Consumption)")
    axs[1, 0].set_xlabel("시간 (초)")
    axs[1, 0].set_ylabel("질량 (톤)")
    axs[1, 0].grid(True, alpha=0.3)

    # 4. 가속도 / G-Force 그래프
    axs[1, 1].plot(res['t'], res['g'], color='tab:red', linewidth=2)
    axs[1, 1].set_title("승객/화물 G-Force (Acceleration)")
    axs[1, 1].set_xlabel("시간 (초)")
    axs[1, 1].set_ylabel("가속도 (G)")
    axs[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)

    # 공학 원리 해설 탭
    with st.expander("🔬 사용된 핵심 추진공학 공식 보기"):
        st.latex(r"\text{치올콥스키 로켓 방정식: } \Delta v = v_e \ln \left( \frac{m_0}{m_f} \right) = I_{sp} \cdot g_0 \cdot \ln \left( \frac{m_0}{m_f} \right)")
        st.latex(r"\text{대기 항력: } F_{\text{drag}} = \frac{1}{2} \rho(h) v^2 A C_d, \quad \rho(h) = \rho_0 e^{-\frac{h}{H}}")
        st.latex(r"\text{고도별 중력 감소: } g(h) = g_0 \left( \frac{R_E}{R_E + h} \right)^2")
