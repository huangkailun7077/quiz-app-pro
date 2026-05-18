/**
 * 学员端 JS
 * Alan 出品
 */

let questions = [];
let currentQuestions = [];
let currentIndex = 0;
let selectedAnswer = null;
let multiSelectedAnswers = [];
let currentMode = ''; // sequential, random, exam
let currentType = 'all'; // all, 单选题，多选题，判断题
let practiceMode = 'answer'; // answer, review
let practiceAnswerCount = 0;
let examStartTime = null;
let examAnswers = {};
let examTimerInterval = null;

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    await loadUserData();
    await loadQuestionsData();
});

// 加载用户数据
async function loadUserData() {
    console.log('[USER] loadUserData 开始执行');
    
    try {
        const response = await fetch('/api/student/stats');
        console.log('[USER] API 响应状态:', response.status);
        
        const result = await response.json();
        console.log('[USER] API 返回数据:', result);
        
        if (result.success) {
            const data = result.data;
            document.getElementById('userName').textContent = sessionStorage.getItem('username') || '学员';
            document.getElementById('statAnswers').textContent = data.totalAnswers;
            document.getElementById('statRate').textContent = data.correctRate + '%';
            document.getElementById('statExams').textContent = data.examCount;
            console.log('[USER] 数据已更新 - 答题数:', data.totalAnswers, '正确率:', data.correctRate, '考试次数:', data.examCount);
        } else {
            console.error('[USER] API 返回失败:', result.message);
        }
    } catch (e) {
        console.error('[USER] 加载用户数据失败:', e);
    }
}

// 加载题库
async function loadQuestionsData() {
    try {
        // 优先使用本地 QUESTIONS_DATA（如果存在）
        if (typeof QUESTIONS_DATA !== 'undefined' && QUESTIONS_DATA.length > 0) {
            questions = QUESTIONS_DATA;
            console.log('题库加载完成（本地），共', questions.length, '题');
            return;
        }
        // 否则从 API 加载
        const response = await fetch('/api/questions');
        questions = await response.json();
        console.log('题库加载完成（API），共', questions.length, '题');
    } catch (e) {
        console.error('加载题库失败:', e);
        alert('加载题库失败，请刷新页面');
    }
}

// 页面切换
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
}

function goHome() {
    console.log('[HOME] goHome 被调用');
    
    // 清理考试计时器
    if (examTimerInterval) {
        clearInterval(examTimerInterval);
        examTimerInterval = null;
    }
    // 隐藏考试导航
    document.getElementById('examTimerBar').classList.add('hidden');
    document.getElementById('examNav').classList.add('hidden');
    document.getElementById('submitExamBtn').style.display = 'none';
    
    showPage('homePage');
    
    // 重新加载用户数据（刷新统计）
    console.log('[HOME] 调用 loadUserData 刷新数据');
    loadUserData();
}

// 显示模式选择
let selectedPracticeMode = '';
let selectedRandomCount = 30; // 随机刷题题量
let selectedSequentialStart = 1; // 顺序刷题起始题号

function showModeSelect(mode) {
    selectedPracticeMode = mode;
    document.getElementById('modeSelectTitle').textContent = mode === 'sequential' ? '顺序刷题' : '随机刷题';
    
    // 顺序刷题显示题号输入
    const sequentialDiv = document.getElementById('sequentialInputDiv');
    if (mode === 'sequential') {
        sequentialDiv.style.display = 'block';
        document.getElementById('totalQuestionsCount').textContent = questions.length;
        document.getElementById('sequentialStartNum').max = questions.length;
        selectedSequentialStart = 1;
    } else {
        sequentialDiv.style.display = 'none';
    }
    
    // 随机刷题显示题量选择
    const randomSelectDiv = document.getElementById('randomCountSelect');
    if (mode === 'random') {
        randomSelectDiv.style.display = 'block';
    } else {
        randomSelectDiv.style.display = 'none';
    }
    
    showPage('modeSelectPage');
}

// 选择随机题量
function selectRandomCount(count) {
    selectedRandomCount = count;
    // 重置所有按钮样式
    document.querySelectorAll('.random-count-btn').forEach(btn => {
        btn.style.opacity = '0.6';
        btn.style.transform = 'scale(0.95)';
    });
    // 选中按钮高亮
    const selectedBtn = document.getElementById(`randomCount${count}`);
    selectedBtn.style.opacity = '1';
    selectedBtn.style.transform = 'scale(1.05)';
    selectedBtn.style.boxShadow = '0 8px 25px rgba(255,255,255,0.5)';
}

// 开始刷题
function startPractice() {
    currentMode = selectedPracticeMode;
    currentType = document.getElementById('questionTypeSelect').value;
    practiceMode = document.getElementById('practiceModeSelect').value;
    practiceAnswerCount = 0;
    
    // 顺序刷题保存起始题号
    if (selectedPracticeMode === 'sequential') {
        selectedSequentialStart = parseInt(document.getElementById('sequentialStartNum').value) || 1;
    }
    
    // 筛选题目
    let filteredQuestions = [...questions];
    
    if (currentType !== 'all') {
        filteredQuestions = filteredQuestions.filter(q => q.type === currentType);
    }
    
    if (currentMode === 'sequential') {
        // 顺序刷题：按 ID 排序，从指定题号开始
        filteredQuestions.sort((a, b) => parseInt(a.id) - parseInt(b.id));
        const startIndex = Math.max(0, selectedSequentialStart - 1);
        currentQuestions = filteredQuestions.slice(startIndex);
        console.log('顺序刷题 - 起始题号:', selectedSequentialStart, '剩余题目:', currentQuestions.length);
    } else if (currentMode === 'random') {
        // 随机刷题：按选择的题量
        const singleChoice = filteredQuestions.filter(q => q.type === '单选题');
        const multiChoice = filteredQuestions.filter(q => q.type === '多选题');
        const trueFalse = filteredQuestions.filter(q => q.type === '判断题');
        
        let singleCount, multiCount, judgeCount;
        
        if (selectedRandomCount === 30) {
            singleCount = 20; multiCount = 5; judgeCount = 5;
        } else if (selectedRandomCount === 50) {
            singleCount = 30; multiCount = 10; judgeCount = 10;
        } else { // 100
            singleCount = 60; multiCount = 20; judgeCount = 20;
        }
        
        // 检查题库数量
        if (singleChoice.length < singleCount || multiChoice.length < multiCount || trueFalse.length < judgeCount) {
            alert(`题库题目数量不足！\n单选题：${singleChoice.length}/${singleCount}\n多选题：${multiChoice.length}/${multiCount}\n判断题：${trueFalse.length}/${judgeCount}`);
            return;
        }
        
        // 随机抽取
        const selectedSingle = shuffleArray([...singleChoice]).slice(0, singleCount);
        const selectedMulti = shuffleArray([...multiChoice]).slice(0, multiCount);
        const selectedJudge = shuffleArray([...trueFalse]).slice(0, judgeCount);
        
        currentQuestions = shuffleArray([...selectedSingle, ...selectedMulti, ...selectedJudge]);
    }
    
    if (currentQuestions.length === 0) {
        alert('该题型暂无题目');
        return;
    }
    
    currentIndex = 0;
    showPage('practicePage');
    
    const modeText = currentMode === 'sequential' ? '顺序' : '随机';
    const typeText = currentType === 'all' ? '全部题型' : currentType;
    const countText = currentMode === 'random' ? `（${selectedRandomCount}题）` : '';
    const modeTypeText = practiceMode === 'review' ? '（背题模式）' : '';
    
    document.getElementById('practiceModeTitle').textContent = `${modeText}刷题 - ${typeText}${countText}${modeTypeText}`;
    
    renderQuestion();
    
    console.log('开始刷题，模式:', currentMode, '题型:', currentType, '题量:', currentQuestions.length, '练习模式:', practiceMode);
}

