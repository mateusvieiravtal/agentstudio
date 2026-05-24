import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── Canvas ────────────────────────────────────────────────────────────────────
BG = '#0D1117'
fig = plt.figure(figsize=(24, 30), facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
ax.set_xlim(0, 24)
ax.set_ylim(0, 30)
ax.axis('off')

# ── Helpers ───────────────────────────────────────────────────────────────────
def box(x, y, w, h, fc, label='', sub='', fs=9, tc='white', ec='white',
        lw=1.2, alpha=1.0, z=3):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08',
                        facecolor=fc, edgecolor=ec, linewidth=lw,
                        alpha=alpha, zorder=z)
    ax.add_patch(p)
    if sub:
        ax.text(x+w/2, y+h*0.64, label, ha='center', va='center',
                fontsize=fs, fontweight='bold', color=tc, zorder=z+1)
        ax.text(x+w/2, y+h*0.28, sub, ha='center', va='center',
                fontsize=max(fs-1.5, 6.5), color=tc, alpha=0.82, zorder=z+1)
    else:
        ax.text(x+w/2, y+h/2, label, ha='center', va='center',
                fontsize=fs, fontweight='bold', color=tc, zorder=z+1)

def layer_bg(x, y, w, h, fc, ec, lw=2, z=1):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.12',
                        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z)
    ax.add_patch(p)

def header(x, y, w, label, fc, fs=9):
    box(x, y, w, 0.38, fc, label=label, fs=fs, ec=fc)

def divider(x, y, w, color='#30363D'):
    ax.plot([x, x+w], [y, y], color=color, lw=0.8, zorder=4)

def tag(x, y, label, color):
    ax.text(x, y, label, ha='center', va='center', fontsize=6.5,
            fontweight='bold', color=color, rotation=90,
            bbox=dict(boxstyle='round,pad=0.25', facecolor=color,
                      alpha=0.15, edgecolor=color, linewidth=0.8))

def arrow(x1, y1, x2, y2, color='#484F58', lw=1.4):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=lw, mutation_scale=12), zorder=6)

def double_arrow(x, y1, y2, color='#484F58'):
    arrow(x, y1, x, y2, color)
    arrow(x, y2, x, y1, color)

# ═════════════════════════════════════════════════════════════════════════════
# TITLE
# ═════════════════════════════════════════════════════════════════════════════
ax.text(12, 29.45, 'AgentStudio', ha='center', fontsize=28,
        fontweight='bold', color='white')
ax.text(12, 28.85, 'Digital Squads — Agent Architecture (GCP)', ha='center',
        fontsize=13, color='#8B949E')

# ═════════════════════════════════════════════════════════════════════════════
# LAYER UI — Human Interface  (y 27.2 – 28.5)
# ═════════════════════════════════════════════════════════════════════════════
L = 27.2; H = 1.1; X0 = 0.8; W = 22.4
layer_bg(X0, L, W, H, '#161B22', '#58A6FF')
header(X0, L+0.72, W, 'HUMAN INTERFACE', '#1F6FEB', 8.5)
box(X0+0.3, L+0.08, 7.8, 0.55, '#1F6FEB',
    label='AgentStudio Canvas  (Pipeline Editor + Visual Studio)', fs=8.5)
box(X0+9.0, L+0.08, 6.2, 0.55, '#0D4A9E',
    label='HITL Gates  (Approve · Review · Redirect)', fs=8.5)
box(X0+16.2, L+0.08, 5.9, 0.55, '#0D4A9E',
    label='Observability UI  (Traces · Costs · Behavior)', fs=8.5)
tag(X0-0.3, L+0.55, 'UI', '#58A6FF')

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 7 — Orchestration  (y 24.7 – 26.9)
# ═════════════════════════════════════════════════════════════════════════════
L = 24.7; H = 2.2
layer_bg(X0, L, W, H, '#161B22', '#3FB950')
header(X0, L+1.82, W, 'LAYER 7 — ORCHESTRATION', '#238636', 8.5)
box(X0+0.3, L+0.12, 7.0, 1.55, '#238636',
    label='Squad Manager', sub='Decomposes goals · Assigns agents\nMonitors progress · Resolves conflicts', fs=9)
box(X0+8.3, L+0.12, 7.0, 1.55, '#196127',
    label='Planner Agent', sub='Task decomposition · Dependency graph\nResource estimation', fs=9)
box(X0+16.3, L+0.12, 5.8, 1.55, '#196127',
    label='Task Router', sub='Skill matching · Load balancing\nPriority queue', fs=9)
tag(X0-0.3, L+1.1, 'ORCH', '#3FB950')

