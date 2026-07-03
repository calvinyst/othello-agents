const API_BASE = 'http://127.0.0.1:8000/api';

let gameId = null;
let eventSource = null;
let currentBoard = [];
let currentMode = 'agent_vs_agent';
let isHumanTurn = false;

// DOM Elements
const boardEl = document.getElementById('othello-board');
const btnStart = document.getElementById('btn-start');
const btnAbort = document.getElementById('btn-abort');
const statusEl = document.getElementById('game-status');
const turnEl = document.getElementById('current-turn');
const scoreBlackEl = document.getElementById('score-black');
const scoreWhiteEl = document.getElementById('score-white');
const modeSelect = document.getElementById('mode-select');
const hostSelect = document.getElementById('host-select');
const timeSlider = document.getElementById('time-slider');
const timeVal = document.getElementById('time-val');

let agentReasonings = { agent_a: {}, agent_b: {}, agent_c: {} };
let lastMoveNum = { agent_a: 0, agent_b: 0, agent_c: 0 };
let currentViewRound = 'latest';
let maxRoundNumber = 0;
let boardHistoryWhite = { 0: null }; // roundNum -> boardState after white's move
let boardHistoryBlack = { 0: null }; // roundNum -> boardState after black's move

// Stream panels
const streams = {
    agent_a: document.getElementById('stream-content-a'),
    agent_b: document.getElementById('stream-content-b'),
    agent_c: document.getElementById('stream-content-c')
};

// Initialization
function initBoard() {
    boardEl.innerHTML = '';
    for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.r = r;
            cell.dataset.c = c;
            cell.addEventListener('click', () => onCellClick(r, c));
            boardEl.appendChild(cell);
        }
    }
}

function updateBoard(boardState, previousBoard) {
    for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
            const val = boardState[r][c];
            const prevVal = previousBoard ? previousBoard[r][c] : 0;
            const idx = r * 8 + c;
            const cell = boardEl.children[idx];
            
            // Clear current piece if it changed to empty (rare in Othello)
            if (val === 0) {
                cell.innerHTML = '';
                continue;
            }
            
            // If empty before and now has piece
            if (prevVal === 0 && val !== 0) {
                const piece = document.createElement('div');
                piece.className = `piece ${val === 1 ? 'black' : 'white'}`;
                cell.innerHTML = '';
                cell.appendChild(piece);
            } 
            // If piece flipped
            else if (prevVal !== val && prevVal !== 0) {
                const piece = cell.querySelector('.piece');
                if (piece) {
                    // Trigger flip animation
                    piece.className = `piece ${val === 1 ? 'black flip-to-black' : 'white flip-to-white'}`;
                }
            }
            // Failsafe: if piece should be there but isn't, or has lost its classes
            else if (prevVal === val && val !== 0) {
                let piece = cell.querySelector('.piece');
                if (!piece) {
                    piece = document.createElement('div');
                    cell.appendChild(piece);
                }
                if (!piece.className.includes('flip')) {
                    piece.className = `piece ${val === 1 ? 'black' : 'white'}`;
                }
            }
        }
    }
    currentBoard = JSON.parse(JSON.stringify(boardState));
}

// UI Event Listeners
timeSlider.addEventListener('input', (e) => {
    timeVal.textContent = e.target.value;
});

['a', 'b', 'c'].forEach(agent => {
    document.getElementById(`toggle-agent-${agent}`).addEventListener('change', (e) => {
        const panel = document.getElementById(`panel-agent-${agent}`);
        if (e.target.checked) panel.classList.remove('hidden');
        else panel.classList.add('hidden');
    });
});