// 显示考试确认
function showExamConfirm() {
    if (!confirm('⏱️ 模拟考试\n\n- 60 分钟\n- 100 道题（60 单选 +20 多选 +20 判断）\n- 满分 100 分\n\n确定开始考试吗？')) {
        return;
    }
    startExam();
}

// 开始考试
function startExam() {
    console.log('开始考试，题库总数:', questions.length);
    
    // 从题库随机抽题
    const singleChoice = questions.filter(q => q.type === '单选题');
    const multiChoice = questions.filter(q => q.type === '多选题');
    const trueFalse = questions.filter(q => q.type === '判断题');
    
    console.log('题型统计 - 单选题:', singleChoice.length, '多选题:', multiChoice.length, '判断题:', trueFalse.length);
    
    // 检查题库数量
    if (singleChoice.length < 60 || multiChoice.length < 20 || trueFalse.length < 20) {
        alert(`题库题目数量不足！\n单选题：${singleChoice.length}/60\n多选题：${multiChoice.length}/20\n判断题：${trueFalse.length}/20`);
        return;
    }
    
    // 随机抽取题目
    const selectedSingle = shuffleArray([...singleChoice]).slice(0, 60);
    const selectedMulti = shuffleArray([...multiChoice]).slice(0, 20);
    const selectedJudge = shuffleArray([...trueFalse]).slice(0, 20);
    
    // 按顺序组合：60 单选 + 20 多选 + 20 判断
    currentQuestions = [...selectedSingle, ...selectedMulti, ...selectedJudge];
    
    currentMode = 'exam';
    practiceAnswerCount = 0;
    
    // 开始计时
    examStartTime = Date.now();
    examAnswers = {};
    
    currentIndex = 0;
    showPage('practicePage');
    document.getElementById('practiceModeTitle').textContent = '⏱️ 模拟考试（60 分钟）';
    
    // 显示考试导航
    document.getElementById('examTimerBar').classList.remove('hidden');
    document.getElementById('examNav').classList.remove('hidden');
    document.getElementById('submitExamBtn').style.display = 'inline-block';
    
    // 生成题号导航
    renderQuestionNumbers();
    
    renderQuestion();
    
    // 显示倒计时
    startExamTimer();
    
    // 更新已答/未答统计
    updateExamStats();
}

// 渲染题目
function renderQuestion() {
    if (currentQuestions.length === 0) return;
    
    const q = currentQuestions[currentIndex];
    const container = document.getElementById('questionContainer');
    
    let optionsHtml = '';
    
    // 判断题特殊处理：生成正确/错误选项
    if (q.type === '判断题') {
        const judgeOptions = { 'A': '正确', 'B': '错误' };
        for (const [letter, text] of Object.entries(judgeOptions)) {
            let optionClass = 'option';
            let optionStyle = '';
            
            // 考试模式：恢复已选答案的颜色
            if (currentMode === 'exam' && examAnswers[q.id]) {
                if (examAnswers[q.id].includes(letter)) {
                    optionStyle = 'background:#E3F2FD;border-color:#2196F3;';
                }
            }
            
            // 背题模式直接显示正确答案
            if (practiceMode === 'review') {
                if (q.answer === text) {
                    optionClass += ' correct';
                }
            }
            
            optionsHtml += `
                <div class="${optionClass}" style="${optionStyle}" onclick="selectOption('${letter}')" id="option-${letter}">
                    <span class="option-letter">${letter}.</span>
                    <span class="option-text">${text}</span>
                </div>
            `;
        }
    } else {
        // 其他题型正常渲染
        for (const [letter, text] of Object.entries(q.options)) {
            let optionClass = 'option';
            let optionStyle = '';
            
            // 考试模式：恢复已选答案的颜色
            if (currentMode === 'exam' && examAnswers[q.id]) {
                if (examAnswers[q.id].includes(letter)) {
                    optionStyle = 'background:#E3F2FD;border-color:#2196F3;font-weight:bold;';
                }
            }
            
            // 背题模式直接显示正确答案
            if (practiceMode === 'review') {
                if (q.answer.includes(letter)) {
                    optionClass += ' correct';
                }
            }
            
            optionsHtml += `
                <div class="${optionClass}" style="${optionStyle}" onclick="selectOption('${letter}')" id="option-${letter}">
                    <span class="option-letter">${letter}.</span>
                    <span class="option-text">${text}</span>
                </div>
            `;
        }
    }
    
    container.innerHTML = `
        <div class="question-card">
            <div class="question-number-display">第 ${q.id} 题 / 共 ${currentQuestions.length} 题</div>
            <div style="margin-bottom: 10px;">
                <span class="question-type ${q.type}">${q.type}</span>
                ${practiceMode === 'review' ? '<span style="margin-left:10px;color:#4CAF50;font-weight:bold;">👁️ 背题模式</span>' : ''}
            </div>
            <div class="question-content">${q.content}</div>
            <div class="options">
                ${optionsHtml}
            </div>
        </div>
    `;
    
    if (q.type === '多选题') {
        multiSelectedAnswers = [];
    } else {
        selectedAnswer = null;
    }
    
    updateSubmitButton();
    
    const feedback = document.getElementById('feedback');
    if (feedback) {
        feedback.className = 'feedback';
        feedback.innerHTML = '';
    }
    
    // 背题模式隐藏提交按钮
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.style.display = practiceMode === 'review' ? 'none' : 'block';
    }
    
    // 考试模式隐藏反馈区域
    const feedbackEl = document.getElementById('feedback');
    if (feedbackEl) {
        feedbackEl.style.display = currentMode === 'exam' ? 'none' : 'block';
    }
    
    // 更新题号导航（考试模式）
    if (currentMode === 'exam') {
        updateQuestionNumbers();
    }
}