# arrows UI ↔ Orch
double_arrow(12, 27.2, 26.9, '#3FB950')

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 6 — Digital Squad  (y 21.5 – 24.4)
# ═════════════════════════════════════════════════════════════════════════════
L = 21.5; H = 2.65
layer_bg(X0, L, W, H, '#161B22', '#D2A8FF')
header(X0, L+2.27, W, 'LAYER 6 — DIGITAL SQUAD  (Software Factory)', '#6E40C9', 8.5)

squad = [
    ('PM', '#6E40C9'),
    ('Architect', '#5A32A3'),
    ('Backend\nEngineer', '#5A32A3'),
    ('Frontend\nEngineer', '#5A32A3'),
    ('QA\nEngineer', '#5A32A3'),
    ('Security\nReviewer', '#5A32A3'),
    ('DevOps\nEngineer', '#5A32A3'),
    ('Tech\nWriter', '#5A32A3'),
]
sw = (W - 0.6) / len(squad)
for i, (name, color) in enumerate(squad):
    box(X0+0.3+i*sw, L+0.15, sw-0.15, 1.95, color, label=name, fs=8.5)
tag(X0-0.3, L+1.3, 'SQUAD', '#D2A8FF')

double_arrow(12, 24.7, 24.4, '#D2A8FF')

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 5 — A2A Communication Bus  (y 20.1 – 21.2)
# ═════════════════════════════════════════════════════════════════════════════
L = 20.1; H = 1.1
layer_bg(X0, L, W, H, '#1C1600', '#FFA657', lw=2.5)
header(X0, L+0.72, W, 'LAYER 5 — A2A COMMUNICATION BUS  (Google A2A Protocol)', '#9E5F1A', 8.5)
box(X0+0.3, L+0.08, 6.8, 0.55, '#9E5F1A',
    label='Pub/Sub  (async broadcast · fan-out)', fs=8.5)
box(X0+8.1, L+0.08, 7.0, 0.55, '#7A4A14',
    label='Cloud Tasks  (guaranteed delivery · retry · DLQ)', fs=8.5)
box(X0+16.1, L+0.08, 6.0, 0.55, '#7A4A14',
    label='Direct HTTP / gRPC  (sync sub-calls)', fs=8.5)
tag(X0-0.3, L+0.55, 'A2A', '#FFA657')

double_arrow(12, 21.5, 21.2, '#FFA657')

# ═════════════════════════════════════════════════════════════════════════════
# CORE SERVICES  (y 11.4 – 19.8)  — 3 columns
# ═════════════════════════════════════════════════════════════════════════════
CY = 11.4; CH = 8.4
COL_W = 7.0

# ── LEFT: Memory ─────────────────────────────────────────────────────────────
MX = X0
layer_bg(MX, CY, COL_W, CH, '#161B22', '#BC8CFF')
header(MX, CY+8.02, COL_W, 'LAYER 2 — MEMORY', '#553098', 8.5)

box(MX+0.25, CY+6.82, COL_W-0.5, 1.0, '#553098',
    label='L1  In-Context Memory', sub='LLM context window · per agent · ~200k tokens', fs=8)
box(MX+0.25, CY+5.57, COL_W-0.5, 1.05, '#5C3AA8',
    label='L2  Working Memory', sub='Memorystore Redis · run-scoped · TTL\nshared scratchpad between agents in a run', fs=7.5)
box(MX+0.25, CY+4.2, COL_W-0.5, 1.15, '#6545B8',
    label='L3  Episodic Memory', sub='AlloyDB · past runs · decisions · outcomes\nqueryable history · audit trail', fs=7.5)
box(MX+0.25, CY+2.85, COL_W-0.5, 1.15, '#7050C8',
    label='L4  Semantic Memory', sub='AlloyDB pgvector  +  Vertex Vector Search\nembeddings · code patterns · knowledge base', fs=7.5)
box(MX+0.25, CY+1.25, COL_W-0.5, 1.35, '#7B5BD8',
    label='L5  Org / Project Context', sub='AlloyDB · shared across entire squad\norg conventions · project state · decisions made\narchitecture records · tech debt log', fs=7.5)
box(MX+0.25, CY+0.2, COL_W-0.5, 0.85, '#4A2090',
    label='Memory Manager  (read · write · TTL · scope policy)', fs=7.5)
tag(MX-0.3, CY+4.2, 'MEM', '#BC8CFF')

# ── MIDDLE: Tools + Skills ────────────────────────────────────────────────────
TX = X0 + COL_W + 0.3
layer_bg(TX, CY, COL_W+0.8, CH, '#161B22', '#FFA657')
header(TX, CY+8.02, COL_W+0.8, 'LAYERS 3 & 4 — TOOLS  +  SKILLS', '#9E5F1A', 8.5)

# Tools section
ax.text(TX+(COL_W+0.8)/2, CY+7.6, 'Tools  (external integrations via MCP)',
        ha='center', fontsize=8, color='#FFA657', fontweight='bold')