btnStart.addEventListener('click', async () => {
    const mode = document.getElementById('mode-select').value;
    const minTime = parseInt(timeSlider.value);
    const hostType = document.getElementById('host-type').value;
    const memoryLimit = document.getElementById('memory-limit').value;
    
    // Clear streams state
    agentReasonings = { agent_a: {}, agent_b: {}, agent_c: {} };
    lastMoveNum = { agent_a: 0, agent_b: 0, agent_c: 0 };
    currentViewRound = 'latest';
    maxRoundNumber = 0;
    boardHistoryWhite = { 0: null };
    boardHistoryBlack = { 0: null };
    updateSelectDropdowns(0);
    Object.values(streams).forEach(el => el.innerHTML = '');
    
    const res = await fetch(`${API_BASE}/game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            mode: mode, 
            min_move_time: minTime,
            agent_c_type: hostType,
            memory_limit: parseInt(memoryLimit)
        })
    });
    const data = await res.json();
    gameId = data.game_id;
    
    btnStart.disabled = true;
    btnAbort.disabled = false;
    statusEl.textContent = 'In Progress';
    
    initBoard();
    updateGameState(data.state);
    
    // Save the true starting board for the aux board diffing
    boardHistoryWhite[0] = JSON.parse(JSON.stringify(data.state.board));
    boardHistoryBlack[0] = JSON.parse(JSON.stringify(data.state.board));
    
    connectSSE();
    
    // Trigger first turn if agent vs agent, or if human vs agent (human is Black, so human goes first)
    if (currentMode === 'agent_vs_agent') {
        fetch(`${API_BASE}/game/${gameId}/trigger_agent`, {method: 'POST'});
    }
});

btnAbort.addEventListener('click', async () => {
    if (!gameId) return;
    await fetch(`${API_BASE}/game/${gameId}/abort`, {method: 'POST'});
    disconnectSSE();
    btnStart.disabled = false;
    btnAbort.disabled = true;
    statusEl.textContent = 'Aborted';
});

async function onCellClick(r, c) {
    if (!gameId || !isHumanTurn) return;
    
    // Try to move
    const res = await fetch(`${API_BASE}/game/${gameId}/move`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({r, c})
    });
    
    const data = await res.json();
    if (data.status === 'error') {
        // Invalid move, ignore or show subtle shake
    }
}

function updateGameState(state) {
    updateBoard(state.board, currentBoard.length ? currentBoard : null);
    scoreBlackEl.textContent = state.black_score;
    scoreWhiteEl.textContent = state.white_score;
    
    if (state.game_over) {
        statusEl.textContent = 'Game Over';
        let winnerText = state.winner === 1 ? 'Black Wins!' : (state.winner === -1 ? 'White Wins!' : 'Tie Game');
        turnEl.innerHTML = `<strong>${winnerText}</strong>`;
        btnStart.disabled = false;
        btnAbort.disabled = true;
        isHumanTurn = false;
    } else {
        const pName = state.current_player === 1 ? 'Black' : 'White';
        turnEl.textContent = `Turn: ${pName}`;
        
        if (currentMode === 'human_vs_agent' && state.current_player === 1) {
            isHumanTurn = true;
            turnEl.textContent += " (Your Turn)";
        } else {
            isHumanTurn = false;
            turnEl.textContent += " (Thinking...)";
        }
    }
}

function connectSSE() {
    if (eventSource) eventSource.close();
    eventSource = new EventSource(`${API_BASE}/game/${gameId}/stream`);
    
    eventSource.addEventListener('board_update', (e) => {
        const data = JSON.parse(e.data);
        updateGameState(data);
        updateBoard(data.board);
        
        // Save board state for the current round
        // Wait, data doesn't have move count, but we can track it
        const piecesOnBoard = data.board.flat().filter(v => v !== 0).length;
        const movesMade = piecesOnBoard - 4; // 4 starting pieces
        const roundNum = Math.ceil(movesMade / 2);
        const isBlackMove = movesMade % 2 !== 0;
        
        if (isBlackMove) {
            boardHistoryBlack[roundNum] = JSON.parse(JSON.stringify(data.board));
        } else {
            boardHistoryWhite[roundNum] = JSON.parse(JSON.stringify(data.board));
        }
    });
    
    eventSource.addEventListener('game_over', (e) => {
        const state = JSON.parse(e.data);
        updateGameState(state);
    });
    
    eventSource.addEventListener('game_aborted', () => {
        statusEl.textContent = 'Aborted';
        disconnectSSE();
        btnStart.disabled = false;
        btnAbort.disabled = true;
    });
    
    function updateStreamUI(agentId, roundNum) {
        const el = streams[agentId];
        if (el && agentReasonings[agentId][roundNum]) {
            let content = agentReasonings[agentId][roundNum];
            // Clean up fragment starts: trim whitespace and capitalize first letter
            content = content.trimStart();
            if (content.length > 0) {
                content = content.charAt(0).toUpperCase() + content.slice(1);
            }
            el.innerHTML = content;
            el.scrollTop = el.scrollHeight;
        }
    }

    const appendToStream = (agentId, delta, moveNum) => {
        if (!moveNum) return; // Ignore legacy messages
        
        const roundNum = Math.ceil(moveNum / 2);
        
        if (!agentReasonings[agentId][roundNum]) {
            agentReasonings[agentId][roundNum] = '';
        }
        
        // Add line breaks for Agent C between moves in the same round
        if (agentId === 'agent_c' && lastMoveNum[agentId] !== 0 && lastMoveNum[agentId] !== moveNum && roundNum === Math.ceil(lastMoveNum[agentId] / 2)) {
             agentReasonings[agentId][roundNum] += '\n\n';
        }
        lastMoveNum[agentId] = moveNum;
        
        agentReasonings[agentId][roundNum] += delta;
        updateSelectDropdowns(Math.max(maxRoundNumber, roundNum));
        
        if (currentViewRound === 'latest' || currentViewRound === roundNum) {
            renderStreams();
        }
    };
    
    eventSource.addEventListener('reasoning_agent_a', (e) => {
        const data = JSON.parse(e.data);
        appendToStream('agent_a', data.delta, data.move_number);
    });
    
    eventSource.addEventListener('reasoning_agent_b', (e) => {
        const data = JSON.parse(e.data);
        appendToStream('agent_b', data.delta, data.move_number);
    });
    
    eventSource.addEventListener('reasoning_agent_c', (e) => {
        const data = JSON.parse(e.data);
        appendToStream('agent_c', data.delta, data.move_number);
    });
    
    eventSource.addEventListener('conclusion_agent_a', (e) => {
        const data = JSON.parse(e.data);
        appendToStream('agent_a', data.delta, 9999); // Virtual move for conclusion
    });
    
    eventSource.addEventListener('conclusion_agent_b', (e) => {
        const data = JSON.parse(e.data);
        appendToStream('agent_b', data.delta, 9999);
    });
}

function disconnectSSE() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

function updateSelectDropdowns(maxRound) {
    if (maxRound <= maxRoundNumber && maxRound !== 0) return;
    maxRoundNumber = maxRound;

    const select = document.getElementById(`global-select`);
    if (!select) return;
    const currentVal = select.value;
    select.innerHTML = '<option value="latest">Latest</option>';
    
    // Find true max round (excluding virtual round 5000)
    let realMax = 0;
    for (let k in boardHistoryBlack) if (parseInt(k) > realMax && parseInt(k) < 5000) realMax = parseInt(k);
    for (let k in boardHistoryWhite) if (parseInt(k) > realMax && parseInt(k) < 5000) realMax = parseInt(k);
    
    const trueMaxRound = Math.max(1, realMax);
    
    if (maxRound >= 5000) {
        const opt = document.createElement('option');
        opt.value = 5000;
        opt.textContent = `🏆 Match Conclusion`;
        opt.style.fontWeight = 'bold';
        opt.style.color = '#fbbf24'; // Amber
        select.appendChild(opt);
    }
    
    for (let i = 1; i <= trueMaxRound; i += 10) {
        const end = Math.min(i + 9, Math.ceil(trueMaxRound / 10) * 10);
        const group = document.createElement('optgroup');
        group.label = `Rounds ${i}-${end}`;
        for (let j = i; j <= Math.min(end, trueMaxRound); j++) {
            const opt = document.createElement('option');
            opt.value = j;
            opt.textContent = `Round ${j}`;
            group.appendChild(opt);
        }
        select.appendChild(group);
    }
    
    // Restore if still valid
    if (currentVal === 'latest' || parseInt(currentVal) <= trueMaxRound || parseInt(currentVal) >= 5000) {
        select.value = currentVal;
    }
}

function renderStreams() {
    ['agent_a', 'agent_b', 'agent_c'].forEach(agentId => {
        const el = streams[agentId];
        if (!el) return;
        
        if (currentViewRound === 'latest') {
            let highest = 0;
            for (let r in agentReasonings[agentId]) {
                if (parseInt(r) > highest) highest = parseInt(r);
            }
            if (highest === 0) el.textContent = '';
            else el.textContent = agentReasonings[agentId][highest];
        } else {
            if (agentReasonings[agentId][currentViewRound]) {
                el.textContent = agentReasonings[agentId][currentViewRound];
            } else {
                // Determine if this agent hasn't played in this round yet, or skipped
                el.textContent = agentId !== 'agent_c' ? '(No move recorded for this round)' : '';
            }
        }
        el.scrollTop = el.scrollHeight;
    });
    
    // Update auxiliary board
    updateAuxBoard();
}

function updateAuxBoard() {
    const auxContainerBlack = document.getElementById('aux-container-black');
    const auxContainerWhite = document.getElementById('aux-container-white');
    const panelAgentC = document.getElementById('panel-agent-c');
    const auxBoardBlack = document.getElementById('aux-board-black');
    const auxBoardWhite = document.getElementById('aux-board-white');
    
    if (!auxContainerBlack || !auxContainerWhite) return;
    
    if (currentViewRound === 'latest' || currentViewRound === 5000) {
        auxContainerBlack.style.display = 'none';
        auxContainerWhite.style.display = 'none';
        if (panelAgentC) {
            if (currentViewRound === 'latest') {
                panelAgentC.style.display = 'flex';
            } else {
                panelAgentC.style.display = 'none';
            }
        }
        return;
    }
    
    // In review mode, hide agent C and show the boards
    if (panelAgentC) panelAgentC.style.display = 'none';
    auxContainerBlack.style.display = 'flex';
    auxContainerWhite.style.display = 'flex';
    
    const stateBlack = boardHistoryBlack[currentViewRound];
    const stateWhite = boardHistoryWhite[currentViewRound];
    const prevStateWhite = currentViewRound > 1 ? boardHistoryWhite[currentViewRound - 1] : boardHistoryWhite[0];
    
    // Render Black's Board
    renderMiniBoard(auxBoardBlack, stateBlack, prevStateWhite, 1);
    
    // Render White's Board
    renderMiniBoard(auxBoardWhite, stateWhite, stateBlack, -1);
}

function renderMiniBoard(container, state, prevState, highlightPlayer) {
    if (!state) {
        container.innerHTML = '<div style="color: white; padding: 20px;">No move yet.</div>';
        return;
    }
    container.innerHTML = '';
    for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            const val = state[r][c];
            if (val !== 0) {
                const piece = document.createElement('div');
                piece.className = `piece ${val === 1 ? 'black' : 'white'}`;
                
                // Highlight if it's new or flipped this move
                if (prevState && prevState[r][c] !== val) {
                    if (prevState[r][c] === 0) {
                        // Placed piece: Amber highlight
                        piece.style.boxShadow = `0 0 12px 3px #fbbf24`;
                        piece.style.border = `2px solid #fbbf24`;
                    } else {
                        // Flipped piece: Sky Blue for Black, Red for White
                        piece.style.boxShadow = `0 0 10px 3px ${highlightPlayer === 1 ? '#0ea5e9' : '#f87171'}`;
                    }
                }
                
                cell.appendChild(piece);
            }
            container.appendChild(cell);
        }
    }
}

window.navGlobal = function(action, val) {
    const select = document.getElementById(`global-select`);
    let current = select.value === 'latest' ? 'latest' : parseInt(select.value);
    
    if (action === 'first') current = maxRoundNumber > 0 ? 1 : 'latest';
    else if (action === 'last') current = 'latest';
    else if (action === 'prev') {
        if (current === 'latest') current = Math.max(1, maxRoundNumber - 1);
        else current = Math.max(1, current - 1);
        if (maxRoundNumber === 0) current = 'latest';
    }
    else if (action === 'next') {
        if (current !== 'latest') {
            current = current + 1;
            if (current >= maxRoundNumber) current = 'latest';
        }
    }
    else if (action === 'goto') {
        current = val === 'latest' ? 'latest' : parseInt(val);
    }
    
    select.value = current;
    currentViewRound = current;
    renderStreams();
};

// Initial Setup
initBoard();