function updateSubmitButton() {
    const submitBtn = document.getElementById('submitBtn');
    if (!submitBtn) return;
    
    const q = currentQuestions[currentIndex];
    if (!q) return;
    
    if (q.type === '多选题') {
        submitBtn.disabled = multiSelectedAnswers.length === 0;
    } else {
        submitBtn.disabled = !selectedAnswer;
    }
}

// 渲染题号导航
function renderQuestionNumbers() {
    const container = document.getElementById('questionNumbers');
    if (!container) return;
    
    let html = '';
    for (let i = 0; i < currentQuestions.length; i++) {
        html += `<div class="q-number" id="qnum-${i}" onclick="goToQuestion(${i})">${i + 1}</div>`;
    }
    container.innerHTML = html;
}

// 更新题号导航状态
function updateQuestionNumbers() {
    console.log('[DEBUG] updateQuestionNumbers 开始执行，考试模式:', currentMode, '已答题数:', Object.keys(examAnswers).length);
    
    // 更新当前题号
    document.getElementById('currentQNum').textContent = currentIndex + 1;
    
    // 更新已答题数
    const answeredCount = Object.keys(examAnswers).length;
    document.getElementById('answeredCount').textContent = answeredCount;
    
    // 更新未答题数
    const unansweredCount = currentQuestions.length - answeredCount;
    document.getElementById('unansweredCount').textContent = unansweredCount;
    
    // 更新所有题号状态
    let greenCount = 0, redCount = 0;
    for (let i = 0; i < currentQuestions.length; i++) {
        const el = document.getElementById(`qnum-${i}`);
        if (!el) {
            console.log('[DEBUG] 题号元素不存在:', i);
            continue;
        }
        
        // 重置样式
        el.classList.remove('current', 'answered', 'wrong');
        el.style.background = '#f0f0f0';
        el.style.color = '';
        el.style.fontWeight = '';
        
        if (i === currentIndex) {
            el.classList.add('current');
        }
        
        // 如果这道题已答，检查对错并标记
        const q = currentQuestions[i];
        const userAnswer = examAnswers[q.id];
        if (userAnswer) {
            // 比较多选题答案时排序后比较
            const userSorted = userAnswer.split('').sort().join('');
            const correctSorted = q.answer.split('').sort().join('');
            const isCorrect = userSorted === correctSorted;
            
            console.log('[DEBUG] 题号', i+1, '- 用户答案:', userAnswer, '正确答案:', q.answer, '对错:', isCorrect);
            
            if (isCorrect) {
                el.style.background = '#4CAF50';
                el.style.color = 'white';
                el.style.fontWeight = 'bold';
                greenCount++;
            } else {
                el.style.background = '#f44336';
                el.style.color = 'white';
                el.style.fontWeight = 'bold';
                redCount++;
            }
        }
    }
    
    console.log('[DEBUG] 题号导航更新完成 - 绿色:', greenCount, '红色:', redCount, '当前:', currentIndex + 1);
}

// 更新考试统计
function updateExamStats() {
    const answeredCount = Object.keys(examAnswers).length;
    const unansweredCount = currentQuestions.length - answeredCount;
    
    let statsHtml = `
        <div style="background:white;border-radius:10px;padding:15px;margin-bottom:15px;box-shadow:0 5px 15px rgba(0,0,0,0.1);">
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:15px;text-align:center;">
                <div>
                    <div style="font-size:1.8em;font-weight:bold;color:#4CAF50;">${answeredCount}</div>
                    <div style="font-size:0.85em;color:#666;">已答题</div>
                </div>
                <div style="border-left:2px solid #eee;">
                    <div style="font-size:1.8em;font-weight:bold;color:#f44336;">${unansweredCount}</div>
                    <div style="font-size:0.85em;color:#666;">未答题</div>
                </div>
                <div style="border-left:2px solid #eee;">
                    <div style="font-size:1.8em;font-weight:bold;color:#2196F3;">${currentQuestions.length}</div>
                    <div style="font-size:0.85em;color:#666;">总题数</div>
                </div>
            </div>
        </div>
    `;
    
    // 插入到题号导航前
    const navContainer = document.getElementById('examNav');
    const existingStats = navContainer.querySelector('.exam-stats');
    if (existingStats) {
        existingStats.outerHTML = statsHtml;
    } else {
        navContainer.insertAdjacentHTML('afterbegin', `<div class="exam-stats">${statsHtml}</div>`);
    }
}

// 跳转到指定题目
function goToQuestion(index) {
    if (index < 0 || index >= currentQuestions.length) return;
    currentIndex = index;
    renderQuestion();
}

