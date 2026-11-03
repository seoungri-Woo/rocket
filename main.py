import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="🚀 쉬운 우주 로켓 발사 게임",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 누구나 쉽게 하는 우주 로켓 발사 게임!")
st.markdown("""
부품을 조합한 뒤 **[🚀 로켓 발사!]** 버튼을 누르세요. 
비행 중에 1단 연료가 떨어지면 **[🔥 1단 부스터 분리]** 버튼을 눌러 우주 궤도(200km) 진입을 성공시켜 보세요!
""")

# HTML5 Canvas 기반의 2D 로켓 발사 아케이드 게임
game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            background-color: #111;
            color: white;
            font-family: 'Malgun Gothic', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            user-select: none;
        }
        #gameContainer {
            position: relative;
            margin-top: 5px;
        }
        canvas {
            border: 3px solid #444;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.8);
        }
        /* 게임 제어 패널 */
        .control-panel {
            display: flex;
            gap: 15px;
            background: #222;
            padding: 12px 20px;
            border-radius: 10px;
            margin-bottom: 10px;
            align-items: center;
            flex-wrap: wrap;
            border: 1px solid #444;
        }
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
            font-size: 14px;
            font-weight: bold;
        }
        select, button {
            padding: 8px 12px;
            border-radius: 6px;
            border: none;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
        }
        select { background: #333; color: #fff; border: 1px solid #555; }
        
        .btn-launch {
            background: #4caf50;
            color: white;
            font-size: 16px;
            padding: 10px 20px;
            transition: 0.2s;
        }
        .btn-launch:hover { background: #45a049; transform: scale(1.05); }
        
        .btn-stage {
            background: #ff9800;
            color: white;
            font-size: 16px;
            padding: 10px 20px;
            display: none;
            animation: pulse 1s infinite alternate;
        }
        @keyframes pulse {
            0% { transform: scale(1); box-shadow: 0 0 5px #ff9800; }
            100% { transform: scale(1.08); box-shadow: 0 0 20px #ff9800; }
        }

        /* 계기판 Overlay */
        .dashboard {
            position: absolute;
            top: 15px;
            left: 15px;
            background: rgba(0,0,0,0.7);
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
            font-size: 15px;
            line-height: 1.6;
        }
        .val { color: #ffcc00; font-weight: bold; }

        /* 결과 창 */
        #resultModal {
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(20, 20, 20, 0.95);
            border: 3px solid #ffcc00;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            width: 320px;
            box-shadow: 0 0 40px rgba(255, 204, 0, 0.5);
        }
        #resultModal h2 { margin-top: 0; }
        .btn-retry {
            background: #ffcc00; color: #000; padding: 10px 20px; font-weight: bold; border-radius: 6px; margin-top: 15px;
        }
    </style>
</head>
<body>

    <!-- 부품 선택 제어판 -->
    <div class="control-panel">
        <div class="control-group">
            <label>📦 인공위성 무게</label>
            <select id="payloadSelect">
                <option value="1">가벼움 (초소형 위성)</option>
                <option value="2" selected>보통 (통신 위성)</option>
                <option value="3">무거움 (대형 탐사선)</option>
            </select>
        </div>
        <div class="control-group">
            <label>⛽ 연료 탱크 크기</label>
            <select id="fuelSelect">
                <option value="1">소형 (가벼움/연료 적음)</option>
                <option value="2" selected>중형 (표준)</option>
                <option value="3">대형 (무겁지만 연료 넉넉)</option>
            </select>
        </div>
        <div class="control-group">
            <label>🔥 엔진 파워</label>
            <select id="engineSelect">
                <option value="1">기본 엔진</option>
                <option value="2" selected>강력한 엔진</option>
                <option value="3">슈퍼 파워 엔진</option>
            </select>
        </div>
        <button id="launchBtn" class="btn-launch" onclick="startLaunch()">🚀 발사 시작!</button>
        <button id="stageBtn" class="btn-stage" onclick="separateStage()">🔥 1단 부스터 분리!</button>
    </div>

    <!-- 게임 화면 영역 -->
    <div id="gameContainer">
        <canvas id="gameCanvas" width="750" height="520"></canvas>
        
        <!-- 실시간 계기판 -->
        <div class="dashboard">
            📍 고도: <span id="altVal" class="val">0</span> km / 200 km<br>
            ⚡ 속도: <span id="speedVal" class="val">0</span> km/h<br>
            ⛽ 1단 연료: <span id="fuel1Val" class="val">100</span>%<br>
            🌌 2단 연료: <span id="fuel2Val" class="val">100</span>%
        </div>

        <!-- 결과 창 -->
        <div id="resultModal">
            <h2 id="resultTitle">🎉 미션 성공!</h2>
            <p id="resultDesc">축하합니다! 인공위성이 성공적으로 지구 저궤도에 안착했습니다.</p>
            <button class="btn-retry" onclick="resetGame()">다시 도전하기</button>
        </div>
    </div>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// 게임 진행 상태 변수
let isFlying = false;
let isSeparated = false;
let isFinished = false;

let altitude = 0; // km (목표 200km)
let speed = 0;    // km/h
let stage1Fuel = 100;
let stage2Fuel = 100;

// 부스터 파편 애니메이션용
let detachedStage = null;
let particles = [];

// 별 배경 생성
const stars = [];
for (let i = 0; i < 80; i++) {
    stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 1
    });
}

function startLaunch() {
    if (isFlying) return;
    
    isFlying = true;
    isSeparated = false;
    isFinished = false;
    altitude = 0;
    speed = 0;
    stage1Fuel = 100;
    stage2Fuel = 100;
    detachedStage = null;
    particles = [];

    document.getElementById('launchBtn').style.display = 'none';
    document.getElementById('resultModal').style.display = 'none';
    
    // 설정값 가져오기
    const payload = parseInt(document.getElementById('payloadSelect').value);
    const fuelSize = parseInt(document.getElementById('fuelSelect').value);
    const enginePower = parseInt(document.getElementById('engineSelect').value);

    // 비행 물리 루프 시작
    gameLoop(payload, fuelSize, enginePower);
}

function separateStage() {
    if (isFlying && !isSeparated && stage1Fuel <= 30) {
        isSeparated = true;
        document.getElementById('stageBtn').style.display = 'none';
        
        // 분리된 1단 부스터 낙하 애니메이션 생성
        detachedStage = {
            x: canvas.width / 2,
            y: 340,
            vy: 2,
            rot: 0
        };
    }
}

function gameLoop(payload, fuelSize, enginePower) {
    if (isFinished) return;

    // --- 물리 연산 ---
    const totalWeight = payload * 1.5 + fuelSize * 2.0;
    const thrust = enginePower * 3.5;

    // 1단 비행 단계
    if (!isSeparated) {
        if (stage1Fuel > 0) {
            stage1Fuel -= (0.35 / fuelSize);
            speed += (thrust - totalWeight * 0.8) * 4;
            if (speed < 0) speed = 0;
            altitude += (speed / 3000);

            // 1단 연료가 25% 이하로 떨어지면 분리 버튼 띄움
            if (stage1Fuel <= 30) {
                document.getElementById('stageBtn').style.display = 'inline-block';
            }
        } else {
            // 1단 연료 고갈됐는데 분리 안 한 경우 감속
            speed *= 0.98;
            altitude += (speed / 3000);
            if (speed < 100) endGame(false, "연료가 고갈되었습니다! 1단 부스터를 타이밍에 맞게 분리해야 합니다.");
        }
    } 
    // 2단 비행 단계 (분리 성공 후)
    else {
        if (stage2Fuel > 0) {
            stage2Fuel -= 0.4;
            speed += (thrust * 1.2 - payload * 1.2) * 5;
            altitude += (speed / 2200);
        } else {
            speed *= 0.98;
            altitude += (speed / 3000);
        }
    }

    // 성공 조건 확인 (고도 200km 이상 & 속도 7,000km/h 이상)
    if (altitude >= 200) {
        if (speed >= 6500) {
            endGame(true, "🎉 축하합니다! 완벽한 부력과 속도로 우주 궤도(200km) 진입에 성공했습니다!");
        } else {
            endGame(false, "고도에는 도달했으나 속도가 부족해 대기권으로 다시 추락했습니다. 엔진 파워를 높여보세요.");
        }
    }

    // UI 업데이트
    document.getElementById('altVal').innerText = Math.floor(altitude);
    document.getElementById('speedVal').innerText = Math.floor(speed);
    document.getElementById('fuel1Val').innerText = Math.max(0, Math.floor(stage1Fuel));
    document.getElementById('fuel2Val').innerText = Math.max(0, Math.floor(stage2Fuel));

    // --- 렌더링 (화면 그리기) ---
    drawScene();

    requestAnimationFrame(() => gameLoop(payload, fuelSize, enginePower));
}

function drawScene() {
    // 1. 고도에 따른 배경색 변화 (지상 하늘색 -> 우주 검은색)
    const skyProgress = Math.min(1, altitude / 150);
    const r = Math.floor(135 * (1 - skyProgress));
    const g = Math.floor(206 * (1 - skyProgress));
    const b = Math.floor(235 * (1 - skyProgress) + 20 * skyProgress);
    ctx.fillStyle = `rgb(${r},${g},${b})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. 우주 별빛 (고도가 높아지면 밝아짐)
    if (skyProgress > 0.3) {
        ctx.fillStyle = `rgba(255, 255, 255, ${skyProgress - 0.2})`;
        stars.forEach(s => {
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    // 3. 지면 및 발사대 (고도가 낮을 때만 표시)
    if (altitude < 30) {
        const groundY = 440 + altitude * 15;
        ctx.fillStyle = '#2e7d32'; // 잔디
        ctx.fillRect(0, groundY, canvas.width, 100);
        
        ctx.fillStyle = '#555'; // 발사대
        ctx.fillRect(canvas.width / 2 - 40, groundY - 60, 15, 60);
    }

    // 4. 고도 게이지 바 (오른쪽)
    ctx.fillStyle = 'rgba(255,255,255,0.2)';
    ctx.fillRect(canvas.width - 40, 50, 20, 400);
    ctx.fillStyle = '#ffcc00';
    const fillH = Math.min(400, (altitude / 200) * 400);
    ctx.fillRect(canvas.width - 40, 450 - fillH, 20, fillH);
    ctx.fillStyle = '#fff';
    ctx.font = '12px sans-serif';
    ctx.fillText('200km (목표)', canvas.width - 95, 60);
    ctx.fillText('0km', canvas.width - 70, 450);

    // 5. 분리된 1단 부스터 애니메이션
    if (detachedStage) {
        ctx.save();
        ctx.translate(detachedStage.x, detachedStage.y);
        ctx.rotate(detachedStage.rot);
        ctx.fillStyle = '#888';
        ctx.fillRect(-12, 0, 24, 40);
        ctx.restore();

        detachedStage.y += detachedStage.vy;
        detachedStage.vy += 0.1;
        detachedStage.rot += 0.05;
    }

    // 6. 로켓 그리기
    const rocketX = canvas.width / 2;
    const rocketY = 300;

    // 엔진 불꽃 입자 효과
    if ((!isSeparated && stage1Fuel > 0) || (isSeparated && stage2Fuel > 0)) {
        for (let i = 0; i < 3; i++) {
            particles.push({
                x: rocketX + (Math.random() * 10 - 5),
                y: rocketY + (isSeparated ? 25 : 55),
                radius: Math.random() * 6 + 4,
                life: 1
            });
        }
    }

    // 불꽃 그려주기
    particles.forEach((p, idx) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, ${Math.floor(p.life * 200)}, 0, ${p.life})`;
        ctx.fill();
        p.y += 4;
        p.life -= 0.08;
        if (p.life <= 0) particles.splice(idx, 1);
    });

    // 로켓 본체
    // 2단 (상단 위성/페어링)
    ctx.fillStyle = '#e63946';
    ctx.beginPath();
    ctx.moveTo(rocketX, rocketY - 30);
    ctx.lineTo(rocketX - 12, rocketY);
    ctx.lineTo(rocketX + 12, rocketY);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(rocketX - 12, rocketY, 24, 25);

    // 1단 (하단 부스터 - 분리 전만 표시)
    if (!isSeparated) {
        ctx.fillStyle = '#aaaaaa';
        ctx.fillRect(rocketX - 14, rocketY + 25, 28, 35);
        // 날개
        ctx.fillStyle = '#333';
        ctx.beginPath();
        ctx.moveTo(rocketX - 14, rocketY + 45);
        ctx.lineTo(rocketX - 22, rocketY + 60);
        ctx.lineTo(rocketX - 14, rocketY + 60);
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(rocketX + 14, rocketY + 45);
        ctx.lineTo(rocketX + 22, rocketY + 60);
        ctx.lineTo(rocketX + 14, rocketY + 60);
        ctx.fill();
    }
}

function endGame(success, message) {
    isFinished = true;
    isFlying = false;

    document.getElementById('resultTitle').innerText = success ? "🎉 미션 성공!" : "💥 발사 실패";
    document.getElementById('resultTitle').style.color = success ? "#4caf50" : "#f44336";
    document.getElementById('resultDesc').innerText = message;
    document.getElementById('resultModal').style.display = 'block';
    document.getElementById('stageBtn').style.display = 'none';
}

function resetGame() {
    isFlying = false;
    isFinished = false;
    document.getElementById('resultModal').style.display = 'none';
    document.getElementById('launchBtn').style.display = 'inline-block';
    document.getElementById('stageBtn').style.display = 'none';
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    altitude = 0;
    speed = 0;
    document.getElementById('altVal').innerText = '0';
    document.getElementById('speedVal').innerText = '0';
    document.getElementById('fuel1Val').innerText = '100';
    document.getElementById('fuel2Val').innerText = '100';
    drawScene();
}

// 최초 화면 그리기
drawScene();

</script>
</body>
</html>
"""

# Streamlit에 화면 출력
components.html(game_html, height=620)
