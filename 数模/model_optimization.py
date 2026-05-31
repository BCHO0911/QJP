"""
模型优化：针对论文5个主要不足进行求解优化
=========================================================
优化1: 中介效应模型（痰湿体质→活动能力/BMI→高血脂）
优化2: GradientBoosting早停+正则化
优化3: Sigmoid平台期下降率
优化4: 干预措施协同效应
优化5: 依从性Monte Carlo模拟
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import f1_score, accuracy_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(42)
N = 1000

# ============================================================
# 模拟数据生成（复现原始论文数据特征）
# ============================================================
constitutions = np.random.choice(range(1,10), size=N,
    p=[0.187,0.090,0.073,0.086,0.278,0.077,0.079,0.073,0.057])

T = np.zeros(N)
for i in range(N):
    if constitutions[i]==5: T[i]=np.random.normal(60,15)
    elif constitutions[i]==2: T[i]=np.random.normal(45,18)
    else: T[i]=np.random.normal(35,20)
T = np.clip(T,0,100)

A = np.clip(70 - 0.3*T + np.random.normal(0,12,N), 0,100)
TC = np.clip(4.0+0.008*T+np.random.normal(0,1.0,N), 1.5,9.2)
TG = np.clip(1.2+0.012*T+np.random.normal(0,0.7,N), 0.3,8.5)
LDL = np.clip(2.5+0.006*T+np.random.normal(0,0.7,N), 0.8,6.1)
HDL = np.clip(1.4-0.002*T+np.random.normal(0,0.25,N), 0.55,2.3)
BMI = np.clip(22+0.03*T+np.random.normal(0,3.0,N), 15.8,35.2)
Glucose = np.clip(5.0+0.003*T+np.random.normal(0,1.2,N), 3.0,12.0)
UA = np.clip(350+0.5*T+np.random.normal(0,80,N), 100,600)

N_abn = np.zeros(N,dtype=int)
N_abn += (TC<3.1)|(TC>6.2)
N_abn += (TG<0.56)|(TG>1.7)
N_abn += (LDL<2.07)|(LDL>3.1)
N_abn += (HDL<1.04)|(HDL>1.55)

risk_score = 2.0*N_abn + 0.02*T - 0.01*A + 0.05*BMI - 0.01*T*A/100
prob = 1/(1+np.exp(-(risk_score-2.5)))
Y = (np.random.random(N)<prob).astype(int)

age_group = np.random.choice(range(1,6), size=N, p=[0.20,0.22,0.20,0.20,0.18])

tanshi_mask = (constitutions==5)

print("="*70)
print("模型优化：针对论文5个主要不足")
print("="*70)

# ============================================================
# 优化1：中介效应模型
# ============================================================
print("\n【优化1】中介效应模型")
print("-"*50)

# Step 1: 总效应
c_model = LogisticRegression()
c_model.fit(T.reshape(-1,1), Y)
c_total = c_model.coef_[0][0]

# Step 2: T→中介变量A和BMI
a_model_A = np.polyfit(T, A, 1)
a_A = a_model_A[0]
a_model_BMI = np.polyfit(T, BMI, 1)
a_BMI = a_model_BMI[0]

# Step 3: 控制中介后的直接效应
cb_model = LogisticRegression()
X_med = np.column_stack([T, A, BMI])
cb_model.fit(X_med, Y)
c_direct = cb_model.coef_[0][0]
b_A = cb_model.coef_[0][1]
b_BMI = cb_model.coef_[0][2]

# 间接效应
indirect_A = a_A * b_A
indirect_BMI = a_BMI * b_BMI
total_indirect = indirect_A + indirect_BMI
mediation_ratio = abs(total_indirect)/(abs(c_direct)+abs(total_indirect))*100

# Bootstrap Sobel检验
n_boot = 5000
ab_samples = np.zeros(n_boot)
for b in range(n_boot):
    idx = np.random.choice(N, N, replace=True)
    a_b = np.polyfit(T[idx], A[idx], 1)
    cb_b = LogisticRegression(max_iter=1000)
    cb_b.fit(np.column_stack([T[idx], A[idx]]), Y[idx])
    ab_samples[b] = a_b[0]*cb_b.coef_[0][1]

sobel_se = np.std(ab_samples)
sobel_z = total_indirect/sobel_se
sobel_p = 2*(1-stats.norm.cdf(abs(sobel_z)))

print(f"总效应 c = {c_total:.4f}")
print(f"通过活动能力: a×b = {indirect_A:.4f}")
print(f"通过BMI: a×b = {indirect_BMI:.4f}")
print(f"直接效应 c' = {c_direct:.4f}")
print(f"中介效应占比 = {mediation_ratio:.1f}%")
print(f"Sobel检验: z={sobel_z:.3f}, p={sobel_p:.4f}")

# 绘图
fig, axes = plt.subplots(1,2,figsize=(14,5))
ax=axes[0]
ax.hist(ab_samples, bins=50, alpha=0.7, color='steelblue', edgecolor='white')
ax.axvline(x=0, color='red', linestyle='--', alpha=0.8)
ax.axvline(x=total_indirect, color='green', linewidth=2, label=f'间接效应={total_indirect:.4f}')
ax.set_xlabel('间接效应 a×b')
ax.set_ylabel('频次')
ax.set_title(f'中介效应Bootstrap分布\n(z={sobel_z:.3f}, p={sobel_p:.4f})')
ax.legend()

ax=axes[1]
node_style = dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8)
ax.set_xlim(-1,4); ax.set_ylim(-1,3); ax.axis('off')
ax.text(0.5,2.5,'痰湿体质(T)',ha='center',va='center',bbox=node_style,fontsize=11)
ax.text(3.5,2.5,'高血脂(Y)',ha='center',va='center',bbox=dict(boxstyle='round,pad=0.5',facecolor='lightcoral',alpha=0.8),fontsize=11)
ax.text(0.5,0.5,'活动能力(A)',ha='center',va='center',bbox=dict(boxstyle='round,pad=0.5',facecolor='lightgreen',alpha=0.8),fontsize=11)
ax.text(3.5,0.5,'BMI',ha='center',va='center',bbox=dict(boxstyle='round,pad=0.5',facecolor='lightgreen',alpha=0.8),fontsize=11)
ax.annotate(f"c'={c_direct:.3f}",xy=(2.8,2.5),xytext=(1.3,2.5),arrowprops=dict(arrowstyle='->',lw=1.5,color='red'),ha='center',va='bottom',fontsize=10)
ax.annotate(f"a={a_A:.3f}",xy=(0.5,2.0),xytext=(0.5,1.2),arrowprops=dict(arrowstyle='->',lw=1.5,color='green'),ha='center',va='center',fontsize=10)
ax.annotate(f"b={b_A:.3f}",xy=(2.8,0.5),xytext=(1.3,0.5),arrowprops=dict(arrowstyle='->',lw=1.5,color='blue'),ha='center',va='bottom',fontsize=10)
ax.set_title('中介效应路径图')
plt.tight_layout()
plt.savefig('figures/mediation_analysis.png',dpi=300,bbox_inches='tight')
plt.close()
print("  → figures/mediation_analysis.png")


# ============================================================
# 优化2：GradientBoosting早停+正则化
# ============================================================
print("\n【优化2】GradientBoosting早停+正则化")
print("-"*50)

features = ['T','A','N_abn','TC','TG','LDL','HDL','BMI','Glucose','UA']
X = np.column_stack([T,A,N_abn,TC,TG,LDL,HDL,BMI,Glucose,UA])
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 原模型
gb_orig = GradientBoostingClassifier(n_estimators=150,max_depth=5,learning_rate=0.1,random_state=42)
cv_orig = cross_val_score(gb_orig, X_scaled, Y, cv=5, scoring='f1_macro')
gb_orig.fit(X_scaled, Y)
train_acc_orig = accuracy_score(Y, gb_orig.predict(X_scaled))

# 优化模型
gb_opt = GradientBoostingClassifier(
    n_estimators=500, max_depth=4, learning_rate=0.05,
    subsample=0.8,
    min_samples_leaf=5, min_samples_split=10,
    max_features=0.8,
    validation_fraction=0.15, n_iter_no_change=15, tol=1e-4,
    random_state=42
)
cv_opt = cross_val_score(gb_opt, X_scaled, Y, cv=5, scoring='f1_macro')
gb_opt.fit(X_scaled, Y)
train_acc_opt = accuracy_score(Y, gb_opt.predict(X_scaled))
actual_trees = getattr(gb_opt, 'n_estimators_', gb_opt.n_estimators)

print(f"原模型: 训练准确率={train_acc_orig:.4f}, CV F1={cv_orig.mean():.4f}±{cv_orig.std():.4f}, 过拟合差值={train_acc_orig-cv_orig.mean():.4f}")
print(f"优化模型: 训练准确率={train_acc_opt:.4f}, CV F1={cv_opt.mean():.4f}±{cv_opt.std():.4f}, 实际树数={actual_trees}")
print(f"过拟合降低: {(train_acc_orig-cv_orig.mean())-(train_acc_opt-cv_opt.mean()):.4f}")

# 绘图
fig,axes = plt.subplots(1,2,figsize=(12,5))
x_pos=np.arange(10)
fi_orig = gb_orig.feature_importances_
fi_opt = gb_opt.feature_importances_
ax=axes[0]
width=0.35
ax.barh(x_pos-width/2, fi_orig[::-1], width, label='原模型(n=150)', alpha=0.8, color='steelblue')
ax.barh(x_pos+width/2, fi_opt[::-1], width, label='优化(早停+正则)', alpha=0.8, color='coral')
ax.set_yticks(x_pos)
ax.set_yticklabels([f[::-1] for f in features[::-1]])
ax.set_xlabel('特征重要性')
ax.set_title('优化前后特征重要性对比')
ax.legend()
ax.grid(True,alpha=0.3,axis='x')

ax=axes[1]
models = ['原模型','优化模型']
cv_means = [cv_orig.mean(), cv_opt.mean()]
cv_stds = [cv_orig.std(), cv_opt.std()]
bars = ax.bar(models, cv_means, yerr=cv_stds, capsize=10, color=['steelblue','coral'], alpha=0.8)
ax.set_ylabel('5折CV F1 Macro')
ax.set_title('交叉验证对比')
ax.set_ylim(0.6,0.8)
for bar,val in zip(bars,cv_means):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005, f'{val:.4f}', ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig('figures/gb_optimization.png',dpi=300,bbox_inches='tight')
plt.close()
print("  → figures/gb_optimization.png")


# ============================================================
# 优化3+4：Sigmoid平台期 + 协同效应
# ============================================================
print("\n【优化3】Sigmoid平台期下降率模型")
print("【优化4】干预措施协同效应")
print("-"*50)

def original_decay_rate(K, n):
    return 0.03*K + max(0, n-5)*0.01

def sigmoid_decay(t, K, n, k=0.8, t_mid=4.0):
    r_max = original_decay_rate(K, n)
    return r_max/(1+np.exp(k*(t-t_mid)))

def synergistic_decay(t, K, n, L, gamma=0.10, k=0.8, t_mid=4.0):
    r_max = original_decay_rate(K, n)
    synergy = 1.0 + gamma*(1 if L>=2 else 0)*(1 if K>=2 else 0)
    return r_max*synergy/(1+np.exp(k*(t-t_mid)))

months = np.arange(0,7)
T0 = 64.0

# 场景1：原模型
r1 = original_decay_rate(1, 10)
T1 = [T0]
for t in range(1,7): T1.append(T1[-1]*(1-r1))

# 场景2：Sigmoid
T2 = [T0]
for t in range(1,7): T2.append(T2[-1]*(1-sigmoid_decay(t,1,10)))

# 场景3：Sigmoid+协同(K=1, 无协同)
T3 = [T0]
for t in range(1,7): T3.append(T3[-1]*(1-synergistic_decay(t,1,10,3)))

# 场景4：Sigmoid+协同(K=2, 有协同)
T4 = [T0]
for t in range(1,7): T4.append(T4[-1]*(1-synergistic_decay(t,2,10,3,gamma=0.10)))

print(f"样本1下降曲线对比(T0=64, L=3, K=1/2, n=10次/周):")
print(f"{'月份':>4} | {'原模型':>8} | {'Sigmoid':>8} | {'协同K=1':>8} | {'协同K=2':>8}")
print("-"*52)
for t in range(7): print(f"{t:>4} | {T1[t]:>8.1f} | {T2[t]:>8.1f} | {T3[t]:>8.1f} | {T4[t]:>8.1f}")

print(f"\n6个月终值: 原={T1[6]:.1f}(↓{T1[0]-T1[6]:.1f}), Sigmoid={T2[6]:.1f}(↓{T2[0]-T2[6]:.1f}), 协同K=2={T4[6]:.1f}(↓{T4[0]-T4[6]:.1f})")

# 绘图
fig,axes = plt.subplots(1,2,figsize=(14,5))
ax=axes[0]
ax.plot(months, T1, 'o-', label='原模型(恒定率)', color='steelblue', linewidth=2)
ax.plot(months, T2, 's--', label='Sigmoid平台期', color='coral', linewidth=2)
ax.plot(months, T3, '^-', label='Sigmoid+协同(K=1)', color='green', linewidth=2)
ax.plot(months, T4, 'd--', label='Sigmoid+协同(K=2,γ=0.10)', color='purple', linewidth=2)
ax.set_xlabel('月份'); ax.set_ylabel('痰湿积分')
ax.set_title('痰湿积分下降曲线对比（样本1）'); ax.legend(); ax.grid(True,alpha=0.3); ax.set_xticks(months)

ax=axes[1]
r_orig = [original_decay_rate(1,10)]*6
r_sig = [sigmoid_decay(t,1,10) for t in range(1,7)]
r_syn = [synergistic_decay(t,1,10,3) for t in range(1,7)]
r_syn2 = [synergistic_decay(t,2,10,3,gamma=0.10) for t in range(1,7)]
mr = np.arange(1,7)
ax.plot(mr, r_orig, 'o-', label='原模型(恒定)', color='steelblue', linewidth=2)
ax.plot(mr, r_sig, 's--', label='Sigmoid平台期', color='coral', linewidth=2)
ax.plot(mr, r_syn, '^-', label='Sigmoid+协同(K=1)', color='green', linewidth=2)
ax.plot(mr, r_syn2, 'd--', label='Sigmoid+协同(K=2)', color='purple', linewidth=2)
ax.set_xlabel('月份'); ax.set_ylabel('月度下降率')
ax.set_title('月度下降率变化'); ax.legend(); ax.grid(True,alpha=0.3); ax.set_xticks(mr)
plt.tight_layout()
plt.savefig('figures/decay_model_comparison.png',dpi=300,bbox_inches='tight')
plt.close()
print("  → figures/decay_model_comparison.png")


# ============================================================
# 优化5：依从性Monte Carlo模拟
# ============================================================
print("\n【优化5】依从性Monte Carlo模拟")
print("-"*50)

alpha_c, beta_c = 8.0, 3.0
N_SIM = 10000

def mc_simulate(T0, L, K, n, n_sim=N_SIM, gamma=0.10):
    final_T = np.zeros(n_sim)
    for s in range(n_sim):
        p_comp = np.random.beta(alpha_c, beta_c)
        n_actual = np.random.binomial(n, p_comp)
        T_cur = T0
        for t in range(1,7):
            r_t = synergistic_decay(t, K, n_actual, L, gamma)
            T_cur *= (1-r_t)
        final_T[s] = T_cur
    return final_T

samples = [
    {'id':1,'T0':64.0,'L':3,'K':1,'n':10},
    {'id':2,'T0':58.0,'L':1,'K':2,'n':1},
    {'id':3,'T0':59.0,'L':2,'K':3,'n':1},
]

print(f"依从性分布: Beta({alpha_c},{beta_c}), 均值={alpha_c/(alpha_c+beta_c):.1%}")
print(f"{'样本':>4} | {'原预测':>8} | {'MC均值':>8} | {'MC中位数':>8} | {'95%CI下限':>10} | {'95%CI上限':>10} | {'达标率':>6}")
print("-"*72)

mc_results = []
for s in samples:
    final_T = mc_simulate(s['T0'], s['L'], s['K'], s['n'])
    T_pred = s['T0']
    for t in range(1,7): T_pred *= (1-synergistic_decay(t,s['K'],s['n'],s['L'],gamma=0.10))
    ci_low = np.percentile(final_T, 2.5)
    ci_high = np.percentile(final_T, 97.5)
    median = np.median(final_T)
    mean = np.mean(final_T)
    target = s['T0'] - 15
    success_rate = (final_T <= target).mean()*100
    mc_results.append({'id':s['id'],'T0':s['T0'],'original':T_pred,'mean':mean,'median':median,'ci_low':ci_low,'ci_high':ci_high,'success_rate':success_rate})
    print(f"S{s['id']:>2} | {T_pred:>8.1f} | {mean:>8.1f} | {median:>8.1f} | {ci_low:>10.1f} | {ci_high:>10.1f} | {success_rate:>5.1f}%")

# 绘图
fig,axes = plt.subplots(2,2,figsize=(14,10))
ax=axes[0,0]
p_comp_s = np.random.beta(alpha_c, beta_c, 10000)
ax.hist(p_comp_s, bins=50, alpha=0.7, color='steelblue', edgecolor='white')
ax.axvline(x=np.mean(p_comp_s), color='red', linestyle='--', label=f'均值={np.mean(p_comp_s):.1%}')
ax.set_xlabel('个体依从性概率'); ax.set_ylabel('频次')
ax.set_title(f'依从性分布 Beta({alpha_c},{beta_c})'); ax.legend(); ax.grid(True,alpha=0.3)

ax=axes[0,1]
ft1 = mc_simulate(64.0, 3, 1, 10)
ax.hist(ft1, bins=50, alpha=0.7, color='coral', edgecolor='white')
ax.axvline(x=64.0, color='gray', linestyle='--', label='初始64.0')
ax.axvline(x=np.mean(ft1), color='red', label=f'MC均值={np.mean(ft1):.1f}')
ax.axvline(x=np.percentile(ft1,2.5), color='green', linestyle=':', label='95%CI')
ax.axvline(x=np.percentile(ft1,97.5), color='green', linestyle=':')
ax.axvline(x=64-15, color='purple', linestyle='-.', label='达标线(49.0)')
ax.set_xlabel('6个月后痰湿积分'); ax.set_ylabel('频次')
ax.set_title('样本1 Monte Carlo分布'); ax.legend(); ax.grid(True,alpha=0.3)

ax=axes[1,0]
sl = [f"样本{r['id']}" for r in mc_results]
ml = [r['mean'] for r in mc_results]
cl = np.array([r['ci_low'] for r in mc_results])
ch = np.array([r['ci_high'] for r in mc_results])
xp = np.arange(3)
yerr_lower = np.maximum(0.1, ml-cl)
yerr_upper = np.maximum(0.1, ch-ml)
ax.errorbar(xp, ml, yerr=[yerr_lower, yerr_upper], fmt='o', capsize=8, markersize=10, color='steelblue', linewidth=2)
ax.set_xticks(xp); ax.set_xticklabels(sl); ax.set_ylabel('6个月后痰湿积分')
ax.set_title('MC模拟结果对比(95%CI)'); ax.grid(True,alpha=0.3,axis='y')
for i,r in enumerate(mc_results): ax.text(i,r['mean']+1.5,f'{r["mean"]:.1f}',ha='center',fontweight='bold')

ax=axes[1,1]
sr = [r['success_rate'] for r in mc_results]
cols = ['green' if s>70 else 'orange' if s>50 else 'red' for s in sr]
bars = ax.bar(sl, sr, color=cols, alpha=0.8, edgecolor='white')
ax.set_ylabel('达标率(%)'); ax.set_title('下降≥15分概率(依从性调整后)')
ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5); ax.set_ylim(0,100)
ax.grid(True,alpha=0.3,axis='y')
for bar,val in zip(bars,sr): ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f'{val:.1f}%', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('figures/monte_carlo_compliance.png',dpi=300,bbox_inches='tight')
plt.close()
print("  → figures/monte_carlo_compliance.png")

# ============================================================
# 汇总
# ============================================================
print("\n"+"="*70)
print("优化结果汇总")
print("="*70)
print(f"\n【优化1】中介效应: 间接效应={total_indirect:.4f}, 中介占比={mediation_ratio:.1f}%, Sobel z={sobel_z:.3f}, p={sobel_p:.4f}")
print(f"【优化2】GB优化: 树数150→{actual_trees}, 过拟合差值 {train_acc_orig-cv_orig.mean():.4f} → {train_acc_opt-cv_opt.mean():.4f}")
print(f"【优化3】Sigmoid终值: 原{T1[6]:.1f} → {T2[6]:.1f}（更保守估计）")
print(f"【优化4】协同效应: K=1→2终值 {T3[6]:.1f} → {T4[6]:.1f}（增效{ T3[6]-T4[6]:.1f}分）")
print(f"【优化5】MC依从性: 样本1原预测{T_pred:.1f}, MC均值{mc_results[0]['mean']:.1f}, 达标率{mc_results[0]['success_rate']:.1f}%")
print("\n全部优化完成！图表已保存至 figures/ 目录")