function selectOption(letter) {
    const q = currentQuestions[currentIndex];
    const feedback = document.getElementById('feedback');
    
    // 背题模式不允许选择
    if (practiceMode === 'review') {
        return;
    }
    
    // 已显示反馈后不允许修改
    if (feedback && (feedback.classList.contains('correct') || feedback.classList.contains('wrong'))) {
        return;
    }
    
    // 处理选择逻辑
    if (q.type === '多选题') {
        const index = multiSelectedAnswers.indexOf(letter);
        if (index > -1) {
            multiSelectedAnswers.splice(index, 1);
            document.getElementById(`option-${letter}`).classList.remove('selected');
        } else {
            multiSelectedAnswers.push(letter);
            document.getElementById(`option-${letter}`).classList.add('selected');
        }
        
        // 如果是考试模式，记录答案并标记选项颜色
        if (currentMode === 'exam') {
            examAnswers[q.id] = multiSelectedAnswers.sort().join('');
            console.log('多选题答案已记录:', q.id, '=', examAnswers[q.id]);
            
            // 更新当前题号的小方块颜色（统一蓝色）
            const currentQNumEl = document.getElementById(`qnum-${currentIndex}`);
            if (currentQNumEl) {
                currentQNumEl.style.background = '#2196F3';
                currentQNumEl.style.color = 'white';
                currentQNumEl.style.fontWeight = 'bold';
            }
            
            // 标记已选选项为蓝色
            multiSelectedAnswers.forEach(l => {
                const opt = document.getElementById(`option-${l}`);
                if (opt) {
                    opt.style.background = '#E3F2FD';
                    opt.style.borderColor = '#2196F3';
                }
            });
        }
        updateSubmitButton();
    } else {
        // 单选题和判断题
        document.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
        document.getElementById(`option-${letter}`).classList.add('selected');
        selectedAnswer = letter;
        
        // 如果是考试模式，记录答案并立即更新小方块颜色
        if (currentMode === 'exam') {
            examAnswers[q.id] = letter;
            console.log('[EXAM] 答案已记录 - 题号:', currentIndex+1, '题目 ID:', q.id, '答案:', examAnswers[q.id]);
            
            // 直接更新当前题号的小方块颜色（统一蓝色）
            const currentQNumEl = document.getElementById(`qnum-${currentIndex}`);
            console.log('[EXAM] 查找题号元素 qnum-' + currentIndex + ':', currentQNumEl ? '找到' : '未找到');
            
            if (currentQNumEl) {
                // 统一标记为蓝色（不区分对错）
                currentQNumEl.style.background = '#2196F3';
                currentQNumEl.style.color = 'white';
                currentQNumEl.style.fontWeight = 'bold';
                console.log('[EXAM] 题号', currentIndex+1, '标记为蓝色（已答）');
            } else {
                console.error('[EXAM] ✗ 找不到题号元素 qnum-' + currentIndex);
            }
            
            // 标记已选选项为蓝色
            const selectedOpt = document.getElementById(`option-${letter}`);
            if (selectedOpt) {
                selectedOpt.style.background = '#E3F2FD';
                selectedOpt.style.borderColor = '#2196F3';
            }
            
            // 考试模式下，单选题/判断题选完后 1 秒自动下一题
            setTimeout(() => {
                if (currentIndex < currentQuestions.length - 1) {
                    currentIndex++;
                    renderQuestion();
                    updateQuestionNumbers();
                }
            }, 1000);
        }
        updateSubmitButton();
    }
}

// 提交答案
async function checkAnswer() {
    const q = currentQuestions[currentIndex];
    let userAnswer;
    let isCorrect;
    
    if (q.type === '判断题') {
        // 判断题：用户选 A/B，答案是"正确"/"错误"
        userAnswer = selectedAnswer; // A 或 B
        const judgeMap = { 'A': '正确', 'B': '错误' };
        const userAnswerText = judgeMap[userAnswer];
        isCorrect = userAnswerText === q.answer;
    } else if (q.type === '多选题') {
        userAnswer = multiSelectedAnswers.sort().join('');
        isCorrect = userAnswer === q.answer;
    } else {
        userAnswer = selectedAnswer;
        isCorrect = userAnswer === q.answer;
    }
    
    if (!userAnswer) {
        alert('请先选择答案！');
        return;
    }
    
    // 考试模式：只保存答案，不显示反馈，直接下一题
    if (currentMode === 'exam') {
        try {
            await fetch('/api/save_answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    questionId: q.id,
                    questionType: q.type,
                    userAnswer: userAnswer,
                    correctAnswer: q.answer,
                    isCorrect: isCorrect
                })
            });
            practiceAnswerCount++;
        } catch (e) {
            console.error('保存失败:', e);
        }
        
        // 直接跳到下一题
        nextQuestion();
        return;
    }
    
    // 练习模式：显示反馈
    const feedback = document.getElementById('feedback');
    
    // 保存到后端
    try {
        await fetch('/api/save_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                questionId: q.id,
                questionType: q.type,
                userAnswer: userAnswer,
                correctAnswer: q.answer,
                isCorrect: isCorrect
            })
        });
        practiceAnswerCount++;
        console.log('答案已保存');
    } catch (e) {
        console.error('保存失败:', e);
    }
    
    if (isCorrect) {
        if (feedback) {
            feedback.className = 'feedback correct';
            feedback.innerHTML = '✅ 回答正确！';
        }
        
        if (q.type === '多选题') {
            q.answer.split('').forEach(letter => {
                const opt = document.getElementById(`option-${letter}`);
                if (opt) opt.classList.add('correct');
            });
        } else if (q.type === '判断题') {
            // 判断题：根据答案文字找到对应选项
            const judgeMap = { '正确': 'A', '错误': 'B' };
            const correctLetter = judgeMap[q.answer];
            const opt = document.getElementById(`option-${correctLetter}`);
            if (opt) opt.classList.add('correct');
        } else {
            const opt = document.getElementById(`option-${userAnswer}`);
            if (opt) opt.classList.add('correct');
        }
    } else {
        if (feedback) {
            feedback.className = 'feedback wrong';
            feedback.innerHTML = `❌ 回答错误，正确答案是：<strong>${q.answer}</strong>`;
        }
        
        if (q.type === '多选题') {
            multiSelectedAnswers.forEach(letter => {
                const opt = document.getElementById(`option-${letter}`);
                if (opt && !q.answer.includes(letter)) {
                    opt.classList.add('wrong');
                }
            });
        } else if (q.type === '判断题') {
            // 判断题：标红用户选的，标绿正确答案
            const wrongLetter = userAnswer;
            const judgeMap = { '正确': 'A', '错误': 'B' };
            const correctLetter = judgeMap[q.answer];
            const optWrong = document.getElementById(`option-${wrongLetter}`);
            const optCorrect = document.getElementById(`option-${correctLetter}`);
            if (optWrong) optWrong.classList.add('wrong');
            if (optCorrect) optCorrect.classList.add('correct');
        } else {
            const opt = document.getElementById(`option-${userAnswer}`);
            if (opt) opt.classList.add('wrong');
        }
        
        // 显示正确答案（判断题和多选题）
        if (q.type === '判断题') {
            const judgeMap = { '正确': 'A', '错误': 'B' };
            const correctLetter = judgeMap[q.answer];
            const opt = document.getElementById(`option-${correctLetter}`);
            if (opt && !opt.classList.contains('wrong')) opt.classList.add('correct');
        } else if (q.type === '多选题') {
            q.answer.split('').forEach(letter => {
                const opt = document.getElementById(`option-${letter}`);
                if (opt) opt.classList.add('correct');
            });
        }
    }
    
    document.querySelectorAll('.option').forEach(opt => {
        opt.style.pointerEvents = 'none';
    });
    
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) submitBtn.disabled = true;
}

function nextQuestion() {
    if (currentIndex < currentQuestions.length - 1) {
        currentIndex++;
        renderQuestion();
    } else {
        // 已完成所有题目
        if (currentMode === 'exam') {
            // 考试模式：自动交卷
            submitExam();
        } else {
            // 练习模式：保存记录
            savePracticeRecord();
            alert('🎉 已完成本组所有题目！');
        }
    }
}