tools = [
    ('GitHub\n(code · PRs\n· issues)', '#7A4A14'),
    ('Code\nExecutor\n(sandboxed)', '#7A4A14'),
    ('Web\nSearch', '#7A4A14'),
    ('Cloud\nBuild /\nGH Actions', '#7A4A14'),
]
tcount = len(tools); tw = (COL_W+0.2) / tcount
for i, (t, c) in enumerate(tools):
    box(TX+0.3+i*tw, CY+5.8, tw-0.15, 1.55, c, label=t, fs=7.5)

box(TX+0.3, CY+4.9, COL_W+0.2, 0.7, '#9E5F1A',
    label='MCP Tool Registry  (Cloud Run · auth via Workload Identity + Secret Manager)', fs=7.5)

divider(TX+0.3, CY+4.75, COL_W+0.2)

# Skills section
ax.text(TX+(COL_W+0.8)/2, CY+4.45, 'Skills  (native Claude-like capabilities)',
        ha='center', fontsize=8, color='#FFB84D', fontweight='bold')

skills = [
    ('Deep\nReasoning\n(CoT · ReAct)', '#6B3400'),
    ('Code Gen\n+\nReview', '#6B3400'),
    ('Test\nGeneration', '#6B3400'),
    ('Doc\nSummarize\n+ Write', '#6B3400'),
]
sk_w = (COL_W+0.2) / len(skills)
for i, (s, c) in enumerate(skills):
    box(TX+0.3+i*sk_w, CY+2.85, sk_w-0.15, 1.45, c, label=s, fs=7.5)

skills2 = [
    ('Data\nAnalysis', '#4A2400'),
    ('Plan\nDecompose', '#4A2400'),
    ('Multi-modal\n(vision · audio)', '#4A2400'),
    ('Computer\nUse', '#4A2400'),
]
for i, (s, c) in enumerate(skills2):
    box(TX+0.3+i*sk_w, CY+1.6, sk_w-0.15, 1.05, c, label=s, fs=7.5)

box(TX+0.3, CY+0.75, COL_W+0.2, 0.65, '#4A2400',
    label='Skill Registry  (versioned · composable · role-bound · pluggable)', fs=7.5)
box(TX+0.3, CY+0.2, COL_W+0.2, 0.45, '#3A1800',
    label='Execution Sandbox  (Cloud Run Jobs · ephemeral · resource-capped)', fs=7.2)
tag(TX-0.3, CY+4.2, 'TOOLS\nSKILLS', '#FFA657')

# ── RIGHT: Guardrails + Observability ────────────────────────────────────────
GX = TX + COL_W + 1.1
GW = W - (GX - X0) - 0.1
layer_bg(GX, CY, GW, CH, '#161B22', '#FF7B72')
header(GX, CY+8.02, GW, 'LAYERS 7 & 8 — GUARDRAILS  +  OBSERVABILITY', '#8B1A1A', 8.5)

ax.text(GX+GW/2, CY+7.6, 'Guardrails',
        ha='center', fontsize=8, color='#FF7B72', fontweight='bold')

guards = [('Cost\nBudgets', '#8B1A1A'), ('Security\nScanner', '#8B1A1A'),
          ('Scope\nLimiter', '#8B1A1A'), ('Output\nValidator', '#8B1A1A')]
gw2 = (GW-0.5) / len(guards)
for i, (g, c) in enumerate(guards):
    box(GX+0.25+i*gw2, CY+5.8, gw2-0.12, 1.55, c, label=g, fs=7.5)

box(GX+0.25, CY+4.9, GW-0.5, 0.7, '#8B1A1A',
    label='CI/CD  (GitHub + GitHub Actions  ·  Semgrep · Bandit · ESLint)', fs=7.5)

divider(GX+0.25, CY+4.75, GW-0.5)

ax.text(GX+GW/2, CY+4.45, 'Observability',
        ha='center', fontsize=8, color='#79C0FF', fontweight='bold')

obs = [('Cloud Trace\n+ OpenTelemetry', '#0D3A5E'),
       ('Cloud\nMonitoring', '#0D3A5E'),
       ('Cloud\nLogging', '#0D3A5E'),
       ('LLMOps\nDashboard', '#0D3A5E')]
ow = (GW-0.5) / len(obs)
for i, (o, c) in enumerate(obs):
    box(GX+0.25+i*ow, CY+3.0, ow-0.12, 1.35, c, label=o, fs=7.5)

box(GX+0.25, CY+2.0, GW-0.5, 0.85, '#0D3A5E',
    label='Token cost · model latency · per-squad analytics', sub='agent behavior · hallucination rate · eval scores', fs=7.5)

box(GX+0.25, CY+1.1, GW-0.5, 0.7, '#0A2A4A',
    label='Eval + Feedback Loop  (quality metrics · ground truth)', fs=7.5)