function prevQuestion() {
    if (currentIndex > 0) {
        currentIndex--;
        renderQuestion();
    } else {
        alert('已经是第一题啦！');
    }
}

// 保存刷题记录
async function savePracticeRecord() {
    try {
        await fetch('/api/save_practice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mode: currentMode,
                questionType: currentType,
                questionCount: practiceAnswerCount,
                practiceMode: practiceMode
            })
        });
        console.log('学习记录已保存');
    } catch (e) {
        console.error('保存学习记录失败:', e);
    }
}

// 考试计时器
function startExamTimer() {
    const timerDisplay = document.getElementById('examTimerText');
    if (!timerDisplay) return;
    
    const maxTime = 60 * 60 * 1000; // 60 分钟
    
    examTimerInterval = setInterval(() => {
        const elapsed = Date.now() - examStartTime;
        const remaining = maxTime - elapsed;
        
        if (remaining <= 0) {
            clearInterval(examTimerInterval);
            alert('⏰ 考试时间到！自动交卷！');
            submitExam();
            return;
        }
        
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        timerDisplay.textContent = `⏱️ ${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // 最后 5 分钟变红闪烁
        const timerBar = document.getElementById('examTimerBar');
        if (remaining <= 5 * 60000) {
            timerBar.classList.add('urgent');
        }
    }, 1000);
}

// 提交考试
function submitExam() {
    console.log('[EXAM] submitExam 被调用');
    
    if (examTimerInterval) {
        clearInterval(examTimerInterval);
        examTimerInterval = null;
    }
    
    // 隐藏考试导航
    const timerBar = document.getElementById('examTimerBar');
    const examNav = document.getElementById('examNav');
    const submitBtn = document.getElementById('submitExamBtn');
    
    if (timerBar) timerBar.classList.add('hidden');
    if (examNav) examNav.classList.add('hidden');
    if (submitBtn) submitBtn.style.display = 'none';
    
    // 检查是否有未答题
    const unansweredCount = currentQuestions.length - Object.keys(examAnswers).length;
    if (unansweredCount > 0) {
        if (!confirm(`还有 ${unansweredCount} 道题未答，确定要交卷吗？`)) {
            if (timerBar) timerBar.classList.remove('hidden');
            if (examNav) examNav.classList.remove('hidden');
            if (submitBtn) submitBtn.style.display = 'inline-block';
            return;
        }
    }
    
    console.log('[EXAM] 开始计算分数，总题数:', currentQuestions.length);
    
    // 计算分数
    let correctCount = 0;
    const wrongIds = [];
    const stats = { single: { correct: 0, total: 0 }, multi: { correct: 0, total: 0 }, judge: { correct: 0, total: 0 } };
    
    currentQuestions.forEach((q, index) => {
        const userAnswer = examAnswers[q.id];
        console.log('[EXAM] 题号', index+1, '用户答案:', userAnswer, '正确答案:', q.answer, '题型:', q.type);
        
        // 判断题特殊处理：用户答案是 A/B，正确答案是 正确/错误
        let isCorrect = false;
        if (q.type === '判断题') {
            const judgeMap = { 'A': '正确', 'B': '错误' };
            const userAnswerText = judgeMap[userAnswer] || '';
            isCorrect = userAnswerText === q.answer;
        } else {
            isCorrect = userAnswer === q.answer;
        }
        
        if (isCorrect) {
            correctCount++;
        } else {
            wrongIds.push(q.id);
        }
        
        // 按题型统计
        if (q.type === '单选题') {
            stats.single.total++;
            if (isCorrect) stats.single.correct++;
        } else if (q.type === '多选题') {
            stats.multi.total++;
            if (isCorrect) stats.multi.correct++;
        } else if (q.type === '判断题') {
            stats.judge.total++;
            if (isCorrect) stats.judge.correct++;
        }
    });
    
    const score = (correctCount / currentQuestions.length * 100).toFixed(1);
    const timeUsed = Math.floor((Date.now() - examStartTime) / 1000);
    
    console.log('[EXAM] 计算完成 - 分数:', score, '正确数:', correctCount, '用时:', timeUsed, '秒');
    
    // 保存到后端
    fetch('/api/save_exam', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            score: parseFloat(score),
            correctCount: correctCount,
            totalCount: currentQuestions.length,
            timeUsed: timeUsed,
            stats: stats,
            wrongIds: wrongIds
        })
    })
    .then(response => {
        console.log('[EXAM] 后端响应:', response.status);
        return response.json();
    })
    .then(result => {
        console.log('[EXAM] 后端返回:', result);
        console.log('[EXAM] 准备显示结果页面');
        
        // 显示考试结果
        showExamResultsWithDetails(score, correctCount, timeUsed, stats);
        
        // 提示用户返回首页查看统计
        if (result.success) {
            console.log('[EXAM] ✅ 考试记录已保存，返回首页可查看统计');
        }
    })
    .catch(e => {
        console.error('[EXAM] 保存考试记录失败:', e);
        // 即使保存失败也显示结果
        showExamResultsWithDetails(score, correctCount, timeUsed, stats);
    });
}

// 显示考试结果（先显示分数和按钮）
function showExamResultsWithDetails(score, correctCount, timeUsed, stats) {
    console.log('[EXAM] === showExamResultsWithDetails 开始执行 ===');
    console.log('[EXAM] 参数：score=', score, 'correctCount=', correctCount, 'timeUsed=', timeUsed);
    
    const container = document.getElementById('questionContainer');
    console.log('[EXAM] 容器:', container ? '找到' : '未找到');
    
    if (!container) {
        console.error('[EXAM] 错误：找不到 questionContainer 元素');
        alert('页面元素未找到，请刷新页面重试');
        return;
    }
    
    ['examTimerBar','examNav','submitExamBtn','controls','questionNumbers'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (id === 'submitExamBtn') el.style.display = 'none';
            else if (id === 'controls' || id === 'questionNumbers') el.style.display = 'none';
            else el.classList.add('hidden');
            console.log('[EXAM] 已隐藏:', id);
        }
    });
    
    const html = `<div style="background:linear-gradient(135deg,#0085D0,#00A8E6);color:white;padding:30px;border-radius:15px;margin-bottom:25px;text-align:center;box-shadow:0 10px 30px rgba(0,133,208,0.3);"><h2 style="margin-bottom:20px;font-size:1.8em;">📊 考试结果</h2><div style="font-size:5em;font-weight:bold;margin:20px 0;text-shadow:0 2px 10px rgba(0,0,0,0.2);">${score}分</div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-top:20px;"><div style="background:rgba(255,255,255,0.2);padding:15px;border-radius:10px;"><div style="font-size:1.8em;font-weight:bold;">${correctCount}/${currentQuestions.length}</div><div style="font-size:0.85em;opacity:0.9;">✅ 正确题目</div></div><div style="background:rgba(255,255,255,0.2);padding:15px;border-radius:10px;"><div style="font-size:1.8em;font-weight:bold;">${Math.floor(timeUsed/60)}:${(timeUsed%60).toString().padStart(2,'0')}</div><div style="font-size:0.85em;opacity:0.9;">⏱️ 考试用时</div></div><div style="background:rgba(255,255,255,0.2);padding:15px;border-radius:10px;"><div style="font-size:1.8em;font-weight:bold;">${score >= 60 ? '✅' : '💪'}</div><div style="font-size:0.85em;opacity:0.9;">${score >= 60 ? '通过' : '继续加油'}</div></div></div><div style="margin-top:20px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.3);"><div style="font-size:0.9em;opacity:0.9;">📈 各题型得分</div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;font-size:0.85em;"><div>单选：${stats.single.correct}/${stats.single.total}</div><div>多选：${stats.multi.correct}/${stats.multi.total}</div><div>判断：${stats.judge.correct}/${stats.judge.total}</div></div></div><div style="margin-top:25px;display:flex;gap:15px;justify-content:center;flex-wrap:wrap;"><button onclick="showExamDetails()" style="background:#4CAF50;color:white;border:none;padding:15px 40px;border-radius:10px;font-size:1.1em;cursor:pointer;font-weight:bold;">📝 答题详情</button><button onclick="goHome()" style="background:white;color:#0085D0;border:none;padding:15px 40px;border-radius:10px;font-size:1.1em;cursor:pointer;font-weight:bold;">🏠 返回首页</button></div></div><div id="examDetailsSection" style="display:none;margin-top:25px;background:white;padding:25px;border-radius:15px;box-shadow:0 5px 20px rgba(0,0,0,0.1);"></div>`;
    
    container.innerHTML = '';
    container.innerHTML = html;
    console.log('[EXAM] HTML 已插入，长度:', container.innerHTML.length);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    console.log('[EXAM] === showExamResultsWithDetails 执行完成 ===');
}

// 显示答题详情
function showExamDetails() {
    const detailsSection = document.getElementById('examDetailsSection');
    if (!detailsSection) return;
    
    detailsSection.style.display = 'block';
    
    let html = '<div style="margin-top:25px;">';
    html += '<h3 style="color:#333;margin-bottom:20px;font-size:1.3em;">📝 完整答卷（共' + currentQuestions.length + '题）</h3>';
    
    currentQuestions.forEach((q, index) => {
        const userAnswer = examAnswers[q.id] || '';
        const isUnanswered = userAnswer === '';
        
        // 判断题特殊处理：用户答案是 A/B，正确答案是 正确/错误
        let isCorrect = false;
        if (q.type === '判断题') {
            const judgeMap = { 'A': '正确', 'B': '错误' };
            const userAnswerText = judgeMap[userAnswer] || '';
            isCorrect = userAnswerText === q.answer;
        } else {
            isCorrect = userAnswer === q.answer;
        }
        
        // 生成选项 HTML
        let optionsHtml = '';
        if (q.type === '判断题') {
            const judgeOptions = { 'A': '正确', 'B': '错误' };
            const correctLetter = q.answer === '正确' ? 'A' : 'B';
            
            for (const [letter, text] of Object.entries(judgeOptions)) {
                const isSelected = userAnswer === letter;
                const isCorrectAnswer = letter === correctLetter;
                
                let optionClass = 'option';
                let optionStyle = '';
                
                if (isSelected && isCorrectAnswer) {
                    optionClass += ' correct'; // 选对了
                    optionStyle = 'background:#4CAF50;color:white;border-color:#4CAF50;';
                } else if (isSelected && !isCorrectAnswer) {
                    optionClass += ' wrong'; // 选错了
                    optionStyle = 'background:#f44336;color:white;border-color:#f44336;';
                } else if (!isSelected && isCorrectAnswer) {
                    optionClass += ' correct'; // 正确答案
                    optionStyle = 'border:2px solid #4CAF50;background:#e8f5e9;color:#2e7d32;';
                }
                
                optionsHtml += `
                    <div class="${optionClass}" style="${optionStyle}cursor:default;">
                        <span class="option-letter">${letter}.</span>
                        <span class="option-text">${text}</span>
                    </div>
                `;
            }
        } else {
            for (const [letter, text] of Object.entries(q.options)) {
                const isSelected = userAnswer.includes(letter);
                const isCorrectAnswer = q.answer.includes(letter);
                
                let optionClass = 'option';
                let optionStyle = '';
                
                if (isSelected && isCorrectAnswer) {
                    optionClass += ' correct'; // 选对了
                } else if (isSelected && !isCorrectAnswer) {
                    optionClass += ' wrong'; // 选错了
                } else if (!isSelected && isCorrectAnswer) {
                    optionClass += ' correct'; // 正确答案
                    optionStyle = 'border:2px solid #4CAF50;background:#e8f5e9;';
                }
                
                optionsHtml += `
                    <div class="${optionClass}" style="${optionStyle}cursor:default;">
                        <span class="option-letter">${letter}.</span>
                        <span class="option-text">${text}</span>
                    </div>
                `;
            }
        }
        
        // 状态标识
        let statusIcon = isCorrect ? '✅' : (isUnanswered ? '⚪' : '❌');
        let statusText = isCorrect ? '正确' : (isUnanswered ? '未答' : '错误');
        let statusColor = isCorrect ? '#4CAF50' : (isUnanswered ? '#999' : '#f44336');
        let borderColor = isCorrect ? '#4CAF50' : (isUnanswered ? '#ccc' : '#f44336');
        
        html += `
            <div style="background:white;border:2px solid ${borderColor};border-radius:10px;padding:15px;margin-bottom:15px;box-shadow:0 2px 10px rgba(0,0,0,0.05);">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid #eee;">
                    <div style="display:flex;align-items:center;">
                        <span style="font-size:1.5em;margin-right:10px;">${statusIcon}</span>
                        <span style="font-weight:bold;color:#333;">第${index + 1}题（${q.type}）</span>
                    </div>
                    <span style="color:${statusColor};font-weight:bold;font-size:0.95em;">
                        ${statusText}
                    </span>
                </div>
                <div style="color:#333;margin-bottom:15px;line-height:1.6;font-size:1.05em;">${q.content}</div>
                <div style="margin:15px 0;">${optionsHtml}</div>
                ${!isCorrect ? `
                    <div style="background:#f9f9f9;padding:12px;border-radius:8px;margin-top:15px;border-left:4px solid ${isUnanswered ? '#f44336' : '#4CAF50'};">
                        ${isUnanswered ? `
                            <div style="color:#f44336;font-weight:bold;margin-bottom:5px;">⚠️ 本题未作答</div>
                            <div style="color:#2e7d32;font-weight:bold;">✅ 正确答案：${q.answer}</div>
                        ` : `
                            <div style="color:#2e7d32;font-weight:bold;margin-bottom:5px;">✅ 正确答案：${q.answer}</div>
                            <div style="color:#f44336;">❌ 你的答案：${userAnswer || '未答'}</div>
                        `}
                    </div>
                ` : `
                    <div style="background:#e8f5e9;padding:12px;border-radius:8px;margin-top:15px;border-left:4px solid #4CAF50;">
                        <div style="color:#2e7d32;font-weight:bold;">✅ 你的答案：${userAnswer}（回答正确）</div>
                    </div>
                `}
            </div>
        `;
    });
    
    html += '</div>';
    document.getElementById('questionContainer').innerHTML = html;
}

// 显示学习记录
async function showRecords() {
    showPage('recordsPage');
    loadExamRecords();
}

// 加载考试记录
async function loadExamRecords() {
    try {
        const response = await fetch('/api/student/exams');
        const result = await response.json();
        
        const container = document.getElementById('examRecordsList');
        
        if (result.success && result.exams.length > 0) {
            let html = '';
            result.exams.slice(0, 20).forEach((exam, index) => {
                const date = exam.createdAt.split('T')[0];
                const time = exam.createdAt.split('T')[1].split('.')[0];
                const rate = (exam.correctCount / exam.totalCount * 100).toFixed(1);
                
                html += `
                    <div class="record-item">
                        <div><strong>第${index + 1}次考试</strong> - ${date} ${time}</div>
                        <div style="margin-top:5px;">分数：<strong>${exam.score}分</strong> | 正确：${exam.correctCount}/${exam.totalCount} (${rate}%) | 用时：${Math.floor(exam.timeUsed/60)}分${exam.timeUsed%60}秒</div>
                        <div style="margin-top:5px;font-size:0.8em;color:#666;">
                            单选题：${exam.stats.single.correct}/${exam.stats.single.total} | 
                            多选题：${exam.stats.multi.correct}/${exam.stats.multi.total} | 
                            判断题：${exam.stats.judge.correct}/${exam.stats.judge.total}
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div style="text-align:center;color:#666;padding:20px;">暂无考试记录</div>';
        }
    } catch (e) {
        console.error('加载记录失败:', e);
        document.getElementById('examRecordsList').innerHTML = '加载失败';
    }
}

// 显示错题集
async function showWrongBook() {
    showPage('wrongBookPage');
    
    try {
        const response = await fetch('/api/student/wrong');
        const result = await response.json();
        
        const container = document.getElementById('wrongBookList');
        
        if (result.success && result.questions && result.questions.length > 0) {
            let html = `<div style="color:#666;margin-bottom:15px;font-size:0.9em;">📚 共 ${result.total} 道错题</div>`;
            
            result.questions.forEach((q, index) => {
                html += `
                    <div style="background:white;border:2px solid #f44336;border-radius:10px;padding:15px;margin-bottom:15px;">
                        <div style="display:flex;align-items:center;margin-bottom:10px;">
                            <span style="font-size:1.5em;margin-right:10px;">❌</span>
                            <span style="font-weight:bold;color:#333;">第${index + 1}题（${q.type}）</span>
                        </div>
                        <div style="color:#333;margin-bottom:10px;font-size:1.05em;line-height:1.6;">${q.content}</div>
                        <div style="background:#ffebee;padding:12px;border-radius:8px;margin:10px 0;">
                            <div style="color:#f44336;font-size:0.9em;margin-bottom:8px;">❌ 你的答案：错误</div>
                            <div style="color:#2e7d32;font-weight:bold;font-size:1em;">✅ 正确答案：${q.answer}</div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        } else if (result.success) {
            container.innerHTML = '<div style="text-align:center;color:#666;padding:60px 20px;"><div style="font-size:3em;margin-bottom:15px;">🎉</div><div style="font-size:1.2em;font-weight:bold;">太棒了！暂无错题</div><div style="margin-top:10px;color:#999;">继续加油，保持全对！</div></div>';
        } else {
            container.innerHTML = `<div style="text-align:center;color:#f44336;padding:40px;">❌ ${result.message || '加载失败'}</div>`;
        }
    } catch (e) {
        console.error('加载错题集失败:', e);
        document.getElementById('wrongBookList').innerHTML = '<div style="text-align:center;color:#f44336;padding:40px;">❌ 加载失败，请刷新页面重试</div>';
    }
}

// 清空错题集
async function clearWrongBook() {
    if (!confirm('确定要清空错题集吗？清空后无法恢复！')) {
        return;
    }
    
    try {
        const response = await fetch('/api/student/wrong/clear', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ 错题集已清空');
            showWrongBook(); // 重新加载
        } else {
            alert(result.message);
        }
    } catch (e) {
        alert('操作失败，请重试');
    }
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

// ============== 题库浏览功能 ==============

// 显示题库浏览
function showQuestionBrowser() {
    showPage('browserPage');
    // 先初始化题组选择器
    initPageSelector();
    loadQuestions();
}

// 初始化题组选择器
async function initPageSelector() {
    const selector = document.getElementById('filterPage');
    selector.innerHTML = '<option value="1">加载中...</option>';
    
    try {
        // 获取总题数
        const response = await fetch('/api/questions/browse?page=1&type=all');
        const result = await response.json();
        
        if (result.success) {
            const totalPages = result.total_pages;
            const total = result.total;
            
            selector.innerHTML = '';
            for (let i = 1; i <= totalPages; i++) {
                const startNum = (i - 1) * 100 + 1;
                const endNum = Math.min(i * 100, total);
                const option = document.createElement('option');
                option.value = i;
                option.textContent = `第${i}组 (${startNum}-${endNum}题)`;
                selector.appendChild(option);
            }
        }
    } catch (e) {
        selector.innerHTML = '<option value="1">第 1 组</option>';
    }
}

// 处理关键字搜索
function handleKeywordSearch(event) {
    if (event.key === 'Enter') {
        loadQuestions();
    }
}

// 处理题号搜索
function handleIdSearch(event) {
    if (event.key === 'Enter') {
        loadQuestions();
    }
}

// 重置筛选
function resetFilters() {
    document.getElementById('filterType').value = 'all';
    document.getElementById('filterKeyword').value = '';
    document.getElementById('filterId').value = '';
    document.getElementById('jumpToId').value = '';
    document.getElementById('filterPage').value = '1';
    loadQuestions();
}

// 跳转到指定题号
async function jumpToQuestion() {
    const targetId = document.getElementById('jumpToId').value.trim();
    
    if (!targetId) {
        alert('请输入题号！');
        return;
    }
    
    // 先尝试在当前页查找
    const qItem = document.getElementById(`qitem-${targetId}`);
    if (qItem) {
        qItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        qItem.style.boxShadow = '0 0 20px rgba(102, 126, 234, 0.5)';
        setTimeout(() => {
            qItem.style.boxShadow = '';
        }, 2000);
        return;
    }
    
    // 不在当前页，查询该题号属于哪一组
    try {
        const response = await fetch(`/api/questions/browse?id=${targetId}`);
        const result = await response.json();
        
        if (result.success && result.questions.length > 0) {
            // 找到题目，计算在哪一组
            const q = result.questions[0];
            const targetPage = Math.floor((parseInt(q.id) - 1) / 100) + 1;
            
            // 切换到对应组
            document.getElementById('filterPage').value = targetPage;
            await loadQuestions();
            
            // 滚动到该题目
            const qItem = document.getElementById(`qitem-${targetId}`);
            if (qItem) {
                qItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                qItem.style.boxShadow = '0 0 20px rgba(102, 126, 234, 0.5)';
                setTimeout(() => {
                    qItem.style.boxShadow = '';
                }, 2000);
            }
        } else {
            alert(`未找到题号为 ${targetId} 的题目`);
        }
    } catch (e) {
        alert('跳转失败，请重试');
    }
}

// 加载题库列表
async function loadQuestions() {
    const page = document.getElementById('filterPage').value;
    const type = document.getElementById('filterType').value;
    const keyword = document.getElementById('filterKeyword').value;
    const questionId = document.getElementById('filterId').value;
    
    const container = document.getElementById('questionsList');
    container.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const params = new URLSearchParams();
        params.append('page', page);
        if (type !== 'all') params.append('type', type);
        if (keyword) params.append('keyword', keyword);
        if (questionId) params.append('id', questionId);
        
        const response = await fetch(`/api/questions/browse?${params.toString()}`);
        const result = await response.json();
        
        if (result.success) {
            // 更新题组选择器
            updatePageSelector(result.total_pages, result.page, result.total);
            
            // 更新总数显示
            const startNum = (result.page - 1) * result.page_size + 1;
            const endNum = Math.min(result.page * result.page_size, result.total);
            document.getElementById('questionTotal').textContent = `共 ${result.total} 题 | 第 ${result.page}/${result.total_pages} 组 (${startNum}-${endNum})`;
            
            if (result.questions.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:#666;padding:40px;">暂无题目</div>';
                return;
            }
            
            let html = '';
            result.questions.forEach(q => {
                const hasOptions = q.options && Object.keys(q.options).length > 0;
                const optionsHtml = hasOptions ? renderQuestionOptions(q) : renderJudgeOptions(q);
                
                html += `
                    <div class="question-item" id="qitem-${q.id}">
                        <div class="question-header">
                            <span class="question-id">第 ${q.id} 题</span>
                            <span class="question-type-badge ${q.type}">${q.type}</span>
                        </div>
                        <div class="question-content">${q.content}</div>
                        <div class="question-options">
                            ${optionsHtml}
                        </div>
                        <button class="toggle-answer-btn" onclick="toggleAnswer('${q.id}')" data-answer="${q.answer}">👁️ 显示答案</button>
                        <div class="answer-section" id="answer-${q.id}" style="display:none;"></div>
                    </div>
                `;
            });
            container.innerHTML = html;
        } else {
            container.innerHTML = '加载失败';
        }
    } catch (e) {
        console.error('加载题库失败:', e);
        container.innerHTML = '加载失败';
    }
}

// 更新题组选择器
function updatePageSelector(totalPages, currentPage, total) {
    const selector = document.getElementById('filterPage');
    
    // 如果选项数量变化，重新生成
    if (selector.options.length !== totalPages) {
        selector.innerHTML = '';
        for (let i = 1; i <= totalPages; i++) {
            const startNum = (i - 1) * 100 + 1;
            const endNum = Math.min(i * 100, total);
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `第${i}组 (${startNum}-${endNum}题)`;
            selector.appendChild(option);
        }
    }
    
    selector.value = currentPage;
}

// 渲染选项（单选/多选）
function renderQuestionOptions(q) {
    let html = '';
    for (const [letter, text] of Object.entries(q.options)) {
        html += `
            <div class="option-row">
                <span class="option-letter">${letter}.</span>
                <span>${text}</span>
            </div>
        `;
    }
    return html;
}

// 渲染判断题选项
function renderJudgeOptions(q) {
    return `
        <div class="option-row">
            <span class="option-letter">A.</span>
            <span>正确</span>
        </div>
        <div class="option-row">
            <span class="option-letter">B.</span>
            <span>错误</span>
        </div>
    `;
}

// 切换答案显示
function toggleAnswer(questionId) {
    const answerDiv = document.getElementById(`answer-${questionId}`);
    const btn = answerDiv.previousElementSibling;
    
    if (answerDiv.style.display === 'none' || answerDiv.style.display === '') {
        // 显示答案 - 从当前题目元素获取答案
        const qItem = document.getElementById(`qitem-${questionId}`);
        const typeBadge = qItem.querySelector('.question-type-badge');
        const qType = typeBadge ? typeBadge.textContent : '';
        
        // 从按钮的 data 属性获取答案（需要在渲染时添加）
        const answer = btn.getAttribute('data-answer');
        
        if (answer) {
            if (qType === '判断题') {
                answerDiv.innerHTML = `✅ 正确答案：${answer}`;
            } else if (qType === '多选题') {
                answerDiv.innerHTML = `✅ 正确答案：${answer.split('').join('、')}`;
            } else {
                answerDiv.innerHTML = `✅ 正确答案：${answer}`;
            }
            
            answerDiv.style.display = 'block';
            btn.textContent = '🙈 隐藏答案';
        } else {
            alert('答案加载失败，请刷新页面');
        }
    } else {
        // 隐藏答案
        answerDiv.style.display = 'none';
        answerDiv.innerHTML = '';
        btn.textContent = '👁️ 显示答案';
    }
}