box(GX+0.25, CY+0.2, GW-0.5, 0.7, '#07192E',
    label='Alert Policies  (Cloud Monitoring · PagerDuty)', fs=7.2)
tag(GX-0.3, CY+4.2, 'GUARD\nOBS', '#FF7B72')

double_arrow(12, 20.1, 19.8, '#FFA657')

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 1 — LLM Gateway  (y 9.5 – 11.1)
# ═════════════════════════════════════════════════════════════════════════════
L = 9.5; H = 1.6
layer_bg(X0, L, W, H, '#0D1F0D', '#56D364', lw=2.5)
header(X0, L+1.22, W, 'LAYER 1 — LLM GATEWAY', '#1A7F37', 8.5)
box(X0+0.3, L+0.1, 5.8, 0.95, '#1A7F37',
    label='LiteLLM Router', sub='cost · latency · capability · fallback chain', fs=9)
box(X0+7.1, L+0.1, 6.5, 0.95, '#1A5F2F',
    label='Vertex AI Model Garden', sub='Gemini Pro/Flash  +  Claude (partner model)', fs=9)
box(X0+14.6, L+0.1, 3.8, 0.95, '#144A24',
    label='OpenAI', sub='GPT-4o fallback', fs=8.5)
box(X0+19.3, L+0.1, 3.6, 0.95, '#144A24',
    label='Ollama', sub='local / private', fs=8.5)
tag(X0-0.3, L+0.8, 'LLM\nGW', '#56D364')

double_arrow(12, 11.4, 11.1, '#56D364')

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 0 — Agent Platform + IAM  (y 7.0 – 9.2)
# ═════════════════════════════════════════════════════════════════════════════
L = 7.0; H = 2.2
layer_bg(X0, L, W, H, '#0D1628', '#4285F4')
header(X0, L+1.82, W, 'LAYER 0 — AGENT IDENTITY & REGISTRY', '#1A56DB', 8.5)
box(X0+0.3, L+0.75, 10.5, 0.95, '#1A56DB',
    label='GCP Agent Platform  (Gemini Enterprise)',
    sub='Agent Registry · Capability Cards · A2A Discovery · native Vertex integration', fs=8.5)
box(X0+11.8, L+0.75, 10.5, 0.95, '#1347B5',
    label='Identity & Permissions',
    sub='Workload Identity per agent · Service Accounts · Secret Manager · IAM scoped', fs=8.5)
box(X0+0.3, L+0.12, 22.0, 0.5, '#0D3A9E',
    label='GCP Foundation  ·  Cloud Run  ·  Cloud Build  ·  GKE  ·  Memorystore  ·  AlloyDB  ·  Cloud Storage  ·  Pub/Sub  ·  Cloud Tasks  ·  Eventarc',
    fs=7.5)
tag(X0-0.3, L+1.1, 'L0', '#4285F4')

double_arrow(12, 9.5, 9.2, '#4285F4')

# ═════════════════════════════════════════════════════════════════════════════
# GitHub / CI-CD  (y 5.3 – 6.7)
# ═════════════════════════════════════════════════════════════════════════════
L = 5.3; H = 1.4
layer_bg(X0, L, W, H, '#161B22', '#30363D')
header(X0, L+1.02, W, 'VERSION CONTROL & CI/CD', '#30363D', 8.5)
box(X0+0.3, L+0.12, 10.5, 0.75, '#21262D',
    label='GitHub  (code · PRs · issues · code review · branch policies)', fs=8.5)
box(X0+11.8, L+0.12, 10.5, 0.75, '#21262D',
    label='GitHub Actions  (lint · test · security scan · build · deploy to GCP)', fs=8.5)

double_arrow(12, 7.0, 6.7, '#30363D')
double_arrow(12, 9.5, 9.2, '#4285F4')

# ═════════════════════════════════════════════════════════════════════════════
# Legend
# ═════════════════════════════════════════════════════════════════════════════
L = 3.5
ax.text(1.2, L+1.5, 'Architecture Principles:', fontsize=9, color='#8B949E',
        fontweight='bold')
principles = [
    '→  A2A Protocol (Google) as the standard for agent communication',
    '→  MCP (Anthropic) as the standard for tool interfaces',
    '→  LiteLLM as single LLM gateway — model-agnostic, cost-aware',
    '→  AlloyDB: unified SQL + pgvector for structured + semantic memory',
    '→  Skills (native) ≠ Tools (external)  ·  both are composable',
    '→  Every agent has an identity, a scope, and a cost budget',
]
for i, p in enumerate(principles):
    ax.text(1.5, L+1.1-i*0.3, p, fontsize=7.5, color='#8B949E')

plt.savefig('/home/user/agentstudio/architecture.png',
            dpi=150, bbox_inches='tight',
            facecolor=BG, edgecolor='none')
print("Done")
